"""
RF Spectrum Receiver Data Analyzer
====================================

Analyzes RF spectrum receiver data exported as multiple Excel files that
together form one continuous measurement session.

Each Excel file shares an identical layout:
    Column A       -> Frequency (auto-detected unit: Hz/kHz/MHz/GHz)
    Column B, C...  -> Amplitude readings, one column per timestamp sweep

Because these are raw instrument exports rather than clean tables, the
program no longer assumes row 0 is the header or that frequency is
already in MHz. Instead it inspects the first workbook and automatically
detects the header row, the row where numeric data begins, the frequency
column, and the frequency unit - see `detect_workbook_structure()` and
`detect_frequency_unit()`.

Given a target frequency, this program stitches together the amplitude
trace at that frequency across ALL Excel files in a folder (in natural
numeric order) and produces a continuous Time vs Amplitude plot, along
with summary statistics.

The data-loading layer is kept separate from the plotting layer so that
additional analyses (waterfall plots, carrier tracking, average spectrum,
peak-hold, noise floor, SNR, drift, occupied bandwidth, etc.) can reuse
the same extracted trace data without re-reading Excel files.

Author: (generated)
"""

from __future__ import annotations

import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

@dataclass
class AnalyzerConfig:
    """Configuration options for the analyzer.

    Attributes:
        folder: Path to the folder containing the Excel files.
        target_frequency_mhz: Frequency requested by the user (MHz).
        freq_tolerance_khz: Maximum acceptable difference between the
            requested frequency and the nearest available frequency,
            expressed in kHz. A warning is printed if exceeded.
        file_extensions: Excel file extensions to search for.
        debug: When True, print detailed diagnostic information (raw
            rows/columns, detected headers, frequency range, sample
            amplitudes) for the first Excel file.
    """

    folder: Path
    target_frequency_mhz: float
    freq_tolerance_khz: float = 50.0
    file_extensions: Tuple[str, ...] = (".xls", ".xlsx")
    debug: bool = False


@dataclass
class FrequencyTrace:
    """Container for a stitched-together frequency trace.

    Attributes:
        requested_frequency_mhz: The frequency the user asked for.
        selected_frequency_mhz: The nearest available frequency actually used.
        row_index: Row index (within each file) corresponding to the
            selected frequency.
        all_times: Concatenated timestamps across all files.
        all_amplitudes: Concatenated amplitude values across all files.
        files_processed: Number of Excel files successfully processed.
        files_skipped: Number of Excel files skipped due to errors.
    """

    requested_frequency_mhz: float
    selected_frequency_mhz: float
    row_index: int
    all_times: np.ndarray = field(default_factory=lambda: np.array([]))
    all_amplitudes: np.ndarray = field(default_factory=lambda: np.array([]))
    files_processed: int = 0
    files_skipped: int = 0


@dataclass
class WorkbookStructure:
    """Auto-detected layout of an instrument-exported Excel workbook.

    Instrument exports frequently do not use row 0 as the header and may
    have preamble rows (instrument metadata, blank rows, etc.) before the
    actual frequency/amplitude table begins. This structure records what
    was detected so every file in the session can be parsed consistently.

    Attributes:
        header_row: Row index (0-based, within the raw/no-header read)
            that contains the timestamp labels.
        data_start_row: Row index (0-based) where numeric frequency/
            amplitude data begins.
        freq_col: Column index containing frequency values.
        freq_unit_scale_to_mhz: Multiplier that converts the raw
            frequency column values into MHz (e.g. 1e-6 if raw values
            are in Hz).
        detected_unit_name: Human-readable name of the detected unit
            ("Hz", "kHz", "MHz", "GHz") for display/debug purposes.
        engine: The pandas/openpyxl engine actually needed to read the
            file (accounts for mislabeled .xls files that are really
            .xlsx internally).
    """

    header_row: int
    data_start_row: int
    freq_col: int
    freq_unit_scale_to_mhz: float
    detected_unit_name: str
    engine: str


# --------------------------------------------------------------------------- #
# File discovery
# --------------------------------------------------------------------------- #

def _natural_sort_key(path: Path) -> List:
    """Build a natural sort key so that '2' sorts before '10'.

    Splits the filename stem into alternating text/number chunks and
    converts numeric chunks to integers for correct ordering.
    """
    parts = re.split(r"(\d+)", path.stem)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def get_excel_files(
    folder: Path, extensions: Sequence[str] = (".xls", ".xlsx")
) -> List[Path]:
    """Find and naturally sort every Excel file in a folder.

    Args:
        folder: Directory to search (non-recursive).
        extensions: Allowed file extensions.

    Returns:
        A naturally sorted list of matching file paths.

    Raises:
        FileNotFoundError: If the folder does not exist.
        ValueError: If no matching Excel files are found.
    """
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = [
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in extensions
        and not p.name.startswith("~$")  # ignore Excel lock/temp files
    ]

    if not files:
        raise ValueError(f"No Excel files ({extensions}) found in {folder}")

    return sorted(files, key=_natural_sort_key)


# --------------------------------------------------------------------------- #
# Excel reading helpers
# --------------------------------------------------------------------------- #

def _detect_excel_engine(path: Path) -> str:
    """Detect the real underlying file format regardless of extension.

    WHY: The instrument exports have a ".xls" extension, but many such
    exports are actually Office Open XML (.xlsx) files internally (some
    instruments just don't bother naming them correctly). Trusting the
    extension causes xlrd to fail on what is really a zip/XML file.
    We instead sniff the file's magic bytes:
        - ZIP/OOXML files start with "PK\\x03\\x04" (or similar PK signature)
        - Legacy OLE2 .xls files start with the CFBF signature D0 CF 11 E0.

    Args:
        path: Path to the Excel file.

    Returns:
        "openpyxl" if the file is really XLSX/OOXML, otherwise "xlrd".
    """
    try:
        with open(path, "rb") as fh:
            header_bytes = fh.read(8)
    except OSError:
        # Fall back to extension-based guess; the actual open() call
        # later will surface any real I/O error.
        return "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"

    if header_bytes[:2] == b"PK":
        return "openpyxl"  # Real XLSX/OOXML content, regardless of extension.
    if header_bytes[:4] == b"\xd0\xcf\x11\xe0":
        return "xlrd"  # Genuine legacy OLE2 .xls content.

    # Unknown signature - fall back to extension as a last resort.
    return "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"


def _read_raw_no_header(path: Path, engine: str) -> Optional[pd.DataFrame]:
    """Read a workbook with no header assumption (all rows as data).

    Used only for structure detection, so we can inspect the raw grid
    and figure out where the real header/data rows are.
    """
    try:
        return pd.read_excel(path, header=None, engine=engine, dtype=object)
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"Could not raw-read {path.name} for structure detection: {exc}")
        return None


def detect_frequency_unit(freq_values: np.ndarray) -> Tuple[float, str]:
    """Infer whether a frequency column is stored in Hz, kHz, MHz, or GHz.

    WHY: Instrument exports store frequency in whatever native unit the
    receiver uses (often Hz), while users think/enter frequencies in MHz.
    Comparing raw values directly against MHz input caused wildly wrong
    "nearest frequency" matches (e.g. 234000000 vs 23.04). We infer the
    unit from the median magnitude of the values, since RF receiver
    sweeps realistically span single-digit MHz to a few GHz.

    Args:
        freq_values: Raw numeric frequency column values.

    Returns:
        Tuple of (scale_to_mhz, unit_name) where multiplying raw values
        by scale_to_mhz converts them into MHz.
    """
    finite_vals = freq_values[np.isfinite(freq_values)]
    if finite_vals.size == 0:
        # No way to infer - assume already MHz.
        return 1.0, "MHz (assumed)"

    median_val = float(np.median(np.abs(finite_vals)))

    if median_val >= 1e9:
        return 1e-9, "GHz-scale raw values treated as Hz->GHz"  # extremely unlikely
    if median_val >= 1e6:
        return 1e-6, "Hz"
    if median_val >= 1e3:
        return 1e-3, "kHz"
    if median_val >= 1:
        return 1.0, "MHz"
    return 1e3, "GHz"


def detect_workbook_structure(path: Path) -> WorkbookStructure:
    """Inspect one workbook and infer header row, data start row, etc.

    WHY: Instrument exports often have preamble rows (metadata, blank
    rows, merged title cells) before the real frequency/amplitude table
    starts, and the timestamp row is not necessarily row 0. Rather than
    hardcoding row numbers, we scan the raw grid and find:
      - The first row where column 0 begins a long run of increasing
        numeric values -> this is `data_start_row`, and column 0 is
        treated as the frequency column.
      - The row immediately above it -> treated as `header_row`
        (expected to hold the timestamp labels).

    Args:
        path: Path to the reference Excel file.

    Returns:
        A populated WorkbookStructure.

    Raises:
        ValueError: If no plausible numeric frequency column can be found.
    """
    engine = _detect_excel_engine(path)
    raw = _read_raw_no_header(path, engine)
    if raw is None or raw.empty:
        raise ValueError(f"Unable to inspect workbook structure for {path}")

    freq_col = 0
    col_values = pd.to_numeric(raw.iloc[:, freq_col], errors="coerce").to_numpy()

    # Find the first row that starts a run of at least 5 consecutive
    # numeric values - this marks where the real data table begins.
    data_start_row = None
    min_run = min(5, max(1, len(col_values) - 1))
    for i in range(len(col_values) - min_run + 1):
        window = col_values[i : i + min_run]
        if np.all(np.isfinite(window)):
            data_start_row = i
            break

    if data_start_row is None:
        raise ValueError(
            f"Could not detect a numeric frequency column in {path.name}. "
            "Workbook layout may be incompatible."
        )

    header_row = data_start_row - 1 if data_start_row > 0 else 0

    freq_values_mhz_raw = pd.to_numeric(
        raw.iloc[data_start_row:, freq_col], errors="coerce"
    ).to_numpy()
    scale_to_mhz, unit_name = detect_frequency_unit(freq_values_mhz_raw)

    return WorkbookStructure(
        header_row=header_row,
        data_start_row=data_start_row,
        freq_col=freq_col,
        freq_unit_scale_to_mhz=scale_to_mhz,
        detected_unit_name=unit_name,
        engine=engine,
    )


def _read_excel_safely(
    path: Path, structure: Optional[WorkbookStructure] = None
) -> Optional[pd.DataFrame]:
    """Read an Excel file, returning None (with a warning) on failure.

    Handles missing files, corrupted files, and empty files gracefully.

    Args:
        path: Path to the Excel file.
        structure: Previously detected WorkbookStructure (from the
            reference file). When provided, the file is read using the
            detected header row and real engine, instead of naively
            trusting row 0 / the file extension.
    """
    if not path.exists():
        warnings.warn(f"Missing file skipped: {path.name}")
        return None

    engine = structure.engine if structure is not None else _detect_excel_engine(path)
    header_row = structure.header_row if structure is not None else 0

    try:
        df = pd.read_excel(path, engine=engine, header=header_row)
    except Exception as exc:  # noqa: BLE001 - we want to catch *any* read error
        warnings.warn(f"Corrupted/unreadable file skipped: {path.name} ({exc})")
        return None

    if df is None or df.empty or df.shape[1] < 2:
        warnings.warn(f"Empty or malformed file skipped: {path.name}")
        return None

    return df


# --------------------------------------------------------------------------- #
# Frequency lookup
# --------------------------------------------------------------------------- #

def find_nearest_frequency(
    first_file: Path,
    target_frequency_mhz: float,
    structure: WorkbookStructure,
) -> Tuple[float, int, np.ndarray]:
    """Locate the nearest available frequency in the reference (first) file.

    Args:
        first_file: Path to the first Excel file (used as the frequency
            reference axis, since all files share the same axis).
        target_frequency_mhz: The frequency the user wants to analyze.
        structure: Auto-detected WorkbookStructure (header row, freq
            column, unit scale) for this measurement session.

    Returns:
        Tuple of (selected_frequency_mhz, row_index, full_frequency_array_mhz).
        `row_index` is relative to the parsed (header-applied) DataFrame,
        i.e. it directly indexes into `df.iloc[row_index]` for every file.

    Raises:
        ValueError: If the file is empty or has no frequency column.
    """
    df = _read_excel_safely(first_file, structure)
    if df is None or df.empty:
        raise ValueError(f"Reference file is empty or unreadable: {first_file}")

    freq_col_name = df.columns[structure.freq_col]
    raw_frequencies = pd.to_numeric(df[freq_col_name], errors="coerce").to_numpy()

    # Convert to MHz using the auto-detected unit scale. This is the core
    # fix for the Hz-vs-MHz comparison bug: everything is normalized to
    # MHz *before* any distance/nearest-value comparison happens.
    frequencies_mhz = raw_frequencies * structure.freq_unit_scale_to_mhz

    if np.all(np.isnan(frequencies_mhz)):
        raise ValueError(f"No valid frequency values found in {first_file}")

    # NaN-safe nearest-value search
    diffs = np.abs(frequencies_mhz - target_frequency_mhz)
    diffs[np.isnan(diffs)] = np.inf
    row_index = int(np.nanargmin(diffs))
    selected_frequency = float(frequencies_mhz[row_index])

    return selected_frequency, row_index, frequencies_mhz


# --------------------------------------------------------------------------- #
# Core extraction
# --------------------------------------------------------------------------- #

def _looks_like_pandas_placeholder(header_value: object) -> bool:
    """Check whether a column header is a pandas auto-generated placeholder.

    WHY: When pandas can't find a real header string for a column, it
    fabricates labels like "Unnamed: 5". Feeding these into
    pd.to_datetime() produced NaT plus a wall of parsing warnings. We
    detect and treat these as "not a real timestamp" up front instead.
    """
    return isinstance(header_value, str) and header_value.strip().lower().startswith(
        "unnamed:"
    )


def extract_frequency_trace(
    files: Sequence[Path],
    row_index: int,
    requested_frequency_mhz: float,
    selected_frequency_mhz: float,
    structure: WorkbookStructure,
) -> FrequencyTrace:
    """Extract and concatenate the amplitude trace at a fixed row index.

    Reads each Excel file exactly once, pulls the timestamp header row
    and the amplitude values at `row_index`, then appends them to master
    lists. Handles NaNs, duplicate timestamps, and missing/corrupted files.

    Args:
        files: Naturally sorted list of Excel file paths.
        row_index: Row index (from the reference file) to extract from
            every subsequent file.
        requested_frequency_mhz: Frequency originally requested by the user.
        selected_frequency_mhz: Nearest frequency actually being traced.
        structure: Auto-detected WorkbookStructure shared by every file
            in this session (header row, engine, frequency column/unit).

    Returns:
        A populated FrequencyTrace object.
    """
    time_chunks: List[np.ndarray] = []
    amp_chunks: List[np.ndarray] = []
    files_processed = 0
    files_skipped = 0
    seen_timestamps: set = set()

    for file_path in files:
        df = _read_excel_safely(file_path, structure)
        if df is None:
            files_skipped += 1
            continue

        if row_index >= len(df):
            warnings.warn(
                f"Row index {row_index} out of range in {file_path.name} "
                f"(only {len(df)} rows) - file skipped"
            )
            files_skipped += 1
            continue

        # Timestamps are every column header except the frequency column.
        timestamp_headers = list(df.columns[1:])
        amplitude_row = pd.to_numeric(
            df.iloc[row_index, 1:], errors="coerce"
        ).to_numpy(dtype=float)

        # WHY: previously we called pd.to_datetime() on every header,
        # including pandas-fabricated "Unnamed: N" placeholders, which
        # produced NaT plus repeated parsing warnings. Now we only
        # attempt datetime parsing on headers that don't look like
        # placeholders; anything else (or anything that still fails to
        # parse) is kept as its original string label instead of being
        # silently converted to NaT.
        real_headers_mask = np.array(
            [not _looks_like_pandas_placeholder(h) for h in timestamp_headers]
        )

        if real_headers_mask.any():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # suppress dateutil format warnings
                parsed = pd.to_datetime(
                    pd.Index(timestamp_headers), errors="coerce"
                )
            if parsed.isna().all():
                # Nothing parsed as a real datetime - use raw labels as-is,
                # falling back to sequential acquisition order downstream.
                timestamps = np.array(timestamp_headers, dtype=object)
            else:
                timestamps = parsed.to_numpy()
        else:
            # Every header is a placeholder - there is no usable timestamp
            # information in this file; fall back to sequential index
            # labels so the caller can still plot something meaningful.
            timestamps = np.array(
                [f"acq_{file_path.stem}_{i}" for i in range(len(timestamp_headers))],
                dtype=object,
            )

        # Drop duplicate timestamps (keep first occurrence) within this file
        # and across the whole session.
        keep_mask = np.ones(len(timestamps), dtype=bool)
        for i, ts in enumerate(timestamps):
            key = str(ts)
            if key in seen_timestamps:
                keep_mask[i] = False
            else:
                seen_timestamps.add(key)

        timestamps = timestamps[keep_mask]
        amplitude_row = amplitude_row[keep_mask]

        # Drop NaN amplitude entries (missing readings) while keeping arrays aligned.
        valid_mask = ~pd.isna(amplitude_row)
        timestamps = timestamps[valid_mask]
        amplitude_row = amplitude_row[valid_mask]

        if len(timestamps) == 0:
            files_skipped += 1
            continue

        time_chunks.append(timestamps)
        amp_chunks.append(amplitude_row)
        files_processed += 1

    if not time_chunks:
        raise ValueError("No valid data extracted from any Excel file.")

    all_times = np.concatenate(time_chunks)
    all_amplitudes = np.concatenate(amp_chunks)

    return FrequencyTrace(
        requested_frequency_mhz=requested_frequency_mhz,
        selected_frequency_mhz=selected_frequency_mhz,
        row_index=row_index,
        all_times=all_times,
        all_amplitudes=all_amplitudes,
        files_processed=files_processed,
        files_skipped=files_skipped,
    )


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #

def plot_trace(trace: FrequencyTrace, max_ticks: int = 20) -> None:
    """Generate a publication-quality Time vs Amplitude plot.

    Args:
        trace: The FrequencyTrace to visualize.
        max_ticks: Maximum number of x-axis tick labels to display.
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    x = trace.all_times
    y = trace.all_amplitudes

    is_datetime = np.issubdtype(np.asarray(x).dtype, np.datetime64)

    if is_datetime:
        ax.plot(x, y, color="blue", linewidth=1.2)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=max_ticks))
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    else:
        # Fallback: treat timestamps as categorical/string labels.
        indices = np.arange(len(x))
        ax.plot(indices, y, color="blue", linewidth=1.2)
        step = max(1, len(indices) // max_ticks)
        ax.set_xticks(indices[::step])
        ax.set_xticklabels([str(v) for v in x[::step]], rotation=45, ha="right")

    ax.set_xlabel("Time")
    ax.set_ylabel("Amplitude (dBm)")
    ax.set_title(f"Amplitude vs Time @ {trace.selected_frequency_mhz:.4f} MHz")
    ax.grid(True, alpha=0.4)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    plt.show()


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #

def print_statistics(trace: FrequencyTrace) -> None:
    """Print summary statistics for a frequency trace.

    Args:
        trace: The FrequencyTrace whose statistics should be printed.
    """
    amplitudes = trace.all_amplitudes
    times = trace.all_times

    print("\n----- Summary Statistics -----")
    print(f"Excel files processed : {trace.files_processed}")
    print(f"Excel files skipped   : {trace.files_skipped}")
    print(f"Selected frequency    : {trace.selected_frequency_mhz:.4f} MHz")
    print(f"Total timestamps      : {len(times)}")
    print(f"Minimum amplitude     : {np.min(amplitudes):.3f} dBm")
    print(f"Maximum amplitude     : {np.max(amplitudes):.3f} dBm")
    print(f"Mean amplitude        : {np.mean(amplitudes):.3f} dBm")
    print(f"Std deviation         : {np.std(amplitudes):.3f} dBm")
    print(f"First timestamp       : {times[0]}")
    print(f"Last timestamp        : {times[-1]}")
    print("-------------------------------\n")


# --------------------------------------------------------------------------- #
# High-level orchestration
# --------------------------------------------------------------------------- #

def print_debug_info(
    first_file: Path, structure: WorkbookStructure, frequencies_mhz: np.ndarray
) -> None:
    """Print diagnostic information to help troubleshoot new datasets.

    Args:
        first_file: The reference Excel file that was inspected.
        structure: Auto-detected WorkbookStructure.
        frequencies_mhz: Full frequency column, already converted to MHz.
    """
    engine = structure.engine
    raw = _read_raw_no_header(first_file, engine)

    print("\n===== DEBUG MODE =====")
    print(f"File inspected        : {first_file.name}")
    print(f"Detected engine       : {engine}")
    print(f"Detected header row   : {structure.header_row}")
    print(f"Detected data start   : {structure.data_start_row}")
    print(f"Detected freq column  : {structure.freq_col}")
    print(f"Detected freq unit    : {structure.detected_unit_name}")
    print(
        f"Frequency range (MHz) : {np.nanmin(frequencies_mhz):.4f} "
        f"to {np.nanmax(frequencies_mhz):.4f}"
    )

    df = _read_excel_safely(first_file, structure)
    if df is not None:
        n_timestamps = max(0, df.shape[1] - 1)
        print(f"Number of timestamps  : {n_timestamps}")
        print("Detected headers (first 10):")
        print(list(df.columns[1:11]))
        print("Sample amplitudes (first 10 rows x first 5 cols):")
        print(df.iloc[:10, :5].to_string())

    if raw is not None:
        print("\nFirst 10 raw rows / first 10 raw columns (no header applied):")
        print(raw.iloc[:10, :10].to_string())

    print("=======================\n")


def analyze(config: AnalyzerConfig) -> FrequencyTrace:
    """Run the full pipeline: discover files, find frequency, extract trace.

    This function performs data loading ONLY (no plotting), so the result
    can be reused for other analyses (waterfall, peak-hold, SNR, etc.).

    Args:
        config: AnalyzerConfig describing the folder and target frequency.

    Returns:
        The populated FrequencyTrace.
    """
    files = get_excel_files(config.folder, config.file_extensions)

    # WHY: The workbook layout (header row, frequency column, unit, real
    # file format) is inferred ONCE from the first file and then reused
    # for every subsequent file, since the problem statement guarantees
    # all files in a session share the same layout. This replaces the
    # old hardcoded "row 0 is the header, values are already MHz" logic.
    structure = detect_workbook_structure(files[0])

    print("----- Detected Workbook Structure -----")
    print(f"Detected file format     : {structure.engine}")
    print(f"Detected header row      : {structure.header_row}")
    print(f"Detected data start row  : {structure.data_start_row}")
    print(f"Detected frequency column: {structure.freq_col}")
    print(f"Detected frequency unit  : {structure.detected_unit_name}")
    print("----------------------------------------\n")

    selected_frequency, row_index, all_freqs_mhz = find_nearest_frequency(
        files[0], config.target_frequency_mhz, structure
    )

    if config.debug:
        print_debug_info(files[0], structure, all_freqs_mhz)

    diff_khz = abs(selected_frequency - config.target_frequency_mhz) * 1000.0

    print("----- Frequency Selection -----")
    print(f"Requested frequency : {config.target_frequency_mhz:.4f} MHz")
    print(f"Selected frequency  : {selected_frequency:.4f} MHz")
    print(f"Difference          : {diff_khz:.3f} kHz")

    if diff_khz > config.freq_tolerance_khz:
        print(
            f"WARNING: Frequency difference ({diff_khz:.3f} kHz) exceeds "
            f"tolerance ({config.freq_tolerance_khz:.3f} kHz)."
        )
    print("--------------------------------\n")

    trace = extract_frequency_trace(
        files=files,
        row_index=row_index,
        requested_frequency_mhz=config.target_frequency_mhz,
        selected_frequency_mhz=selected_frequency,
        structure=structure,
    )

    return trace


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """Command-line entry point.

    Prompts the user (or reads CLI args) for the data folder and the
    target frequency, runs the analysis, prints statistics, and plots
    the result.
    """
    # --- Gather inputs -----------------------------------------------------
    if len(sys.argv) >= 3:
        folder_str = sys.argv[1]
        freq_str = sys.argv[2]
        tolerance_str = sys.argv[3] if len(sys.argv) >= 4 else "50"
        debug_str = sys.argv[4] if len(sys.argv) >= 5 else "no"
    else:
        folder_str = input("Enter path to the folder containing Excel files: ").strip()
        freq_str = input("Enter target frequency in MHz (e.g. 23.04): ").strip()
        tolerance_str = input(
            "Enter frequency tolerance in kHz [default 50]: "
        ).strip() or "50"
        debug_str = input(
            "Enable debug mode? (y/N): "
        ).strip() or "no"

    try:
        folder = Path(folder_str).expanduser().resolve()
        target_frequency_mhz = float(freq_str)
        freq_tolerance_khz = float(tolerance_str)
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        return

    debug_enabled = debug_str.strip().lower() in ("y", "yes", "true", "1")

    config = AnalyzerConfig(
        folder=folder,
        target_frequency_mhz=target_frequency_mhz,
        freq_tolerance_khz=freq_tolerance_khz,
        debug=debug_enabled,
    )

    # --- Run pipeline --------------------------------------------------------
    try:
        trace = analyze(config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return

    print_statistics(trace)
    plot_trace(trace)


if __name__ == "__main__":
    main()