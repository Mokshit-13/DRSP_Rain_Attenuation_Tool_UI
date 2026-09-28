from __future__ import annotations

from pathlib import Path


# ==========================================================
# BACKEND IMPORTS
# ==========================================================

from data_inspector import (
    inspect_file,
    inspect_month,
    inspect_year,
    generate_observations,
    save_txt_report,
    save_excel_report,
)


# ==========================================================
# HELPERS
# ==========================================================

def _find_txt_files(
    folder: Path,
) -> list[Path]:
    """
    Return all TXT files directly inside a folder.
    """

    if not folder.exists():
        raise FileNotFoundError(
            f"Folder does not exist:\n{folder}"
        )

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Path is not a folder:\n{folder}"
        )

    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".txt"
    )


def _build_data(
    mode: str,
    source: str,
    reports: list,
) -> dict:
    """
    Builds the same data structure expected by the existing
    data_inspector report-generation functions.
    """

    return {
        "mode": mode,
        "source": source,
        "reports": reports,
    }


# ==========================================================
# SINGLE FILE
# ==========================================================

def inspect_selected_file(
    file_path: str | Path,
) -> dict:

    path = Path(
        file_path
    ).resolve()

    report = inspect_file(
        path
    )

    return _build_data(
        mode="file",
        source=path.parent.name,
        reports=[report],
    )


# ==========================================================
# SINGLE DAY
# ==========================================================

def inspect_selected_day(
    day_folder: str | Path,
) -> dict:
    """
    The original inspector does not expose a dedicated
    inspect_day() API, so the GUI adapter inspects each TXT
    file directly inside the selected day folder.
    """

    day_path = Path(
        day_folder
    ).resolve()

    txt_files = _find_txt_files(
        day_path
    )

    reports = []

    for txt_file in txt_files:

        report = inspect_file(
            txt_file
        )

        report["day_folder"] = (
            day_path.name
        )

        reports.append(
            report
        )

    return _build_data(
        mode="file",
        source=day_path.name,
        reports=reports,
    )


# ==========================================================
# SINGLE MONTH
# ==========================================================

def inspect_selected_month(
    month_folder: str | Path,
) -> dict:

    month_path = Path(
        month_folder
    ).resolve()

    reports = inspect_month(
        month_path
    )

    return _build_data(
        mode="month",
        source=month_path.name,
        reports=reports,
    )


# ==========================================================
# ENTIRE YEAR
# ==========================================================

def inspect_selected_year(
    year_folder: str | Path,
) -> dict:

    year_path = Path(
        year_folder
    ).resolve()

    reports = inspect_year(
        year_path
    )

    return _build_data(
        mode="year",
        source=year_path.name,
        reports=reports,
    )


# ==========================================================
# RUN INSPECTION
# ==========================================================

def run_inspection(
    selected_path: str | Path,
    selected_type: str,
    inspection_mode: str,
) -> dict:

    path = Path(
        selected_path
    ).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Selected path does not exist:\n{path}"
        )

    if inspection_mode == "file":

        if path.is_dir():

            # If a day folder is selected, inspect all TXT
            # files inside it.
            return inspect_selected_day(
                path
            )

        return inspect_selected_file(
            path
        )

    if inspection_mode == "day":

        return inspect_selected_day(
            path
        )

    if inspection_mode == "month":

        return inspect_selected_month(
            path
        )

    if inspection_mode == "year":

        return inspect_selected_year(
            path
        )

    raise ValueError(
        f"Unsupported inspection mode: "
        f"{inspection_mode}"
    )


# ==========================================================
# OBSERVATIONS
# ==========================================================

def get_observations(
    inspection_data: dict,
) -> list[str]:

    return generate_observations(
        inspection_data
    )


# ==========================================================
# EXPORT TXT
# ==========================================================

def export_txt(
    inspection_data: dict,
) -> Path:

    return save_txt_report(
        inspection_data
    )


# ==========================================================
# EXPORT EXCEL
# ==========================================================

def export_excel(
    inspection_data: dict,
) -> Path:

    return save_excel_report(
        inspection_data
    )


# ==========================================================
# SUMMARY
# ==========================================================

def build_summary(
    inspection_data: dict,
) -> dict:

    reports = inspection_data.get(
        "reports",
        [],
    )

    valid_reports = [
        report
        for report in reports
        if not report.get("error")
    ]

    error_reports = [
        report
        for report in reports
        if report.get("error")
    ]

    total_rows = 0
    total_size = 0

    for report in valid_reports:

        general = report.get(
            "general",
            {},
        )

        total_rows += general.get(
            "Number of Rows",
            0,
        ) or 0

        total_size += general.get(
            "File Size (bytes)",
            0,
        ) or 0

    return {
        "total_files": len(
            reports
        ),
        "valid_files": len(
            valid_reports
        ),
        "error_files": len(
            error_reports
        ),
        "total_rows": total_rows,
        "total_size": total_size,
    }