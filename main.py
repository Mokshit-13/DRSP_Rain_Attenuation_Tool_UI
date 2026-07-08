from tkinter import Tk
from tkinter.filedialog import askdirectory

from batch_processor import process_month


def select_dataset_mode():
    """
    Displays the dataset-type menu ONCE, at program start, and returns the
    selected mode.

    This is the single source of truth for dataset_mode. Every other
    module (batch_processor.py, utils.py, analysis_engine.py) simply
    receives this value as a parameter — the user is never asked again.

    Returns
    -------
    "current" — 2019-onwards 4-channel NARL dataset
    "legacy"  — 2017 single-channel legacy dataset
    None      — user chose to exit
    """
    while True:
        print("=" * 57)
        print("DRSP Rain Attenuation Tool")
        print("=" * 57)
        print()
        print("Select Dataset Type")
        print()
        print("1. New Dataset (2019 onwards)")
        print("2. Old Dataset")
        print("0. Exit")
        print()
        print("=" * 57)

        choice = input("Enter Choice : ").strip()

        if choice == "1":
            return "current"
        elif choice == "2":
            return "legacy"
        elif choice == "0":
            return None
        else:
            print("\nInvalid choice. Please enter 1, 2, or 0.\n")


def select_month_folder():

    root = Tk()
    root.withdraw()

    folder = askdirectory(
        title="Select Month Folder"
    )

    root.destroy()

    return folder


def main():

    dataset_mode = select_dataset_mode()

    if dataset_mode is None:
        print("Exiting.")
        return

    month_folder = select_month_folder()

    if not month_folder:
        print("No folder selected.")
        return

    process_month(month_folder, dataset_mode=dataset_mode)


if __name__ == "__main__":
    main()