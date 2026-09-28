from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QThread,
    Signal,
    Qt,
)

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QSplitter,
    QAbstractItemView,
    QTabWidget,
)

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)

from matplotlib.figure import Figure

from services.statistics_service import (
    flatten_results,
    get_global_top_events,
    run_statistics,
)

from services.exceedance_service import (
    build_exceedance_curve_data,
    export_excel_report,
    export_txt_report,
    get_available_channels,
    run_exceedance_analysis,
)

from ui.widgets.detachable_panel import (
    DetachablePanel,
)


# ==========================================================
# STATISTICS WORKER
# ==========================================================

class StatisticsWorker(QThread):

    completed = Signal(
        dict
    )

    failed = Signal(
        str
    )

    def __init__(
        self,
        year_folder: Path,
    ):

        super().__init__()

        self.year_folder = year_folder

    def run(self):

        try:

            result = run_statistics(
                self.year_folder
            )

            self.completed.emit(
                result
            )

        except Exception as exc:

            self.failed.emit(
                str(exc)
            )


# ==========================================================
# EXCEEDANCE WORKER
# ==========================================================

class ExceedanceWorker(QThread):

    progress = Signal(
        str,
        int,
        int,
    )

    completed = Signal(
        dict
    )

    failed = Signal(
        str
    )

    def __init__(
        self,
        year_folder: Path,
        channel_name: str,
    ):

        super().__init__()

        self.year_folder = year_folder

        self.channel_name = (
            channel_name
        )

    def run(self):

        try:

            def progress_callback(
                month_label,
                month_index,
                total_months,
            ):

                self.progress.emit(
                    month_label,
                    month_index,
                    total_months,
                )

            result = run_exceedance_analysis(
                self.year_folder,
                self.channel_name,
                progress_callback=(
                    progress_callback
                ),
            )

            self.completed.emit(
                result
            )

        except Exception as exc:

            self.failed.emit(
                str(exc)
            )


# ==========================================================
# ANALYSIS PAGE
# ==========================================================

class AnalysisPage(QWidget):

    def __init__(self):

        super().__init__()

        self.selected_year: Path | None = None

        self.statistics_data: dict | None = None

        self.statistics_worker = None

        self.exceedance_data: dict | None = None

        self.exceedance_worker = None

        self.setup_ui()

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def setup_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            16,
            20,
            12,
        )

        layout.setSpacing(
            10
        )

        title = QLabel(
            "Analysis"
        )

        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Statistical and exceedance analysis of processed "
            "rain attenuation data."
        )

        subtitle.setObjectName(
            "PageSubtitle"
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        self.analysis_tabs = QTabWidget()

        self.statistics_tab = (
            self.create_statistics_tab()
        )

        self.exceedance_tab = (
            self.create_exceedance_tab()
        )

        self.analysis_tabs.addTab(
            self.statistics_tab,
            "Statistics",
        )

        self.analysis_tabs.addTab(
            self.exceedance_tab,
            "Exceedance Analysis",
        )

        layout.addWidget(
            self.analysis_tabs,
            stretch=1,
        )

    # ==========================================================
    # STATISTICS TAB
    # ==========================================================

    def create_statistics_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            5,
            10,
            5,
            5,
        )

        layout.setSpacing(
            10
        )

        dataset_group = QGroupBox(
            "Processed Data Selection"
        )

        dataset_layout = QGridLayout(
            dataset_group
        )

        dataset_layout.addWidget(
            QLabel(
                "Year Folder:"
            ),
            0,
            0,
        )

        self.statistics_path_label = QLabel(
            "No Processed_Data year selected"
        )

        self.statistics_path_label.setWordWrap(
            True
        )

        self.statistics_browse_button = (
            QPushButton(
                "Browse"
            )
        )

        self.statistics_browse_button.clicked.connect(
            self.browse_statistics_folder
        )

        dataset_layout.addWidget(
            self.statistics_path_label,
            0,
            1,
        )

        dataset_layout.addWidget(
            self.statistics_browse_button,
            0,
            2,
        )

        dataset_layout.addWidget(
            QLabel(
                "Target Channel:"
            ),
            1,
            0,
        )

        self.statistics_channel_label = QLabel(
            "Att_Channel-1"
        )

        dataset_layout.addWidget(
            self.statistics_channel_label,
            1,
            1,
        )

        dataset_layout.addWidget(
            QLabel(
                "Top Events / Month:"
            ),
            2,
            0,
        )

        self.statistics_top_n_label = QLabel(
            "3"
        )

        dataset_layout.addWidget(
            self.statistics_top_n_label,
            2,
            1,
        )

        layout.addWidget(
            dataset_group
        )

        control_layout = QHBoxLayout()

        self.statistics_run_button = (
            QPushButton(
                "Run Statistics"
            )
        )

        self.statistics_run_button.setMinimumHeight(
            38
        )

        self.statistics_run_button.setEnabled(
            False
        )

        self.statistics_run_button.clicked.connect(
            self.run_statistics
        )

        control_layout.addWidget(
            self.statistics_run_button
        )

        control_layout.addStretch()

        layout.addLayout(
            control_layout
        )

        status_group = QGroupBox(
            "Analysis Status"
        )

        status_layout = QVBoxLayout(
            status_group
        )

        self.statistics_status_label = QLabel(
            "Status: Ready"
        )

        self.statistics_progress_bar = (
            QProgressBar()
        )

        self.statistics_progress_bar.setRange(
            0,
            100,
        )

        self.statistics_progress_bar.setValue(
            0
        )

        self.statistics_progress_bar.setFormat(
            "Ready"
        )

        self.statistics_summary_label = QLabel(
            "No analysis performed yet."
        )

        status_layout.addWidget(
            self.statistics_status_label
        )

        status_layout.addWidget(
            self.statistics_progress_bar
        )

        status_layout.addWidget(
            self.statistics_summary_label
        )

        layout.addWidget(
            status_group
        )

        self.statistics_top_table = (
            QTableWidget()
        )

        self.configure_table(
            self.statistics_top_table,
            [
                "Rank",
                "Month",
                "Attenuation (dB)",
                "Date",
                "Time",
                "File",
            ],
        )

        self.statistics_top_panel = (
            DetachablePanel(
                "Highest Attenuation Events",
                self.statistics_top_table,
            )
        )

        self.statistics_monthly_table = (
            QTableWidget()
        )

        self.configure_table(
            self.statistics_monthly_table,
            [
                "Month",
                "Rank",
                "Attenuation (dB)",
                "Date",
                "Time",
                "File",
            ],
        )

        self.statistics_monthly_panel = (
            DetachablePanel(
                "Monthly Top Attenuation Events",
                self.statistics_monthly_table,
            )
        )

        splitter = QSplitter(
            Qt.Vertical
        )

        splitter.setHandleWidth(
            8
        )

        splitter.addWidget(
            self.statistics_top_panel
        )

        splitter.addWidget(
            self.statistics_monthly_panel
        )

        splitter.setStretchFactor(
            0,
            1,
        )

        splitter.setStretchFactor(
            1,
            2,
        )

        layout.addWidget(
            splitter,
            stretch=1,
        )

        return page

    # ==========================================================
    # EXCEEDANCE TAB
    # ==========================================================

    def create_exceedance_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            5,
            10,
            5,
            5,
        )

        layout.setSpacing(
            10
        )

        selection_group = QGroupBox(
            "Processed Data Selection"
        )

        selection_layout = QGridLayout(
            selection_group
        )

        selection_layout.addWidget(
            QLabel(
                "Year Folder:"
            ),
            0,
            0,
        )

        self.exceedance_path_label = QLabel(
            "No Processed_Data year selected"
        )

        self.exceedance_path_label.setWordWrap(
            True
        )

        self.exceedance_browse_button = (
            QPushButton(
                "Browse"
            )
        )

        self.exceedance_browse_button.clicked.connect(
            self.browse_exceedance_folder
        )

        selection_layout.addWidget(
            self.exceedance_path_label,
            0,
            1,
        )

        selection_layout.addWidget(
            self.exceedance_browse_button,
            0,
            2,
        )

        # ------------------------------------------------------
        # CHANNEL
        # ------------------------------------------------------

        selection_layout.addWidget(
            QLabel(
                "Channel:"
            ),
            1,
            0,
        )

        self.exceedance_channel_combo = (
            QComboBox()
        )

        self.exceedance_channel_combo.setEnabled(
            False
        )

        selection_layout.addWidget(
            self.exceedance_channel_combo,
            1,
            1,
        )

        # ------------------------------------------------------
        # METHOD
        # ------------------------------------------------------

        selection_layout.addWidget(
            QLabel(
                "Exceedance Method:"
            ),
            2,
            0,
        )

        self.exceedance_method_combo = (
            QComboBox()
        )

        self.exceedance_method_combo.addItem(
            "Total Seconds",
            "total",
        )

        self.exceedance_method_combo.addItem(
            "Ratio",
            "ratio",
        )

        selection_layout.addWidget(
            self.exceedance_method_combo,
            2,
            1,
        )

        # ------------------------------------------------------
        # THRESHOLD INFO
        # ------------------------------------------------------

        selection_layout.addWidget(
            QLabel(
                "Threshold Range:"
            ),
            3,
            0,
        )

        self.exceedance_threshold_label = QLabel(
            "Select a year and channel"
        )

        selection_layout.addWidget(
            self.exceedance_threshold_label,
            3,
            1,
        )

        layout.addWidget(
            selection_group
        )

        # ======================================================
        # CONTROLS
        # ======================================================

        exceedance_control = QHBoxLayout()

        self.exceedance_run_button = (
            QPushButton(
                "Run Exceedance Analysis"
            )
        )

        self.exceedance_run_button.setMinimumHeight(
            40
        )

        self.exceedance_run_button.setEnabled(
            False
        )

        self.exceedance_run_button.clicked.connect(
            self.run_exceedance
        )

        exceedance_control.addWidget(
            self.exceedance_run_button
        )

        self.exceedance_export_txt_button = (
            QPushButton(
                "Export TXT"
            )
        )

        self.exceedance_export_txt_button.setEnabled(
            False
        )

        self.exceedance_export_txt_button.clicked.connect(
            self.export_exceedance_txt
        )

        exceedance_control.addWidget(
            self.exceedance_export_txt_button
        )

        self.exceedance_export_excel_button = (
            QPushButton(
                "Export Excel"
            )
        )

        self.exceedance_export_excel_button.setEnabled(
            False
        )

        self.exceedance_export_excel_button.clicked.connect(
            self.export_exceedance_excel
        )

        exceedance_control.addWidget(
            self.exceedance_export_excel_button
        )

        exceedance_control.addStretch()

        layout.addLayout(
            exceedance_control
        )

        # ======================================================
        # STATUS
        # ======================================================

        exceedance_status_group = (
            QGroupBox(
                "Exceedance Analysis Status"
            )
        )

        status_layout = QVBoxLayout(
            exceedance_status_group
        )

        self.exceedance_status_label = QLabel(
            "Status: Ready"
        )

        self.exceedance_progress_bar = (
            QProgressBar()
        )

        self.exceedance_progress_bar.setRange(
            0,
            100,
        )

        self.exceedance_progress_bar.setValue(
            0
        )

        self.exceedance_progress_bar.setFormat(
            "Ready"
        )

        self.exceedance_detail_label = QLabel(
            "No analysis performed yet."
        )

        status_layout.addWidget(
            self.exceedance_status_label
        )

        status_layout.addWidget(
            self.exceedance_progress_bar
        )

        status_layout.addWidget(
            self.exceedance_detail_label
        )

        layout.addWidget(
            exceedance_status_group
        )

        # ======================================================
        # TABLE
        # ======================================================

        self.exceedance_table = (
            QTableWidget()
        )

        self.exceedance_table_panel = (
            DetachablePanel(
                "Monthly Exceedance Table",
                self.exceedance_table,
            )
        )

        # ======================================================
        # PLOT
        # ======================================================

        self.exceedance_figure = Figure(
            figsize=(8, 4.5),
            tight_layout=True,
        )

        self.exceedance_canvas = (
            FigureCanvas(
                self.exceedance_figure
            )
        )

        self.exceedance_plot_panel = (
            DetachablePanel(
                "Annual Exceedance Curve",
                self.exceedance_canvas,
            )
        )

        # ======================================================
        # RESULTS SPLITTER
        # ======================================================

        results_splitter = QSplitter(
            Qt.Vertical
        )

        results_splitter.setHandleWidth(
            8
        )

        results_splitter.addWidget(
            self.exceedance_table_panel
        )

        results_splitter.addWidget(
            self.exceedance_plot_panel
        )

        results_splitter.setStretchFactor(
            0,
            2,
        )

        results_splitter.setStretchFactor(
            1,
            2,
        )

        layout.addWidget(
            results_splitter,
            stretch=1,
        )

        return page

    # ==========================================================
    # TABLE CONFIGURATION
    # ==========================================================

    @staticmethod
    def configure_table(
        table: QTableWidget,
        headers: list[str],
    ):

        table.setColumnCount(
            len(headers)
        )

        table.setHorizontalHeaderLabels(
            headers
        )

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        table.setAlternatingRowColors(
            True
        )

        table.setWordWrap(
            False
        )

        table.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )

        table.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )

        header = (
            table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Interactive
        )

    # ==========================================================
    # STATISTICS BROWSE
    # ==========================================================

    def browse_statistics_folder(
        self,
    ):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Processed_Data Year Folder",
        )

        if not folder:
            return

        self.set_year_folder(
            Path(folder)
        )

    # ==========================================================
    # EXCEEDANCE BROWSE
    # ==========================================================

    def browse_exceedance_folder(
        self,
    ):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Processed_Data Year Folder",
        )

        if not folder:
            return

        self.set_year_folder(
            Path(folder)
        )

    # ==========================================================
    # SET YEAR
    # ==========================================================

    def set_year_folder(
        self,
        path: Path,
    ):

        self.selected_year = (
            path
        )

        self.statistics_path_label.setText(
            str(path)
        )

        self.exceedance_path_label.setText(
            str(path)
        )

        self.statistics_run_button.setEnabled(
            True
        )

        # ------------------------------------------------------
        # Populate channels from actual processed data
        # ------------------------------------------------------

        try:

            channels = get_available_channels(
                path
            )

        except Exception:

            channels = []

        self.exceedance_channel_combo.clear()

        for channel in channels:

            self.exceedance_channel_combo.addItem(
                channel,
                channel,
            )

        self.exceedance_channel_combo.setEnabled(
            bool(channels)
        )

        if channels:

            self.update_exceedance_threshold_info()

            self.exceedance_run_button.setEnabled(
                True
            )

        else:

            self.exceedance_run_button.setEnabled(
                False
            )

            self.exceedance_threshold_label.setText(
                "No supported attenuation channels found."
            )

        self.statistics_status_label.setText(
            "Status: Year folder selected"
        )

        self.exceedance_status_label.setText(
            "Status: Year folder selected"
        )

    # ==========================================================
    # CHANNEL CHANGE
    # ==========================================================

    def update_exceedance_threshold_info(
        self,
    ):

        channel = (
            self.exceedance_channel_combo.currentData()
        )

        if not channel:

            return

        # The actual upper limit comes back from the
        # engine after analysis. Here we simply show
        # that the channel is ready.

        self.exceedance_threshold_label.setText(
            f"{channel} selected"
        )

    # ==========================================================
    # RUN STATISTICS
    # ==========================================================

    def run_statistics(
        self,
    ):

        if self.selected_year is None:
            return

        if self.statistics_worker is not None:
            return

        self.statistics_run_button.setEnabled(
            False
        )

        self.statistics_browse_button.setEnabled(
            False
        )

        self.statistics_status_label.setText(
            "Status: Analysing processed data..."
        )

        self.statistics_progress_bar.setRange(
            0,
            0,
        )

        self.statistics_progress_bar.setFormat(
            "Analysing..."
        )

        self.statistics_summary_label.setText(
            "Reading attenuation files..."
        )

        self.statistics_worker = (
            StatisticsWorker(
                self.selected_year
            )
        )

        self.statistics_worker.completed.connect(
            self.statistics_completed
        )

        self.statistics_worker.failed.connect(
            self.statistics_failed
        )

        self.statistics_worker.finished.connect(
            self.statistics_worker_finished
        )

        self.statistics_worker.start()

    # ==========================================================
    # STATISTICS COMPLETE
    # ==========================================================

    def statistics_completed(
        self,
        data: dict,
    ):

        self.statistics_data = data

        month_count = data.get(
            "month_count",
            0,
        )

        rows = flatten_results(
            data
        )

        self.display_statistics_monthly(
            rows
        )

        global_top = (
            get_global_top_events(
                data,
                limit=10,
            )
        )

        self.display_statistics_global(
            global_top
        )

        self.statistics_progress_bar.setRange(
            0,
            100,
        )

        self.statistics_progress_bar.setValue(
            100
        )

        self.statistics_progress_bar.setFormat(
            "100% — Complete"
        )

        self.statistics_status_label.setText(
            "Status: SUCCESS"
        )

        self.statistics_summary_label.setText(
            f"Analysed {month_count} month(s) | "
            f"{len(rows)} top-event records generated | "
            f"Target: "
            f"{data.get('target_channel', '-')}"
        )

    # ==========================================================
    # STATISTICS FAILURE
    # ==========================================================

    def statistics_failed(
        self,
        message: str,
    ):

        self.statistics_progress_bar.setRange(
            0,
            100,
        )

        self.statistics_progress_bar.setValue(
            0
        )

        self.statistics_progress_bar.setFormat(
            "Failed"
        )

        self.statistics_status_label.setText(
            "Status: FAILED"
        )

        self.statistics_summary_label.setText(
            f"Statistics analysis failed:\n"
            f"{message}"
        )

    # ==========================================================
    # STATISTICS TABLES
    # ==========================================================

    def display_statistics_global(
        self,
        rows,
    ):

        self.statistics_top_table.clearContents()

        self.statistics_top_table.setRowCount(
            len(rows)
        )

        self.statistics_top_table.setColumnCount(
            6
        )

        self.statistics_top_table.setHorizontalHeaderLabels(
            [
                "Rank",
                "Month",
                "Attenuation (dB)",
                "Date",
                "Time",
                "File",
            ]
        )

        for row_index, row in enumerate(
            rows
        ):

            values = [
                row_index + 1,
                row.get(
                    "month",
                    "",
                ),
                f"{row.get('attenuation', 0):.2f}",
                row.get(
                    "date",
                    "",
                ),
                row.get(
                    "time",
                    "",
                ),
                row.get(
                    "file",
                    "",
                ),
            ]

            for column_index, value in enumerate(
                values
            ):

                self.statistics_top_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

    def display_statistics_monthly(
        self,
        rows,
    ):

        self.statistics_monthly_table.clearContents()

        self.statistics_monthly_table.setRowCount(
            len(rows)
        )

        self.statistics_monthly_table.setColumnCount(
            6
        )

        self.statistics_monthly_table.setHorizontalHeaderLabels(
            [
                "Month",
                "Rank",
                "Attenuation (dB)",
                "Date",
                "Time",
                "File",
            ]
        )

        for row_index, row in enumerate(
            rows
        ):

            values = [
                row.get(
                    "month",
                    "",
                ),
                row.get(
                    "rank",
                    "",
                ),
                f"{row.get('attenuation', 0):.2f}",
                row.get(
                    "date",
                    "",
                ),
                row.get(
                    "time",
                    "",
                ),
                row.get(
                    "file",
                    "",
                ),
            ]

            for column_index, value in enumerate(
                values
            ):

                self.statistics_monthly_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

    # ==========================================================
    # STATISTICS CLEANUP
    # ==========================================================

    def statistics_worker_finished(
        self,
    ):

        if self.statistics_worker is not None:

            self.statistics_worker.deleteLater()

        self.statistics_worker = None

        self.statistics_run_button.setEnabled(
            self.selected_year is not None
        )

        self.statistics_browse_button.setEnabled(
            True
        )

    # ==========================================================
    # RUN EXCEEDANCE
    # ==========================================================

    def run_exceedance(
        self,
    ):

        if self.selected_year is None:
            return

        if self.exceedance_worker is not None:
            return

        channel = (
            self.exceedance_channel_combo.currentData()
        )

        if not channel:
            return

        self.exceedance_data = None

        self.exceedance_run_button.setEnabled(
            False
        )

        self.exceedance_browse_button.setEnabled(
            False
        )

        self.exceedance_channel_combo.setEnabled(
            False
        )

        self.exceedance_export_txt_button.setEnabled(
            False
        )

        self.exceedance_export_excel_button.setEnabled(
            False
        )

        self.exceedance_status_label.setText(
            f"Status: Processing — {channel}"
        )

        self.exceedance_progress_bar.setRange(
            0,
            100,
        )

        self.exceedance_progress_bar.setValue(
            0
        )

        self.exceedance_progress_bar.setFormat(
            "Preparing..."
        )

        self.exceedance_detail_label.setText(
            "Scanning processed attenuation files..."
        )

        self.exceedance_table.clearContents()

        self.exceedance_table.setRowCount(
            0
        )

        self.exceedance_figure.clear()

        self.exceedance_canvas.draw()

        self.exceedance_worker = (
            ExceedanceWorker(
                self.selected_year,
                channel,
            )
        )

        self.exceedance_worker.progress.connect(
            self.exceedance_progress
        )

        self.exceedance_worker.completed.connect(
            self.exceedance_completed
        )

        self.exceedance_worker.failed.connect(
            self.exceedance_failed
        )

        self.exceedance_worker.finished.connect(
            self.exceedance_worker_finished
        )

        self.exceedance_worker.start()

    # ==========================================================
    # EXCEEDANCE PROGRESS
    # ==========================================================

    def exceedance_progress(
        self,
        month_label,
        month_index,
        total_months,
    ):

        if total_months <= 0:
            return

        percentage = int(
            (
                month_index
                / total_months
            )
            * 100
        )

        self.exceedance_progress_bar.setRange(
            0,
            total_months,
        )

        self.exceedance_progress_bar.setValue(
            month_index
        )

        self.exceedance_progress_bar.setFormat(
            f"{percentage}% "
            f"({month_index}/{total_months})"
        )

        self.exceedance_status_label.setText(
            f"Status: Processing — "
            f"{month_label}"
        )

        self.exceedance_detail_label.setText(
            f"Processed month: "
            f"{month_label}"
        )

    # ==========================================================
    # EXCEEDANCE COMPLETE
    # ==========================================================

    def exceedance_completed(
        self,
        data,
    ):

        self.exceedance_data = data

        method = (
            self.exceedance_method_combo.currentData()
        )

        if method == "ratio":

            headers = data[
                "headers_ratio"
            ]

            rows = data[
                "rows_ratio"
            ]

        else:

            headers = data[
                "headers_total"
            ]

            rows = data[
                "rows_total"
            ]

        self.populate_exceedance_table(
            headers,
            rows,
        )

        self.update_exceedance_curve(
            data,
            method,
        )

        self.exceedance_threshold_label.setText(
            f"{data.get('lower_limit', 0):.2f}"
            f" – "
            f"{data.get('upper_limit', 0):.2f}"
            f" dB  |  Step: "
            f"{data.get('step_size', 0):.2f}"
            f" dB"
        )

        self.exceedance_progress_bar.setRange(
            0,
            100,
        )

        self.exceedance_progress_bar.setValue(
            100
        )

        self.exceedance_progress_bar.setFormat(
            "100% — Complete"
        )

        self.exceedance_status_label.setText(
            "Status: SUCCESS"
        )

        self.exceedance_detail_label.setText(
            f"Year: {data.get('year', '-')}"
            f"  |  Channel: "
            f"{data.get('target_channel', '-')}"
            f"  |  Months: "
            f"{len(data.get('month_labels', []))}"
            f"  |  Thresholds: "
            f"{data.get('threshold_count', 0)}"
            f"  |  Method: "
            f"{'Ratio' if method == 'ratio' else 'Total Seconds'}"
        )

        # The analysis result is now available for export.
        self.exceedance_export_txt_button.setEnabled(
            True
        )

        self.exceedance_export_excel_button.setEnabled(
            True
        )

        window = self.window()
        if hasattr(window, "console_text"):
            window.console_text.append(
                "[DRSP] Exceedance analysis completed successfully: "
                f"{data.get('year', '-')} / "
                f"{data.get('target_channel', '-')}"
            )

    # ==========================================================
    # EXCEEDANCE FAILURE
    # ==========================================================

    def exceedance_failed(
        self,
        message: str,
    ):

        self.exceedance_progress_bar.setRange(
            0,
            100,
        )

        self.exceedance_progress_bar.setValue(
            0
        )

        self.exceedance_progress_bar.setFormat(
            "Failed"
        )

        self.exceedance_status_label.setText(
            "Status: FAILED"
        )

        self.exceedance_detail_label.setText(
            f"Exceedance analysis failed:\n"
            f"{message}"
        )

    # ==========================================================
    # TABLE
    # ==========================================================

    def populate_exceedance_table(
        self,
        headers,
        rows,
    ):

        self.exceedance_table.clear()

        self.exceedance_table.setColumnCount(
            len(headers)
        )

        display_headers = []

        for header in headers:

            if header == "Lower Limit":

                display_headers.append(
                    "Lower Limit (dB)"
                )

            elif header == "Upper Limit":

                display_headers.append(
                    "Upper Limit (dB)"
                )

            else:

                display_headers.append(
                    header
                )

        self.exceedance_table.setHorizontalHeaderLabels(
            display_headers
        )

        self.exceedance_table.setRowCount(
            len(rows)
        )

        for row_index, row in enumerate(
            rows
        ):

            for column_index, value in enumerate(
                row
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.exceedance_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        header = (
            self.exceedance_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Interactive
        )

        for column in range(
            self.exceedance_table.columnCount()
        ):

            self.exceedance_table.setColumnWidth(
                column,
                120,
            )

        self.exceedance_table.verticalHeader().setDefaultSectionSize(
            26
        )

    # ==========================================================
    # CURVE
    # ==========================================================

    def update_exceedance_curve(
        self,
        data: dict,
        method: str,
    ):

        x_values, y_values = (
            build_exceedance_curve_data(
                data,
                method,
            )
        )

        self.exceedance_figure.clear()

        axis = (
            self.exceedance_figure.add_subplot(
                111
            )
        )

        if x_values:

            axis.plot(
                x_values,
                y_values,
                linewidth=1.5,
            )

        axis.set_title(
            f"Annual Exceedance Curve — "
            f"{data.get('target_channel', '-')}"
        )

        axis.set_xlabel(
            "Attenuation Threshold (dB)"
        )

        if method == "ratio":

            axis.set_ylabel(
                "Exceedance Ratio (%)"
            )

        else:

            axis.set_ylabel(
                "% Time Exceeded"
            )

        axis.grid(
            True,
            alpha=0.3,
        )

        self.exceedance_figure.tight_layout()

        self.exceedance_canvas.draw()

    # ==========================================================
    # EXPORT TXT
    # ==========================================================

    def export_exceedance_txt(
        self,
    ):

        if self.exceedance_data is None:
            return

        try:

            method = (
                self.exceedance_method_combo.currentData()
            )

            path = export_txt_report(
                self.exceedance_data,
                method,
            )

            self.exceedance_status_label.setText(
                "Status: TXT report exported"
            )

            window = self.window()

            if hasattr(
                window,
                "console_text",
            ):

                window.console_text.append(
                    "[DRSP] Exceedance TXT report saved: "
                    f"{path}"
                )

        except Exception as exc:

            self.exceedance_status_label.setText(
                "Status: TXT export failed"
            )

            self.exceedance_detail_label.setText(
                str(exc)
            )

    # ==========================================================
    # EXPORT EXCEL
    # ==========================================================

    def export_exceedance_excel(
        self,
    ):

        if self.exceedance_data is None:
            return

        try:

            method = (
                self.exceedance_method_combo.currentData()
            )

            path = export_excel_report(
                self.exceedance_data,
                method,
            )

            self.exceedance_status_label.setText(
                "Status: Excel report exported"
            )

            window = self.window()

            if hasattr(
                window,
                "console_text",
            ):

                window.console_text.append(
                    "[DRSP] Exceedance Excel report saved: "
                    f"{path}"
                )

        except Exception as exc:

            self.exceedance_status_label.setText(
                "Status: Excel export failed"
            )

            self.exceedance_detail_label.setText(
                str(exc)
            )

    # ==========================================================
    # EXCEEDANCE WORKER FINISHED
    # ==========================================================

    def exceedance_worker_finished(
        self,
    ):

        if self.exceedance_worker is not None:

            self.exceedance_worker.deleteLater()

        self.exceedance_worker = None

        self.exceedance_channel_combo.setEnabled(
            True
        )

        self.exceedance_browse_button.setEnabled(
            True
        )

        self.exceedance_run_button.setEnabled(
            (
                self.selected_year is not None
                and self.exceedance_channel_combo.count()
                > 0
            )
        )

        # Keep export controls disabled after a failed/cancelled run.
        # On success, exceedance_completed() has already enabled them.
        if self.exceedance_data is None:
            self.exceedance_export_txt_button.setEnabled(False)
            self.exceedance_export_excel_button.setEnabled(False)

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        self.statistics_top_panel.close_popout_if_open()

        self.statistics_monthly_panel.close_popout_if_open()

        self.exceedance_table_panel.close_popout_if_open()

        self.exceedance_plot_panel.close_popout_if_open()

        if self.statistics_worker is not None:

            self.statistics_worker.quit()

            self.statistics_worker.wait(
                2000
            )

        if self.exceedance_worker is not None:

            self.exceedance_worker.quit()

            self.exceedance_worker.wait(
                2000
            )

        event.accept()