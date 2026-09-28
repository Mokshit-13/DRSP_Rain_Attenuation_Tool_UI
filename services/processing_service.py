from __future__ import annotations

from pathlib import Path


# ==========================================================
# DATASET FORMAT MAPPING
# ==========================================================

FORMAT_TO_BACKEND_MODE = {
    "NAR": "legacy",
    "NARL": "current",
}


def get_backend_dataset_mode(
    dataset_format: str,
) -> str:

    normalized = (
        str(
            dataset_format
        )
        .strip()
        .upper()
    )

    if normalized not in (
        FORMAT_TO_BACKEND_MODE
    ):

        raise ValueError(
            "Unsupported dataset format: "
            f"{dataset_format}"
        )

    return (
        FORMAT_TO_BACKEND_MODE[
            normalized
        ]
    )


def _validate_format(
    dataset_format: str,
) -> str:

    normalized = (
        str(
            dataset_format
        )
        .strip()
        .upper()
    )

    if normalized not in (
        "NAR",
        "NARL",
    ):

        raise ValueError(
            "Cannot process dataset "
            f"with format: {dataset_format}"
        )

    return normalized


# ==========================================================
# SINGLE DAY
# ==========================================================

def process_single_day(
    day_folder: str | Path,
    dataset_format: str,
) -> dict:
    """
    Single-day processing intentionally remains in the Qt main
    application because it uses the interactive Matplotlib plot.
    """

    # ------------------------------------------------------
    # These imports happen only when single-day processing
    # is requested.
    # ------------------------------------------------------

    from analysis_engine import (
        process_file,
    )

    from batch_processor import (
        create_output_directory,
        get_year,
    )

    from utils import (
        find_main_data_file,
    )

    day_path = Path(
        day_folder
    ).resolve()

    if not day_path.exists():

        raise FileNotFoundError(
            "Day folder does not exist:\n"
            f"{day_path}"
        )

    if not day_path.is_dir():

        raise NotADirectoryError(
            "Selected path is not a folder:\n"
            f"{day_path}"
        )

    dataset_format = _validate_format(
        dataset_format
    )

    backend_mode = (
        get_backend_dataset_mode(
            dataset_format
        )
    )

    month_path = (
        day_path.parent
    )

    year = get_year(
        month_path
    )

    output_dir = (
        create_output_directory(
            "Processed_Data",
            year,
            month_path.name,
            day_path.name,
        )
    )

    main_file = (
        find_main_data_file(
            day_path,
            dataset_mode=backend_mode,
        )
    )

    if main_file is None:

        raise RuntimeError(
            "No valid main NAR/NARL "
            "data file was found in:\n"
            f"{day_path}"
        )

    result = process_file(
        str(main_file),
        dataset_mode=backend_mode,
        processing_mode="single",
        verbose=False,
        output_dir=str(
            output_dir
        ),
    )

    return {
        "status": result.get(
            "status",
            "UNKNOWN",
        ),

        "mode": "single",

        "dataset_format": (
            dataset_format
        ),

        "backend_mode": (
            backend_mode
        ),

        "selected_path": (
            day_path
        ),

        "main_file": Path(
            main_file
        ),

        "output_dir": Path(
            output_dir
        ),

        "references": result.get(
            "references",
            {},
        ),

        "maximum_attenuation": result.get(
            "maximum_attenuation",
            {},
        ),

        "second_dataframe": result.get(
            "second_dataframe"
        ),

        "attenuation_dataframe": result.get(
            "attenuation_dataframe"
        ),
    }