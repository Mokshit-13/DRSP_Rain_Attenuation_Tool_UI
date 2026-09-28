from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.inspection_service import (
    build_summary,
    export_excel,
    export_txt,
    get_observations,
    run_inspection,
)


class InspectionPage(QWidget):

    def __init__(self):

        super().__init__()

        self.selected_path: Path | None = None
        self.selected_type: str | None = None
        self.selected_format: str | None = None

        self.inspection_data: dict | None = None

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
            "Data Inspection"
        )

        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Inspect raw NARL/NAR datasets without modifying the source data."
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
        # SELECTED DATASET
        # ======================================================

        selected_group = QGroupBox(
            "Selected Dataset"
        )

        selected_layout = QGridLayout(
            selected_group
        )

        self.selected_name = QLabel(
            "No dataset selected"
        )

        self.selected_path_label = QLabel(
            "-"
        )

        self.selected_type_label = QLabel(
            "-"
        )

        self.selected_format_label = QLabel(
            "-"
        )

        self.selected_path_label.setWordWrap(
            True
        )

        selected_layout.addWidget(
            QLabel("Selection:"),
            0,
            0,
        )

        selected_layout.addWidget(
            self.selected_name,
            0,
            1,
        )

        selected_layout.addWidget(
            QLabel("Path:"),
            1,
            0,
        )

        selected_layout.addWidget(
            self.selected_path_label,
            1,
            1,
        )

        selected_layout.addWidget(
            QLabel("Type:"),
            2,
            0,
        )

        selected_layout.addWidget(
            self.selected_type_label,
            2,
            1,
        )

        selected_layout.addWidget(
            QLabel("Format:"),
            3,
            0,
        )

        selected_layout.addWidget(
            self.selected_format_label,
            3,
            1,
        )

        main_layout.addWidget(
            selected_group
        )

        # ======================================================
        # INSPECTION CONFIGURATION
        # ======================================================

        config_group = QGroupBox(
            "Inspection Configuration"
        )

        config_layout = QHBoxLayout(
            config_group
        )

        config_layout.addWidget(
            QLabel("Inspection Mode:")
        )

        self.mode_combo = QComboBox()

        self.mode_combo.addItem(
            "Selected File",
            "file",
        )

        self.mode_combo.addItem(
            "Selected Day",
            "day",
        )

        self.mode_combo.addItem(
            "Selected Month",
            "month",
        )

        self.mode_combo.addItem(
            "Entire Year",
            "year",
        )

        self.mode_combo.currentIndexChanged.connect(
            self.update_mode_state
        )

        config_layout.addWidget(
            self.mode_combo
        )

        config_layout.addStretch()

        self.inspect_button = QPushButton(
            "Inspect Dataset"
        )

        self.inspect_button.setMinimumHeight(
            38
        )

        self.inspect_button.setEnabled(
            False
        )

        self.inspect_button.clicked.connect(
            self.run_current_inspection
        )

        config_layout.addWidget(
            self.inspect_button
        )

        main_layout.addWidget(
            config_group
        )

        # ======================================================
        # SUMMARY
        # ======================================================

        summary_group = QGroupBox(
            "Inspection Summary"
        )

        summary_layout = QGridLayout(
            summary_group
        )

        self.total_files_label = QLabel(
            "0"
        )

        self.valid_files_label = QLabel(
            "0"
        )

        self.error_files_label = QLabel(
            "0"
        )

        self.total_rows_label = QLabel(
            "0"
        )

        self.total_size_label = QLabel(
            "0 bytes"
        )

        summary_layout.addWidget(
            QLabel("Files Scanned:"),
            0,
            0,
        )

        summary_layout.addWidget(
            self.total_files_label,
            0,
            1,
        )

        summary_layout.addWidget(
            QLabel("Valid Files:"),
            0,
            2,
        )

        summary_layout.addWidget(
            self.valid_files_label,
            0,
            3,
        )

        summary_layout.addWidget(
            QLabel("Files With Errors:"),
            1,
            0,
        )

        summary_layout.addWidget(
            self.error_files_label,
            1,
            1,
        )

        summary_layout.addWidget(
            QLabel("Total Rows:"),
            1,
            2,
        )

        summary_layout.addWidget(
            self.total_rows_label,
            1,
            3,
        )

        summary_layout.addWidget(
            QLabel("Total Size:"),
            2,
            0,
        )

        summary_layout.addWidget(
            self.total_size_label,
            2,
            1,
        )

        main_layout.addWidget(
            summary_group
        )

        # ======================================================
        # RESULTS SPLITTER
        # ======================================================

        splitter = QSplitter()

        # ------------------------------------------------------
        # FILE LIST
        # ------------------------------------------------------

        file_group = QGroupBox(
            "Inspected Files"
        )

        file_layout = QVBoxLayout(
            file_group
        )

        self.file_tree = QTreeWidget()

        self.file_tree.setHeaderLabels(
            [
                "File",
                "Status",
            ]
        )

        self.file_tree.setColumnWidth(
            0,
            280,
        )

        self.file_tree.itemClicked.connect(
            self.show_report_details
        )

        file_layout.addWidget(
            self.file_tree
        )

        # ------------------------------------------------------
        # DETAILS
        # ------------------------------------------------------

        detail_group = QGroupBox(
            "Inspection Details"
        )

        detail_layout = QVBoxLayout(
            detail_group
        )

        self.detail_tree = QTreeWidget()

        self.detail_tree.setHeaderLabels(
            [
                "Property",
                "Value",
            ]
        )

        self.detail_tree.setColumnWidth(
            0,
            260,
        )

        detail_layout.addWidget(
            self.detail_tree
        )

        splitter.addWidget(
            file_group
        )

        splitter.addWidget(
            detail_group
        )

        splitter.setSizes(
            [
                450,
                800,
            ]
        )

        main_layout.addWidget(
            splitter,
            stretch=1,
        )

        # ======================================================
        # OBSERVATIONS
        # ======================================================

        observation_group = QGroupBox(
            "Inspector's Observations"
        )

        observation_layout = QVBoxLayout(
            observation_group
        )

        self.observation_label = QLabel(
            "No observations yet."
        )

        self.observation_label.setWordWrap(
            True
        )

        observation_layout.addWidget(
            self.observation_label
        )

        main_layout.addWidget(
            observation_group
        )

        # ======================================================
        # EXPORT
        # ======================================================

        export_layout = QHBoxLayout()

        self.export_txt_button = QPushButton(
            "Export TXT Report"
        )

        self.export_excel_button = QPushButton(
            "Export Excel Report"
        )

        self.export_txt_button.setEnabled(
            False
        )

        self.export_excel_button.setEnabled(
            False
        )

        self.export_txt_button.clicked.connect(
            self.export_txt_report
        )

        self.export_excel_button.clicked.connect(
            self.export_excel_report
        )

        export_layout.addWidget(
            self.export_txt_button
        )

        export_layout.addWidget(
            self.export_excel_button
        )

        export_layout.addStretch()

        main_layout.addLayout(
            export_layout
        )

    # ==========================================================
    # DATASET SELECTION
    # ==========================================================

    def set_selected_dataset(
        self,
        selected_path,
        selected_type,
        selected_format,
    ):

        if selected_path is None:

            self.selected_path = None
            self.selected_type = None
            self.selected_format = None

            self.selected_name.setText(
                "No dataset selected"
            )

            self.selected_path_label.setText(
                "-"
            )

            self.selected_type_label.setText(
                "-"
            )

            self.selected_format_label.setText(
                "-"
            )

            self.inspect_button.setEnabled(
                False
            )

            return

        self.selected_path = Path(
            selected_path
        )

        self.selected_type = (
            selected_type
        )

        self.selected_format = (
            selected_format
        )

        self.selected_name.setText(
            self.selected_path.name
        )

        self.selected_path_label.setText(
            str(
                self.selected_path
            )
        )

        self.selected_type_label.setText(
            selected_type or "-"
        )

        self.selected_format_label.setText(
            selected_format or "-"
        )

        self.select_default_mode()

    # ==========================================================
    # DEFAULT MODE
    # ==========================================================

    def select_default_mode(self):

        if self.selected_type == "File":

            self.mode_combo.setCurrentIndex(
                self.mode_combo.findData(
                    "file"
                )
            )

        elif self.selected_type in (
            "Day",
            "Rain Day",
        ):

            self.mode_combo.setCurrentIndex(
                self.mode_combo.findData(
                    "day"
                )
            )

        elif self.selected_type == "Month Folder":

            self.mode_combo.setCurrentIndex(
                self.mode_combo.findData(
                    "month"
                )
            )

        elif self.selected_type == "Year Folder":

            self.mode_combo.setCurrentIndex(
                self.mode_combo.findData(
                    "year"
                )
            )

        self.update_mode_state()

    # ==========================================================
    # MODE STATE
    # ==========================================================

    def update_mode_state(self):

        mode = (
            self.mode_combo.currentData()
        )

        valid = False

        if self.selected_path is not None:

            if mode == "file":

                valid = (
                    self.selected_type
                    == "File"
                )

            elif mode == "day":

                valid = (
                    self.selected_type
                    in (
                        "Day",
                        "Rain Day",
                    )
                )

            elif mode == "month":

                valid = (
                    self.selected_type
                    == "Month Folder"
                )

            elif mode == "year":

                valid = (
                    self.selected_type
                    == "Year Folder"
                )

        self.inspect_button.setEnabled(
            valid
        )

    # ==========================================================
    # RUN INSPECTION
    # ==========================================================

    def run_current_inspection(self):

        if self.selected_path is None:
            return

        mode = (
            self.mode_combo.currentData()
        )

        try:

            self.inspect_button.setEnabled(
                False
            )

            self.clear_results()

            self.status_message(
                f"Inspecting {mode}..."
            )

            data = run_inspection(
                self.selected_path,
                self.selected_type,
                mode,
            )

            self.inspection_data = data

            self.display_summary(
                data
            )

            self.display_file_list(
                data
            )

            self.display_observations(
                data
            )

            self.export_txt_button.setEnabled(
                True
            )

            self.export_excel_button.setEnabled(
                True
            )

            self.status_message(
                "Inspection completed successfully."
            )

        except Exception as exc:

            self.inspection_data = None

            self.status_message(
                f"Inspection failed: {exc}"
            )

        finally:

            self.update_mode_state()

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def display_summary(
        self,
        data: dict,
    ):

        summary = build_summary(
            data
        )

        self.total_files_label.setText(
            str(
                summary[
                    "total_files"
                ]
            )
        )

        self.valid_files_label.setText(
            str(
                summary[
                    "valid_files"
                ]
            )
        )

        self.error_files_label.setText(
            str(
                summary[
                    "error_files"
                ]
            )
        )

        self.total_rows_label.setText(
            f"{summary['total_rows']:,}"
        )

        self.total_size_label.setText(
            self.format_size(
                summary[
                    "total_size"
                ]
            )
        )

    # ==========================================================
    # FILE LIST
    # ==========================================================

    def display_file_list(
        self,
        data: dict,
    ):

        self.file_tree.clear()

        reports = data.get(
            "reports",
            [],
        )

        for index, report in enumerate(
            reports
        ):

            general = report.get(
                "general",
                {},
            )

            name = general.get(
                "File Name",
                Path(
                    report.get(
                        "file_path",
                        f"File {index + 1}",
                    )
                ).name,
            )

            status = (
                "ERROR"
                if report.get("error")
                else "OK"
            )

            item = QTreeWidgetItem(
                [
                    name,
                    status,
                ]
            )

            item.setData(
                0,
                32,
                index,
            )

            self.file_tree.addTopLevelItem(
                item
            )

        if reports:

            self.file_tree.setCurrentItem(
                self.file_tree.topLevelItem(
                    0
                )
            )

            self.show_report_details(
                self.file_tree.topLevelItem(
                    0
                ),
                0,
            )

    # ==========================================================
    # REPORT DETAILS
    # ==========================================================

    def show_report_details(
        self,
        item,
        column,
    ):

        del column

        if self.inspection_data is None:
            return

        index = item.data(
            0,
            32,
        )

        if index is None:
            return

        reports = self.inspection_data.get(
            "reports",
            [],
        )

        if not (
            0 <= index < len(
                reports
            )
        ):
            return

        report = reports[index]

        self.detail_tree.clear()

        self.add_detail_section(
            "General Information",
            report.get(
                "general",
                {},
            ),
        )

        self.add_detail_section(
            "Time Analysis",
            report.get(
                "time",
                {},
            ),
        )

        self.add_channel_details(
            report.get(
                "channels",
                {},
            )
        )

        self.add_detail_section(
            "Data Quality",
            report.get(
                "quality",
                {},
            ),
        )

        self.add_detail_section(
            "Dataset Structure",
            report.get(
                "structure",
                {},
            ),
        )

        compatibility = (
            report.get(
                "compatibility",
                {},
            )
        )

        self.add_detail_section(
            "Compatibility",
            compatibility,
        )

        classification = report.get(
            "filename_classification"
        )

        if classification:

            item = QTreeWidgetItem(
                [
                    "Filename Classification",
                    str(
                        classification
                    ),
                ]
            )

            self.detail_tree.addTopLevelItem(
                item
            )

        error = report.get(
            "error"
        )

        if error:

            item = QTreeWidgetItem(
                [
                    "Error",
                    str(error),
                ]
            )

            self.detail_tree.addTopLevelItem(
                item
            )

        self.detail_tree.expandAll()

    # ==========================================================
    # DETAIL HELPERS
    # ==========================================================

    def add_detail_section(
        self,
        title: str,
        values: dict,
    ):

        if not values:
            return

        section = QTreeWidgetItem(
            [
                title,
                "",
            ]
        )

        self.detail_tree.addTopLevelItem(
            section
        )

        for key, value in values.items():

            child = QTreeWidgetItem(
                [
                    str(key),
                    self.format_value(
                        value
                    ),
                ]
            )

            section.addChild(
                child
            )

    def add_channel_details(
        self,
        channels: dict,
    ):

        if not channels:
            return

        section = QTreeWidgetItem(
            [
                "Channel Information",
                "",
            ]
        )

        self.detail_tree.addTopLevelItem(
            section
        )

        for key, value in channels.items():

            if key == "Per-Channel Statistics":

                stats_parent = QTreeWidgetItem(
                    [
                        key,
                        "",
                    ]
                )

                section.addChild(
                    stats_parent
                )

                for channel_name, stats in (
                    value.items()
                ):

                    channel_item = QTreeWidgetItem(
                        [
                            channel_name,
                            "",
                        ]
                    )

                    stats_parent.addChild(
                        channel_item
                    )

                    for stat_name, stat_value in (
                        stats.items()
                    ):

                        child = QTreeWidgetItem(
                            [
                                str(stat_name),
                                self.format_value(
                                    stat_value
                                ),
                            ]
                        )

                        channel_item.addChild(
                            child
                        )

                continue

            child = QTreeWidgetItem(
                [
                    str(key),
                    self.format_value(
                        value
                    ),
                ]
            )

            section.addChild(
                child
            )

    # ==========================================================
    # OBSERVATIONS
    # ==========================================================

    def display_observations(
        self,
        data: dict,
    ):

        observations = get_observations(
            data
        )

        if not observations:

            self.observation_label.setText(
                "No observations available."
            )

            return

        self.observation_label.setText(
            "\n".join(
                f"• {observation}"
                for observation in observations
            )
        )

    # ==========================================================
    # EXPORT TXT
    # ==========================================================

    def export_txt_report(
        self,
    ):

        if self.inspection_data is None:
            return

        try:

            path = export_txt(
                self.inspection_data
            )

            self.status_message(
                f"TXT report saved: {path}"
            )

        except Exception as exc:

            self.status_message(
                f"TXT export failed: {exc}"
            )

    # ==========================================================
    # EXPORT EXCEL
    # ==========================================================

    def export_excel_report(
        self,
    ):

        if self.inspection_data is None:
            return

        try:

            path = export_excel(
                self.inspection_data
            )

            self.status_message(
                f"Excel report saved: {path}"
            )

        except Exception as exc:

            self.status_message(
                f"Excel export failed: {exc}"
            )

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear_results(
        self,
    ):

        self.total_files_label.setText(
            "0"
        )

        self.valid_files_label.setText(
            "0"
        )

        self.error_files_label.setText(
            "0"
        )

        self.total_rows_label.setText(
            "0"
        )

        self.total_size_label.setText(
            "0 bytes"
        )

        self.file_tree.clear()
        self.detail_tree.clear()

        self.observation_label.setText(
            "Inspecting..."
        )

        self.export_txt_button.setEnabled(
            False
        )

        self.export_excel_button.setEnabled(
            False
        )

    # ==========================================================
    # STATUS
    # ==========================================================

    def status_message(
        self,
        message: str,
    ):

        window = self.window()

        if window is not None:

            window.statusBar().showMessage(
                message
            )

            if hasattr(
                window,
                "console",
            ):

                window.console.append(
                    f"[DRSP] {message}"
                )

    # ==========================================================
    # FORMAT VALUE
    # ==========================================================

    @staticmethod
    def format_value(
        value,
    ) -> str:

        if isinstance(
            value,
            float,
        ):

            return f"{value:.6g}"

        if isinstance(
            value,
            list,
        ):

            return ", ".join(
                str(item)
                for item in value
            )

        if isinstance(
            value,
            dict,
        ):

            return (
                f"{len(value)} entries"
            )

        return str(
            value
        )

    @staticmethod
    def format_size(
        size: int,
    ) -> str:

        if size < 1024:

            return f"{size} bytes"

        if size < 1024 ** 2:

            return (
                f"{size / 1024:.2f} KB"
            )

        if size < 1024 ** 3:

            return (
                f"{size / (1024 ** 2):.2f} MB"
            )

        return (
            f"{size / (1024 ** 3):.2f} GB"
        )