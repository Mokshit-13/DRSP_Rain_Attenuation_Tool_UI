from __future__ import annotations

from pathlib import Path
import csv

from openpyxl import Workbook
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

from exceedence_engine import (
    TARGET_CHANNELS,
    CHANNEL_UPPER_LIMITS,
    DEFAULT_UPPER_LIMIT,
    LOWER_LIMIT,
    STEP_SIZE,
    calculate_monthly_exceedance,
    build_table,
    build_table_ratio,
    detect_available_channels,
    save_report,
)


# ==========================================================
# CONSTANTS
# ==========================================================

SECONDS_PER_YEAR = 365 * 24 * 60 * 60


# ==========================================================
# VALIDATION
# ==========================================================

def validate_year_folder(
    year_folder: str | Path,
) -> Path:

    path = Path(
        year_folder
    ).resolve()

    if not path.exists():

        raise FileNotFoundError(
            f"Processed_Data year folder does not exist:\n"
            f"{path}"
        )

    if not path.is_dir():

        raise NotADirectoryError(
            f"Selected path is not a folder:\n"
            f"{path}"
        )

    return path


# ==========================================================
# CHANNEL DISCOVERY
# ==========================================================

def get_available_channels(
    year_folder: str | Path,
) -> list[str]:

    year_path = validate_year_folder(
        year_folder
    )

    detected = detect_available_channels(
        str(year_path)
    )

    # Keep only channels supported by the current engine
    supported = [
        channel
        for channel in detected
        if channel in TARGET_CHANNELS
    ]

    return supported


# ==========================================================
# EXCEEDANCE ANALYSIS
# ==========================================================

def run_exceedance_analysis(
    year_folder: str | Path,
    channel_name: str,
    progress_callback=None,
) -> dict:

    year_path = validate_year_folder(
        year_folder
    )

    if channel_name not in TARGET_CHANNELS:

        raise ValueError(
            f"Unsupported attenuation channel: "
            f"{channel_name}"
        )

    thresholds, month_labels, counts = (
        calculate_monthly_exceedance(
            str(year_path),
            channel_name,
            progress_callback=(
                progress_callback
            ),
        )
    )

    if not month_labels:

        raise RuntimeError(
            "No processed-data month folders were found "
            "for exceedance analysis."
        )

    upper_limit = (
        CHANNEL_UPPER_LIMITS.get(
            channel_name,
            DEFAULT_UPPER_LIMIT,
        )
    )

    # ------------------------------------------------------
    # Method 1
    # ------------------------------------------------------

    headers_total, rows_total = build_table(
        thresholds,
        month_labels,
        counts,
        upper_limit,
    )

    # ------------------------------------------------------
    # Method 2
    # ------------------------------------------------------

    headers_ratio, rows_ratio = (
        build_table_ratio(
            thresholds,
            month_labels,
            counts,
            upper_limit,
        )
    )

    # ------------------------------------------------------
    # Return everything
    # ------------------------------------------------------

    return {
        "status": "SUCCESS",

        "year": year_path.name,

        "year_path": year_path,

        "channel_name": channel_name,

        "target_channel": channel_name,

        "lower_limit": float(
            LOWER_LIMIT
        ),

        "upper_limit": float(
            upper_limit
        ),

        "step_size": float(
            STEP_SIZE
        ),

        "thresholds": thresholds,

        "month_labels": month_labels,

        "counts": counts,

        "threshold_count": len(
            thresholds
        ),

        "headers_total": headers_total,

        "rows_total": rows_total,

        "headers_ratio": headers_ratio,

        "rows_ratio": rows_ratio,
    }


# ==========================================================
# CURVE DATA
# ==========================================================

def build_exceedance_curve_data(
    analysis_data: dict,
    method: str = "total",
) -> tuple[list[float], list[float]]:

    thresholds = analysis_data.get(
        "thresholds",
        [],
    )

    if method == "ratio":

        rows = analysis_data.get(
            "rows_ratio",
            [],
        )

    else:

        rows = analysis_data.get(
            "rows_total",
            [],
        )

    x_values = []

    y_values = []

    for index, threshold in enumerate(
        thresholds
    ):

        x_values.append(
            float(
                threshold
            )
        )

        # Last column in both engine tables
        # is the percentage column.
        if index < len(rows):

            row = rows[index]

            if row:

                try:

                    value = float(
                        row[-1]
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    value = 0.0

            else:

                value = 0.0

        else:

            value = 0.0

        # Method 2 in the engine returns ratio,
        # not percentage, so convert to percentage.
        if method == "ratio":

            value *= 100.0

        y_values.append(
            value
        )

    return (
        x_values,
        y_values,
    )


# ==========================================================
# TXT EXPORT
# ==========================================================

def export_txt_report(
    analysis_data: dict,
    method: str = "total",
) -> Path:
    """
    Export the currently displayed exceedance table as a real TXT file.

    The output is written alongside the selected Processed_Data year folder,
    using the same method-specific subfolder names as the original engine.
    """
    year = str(analysis_data["year"])
    channel_name = str(analysis_data["channel_name"])
    year_path = Path(analysis_data["year_path"])

    if method == "ratio":
        headers = analysis_data["headers_ratio"]
        rows = analysis_data["rows_ratio"]
        folder_name = "Exceedence_by_Ratio"
        method_label = "Ratio"
    else:
        headers = analysis_data["headers_total"]
        rows = analysis_data["rows_total"]
        folder_name = "Exceedence_by_Total_Seconds"
        method_label = "Total Seconds"

    # Put the export beside the selected Processed_Data year folder.
    # Example:
    #   Processed_Data/Exceedence_by_Total_Seconds/...
    output_dir = year_path.parent / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir
        / f"Exceedance_Table_{year}_{channel_name.replace('Att_', '')}.txt"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        handle.write("DRSP Rain Attenuation Tool\n")
        handle.write("Exceedance Analysis Report\n")
        handle.write("=" * 80 + "\n")
        handle.write(f"Year: {year}\n")
        handle.write(f"Channel: {channel_name}\n")
        handle.write(f"Method: {method_label}\n")
        handle.write(
            f"Lower Limit (dB): {analysis_data.get('lower_limit', 0):.2f}\n"
        )
        handle.write(
            f"Upper Limit (dB): {analysis_data.get('upper_limit', 0):.2f}\n"
        )
        handle.write(
            f"Step Size (dB): {analysis_data.get('step_size', 0):.2f}\n"
        )
        handle.write("=" * 80 + "\n\n")

        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
        )

        display_headers = []
        for header in headers:
            if header == "Lower Limit":
                display_headers.append("Lower Limit (dB)")
            elif header == "Upper Limit":
                display_headers.append("Upper Limit (dB)")
            else:
                display_headers.append(str(header))

        writer.writerow(display_headers)

        for row in rows:
            writer.writerow(
                [
                    "" if value is None else value
                    for value in row
                ]
            )

    return output_path


# ==========================================================
# EXCEL EXPORT
# ==========================================================

def export_excel_report(
    analysis_data: dict,
    method: str = "total",
) -> Path:

    year = analysis_data[
        "year"
    ]

    channel_name = analysis_data[
        "channel_name"
    ]

    if method == "ratio":

        headers = analysis_data[
            "headers_ratio"
        ]

        rows = analysis_data[
            "rows_ratio"
        ]

        folder_name = (
            "Exceedence_by_Ratio"
        )

    else:

        headers = analysis_data[
            "headers_total"
        ]

        rows = analysis_data[
            "rows_total"
        ]

        folder_name = (
            "Exceedence_by_Total_Seconds"
        )

    year_path = Path(
        analysis_data["year_path"]
    )

    output_dir = (
        year_path.parent
        / folder_name
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"Exceedance_Table_{year}_{channel_name.replace('Att_', '')}.xlsx"
    )

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = (
        channel_name.replace(
            "Att_",
            "",
        )[:31]
    )

    # ------------------------------------------------------
    # STYLES
    # ------------------------------------------------------

    header_fill = PatternFill(
        "solid",
        fgColor="BDD7EE",
    )

    thin_side = Side(
        style="thin"
    )

    thin_border = Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side,
    )

    # ------------------------------------------------------
    # HEADERS
    # ------------------------------------------------------

    for column_index, header in enumerate(
        headers,
        start=1,
    ):

        if header == "Lower Limit":

            display_header = (
                "Lower Limit (dB)"
            )

        elif header == "Upper Limit":

            display_header = (
                "Upper Limit (dB)"
            )

        else:

            display_header = header

        cell = worksheet.cell(
            row=1,
            column=column_index,
            value=display_header,
        )

        cell.font = Font(
            name="Arial",
            bold=True,
            size=10,
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        cell.fill = header_fill

        cell.border = thin_border

    worksheet.freeze_panes = "A2"

    # ------------------------------------------------------
    # DATA
    # ------------------------------------------------------

    for row_index, row_data in enumerate(
        rows,
        start=2,
    ):

        for column_index, value in enumerate(
            row_data,
            start=1,
        ):

            cell_value = value

            # Threshold columns
            if column_index <= 2:

                try:

                    cell_value = float(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass

            cell = worksheet.cell(
                row=row_index,
                column=column_index,
                value=cell_value,
            )

            cell.font = Font(
                name="Arial",
                size=10,
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

            cell.border = thin_border

            if column_index <= 2:

                cell.number_format = (
                    "0.00"
                )

            elif (
                column_index
                == len(row_data)
            ):

                cell.number_format = (
                    "0.000000"
                )

    # ------------------------------------------------------
    # COLUMN WIDTHS
    # ------------------------------------------------------

    for column_index, header in enumerate(
        headers,
        start=1,
    ):

        column_letter = (
            get_column_letter(
                column_index
            )
        )

        maximum_width = len(
            str(header)
        )

        for row_index in range(
            2,
            len(rows) + 2,
        ):

            value = worksheet.cell(
                row=row_index,
                column=column_index,
            ).value

            if value is not None:

                maximum_width = max(
                    maximum_width,
                    len(
                        str(value)
                    ),
                )

        worksheet.column_dimensions[
            column_letter
        ].width = (
            maximum_width + 4
        )

    workbook.save(
        output_path
    )

    return output_path