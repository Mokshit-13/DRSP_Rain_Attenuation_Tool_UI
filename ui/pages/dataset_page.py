from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QLineEdit,
    QStyle,
)

from services.dataset_service import (
    DayFolderInfo,
    inspect_day_folder,
    scan_dataset_root,
)


class DatasetPage(QWidget):

    def __init__(self):

        super().__init__()

        self.dataset_root: Path | None = None
        self.dataset_mode = "auto"

        self.selected_path: Path | None = None
        self.selected_type: str | None = None
        self.selected_format: str | None = None

        self.setup_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            25,
            20,
            25,
            20,
        )

        main_layout.setSpacing(
            12
        )

        # ======================================================
        # HEADER
        # ======================================================

        title = QLabel(
            "Dataset Explorer"
        )

        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Explore and identify NARL beacon datasets before processing."
        )

        subtitle.setObjectName(
            "PageSubtitle"
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
        )

        # ======================================================
        # CONTROLS
        # ======================================================

        control_frame = QFrame()

        control_frame.setObjectName(
            "DatasetControl"
        )

        control_layout = QHBoxLayout(
            control_frame
        )

        root_label = QLabel(
            "Root Folder"
        )

        self.root_edit = QLineEdit()

        self.root_edit.setReadOnly(
            True
        )

        self.root_edit.setPlaceholderText(
            "Select a NARL year folder..."
        )

        browse_button = QPushButton(
            "Browse"
        )

        browse_button.clicked.connect(
            self.select_dataset_root
        )

        mode_label = QLabel(
            "Dataset Type"
        )

        self.mode_combo = QComboBox()

        self.mode_combo.addItem(
            "Auto Detect",
            "auto",
        )

        self.mode_combo.addItem(
            "NARL Format",
            "narl",
        )

        self.mode_combo.addItem(
            "NAR Format",
            "nar",
        )

        self.mode_combo.currentIndexChanged.connect(
            self.dataset_mode_changed
        )

        scan_button = QPushButton(
            "Scan"
        )

        scan_button.clicked.connect(
            self.scan_current_dataset
        )

        control_layout.addWidget(
            root_label
        )

        control_layout.addWidget(
            self.root_edit,
            stretch=1,
        )

        control_layout.addWidget(
            browse_button
        )

        control_layout.addSpacing(
            15
        )

        control_layout.addWidget(
            mode_label
        )

        control_layout.addWidget(
            self.mode_combo
        )

        control_layout.addWidget(
            scan_button
        )

        main_layout.addWidget(
            control_frame
        )

        # ======================================================
        # MAIN SPLITTER
        # ======================================================

        splitter = QSplitter(
            Qt.Horizontal
        )

        # ======================================================
        # TREE
        # ======================================================

        tree_frame = QFrame()

        tree_layout = QVBoxLayout(
            tree_frame
        )

        tree_title = QLabel(
            "Dataset Structure"
        )

        tree_title.setObjectName(
            "SectionTitle"
        )

        self.tree = QTreeWidget()

        self.tree.setHeaderLabels(
            [
                "Name",
                "Type",
            ]
        )

        self.tree.setColumnWidth(
            0,
            380,
        )

        self.tree.itemClicked.connect(
            self.tree_item_selected
        )

        tree_layout.addWidget(
            tree_title
        )

        tree_layout.addWidget(
            self.tree
        )

        # ======================================================
        # DETAILS
        # ======================================================

        details_frame = QFrame()

        details_layout = QVBoxLayout(
            details_frame
        )

        details_title = QLabel(
            "Dataset Information"
        )

        details_title.setObjectName(
            "SectionTitle"
        )

        details_layout.addWidget(
            details_title
        )

        self.details_box = QGroupBox(
            "Selection"
        )

        form = QFormLayout(
            self.details_box
        )

        self.detail_name = QLabel("-")
        self.detail_path = QLabel("-")
        self.detail_type = QLabel("-")
        self.detail_format = QLabel("-")
        self.detail_rain = QLabel("-")
        self.detail_main = QLabel("-")
        self.detail_f = QLabel("-")
        self.detail_n = QLabel("-")
        self.detail_summary = QLabel("-")
        self.detail_plots = QLabel("-")

        for label in (
            self.detail_path,
            self.detail_main,
            self.detail_f,
            self.detail_n,
        ):

            label.setWordWrap(
                True
            )

        form.addRow(
            "Name:",
            self.detail_name,
        )

        form.addRow(
            "Path:",
            self.detail_path,
        )

        form.addRow(
            "Type:",
            self.detail_type,
        )

        form.addRow(
            "Format:",
            self.detail_format,
        )

        form.addRow(
            "Rain Day:",
            self.detail_rain,
        )

        form.addRow(
            "Main Data:",
            self.detail_main,
        )

        form.addRow(
            "F Data:",
            self.detail_f,
        )

        form.addRow(
            "N Data:",
            self.detail_n,
        )

        form.addRow(
            "Summary Files:",
            self.detail_summary,
        )

        form.addRow(
            "Plot Files:",
            self.detail_plots,
        )

        details_layout.addWidget(
            self.details_box
        )

        details_layout.addStretch()

        splitter.addWidget(
            tree_frame
        )

        splitter.addWidget(
            details_frame
        )

        splitter.setSizes(
            [
                700,
                500,
            ]
        )

        main_layout.addWidget(
            splitter,
            stretch=1,
        )

        # ======================================================
        # SUMMARY
        # ======================================================

        self.summary_label = QLabel(
            "No dataset selected."
        )

        self.summary_label.setObjectName(
            "DatasetSummary"
        )

        main_layout.addWidget(
            self.summary_label
        )

    # ==========================================================
    # SELECTION
    # ==========================================================

    def clear_selection(self):

        self.selected_path = None
        self.selected_type = None
        self.selected_format = None

    def select_dataset_root(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select NARL Year Folder",
        )

        if not folder:
            return

        self.dataset_root = Path(
            folder
        )

        self.root_edit.setText(
            str(
                self.dataset_root
            )
        )

        self.clear_selection()

        self.scan_current_dataset()

    # ==========================================================
    # DATASET MODE
    # ==========================================================

    def dataset_mode_changed(self):

        self.dataset_mode = (
            self.mode_combo.currentData()
        )

        self.clear_selection()

        if self.dataset_root:

            self.scan_current_dataset()

    # ==========================================================
    # SCAN
    # ==========================================================

    def scan_current_dataset(self):

        if self.dataset_root is None:

            self.summary_label.setText(
                "Please select a dataset folder."
            )

            return

        self.tree.clear()
        self.clear_selection()

        try:

            summary = scan_dataset_root(
                self.dataset_root,
                self.dataset_mode,
            )

        except Exception as exc:

            self.summary_label.setText(
                f"Scan failed: {exc}"
            )

            return

        self.populate_tree()

        self.summary_label.setText(
            f"Format: {summary.dataset_format}"
            f"    |    Months: {summary.month_count}"
            f"    |    Days: {summary.day_count}"
            f"    |    Rain Days: {summary.rain_day_count}"
            f"    |    Main Files: {summary.main_file_count}"
            f"    |    F Files: {summary.f_file_count}"
            f"    |    N Files: {summary.n_file_count}"
            f"    |    Summary: {summary.summary_file_count}"
            f"    |    Plots: {summary.plot_file_count}"
        )

    # ==========================================================
    # TREE
    # ==========================================================

    def populate_tree(self):

        if self.dataset_root is None:
            return

        folder_icon = self.style().standardIcon(
            QStyle.SP_DirIcon
        )

        file_icon = self.style().standardIcon(
            QStyle.SP_FileIcon
        )

        # ------------------------------------------------------
        # ROOT YEAR NODE
        # ------------------------------------------------------

        root_item = QTreeWidgetItem(
            [
                self.dataset_root.name,
                "Year",
            ]
        )

        root_item.setIcon(
            0,
            folder_icon,
        )

        root_item.setData(
            0,
            Qt.UserRole,
            str(
                self.dataset_root
            ),
        )

        self.tree.addTopLevelItem(
            root_item
        )

        # ------------------------------------------------------
        # MONTHS
        # ------------------------------------------------------

        month_folders = sorted(
            path
            for path in self.dataset_root.iterdir()
            if path.is_dir()
        )

        for month_folder in month_folders:

            month_item = QTreeWidgetItem(
                [
                    month_folder.name,
                    "Month",
                ]
            )

            month_item.setIcon(
                0,
                folder_icon,
            )

            month_item.setData(
                0,
                Qt.UserRole,
                str(
                    month_folder
                ),
            )

            root_item.addChild(
                month_item
            )

            # --------------------------------------------------
            # DAYS
            # --------------------------------------------------

            day_folders = sorted(
                path
                for path in month_folder.iterdir()
                if path.is_dir()
            )

            for day_folder in day_folders:

                is_rain = self.is_rain_day(
                    day_folder.name
                )

                display_name = (
                    "[R] "
                    + day_folder.name
                    if is_rain
                    else day_folder.name
                )

                day_item = QTreeWidgetItem(
                    [
                        display_name,
                        "Rain Day"
                        if is_rain
                        else "Day",
                    ]
                )

                day_item.setIcon(
                    0,
                    folder_icon,
                )

                day_item.setData(
                    0,
                    Qt.UserRole,
                    str(
                        day_folder
                    ),
                )

                if is_rain:

                    font = day_item.font(0)

                    font.setBold(
                        True
                    )

                    day_item.setFont(
                        0,
                        font,
                    )

                month_item.addChild(
                    day_item
                )

                # ----------------------------------------------
                # FILES
                # ----------------------------------------------

                file_paths = sorted(
                    path
                    for path in day_folder.iterdir()
                    if path.is_file()
                )

                for file_path in file_paths:

                    file_item = QTreeWidgetItem(
                        [
                            file_path.name,
                            "File",
                        ]
                    )

                    file_item.setIcon(
                        0,
                        file_icon,
                    )

                    file_item.setData(
                        0,
                        Qt.UserRole,
                        str(
                            file_path
                        ),
                    )

                    day_item.addChild(
                        file_item
                    )

    # ==========================================================
    # TREE SELECTION
    # ==========================================================

    def tree_item_selected(
        self,
        item,
        column,
    ):

        del column

        path_value = item.data(
            0,
            Qt.UserRole,
        )

        if not path_value:
            return

        path = Path(
            path_value
        )

        self.detail_name.setText(
            path.name
        )

        self.detail_path.setText(
            str(
                path
            )
        )

        # ------------------------------------------------------
        # YEAR
        # ------------------------------------------------------

        if (
            self.dataset_root is not None
            and path == self.dataset_root
        ):

            self.selected_path = path
            self.selected_type = "Year Folder"

            self.selected_format = (
                self.detect_format_for_path(
                    path
                )
            )

            self.detail_type.setText(
                "Year Folder"
            )

            self.detail_format.setText(
                self.selected_format
            )

            self.detail_rain.setText(
                "-"
            )

            self.clear_file_details()

            return

        # ------------------------------------------------------
        # DIRECTORY
        # ------------------------------------------------------

        if path.is_dir():

            # --------------------------------------------------
            # MONTH
            # --------------------------------------------------

            if (
                self.dataset_root is not None
                and path.parent == self.dataset_root
            ):

                self.selected_path = path
                self.selected_type = "Month Folder"

                self.selected_format = (
                    self.detect_format_for_path(
                        path
                    )
                )

                self.detail_type.setText(
                    "Month Folder"
                )

                self.detail_format.setText(
                    self.selected_format
                )

                self.detail_rain.setText(
                    "-"
                )

                self.clear_file_details()

                return

            # --------------------------------------------------
            # DAY
            # --------------------------------------------------

            info = inspect_day_folder(
                path,
                self.dataset_mode,
            )

            self.selected_path = path
            self.selected_type = (
                "Rain Day"
                if info.is_rain_day
                else "Day"
            )

            self.selected_format = (
                info.dataset_format
            )

            self.update_day_details(
                info
            )

            return

        # ------------------------------------------------------
        # FILE
        # ------------------------------------------------------

        self.selected_path = path
        self.selected_type = "File"
        self.selected_format = None

        self.detail_type.setText(
            "Data File"
        )

        self.detail_format.setText(
            "-"
        )

        self.detail_rain.setText(
            "-"
        )

        self.clear_file_details()

    # ==========================================================
    # FORMAT DETECTION
    # ==========================================================

    @staticmethod
    def detect_format_for_path(
        path: Path,
    ) -> str:

        from services.dataset_service import (
            detect_dataset_format,
        )

        return detect_dataset_format(
            path
        )

    # ==========================================================
    # DAY DETAILS
    # ==========================================================

    def update_day_details(
        self,
        info: DayFolderInfo,
    ):

        self.detail_type.setText(
            "Rain Day"
            if info.is_rain_day
            else "Normal Day"
        )

        self.detail_format.setText(
            info.dataset_format
        )

        self.detail_rain.setText(
            "Yes"
            if info.is_rain_day
            else "No"
        )

        self.detail_main.setText(
            self.format_files(
                info.main_files
            )
        )

        self.detail_f.setText(
            self.format_files(
                info.f_files
            )
        )

        self.detail_n.setText(
            self.format_files(
                info.n_files
            )
        )

        self.detail_summary.setText(
            str(
                len(
                    info.summary_files
                )
            )
        )

        self.detail_plots.setText(
            str(
                len(
                    info.plot_files
                )
            )
        )

    # ==========================================================
    # CLEAR DETAILS
    # ==========================================================

    def clear_file_details(self):

        self.detail_main.setText("-")
        self.detail_f.setText("-")
        self.detail_n.setText("-")
        self.detail_summary.setText("-")
        self.detail_plots.setText("-")

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def get_selection(self):

        return (
            self.selected_path,
            self.selected_type,
            self.selected_format,
        )

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def format_files(
        files: list[Path],
    ) -> str:

        if not files:
            return "Not found"

        if len(files) == 1:
            return files[0].name

        return (
            f"{len(files)} files"
        )

    @staticmethod
    def is_rain_day(
        folder_name: str,
    ) -> bool:

        import re

        return bool(
            re.search(
                r"(?:\bR|-R)\s*$",
                folder_name,
                re.IGNORECASE,
            )
        )