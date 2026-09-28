from __future__ import annotations

from pathlib import Path

from statistics_engine import (
    analyze_month,
    find_months,
    TARGET_CHANNEL,
    TOP_N,
)


# ==========================================================
# STATISTICS SERVICE
# ==========================================================

def validate_processed_year(
    year_folder: str | Path,
) -> Path:

    path = Path(
        year_folder
    ).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Processed-data folder does not exist:\n{path}"
        )

    if not path.is_dir():
        raise NotADirectoryError(
            f"Selected path is not a folder:\n{path}"
        )

    return path


def get_months(
    year_folder: str | Path,
) -> list[Path]:

    path = validate_processed_year(
        year_folder
    )

    return find_months(
        str(path)
    )


def run_statistics(
    year_folder: str | Path,
) -> dict:

    year_path = validate_processed_year(
        year_folder
    )

    month_folders = find_months(
        str(year_path)
    )

    results = []

    for month_folder in month_folders:

        top_values = analyze_month(
            month_folder
        )

        results.append(
            {
                "month": month_folder.name,
                "values": top_values,
            }
        )

    return {
        "status": "SUCCESS",
        "year": year_path.name,
        "year_path": year_path,
        "target_channel": TARGET_CHANNEL,
        "top_n": TOP_N,
        "months": results,
        "month_count": len(
            results
        ),
    }


def flatten_results(
    statistics_data: dict,
) -> list[dict]:

    rows = []

    for month_data in statistics_data.get(
        "months",
        [],
    ):

        month_name = month_data[
            "month"
        ]

        values = month_data.get(
            "values",
            [],
        )

        for rank, entry in enumerate(
            values,
            start=1,
        ):

            rows.append(
                {
                    "month": month_name,
                    "rank": rank,
                    "attenuation": entry.get(
                        "value",
                        0,
                    ),
                    "date": entry.get(
                        "date",
                        "",
                    ),
                    "time": entry.get(
                        "time",
                        "",
                    ),
                    "file": entry.get(
                        "file",
                        "",
                    ),
                }
            )

    return rows


def get_global_top_events(
    statistics_data: dict,
    limit: int = 10,
) -> list[dict]:

    rows = flatten_results(
        statistics_data
    )

    rows.sort(
        key=lambda row: row["attenuation"],
        reverse=True,
    )

    return rows[
        :limit
    ]