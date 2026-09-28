from __future__ import annotations

import contextlib
import importlib
import io
import json
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QPushButton,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from ui.widgets.detachable_panel import DetachablePanel


# ============================================================
# WORKER
# ============================================================

class ToolWorker(QThread):
    completed = Signal(object, str)
    failed = Signal(str)

    def __init__(self, function: Callable[[], Any]):
        super().__init__()
        self.function = function

    def run(self):
        try:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                result = self.function()
            self.completed.emit(result, buffer.getvalue())
        except Exception as exc:
            self.failed.emit(str(exc))


# ============================================================
# TOOLS PAGE
# ============================================================

class ToolsPage(QWidget):
    """
    Unified engineering-tool workspace for legacy DRSP utilities.

    Uses the existing backend algorithms instead of reimplementing them:
      - data_inspector.py
      - data_validator.py
      - FSxanalyzer.py
    """

    def __init__(self):
        super().__init__()

        self.worker: ToolWorker | None = None
        self.current_report_text = ""
        self.inspector_result: Any = None
        self.validator_result: Any = None
        self.spectrum_trace: Any = None

        self.figure = Figure(figsize=(10, 5.5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.setup_ui()
        self.clear_spectrum_plot()

    # ========================================================
    # MAIN UI
    # ========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(10)

        title = QLabel("Tools")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Run the original DRSP inspection, validation, and RF spectrum "
            "utilities through a click-driven engineering interface."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_inspector_tab(), "Data Inspector")
        self.tabs.addTab(self.create_validator_tab(), "Data Validator")
        self.tabs.addTab(self.create_spectrum_tab(), "RF Spectrum Analyzer")

        layout.addWidget(self.tabs, stretch=1)

    # ========================================================
    # DATA INSPECTOR
    # ========================================================

    def create_inspector_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(10)

        controls = QGroupBox("Inspection Selection")
        form = QFormLayout(controls)

        self.inspector_mode = QComboBox()
        self.inspector_mode.addItem("Single File", "file")
        self.inspector_mode.addItem("Single Month", "month")
        self.inspector_mode.addItem("Entire Year", "year")
        self.inspector_mode.currentIndexChanged.connect(self.update_inspector_controls)

        self.inspector_path = QLineEdit()
        self.inspector_path.setReadOnly(True)
        self.inspector_path.setPlaceholderText("Select an input...")

        self.inspector_browse = QPushButton("Browse")
        self.inspector_browse.clicked.connect(self.browse_inspector_path)

        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self.inspector_path, stretch=1)
        path_layout.addWidget(self.inspector_browse)

        form.addRow("Mode:", self.inspector_mode)
        form.addRow("Input:", path_row)

        controls_row = QHBoxLayout()

        self.inspect_button = QPushButton("Run Inspection")
        self.inspect_button.setMinimumHeight(38)
        self.inspect_button.clicked.connect(self.run_inspection)
        controls_row.addWidget(self.inspect_button)

        self.inspect_export_button = QPushButton("Export Report")
        self.inspect_export_button.setMinimumHeight(38)
        self.inspect_export_button.setEnabled(False)
        self.inspect_export_button.clicked.connect(self.export_inspection_report)
        controls_row.addWidget(self.inspect_export_button)
        controls_row.addStretch()

        layout.addWidget(controls)
        layout.addLayout(controls_row)

        result_content = QWidget()
        result_layout = QVBoxLayout(result_content)
        result_layout.setContentsMargins(0, 0, 0, 0)

        self.inspector_output = QPlainTextEdit()
        self.inspector_output.setReadOnly(True)
        self.inspector_output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.inspector_output.setPlaceholderText("Inspection results will appear here.")
        result_layout.addWidget(self.inspector_output)

        self.inspector_panel = DetachablePanel(
            "Inspection Results",
            result_content,
        )
        layout.addWidget(self.inspector_panel, stretch=1)

        self.update_inspector_controls()
        return page

    def update_inspector_controls(self):
        if not hasattr(self, "inspector_mode"):
            return
        mode = self.inspector_mode.currentData()
        self.inspector_path.clear()
        self.inspector_path.setPlaceholderText(
            "Select a raw TXT file..." if mode == "file" else "Select a folder..."
        )

    def browse_inspector_path(self):
        mode = self.inspector_mode.currentData()

        if mode == "file":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Raw Data File",
                "",
                "Text Files (*.txt);;All Files (*)",
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Folder",
            )

        if path:
            self.inspector_path.setText(path)

    def run_inspection(self):
        source = self.inspector_path.text().strip()
        mode = self.inspector_mode.currentData()

        if not source:
            self.inspector_output.setPlainText("Please select an input first.")
            return

        self.set_busy(self.inspect_button, True, "Running...")
        self.inspector_export_button.setEnabled(False)
        self.inspector_output.setPlainText("Running inspection...\n")

        def task():
            module = importlib.import_module("data_inspector")
            target = Path(source)

            if mode == "file":
                return module.inspect_file(target)
            if mode == "month":
                return module.inspect_month(target)
            return module.inspect_year(target)

        self.start_worker(
            task,
            self.inspection_completed,
            self.inspection_failed,
        )

    def inspection_completed(self, result: Any, captured: str):
        self.inspector_result = result
        self.current_report_text = self.format_result(result, captured)
        self.inspector_output.setPlainText(self.current_report_text)
        self.inspect_export_button.setEnabled(True)
        self.set_busy(self.inspect_button, False, "Run Inspection")
        self.log_console("[DRSP] Data inspection completed.")

    def inspection_failed(self, message: str):
        self.inspector_output.setPlainText(f"Inspection failed:\n{message}")
        self.set_busy(self.inspect_button, False, "Run Inspection")
        self.log_console(f"[DRSP] Data inspection failed: {message}")

    def export_inspection_report(self):
        self.export_text_report(
            self.current_report_text,
            "Export Inspection Report",
            "Inspection_Report.txt",
        )

    # ========================================================
    # DATA VALIDATOR
    # ========================================================

    def create_validator_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(10)

        controls = QGroupBox("Validation Selection")
        form = QFormLayout(controls)

        self.validator_mode = QComboBox()
        self.validator_mode.addItem("Single File", "file")
        self.validator_mode.addItem("Single Month", "month")
        self.validator_mode.addItem("Entire Year", "year")
        self.validator_mode.currentIndexChanged.connect(self.update_validator_controls)

        self.validator_path = QLineEdit()
        self.validator_path.setReadOnly(True)
        self.validator_path.setPlaceholderText("Select an input...")

        self.validator_browse = QPushButton("Browse")
        self.validator_browse.clicked.connect(self.browse_validator_path)

        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self.validator_path, stretch=1)
        path_layout.addWidget(self.validator_browse)

        form.addRow("Mode:", self.validator_mode)
        form.addRow("Input:", path_row)

        controls_row = QHBoxLayout()

        self.validate_button = QPushButton("Run Validation")
        self.validate_button.setMinimumHeight(38)
        self.validate_button.clicked.connect(self.run_validation)
        controls_row.addWidget(self.validate_button)

        self.validate_export_button = QPushButton("Export Report")
        self.validate_export_button.setMinimumHeight(38)
        self.validate_export_button.setEnabled(False)
        self.validate_export_button.clicked.connect(self.export_validation_report)
        controls_row.addWidget(self.validate_export_button)
        controls_row.addStretch()

        layout.addWidget(controls)
        layout.addLayout(controls_row)

        result_content = QWidget()
        result_layout = QVBoxLayout(result_content)
        result_layout.setContentsMargins(0, 0, 0, 0)

        self.validator_output = QPlainTextEdit()
        self.validator_output.setReadOnly(True)
        self.validator_output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.validator_output.setPlaceholderText("Validation results will appear here.")
        result_layout.addWidget(self.validator_output)

        self.validator_panel = DetachablePanel(
            "Validation Results",
            result_content,
        )
        layout.addWidget(self.validator_panel, stretch=1)

        self.update_validator_controls()
        return page

    def update_validator_controls(self):
        if not hasattr(self, "validator_mode"):
            return
        mode = self.validator_mode.currentData()
        self.validator_path.clear()
        self.validator_path.setPlaceholderText(
            "Select a raw TXT file..." if mode == "file" else "Select a folder..."
        )

    def browse_validator_path(self):
        mode = self.validator_mode.currentData()

        if mode == "file":
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Raw NARL Data File",
                "",
                "Text Files (*.txt);;All Files (*)",
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Folder",
            )

        if path:
            self.validator_path.setText(path)

    def run_validation(self):
        source = self.validator_path.text().strip()
        mode = self.validator_mode.currentData()

        if not source:
            self.validator_output.setPlainText("Please select an input first.")
            return

        self.set_busy(self.validate_button, True, "Running...")
        self.validate_export_button.setEnabled(False)
        self.validator_output.setPlainText("Running validation...\n")

        def task():
            module = importlib.import_module("data_validator")
            target = Path(source)

            if mode == "file":
                return module.scan_file(target)
            if mode == "month":
                return module.scan_month(target, show_progress=False)
            return module.scan_year(target)

        self.start_worker(
            task,
            self.validation_completed,
            self.validation_failed,
        )

    def validation_completed(self, result: Any, captured: str):
        self.validator_result = result
        self.current_report_text = self.format_result(result, captured)
        self.validator_output.setPlainText(self.current_report_text)
        self.validate_export_button.setEnabled(True)
        self.set_busy(self.validate_button, False, "Run Validation")
        self.log_console("[DRSP] Data validation completed.")

    def validation_failed(self, message: str):
        self.validator_output.setPlainText(f"Validation failed:\n{message}")
        self.set_busy(self.validate_button, False, "Run Validation")
        self.log_console(f"[DRSP] Data validation failed: {message}")

    def export_validation_report(self):
        self.export_text_report(
            self.current_report_text,
            "Export Validation Report",
            "Validation_Report.txt",
        )

    # ========================================================
    # RF SPECTRUM ANALYZER
    # ========================================================

    def create_spectrum_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(10)

        selection = QGroupBox("RF Spectrum Receiver Data")
        form = QFormLayout(selection)

        self.spectrum_folder = QLineEdit()
        self.spectrum_folder.setReadOnly(True)
        self.spectrum_folder.setPlaceholderText("Select folder containing Excel receiver exports...")

        browse_row = QWidget()
        browse_layout = QHBoxLayout(browse_row)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        browse_layout.addWidget(self.spectrum_folder, stretch=1)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_spectrum_folder)
        browse_layout.addWidget(browse_button)

        self.spectrum_frequency = QDoubleSpinBox()
        self.spectrum_frequency.setRange(0.000001, 1000000.0)
        self.spectrum_frequency.setDecimals(6)
        self.spectrum_frequency.setValue(240.0)
        self.spectrum_frequency.setSuffix(" MHz")

        self.spectrum_tolerance = QDoubleSpinBox()
        self.spectrum_tolerance.setRange(0.001, 100000.0)
        self.spectrum_tolerance.setDecimals(3)
        self.spectrum_tolerance.setValue(50.0)
        self.spectrum_tolerance.setSuffix(" kHz")

        form.addRow("Input Folder:", browse_row)
        form.addRow("Target Frequency:", self.spectrum_frequency)
        form.addRow("Frequency Tolerance:", self.spectrum_tolerance)

        action_row = QHBoxLayout()

        self.spectrum_run_button = QPushButton("Analyze Spectrum")
        self.spectrum_run_button.setMinimumHeight(38)
        self.spectrum_run_button.clicked.connect(self.run_spectrum_analysis)
        action_row.addWidget(self.spectrum_run_button)

        self.spectrum_export_button = QPushButton("Export Plot")
        self.spectrum_export_button.setMinimumHeight(38)
        self.spectrum_export_button.setEnabled(False)
        self.spectrum_export_button.clicked.connect(self.export_spectrum_plot)
        action_row.addWidget(self.spectrum_export_button)
        action_row.addStretch()

        layout.addWidget(selection)
        layout.addLayout(action_row)

        plot_content = QWidget()
        plot_layout = QVBoxLayout(plot_content)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas, stretch=1)

        self.spectrum_plot_panel = DetachablePanel(
            "RF Spectrum Trace",
            plot_content,
        )
        layout.addWidget(self.spectrum_plot_panel, stretch=1)

        return page

    def browse_spectrum_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select RF Spectrum Excel Folder",
        )
        if path:
            self.spectrum_folder.setText(path)

    def run_spectrum_analysis(self):
        source = self.spectrum_folder.text().strip()
        if not source:
            self.log_console("[DRSP] Please select an RF spectrum folder first.")
            return

        requested = float(self.spectrum_frequency.value())
        tolerance = float(self.spectrum_tolerance.value())

        self.set_busy(self.spectrum_run_button, True, "Analyzing...")
        self.spectrum_export_button.setEnabled(False)
        self.clear_spectrum_plot(message="Analyzing RF spectrum data...")

        def task():
            module = importlib.import_module("FSxanalyzer")
            config = module.AnalyzerConfig(
                folder=Path(source),
                target_frequency_mhz=requested,
                freq_tolerance_khz=tolerance,
                debug=False,
            )
            return module.analyze(config)

        self.start_worker(
            task,
            self.spectrum_completed,
            self.spectrum_failed,
        )

    def spectrum_completed(self, trace: Any, captured: str):
        self.spectrum_trace = trace
        self.draw_spectrum_trace(trace)
        self.spectrum_export_button.setEnabled(True)
        self.set_busy(self.spectrum_run_button, False, "Analyze Spectrum")

        self.log_console(
            "[DRSP] RF spectrum analysis completed."
        )

        if captured.strip():
            self.log_console(captured.strip().splitlines()[-1])

    def spectrum_failed(self, message: str):
        self.clear_spectrum_plot(message=f"RF spectrum analysis failed:\n{message}")
        self.set_busy(self.spectrum_run_button, False, "Analyze Spectrum")
        self.log_console(f"[DRSP] RF spectrum analysis failed: {message}")

    def draw_spectrum_trace(self, trace: Any):
        self.figure.clear()
        axis = self.figure.add_subplot(111)

        times = getattr(trace, "all_times", [])
        amplitudes = getattr(trace, "all_amplitudes", [])

        axis.plot(times, amplitudes, linewidth=0.9)

        requested = getattr(trace, "requested_frequency_mhz", None)
        selected = getattr(trace, "selected_frequency_mhz", None)
        files_processed = getattr(trace, "files_processed", None)
        files_skipped = getattr(trace, "files_skipped", None)

        axis.set_title("RF Spectrum Receiver — Frequency Trace")
        axis.set_xlabel("Time")
        axis.set_ylabel("Amplitude (dBm)")
        axis.grid(True, alpha=0.3)

        title_parts = []
        if requested is not None:
            title_parts.append(f"Requested: {requested:.4f} MHz")
        if selected is not None:
            title_parts.append(f"Selected: {selected:.4f} MHz")
        if files_processed is not None:
            title_parts.append(f"Files: {files_processed}")
        if files_skipped is not None:
            title_parts.append(f"Skipped: {files_skipped}")

        if title_parts:
            axis.text(
                0.01,
                0.99,
                " | ".join(title_parts),
                transform=axis.transAxes,
                va="top",
                ha="left",
            )

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def clear_spectrum_plot(self, message: str = ""):
        self.figure.clear()
        axis = self.figure.add_subplot(111)

        if message:
            axis.text(
                0.5,
                0.5,
                message,
                ha="center",
                va="center",
            )
        else:
            axis.text(
                0.5,
                0.5,
                "Select an RF spectrum Excel folder\nand analyze a target frequency.",
                ha="center",
                va="center",
            )

        axis.set_axis_off()
        self.canvas.draw_idle()

    def export_spectrum_plot(self):
        if self.spectrum_trace is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export RF Spectrum Plot",
            "RF_Spectrum_Trace.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)",
        )

        if not file_path:
            return

        try:
            self.figure.savefig(
                file_path,
                dpi=300,
                bbox_inches="tight",
            )
            self.log_console(f"[DRSP] RF spectrum plot exported: {file_path}")
        except Exception as exc:
            self.log_console(f"[DRSP] RF spectrum export failed: {exc}")

    # ========================================================
    # COMMON HELPERS
    # ========================================================

    def start_worker(
        self,
        function: Callable[[], Any],
        success_handler: Callable[[Any, str], None],
        failure_handler: Callable[[str], None],
    ):
        if self.worker is not None and self.worker.isRunning():
            return

        self.worker = ToolWorker(function)
        self.worker.completed.connect(success_handler)
        self.worker.failed.connect(failure_handler)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def worker_finished(self):
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()

    @staticmethod
    def set_busy(button: QPushButton, busy: bool, text: str):
        button.setEnabled(not busy)
        button.setText(text)

    @staticmethod
    def format_result(result: Any, captured: str = "") -> str:
        parts: list[str] = []

        if captured.strip():
            parts.append("BACKEND OUTPUT\n" + captured.strip())

        if result is not None:
            parts.append("RESULT\n" + ToolsPage.pretty_json(result))

        return "\n\n".join(parts).strip() or "No result returned."

    @staticmethod
    def pretty_json(value: Any) -> str:
        try:
            return json.dumps(value, indent=2, default=str, ensure_ascii=False)
        except Exception:
            return str(value)

    def export_text_report(self, text: str, title: str, default_name: str):
        if not text.strip():
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            default_name,
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            Path(file_path).write_text(text, encoding="utf-8")
            self.log_console(f"[DRSP] Report exported: {file_path}")
        except Exception as exc:
            self.log_console(f"[DRSP] Report export failed: {exc}")

    def log_console(self, message: str):
        window = self.window()
        if hasattr(window, "console_text"):
            window.console_text.append(message)

    # ========================================================
    # CLEANUP
    # ========================================================

    def closeEvent(self, event):
        for panel_name in (
            "inspector_panel",
            "validator_panel",
            "spectrum_plot_panel",
        ):
            panel = getattr(self, panel_name, None)
            if panel is not None:
                panel.close_popout_if_open()

        worker = getattr(self, "worker", None)
        if worker is not None and worker.isRunning():
            worker.quit()
            worker.wait(1500)

        event.accept()
