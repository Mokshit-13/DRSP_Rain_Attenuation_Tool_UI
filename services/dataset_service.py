from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# ==========================================================
# FILE PATTERNS
# ==========================================================

NARL_MAIN_PATTERN = re.compile(
    r"^NARL_\d{1,2}_\d{1,2}_\d{4}$",
    re.IGNORECASE,
)

NAR_MAIN_PATTERN = re.compile(
    r"^NAR_\d{1,2}_\d{1,2}_\d{4}$",
    re.IGNORECASE,
)

NARL_F_PATTERN = re.compile(
    r"^NARL_F_",
    re.IGNORECASE,
)

NARL_N_PATTERN = re.compile(
    r"^NARL_N_",
    re.IGNORECASE,
)

NAR_F_PATTERN = re.compile(
    r"^NAR_F_",
    re.IGNORECASE,
)

NAR_N_PATTERN = re.compile(
    r"^NAR_N_",
    re.IGNORECASE,
)


# ==========================================================
# DATA CLASSES
# ==========================================================

@dataclass
class DayFolderInfo:
    path: Path
    is_rain_day: bool
    dataset_format: str

    main_files: list[Path]
    f_files: list[Path]
    n_files: list[Path]
    summary_files: list[Path]
    plot_files: list[Path]
    other_files: list[Path]


@dataclass
class DatasetSummary:
    root: Path
    dataset_format: str

    month_count: int
    day_count: int
    rain_day_count: int

    main_file_count: int
    f_file_count: int
    n_file_count: int

    summary_file_count: int
    plot_file_count: int


# ==========================================================
# RAIN DAY DETECTION
# ==========================================================

def is_rain_day_folder(folder_name: str) -> bool:
    """
    Detect folders such as:

        12042021 1Hz R
        14042021 1Hz R

    The folder is considered a rain day when its name ends
    with a standalone 'R'.
    """

    return bool(
        re.search(
            r"\bR\s*$",
            folder_name,
            re.IGNORECASE,
        )
    )


# ==========================================================
# FILE CLASSIFICATION
# ==========================================================

def classify_file(
    file_path: Path,
    dataset_mode: str = "auto",
) -> str:
    """
    Classify a file as:

        main
        f
        n
        summary
        plot
        other

    dataset_mode:
        auto
        narl
        nar

    Uses file_path.stem for the main-file patterns so the
    logic is independent of whether Windows displays .txt.
    """

    name = file_path.stem

    # ------------------------------------------------------
    # MAIN DATA FILE
    # ------------------------------------------------------

    if dataset_mode in ("auto", "narl"):

        if NARL_MAIN_PATTERN.match(name):
            return "main"

    if dataset_mode in ("auto", "nar"):

        if NAR_MAIN_PATTERN.match(name):
            return "main"

    # ------------------------------------------------------
    # F CHANNEL
    # ------------------------------------------------------

    if dataset_mode in ("auto", "narl"):

        if NARL_F_PATTERN.match(name):
            return "f"

    if dataset_mode in ("auto", "nar"):

        if NAR_F_PATTERN.match(name):
            return "f"

    # ------------------------------------------------------
    # N CHANNEL
    # ------------------------------------------------------

    if dataset_mode in ("auto", "narl"):

        if NARL_N_PATTERN.match(name):
            return "n"

    if dataset_mode in ("auto", "nar"):

        if NAR_N_PATTERN.match(name):
            return "n"

    # ------------------------------------------------------
    # SUMMARY FILE
    # ------------------------------------------------------

    if "summary" in name.lower():
        return "summary"

    # ------------------------------------------------------
    # PLOT FILE
    # ------------------------------------------------------

    if file_path.suffix.lower() == ".png":
        return "plot"

    return "other"


# ==========================================================
# DAY FORMAT DETECTION
# ==========================================================

def detect_day_format(
    files: list[Path],
) -> str:
    """
    Detect whether the day contains NAR or NARL main data.
    """

    has_narl = any(
        NARL_MAIN_PATTERN.match(file.stem)
        for file in files
    )

    has_nar = any(
        NAR_MAIN_PATTERN.match(file.stem)
        for file in files
    )

    if has_narl and has_nar:
        return "Mixed"

    if has_narl:
        return "NARL"

    if has_nar:
        return "NAR"

    return "Unknown"


# ==========================================================
# INSPECT ONE DAY FOLDER
# ==========================================================

def inspect_day_folder(
    day_folder: Path,
    dataset_mode: str = "auto",
) -> DayFolderInfo:

    main_files: list[Path] = []
    f_files: list[Path] = []
    n_files: list[Path] = []
    summary_files: list[Path] = []
    plot_files: list[Path] = []
    other_files: list[Path] = []

    try:

        files = sorted(
            item
            for item in day_folder.iterdir()
            if item.is_file()
        )

    except OSError:

        files = []

    dataset_format = detect_day_format(files)

    for file_path in files:

        category = classify_file(
            file_path,
            dataset_mode,
        )

        if category == "main":

            main_files.append(file_path)

        elif category == "f":

            f_files.append(file_path)

        elif category == "n":

            n_files.append(file_path)

        elif category == "summary":

            summary_files.append(file_path)

        elif category == "plot":

            plot_files.append(file_path)

        else:

            other_files.append(file_path)

    return DayFolderInfo(
        path=day_folder,
        is_rain_day=is_rain_day_folder(
            day_folder.name
        ),
        dataset_format=dataset_format,
        main_files=main_files,
        f_files=f_files,
        n_files=n_files,
        summary_files=summary_files,
        plot_files=plot_files,
        other_files=other_files,
    )


# ==========================================================
# DATASET FORMAT DETECTION
# ==========================================================

def detect_dataset_format(
    root: Path,
) -> str:
    """
    Scan the complete dataset tree and determine whether
    the dataset uses NAR, NARL, or mixed formats.
    """

    narl_count = 0
    nar_count = 0

    try:

        txt_files = root.rglob("*.txt")

    except OSError:

        return "Unknown"

    for path in txt_files:

        if NARL_MAIN_PATTERN.match(path.stem):

            narl_count += 1

        elif NAR_MAIN_PATTERN.match(path.stem):

            nar_count += 1

    if narl_count > 0 and nar_count > 0:
        return "Mixed"

    if narl_count > 0:
        return "NARL"

    if nar_count > 0:
        return "NAR"

    return "Unknown"


# ==========================================================
# SCAN COMPLETE DATASET
# ==========================================================

def scan_dataset_root(
    root: Path,
    dataset_mode: str = "auto",
) -> DatasetSummary:

    if not root.exists():

        raise FileNotFoundError(
            f"Dataset folder does not exist:\n{root}"
        )

    if not root.is_dir():

        raise NotADirectoryError(
            f"Selected path is not a folder:\n{root}"
        )

    # ------------------------------------------------------
    # DETERMINE FORMAT
    # ------------------------------------------------------

    if dataset_mode == "auto":

        detected_format = detect_dataset_format(root)

    elif dataset_mode == "narl":

        detected_format = "NARL"

    elif dataset_mode == "nar":

        detected_format = "NAR"

    else:

        detected_format = "Unknown"

    # ------------------------------------------------------
    # MONTH FOLDERS
    # ------------------------------------------------------

    month_folders = sorted(
        item
        for item in root.iterdir()
        if item.is_dir()
    )

    # ------------------------------------------------------
    # COUNTERS
    # ------------------------------------------------------

    day_count = 0
    rain_day_count = 0

    main_file_count = 0
    f_file_count = 0
    n_file_count = 0

    summary_file_count = 0
    plot_file_count = 0

    # ------------------------------------------------------
    # SCAN MONTHS
    # ------------------------------------------------------

    for month_folder in month_folders:

        day_folders = sorted(
            item
            for item in month_folder.iterdir()
            if item.is_dir()
        )

        for day_folder in day_folders:

            info = inspect_day_folder(
                day_folder,
                dataset_mode,
            )

            day_count += 1

            if info.is_rain_day:
                rain_day_count += 1

            main_file_count += len(
                info.main_files
            )

            f_file_count += len(
                info.f_files
            )

            n_file_count += len(
                info.n_files
            )

            summary_file_count += len(
                info.summary_files
            )

            plot_file_count += len(
                info.plot_files
            )

    return DatasetSummary(
        root=root,
        dataset_format=detected_format,

        month_count=len(
            month_folders
        ),

        day_count=day_count,

        rain_day_count=rain_day_count,

        main_file_count=main_file_count,

        f_file_count=f_file_count,

        n_file_count=n_file_count,

        summary_file_count=summary_file_count,

        plot_file_count=plot_file_count,
    )


# ==========================================================
# FIND MAIN DATA FILE
# ==========================================================

def find_main_file(
    day_folder: Path,
    dataset_mode: str = "auto",
) -> Path | None:

    info = inspect_day_folder(
        day_folder,
        dataset_mode,
    )

    if len(info.main_files) == 1:

        return info.main_files[0]

    return None