from pathlib import Path
import re
from typing import Callable


from utils import find_main_data_file
from analysis_engine import process_file


# ==============================================================================
# PROGRESS CALLBACK TYPE
# ==============================================================================

ProgressCallback = Callable[
    [
        int,          # completed
        int,          # total
        str,          # current item
        int,          # failed
        str,          # group/month name
        str,          # status
    ],
    None,
]


def _notify_progress(
    callback: ProgressCallback | None,
    completed: int,
    total: int,
    current_item: str,
    failed: int,
    group_name: str,
    status: str,
) -> None:
    """
    Safely send progress information to an optional GUI callback.

    Existing command-line behaviour is preserved when callback is None.
    """

    if callback is None:
        return

    callback(
        completed,
        total,
        current_item,
        failed,
        group_name,
        status,
    )


# ==============================================================================
# PROGRESS DISPLAY HELPERS
# ==============================================================================

def _progress_bar(
    current: int,
    total: int,
    width: int = 28,
) -> str:
    """
    Returns a filled/empty progress bar string.

    Example:
        [████████--------------------] 8/20 (40%)
    """

    filled = (
        int(width * current / total)
        if total > 0
        else 0
    )

    bar = (
        "█" * filled
        + "-" * (width - filled)
    )

    pct = (
        int(100 * current / total)
        if total > 0
        else 0
    )

    return (
        f"[{bar}] "
        f"{current}/{total} "
        f"({pct}%)"
    )


def _date_label(
    folder_name: str,
) -> str:
    """
    Attempts to extract a DD-MM-YYYY label from the folder name.

    Supported patterns:

        NARL_14_5_2022
        2022-01-14
        14-01-2022
        14_01_2022
        02082017

    Falls back to the original folder name.
    """

    # NARL_D_M_YYYY
    match = re.search(
        r"NARL_(\d{1,2})_(\d{1,2})_(\d{4})",
        folder_name,
        re.IGNORECASE,
    )

    if match:

        return (
            f"{match.group(1).zfill(2)}-"
            f"{match.group(2).zfill(2)}-"
            f"{match.group(3)}"
        )

    # YYYY-MM-DD
    match = re.search(
        r"(\d{4})-(\d{2})-(\d{2})",
        folder_name,
    )

    if match:

        return (
            f"{match.group(3)}-"
            f"{match.group(2)}-"
            f"{match.group(1)}"
        )

    # DD-MM-YYYY / DD_MM_YYYY
    match = re.search(
        r"(\d{1,2})[-_](\d{1,2})[-_](\d{4})",
        folder_name,
    )

    if match:

        return (
            f"{match.group(1).zfill(2)}-"
            f"{match.group(2).zfill(2)}-"
            f"{match.group(3)}"
        )

    # DDMMYYYY
    match = re.search(
        r"(?<!\d)(\d{2})(\d{2})(\d{4})(?!\d)",
        folder_name,
    )

    if match:

        return (
            f"{match.group(1)}-"
            f"{match.group(2)}-"
            f"{match.group(3)}"
        )

    return folder_name


def _is_rainy_folder(
    folder_name: str,
) -> bool:
    """
    Returns True if the folder name contains a recognised
    rain-day suffix.

    Examples:

        07012020 1Hz R
        05012020 1Hz L-R
        18012020 1Hz VL-R
        02082017 R
        28052017 VL-R
    """

    name_upper = folder_name.upper()

    recognised_patterns = (
        r"\sR\s*$",
        r"\sL-R\s*$",
        r"\sVL-R\s*$",
        r"-R\s*$",
        r"-LR\s*$",
        r"-VLR\s*$",
    )

    for pattern in recognised_patterns:

        if re.search(
            pattern,
            name_upper,
        ):
            return True

    return False


def discover_rainy_day_folders(
    month_folder,
) -> list[Path]:
    """
    Returns all recognised rainy-day folders inside a month.

    This is exposed publicly so both the GUI service and the
    existing batch processor use the same rainy-day detection.
    """

    month_path = Path(
        month_folder
    )

    return sorted(
        [
            folder
            for folder in month_path.iterdir()
            if folder.is_dir()
            and _is_rainy_folder(
                folder.name
            )
        ]
    )


def get_year(
    month_folder,
) -> str:
    """
    Determines the year from the selected month folder.

    Example:

        E:/2017/august 2017

    returns:

        2017
    """

    month_path = Path(
        month_folder
    )

    parent_name = (
        month_path.parent.name
    )

    if (
        parent_name.isdigit()
        and len(parent_name) == 4
    ):

        return parent_name

    match = re.search(
        r"(\d{4})",
        month_path.name,
    )

    if match:
        return match.group(1)

    return parent_name


def create_output_directory(
    processed_data_root: str,
    year: str,
    month_name: str,
    day_folder_name: str,
) -> Path:
    """
    Creates:

        Processed_Data/
            YEAR/
                MONTH/
                    DAY/
    """

    output_dir = (
        Path(processed_data_root)
        / year
        / month_name
        / day_folder_name
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return output_dir


# ==============================================================================
# TERMINAL PROGRESS DISPLAY
# ==============================================================================

def _render_display(
    month_name: str,
    daily_folders: list,
    completed: list,
    current_label: str | None,
    total: int,
) -> str:

    done = len(
        completed
    )

    lines = []

    lines.append(
        "=" * 57
    )

    lines.append(
        "DRSP Rain Attenuation Tool"
    )

    lines.append(
        "=" * 57
    )

    lines.append("")

    lines.append(
        "Processing Month"
    )

    lines.append("")

    lines.append(
        f"  {month_name}"
    )

    lines.append("")

    lines.append(
        "Progress"
    )

    lines.append("")

    lines.append(
        f"  {_progress_bar(done, total)}"
    )

    lines.append("")

    visible_done = (
        completed[-4:]
        if len(completed) > 4
        else completed
    )

    for label in visible_done:

        lines.append(
            f"  ✓ {label}"
        )

    if current_label is not None:

        lines.append(
            f"  ⏳ {current_label}"
        )

    lines.append("")

    lines.append(
        "=" * 57
    )

    return "\n".join(
        lines
    )


def _clear_lines(
    n: int,
) -> None:
    """
    Moves the terminal cursor upward and clears lines.
    """

    for _ in range(n):

        print(
            "\033[A\033[2K",
            end="",
        )


# ==============================================================================
# PUBLIC API
# ==============================================================================

def process_month(
    month_folder,
    dataset_mode: str = "current",
    processing_mode: str = "month",
    processed_data_root: str = "Processed_Data",
    progress_callback: ProgressCallback | None = None,
):
    """
    Process all rainy-day folders in a month.

    Parameters
    ----------
    month_folder:
        Selected month folder.

    dataset_mode:
        "current" or "legacy".

    processing_mode:
        "month" or "year".

    processed_data_root:
        Root output directory.

    progress_callback:
        Optional GUI callback.

        Callback receives:

            completed
            total
            current_item
            failed
            month_name
            status

        Existing CLI behaviour remains unchanged when this
        argument is not supplied.
    """

    month_path = Path(
        month_folder
    )

    month_name = (
        month_path.name
    )

    year = get_year(
        month_path
    )

    daily_folders = sorted(
        [
            folder
            for folder in month_path.iterdir()
            if folder.is_dir()
        ]
    )

    rainy_folders = (
        discover_rainy_day_folders(
            month_path
        )
    )

    total = len(
        rainy_folders
    )

    completed = []
    failed = []

    # ------------------------------------------------------------------
    # GUI MODE
    # ------------------------------------------------------------------

    if progress_callback is not None:

        _notify_progress(
            progress_callback,
            0,
            total,
            "",
            0,
            month_name,
            "started",
        )

    # ------------------------------------------------------------------
    # CLI MODE
    # ------------------------------------------------------------------

    display = None
    last_line_count = 0

    if progress_callback is None:

        display = _render_display(
            month_name,
            daily_folders,
            completed,
            None,
            total,
        )

        print(
            display
        )

        last_line_count = (
            display.count("\n") + 1
        )

    # ------------------------------------------------------------------
    # PROCESS EACH RAINY DAY
    # ------------------------------------------------------------------

    for folder in rainy_folders:

        day_label = _date_label(
            folder.name
        )

        # --------------------------------------------------------------
        # GUI: current item
        # --------------------------------------------------------------

        if progress_callback is not None:

            _notify_progress(
                progress_callback,
                len(completed),
                total,
                day_label,
                len(failed),
                month_name,
                "processing",
            )

        # --------------------------------------------------------------
        # CLI: current item
        # --------------------------------------------------------------

        else:

            _clear_lines(
                last_line_count
            )

            display = _render_display(
                month_name,
                rainy_folders,
                completed,
                day_label,
                total,
            )

            print(
                display
            )

            last_line_count = (
                display.count("\n") + 1
            )

        # --------------------------------------------------------------
        # OUTPUT DIRECTORY
        # --------------------------------------------------------------

        output_dir = (
            create_output_directory(
                processed_data_root,
                year,
                month_name,
                folder.name,
            )
        )

        # --------------------------------------------------------------
        # LOCATE MAIN FILE
        # --------------------------------------------------------------

        main_file = (
            find_main_data_file(
                folder,
                dataset_mode=dataset_mode,
            )
        )

        # --------------------------------------------------------------
        # PROCESS DAY
        # --------------------------------------------------------------

        result = process_file(
            main_file,
            dataset_mode=dataset_mode,
            processing_mode=processing_mode,
            verbose=False,
            output_dir=str(
                output_dir
            ),
        )

        # --------------------------------------------------------------
        # RECORD RESULT
        # --------------------------------------------------------------

        if result["status"] == "SUCCESS":

            completed.append(
                day_label
            )

        else:

            failed.append(
                day_label
            )

        # --------------------------------------------------------------
        # GUI: day completed
        # --------------------------------------------------------------

        if progress_callback is not None:

            _notify_progress(
                progress_callback,
                len(completed),
                total,
                "",
                len(failed),
                month_name,
                "day_complete",
            )

        # --------------------------------------------------------------
        # CLI: refresh terminal
        # --------------------------------------------------------------

        else:

            _clear_lines(
                last_line_count
            )

            display = _render_display(
                month_name,
                rainy_folders,
                completed,
                None,
                total,
            )

            print(
                display
            )

            last_line_count = (
                display.count("\n") + 1
            )

    # ------------------------------------------------------------------
    # CLI SUMMARY
    # ------------------------------------------------------------------

    if progress_callback is None:

        _clear_lines(
            last_line_count
        )

        print(
            "=" * 57
        )

        print()

        print(
            "  Processing Complete"
        )

        print()

        print(
            f"  Year            : {year}"
        )

        print(
            f"  Month           : {month_name}"
        )

        print(
            f"  Rainy days      : {total}"
        )

        print(
            f"  Successful      : {len(completed)}"
        )

        print(
            f"  Failed          : {len(failed)}"
        )

        print()

        print(
            "=" * 57
        )

    # ------------------------------------------------------------------
    # GUI FINAL EVENT
    # ------------------------------------------------------------------

    if progress_callback is not None:

        _notify_progress(
            progress_callback,
            len(completed),
            total,
            "",
            len(failed),
            month_name,
            "finished",
        )

    # ------------------------------------------------------------------
    # RETURN SUMMARY
    # ------------------------------------------------------------------

    return {
        "status": "SUCCESS",
        "year": year,
        "month": month_name,
        "total": total,
        "successful": len(
            completed
        ),
        "failed": len(
            failed
        ),
        "completed_days": completed,
        "failed_days": failed,
    }