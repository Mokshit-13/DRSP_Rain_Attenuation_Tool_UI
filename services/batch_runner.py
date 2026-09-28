from __future__ import annotations

import multiprocessing as mp
from pathlib import Path


# ==========================================================
# BATCH PROCESS ENTRY POINT
# ==========================================================

def run_batch_process(
    mode: str,
    selected_path: str,
    dataset_format: str,
    progress_queue,
) -> None:
    """
    Entry point executed inside a completely separate Python
    process.

    IMPORTANT:
    Matplotlib is forced to use the non-GUI Agg backend BEFORE
    importing batch_processor / analysis_engine.

    This prevents Matplotlib GUI warnings when batch processing
    creates and saves figures.
    """

    try:

        # ------------------------------------------------------
        # IMPORTANT: configure Matplotlib before importing
        # analysis_engine.
        # ------------------------------------------------------

        import matplotlib

        matplotlib.use(
            "Agg",
            force=True,
        )

        # ------------------------------------------------------
        # Only now import the existing processing backend.
        # ------------------------------------------------------

        from batch_processor import (
            discover_rainy_day_folders,
            get_year,
            process_month,
        )

        from utils import (
            find_main_data_file,
        )

        # ------------------------------------------------------
        # Dataset format mapping
        # ------------------------------------------------------

        format_map = {
            "NAR": "legacy",
            "NARL": "current",
        }

        normalized_format = (
            str(dataset_format)
            .strip()
            .upper()
        )

        if normalized_format not in format_map:

            raise ValueError(
                "Unsupported dataset format: "
                f"{dataset_format}"
            )

        backend_mode = format_map[
            normalized_format
        ]

        selected = Path(
            selected_path
        ).resolve()

        # ======================================================
        # MONTH
        # ======================================================

        if mode == "month":

            _run_month(
                selected,
                backend_mode,
                progress_queue,
                process_month,
            )

            return

        # ======================================================
        # YEAR
        # ======================================================

        if mode == "year":

            _run_year(
                selected,
                backend_mode,
                progress_queue,
                process_month,
                discover_rainy_day_folders,
            )

            return

        raise ValueError(
            f"Unsupported batch mode: {mode}"
        )

    except Exception as exc:

        progress_queue.put(
            {
                "type": "error",
                "message": str(exc),
            }
        )


# ==========================================================
# MONTH
# ==========================================================

def _run_month(
    month_path: Path,
    backend_mode: str,
    progress_queue,
    process_month,
) -> None:

    def progress_callback(
        completed: int,
        total: int,
        current_item: str,
        failed: int,
        group_name: str,
        status: str,
    ):

        progress_queue.put(
            {
                "type": "progress",
                "completed": completed,
                "total": total,
                "current_item": current_item,
                "failed": failed,
                "group_name": group_name,
                "status": status,
            }
        )

    result = process_month(
        month_path,
        dataset_mode=backend_mode,
        processing_mode="month",
        processed_data_root="Processed_Data",
        progress_callback=progress_callback,
    )

    progress_queue.put(
        {
            "type": "complete",
            "result": {
                "status": "SUCCESS",
                "mode": "month",
                "month_name": month_path.name,
                "rain_day_count": result["total"],
                "successful": result["successful"],
                "failed": result["failed"],
            },
        }
    )


# ==========================================================
# YEAR
# ==========================================================

def _run_year(
    year_path: Path,
    backend_mode: str,
    progress_queue,
    process_month,
    discover_rainy_day_folders,
) -> None:

    month_folders = sorted(
        folder
        for folder in year_path.iterdir()
        if folder.is_dir()
    )

    # ------------------------------------------------------
    # Calculate total rainy days first
    # ------------------------------------------------------

    total_rain_days = 0

    month_information = []

    for month_path in month_folders:

        rainy_days = (
            discover_rainy_day_folders(
                month_path
            )
        )

        count = len(
            rainy_days
        )

        month_information.append(
            (
                month_path,
                count,
            )
        )

        total_rain_days += count

    overall_completed = 0
    overall_failed = 0

    progress_queue.put(
        {
            "type": "progress",
            "completed": 0,
            "total": total_rain_days,
            "current_item": "",
            "failed": 0,
            "group_name": year_path.name,
            "status": "started",
        }
    )

    # ------------------------------------------------------
    # Process each month
    # ------------------------------------------------------

    for month_path, month_total in month_information:

        base_completed = (
            overall_completed
        )

        base_failed = (
            overall_failed
        )

        def month_callback(
            local_completed: int,
            local_total: int,
            current_item: str,
            local_failed: int,
            group_name: str,
            status: str,
        ):

            del local_total

            progress_queue.put(
                {
                    "type": "progress",
                    "completed": (
                        base_completed
                        + local_completed
                    ),
                    "total": total_rain_days,
                    "current_item": current_item,
                    "failed": (
                        base_failed
                        + local_failed
                    ),
                    "group_name": group_name,
                    "status": status,
                }
            )

        result = process_month(
            month_path,
            dataset_mode=backend_mode,
            processing_mode="year",
            processed_data_root="Processed_Data",
            progress_callback=month_callback,
        )

        overall_completed += result[
            "successful"
        ]

        overall_failed += result[
            "failed"
        ]

    # ------------------------------------------------------
    # Complete
    # ------------------------------------------------------

    progress_queue.put(
        {
            "type": "progress",
            "completed": overall_completed,
            "total": total_rain_days,
            "current_item": "",
            "failed": overall_failed,
            "group_name": year_path.name,
            "status": "finished",
        }
    )

    progress_queue.put(
        {
            "type": "complete",
            "result": {
                "status": "SUCCESS",
                "mode": "year",
                "year": year_path.name,
                "month_count": len(
                    month_folders
                ),
                "rain_day_count": total_rain_days,
                "successful": overall_completed,
                "failed": overall_failed,
            },
        }
    )