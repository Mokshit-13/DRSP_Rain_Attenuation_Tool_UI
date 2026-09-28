from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from queue import Empty

from PySide6.QtCore import (
    QThread,
    Signal,
)

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.processing_service import (
    process_single_day,
)


# ==========================================================
# BATCH WORKER
# ==========================================================

class BatchWorker(QThread):

    progress = Signal(
        int,
        int,
        str,
        int,
        str,
        str,
    )

    completed = Signal(
        dict
    )

    failed = Signal(
        str
    )

    def __init__(
        self,
        mode: str,
        selected_path: Path,
        dataset_format: str,
    ):

        super().__init__()

        self.mode = mode
        self.selected_path = selected_path
        self.dataset_format = dataset_format

        self.process = None
        self.progress_queue = None

    def run(self):

        try:

            # --------------------------------------------------
            # Windows-safe multiprocessing context
            # --------------------------------------------------

            context = mp.get_context(
                "spawn"
            )

            self.progress_queue = (
                context.Queue()
            )

            # --------------------------------------------------
            # Start completely separate Python process
            # --------------------------------------------------

            from services.batch_runner import (
                run_batch_process,
            )

            self.process = context.Process(
                target=run_batch_process,
                args=(
                    self.mode,
                    str(
                        self.selected_path
                    ),
                    self.dataset_format,
                    self.progress_queue,
                ),
            )

            self.process.start()

            # --------------------------------------------------
            # Read messages from child process
            # --------------------------------------------------

            finished = False

            while (
                self.process.is_alive()
                or not self.progress_queue.empty()
            ):

                try:

                    message = (
                        self.progress_queue.get(
                            timeout=0.1
                        )
                    )

                except Empty:

                    continue

                message_type = message.get(
                    "type"
                )

                # ----------------------------------------------
                # PROGRESS
                # ----------------------------------------------

                if (
                    message_type
                    == "progress"
                ):

                    self.progress.emit(
                        message.get(
                            "completed",
                            0,
                        ),
                        message.get(
                            "total",
                            0,
                        ),
                        message.get(
                            "current_item",
                            "",
                        ),
                        message.get(
                            "failed",
                            0,
                        ),
                        message.get(
                            "group_name",
                            "",
                        ),
                        message.get(
                            "status",
                            "",
                        ),
                    )

                # ----------------------------------------------
                # COMPLETE
                # ----------------------------------------------

                elif (
                    message_type
                    == "complete"
                ):

                    finished = True

                    self.completed.emit(
                        message.get(
                            "result",
                            {},
                        )
                    )

                # ----------------------------------------------
                # ERROR
                # ----------------------------------------------

                elif (
                    message_type
                    == "error"
                ):

                    finished = True

                    self.failed.emit(
                        message.get(
                            "message",
                            "Unknown batch error.",
                        )
                    )

            # --------------------------------------------------
            # Wait for process termination
            # --------------------------------------------------

            if self.process is not None:

                self.process.join()

            # --------------------------------------------------
            # Child crashed without sending a message
            # --------------------------------------------------

            if (
                not finished
                and self.process is not None
                and self.process.exitcode
                not in (
                    0,
                    None,
                )
            ):

                self.failed.emit(
                    "Batch worker process terminated "
                    f"with exit code "
                    f"{self.process.exitcode}."
                )

        except Exception as exc:

            self.failed.emit(
                str(exc)
            )

    def stop_process(
        self,
    ):

        if (
            self.process is not None
            and self.process.is_alive()
        ):

            self.process.terminate()

            self.process.join(
                timeout=2
            )


# ==========================================================
# PROCESSING PAGE
# ==========================================================

class ProcessingPage(QWidget):

    def __init__(self):

        super().__init__()

        self.selected_path: Path | None = None
        self.selected_type: str | None = None
        self.selected_format: str | None = None

        self.worker: BatchWorker | None = None

        self.progress_total = 0
        self.progress_completed = 0
        self.progress_failed = 0

        self.setup_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            25,
            20,
            25,
            20,
        )

        layout.setSpacing(
            15
        )

        # ======================================================
        # HEADER
        # ======================================================

        title = QLabel(
            "Data Processing"
        )

        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Process selected NARL beacon measurement data."
        )

        subtitle.setObjectName(
            "PageSubtitle"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)

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

        self.selected_format_label = QLabel(
            "-"
        )

        self.selected_type_label = QLabel(
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

        layout.addWidget(
            selected_group
        )

        # ======================================================
        # PROCESSING CONFIGURATION
        # ======================================================

        config_group = QGroupBox(
            "Processing Configuration"
        )

        config_layout = QGridLayout(
            config_group
        )

        config_layout.addWidget(
            QLabel(
                "Processing Mode:"
            ),
            0,
            0,
        )

        self.mode_combo = QComboBox()

        self.mode_combo.addItem(
            "Single Day",
            "single",
        )

        self.mode_combo.addItem(
            "Monthly Batch",
            "month",
        )

        self.mode_combo.addItem(
            "Yearly Batch",
            "year",
        )

        self.mode_combo.currentIndexChanged.connect(
            self.update_mode_information
        )

        config_layout.addWidget(
            self.mode_combo,
            0,
            1,
        )

        self.mode_description = QLabel(
            "Process one selected measurement day "
            "with the interactive attenuation plot."
        )

        self.mode_description.setWordWrap(
            True
        )

        config_layout.addWidget(
            self.mode_description,
            1,
            0,
            1,
            2,
        )

        self.process_button = QPushButton(
            "Process Selected Dataset"
        )

        self.process_button.setMinimumHeight(
            48
        )

        self.process_button.setEnabled(
            False
        )

        self.process_button.clicked.connect(
            self.start_processing
        )

        config_layout.addWidget(
            self.process_button,
            2,
            0,
            1,
            2,
        )

        layout.addWidget(
            config_group
        )

        # ======================================================
        # PROCESSING STATUS
        # ======================================================

        progress_group = QGroupBox(
            "Processing Status"
        )

        progress_layout = QVBoxLayout(
            progress_group
        )

        self.status_label = QLabel(
            "Status: Ready"
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setFormat(
            "Ready"
        )

        self.progress_detail_label = QLabel(
            "Completed: 0 / 0"
        )

        self.current_item_label = QLabel(
            "Current: —"
        )

        progress_layout.addWidget(
            self.status_label
        )

        progress_layout.addWidget(
            self.progress_bar
        )

        progress_layout.addWidget(
            self.progress_detail_label
        )

        progress_layout.addWidget(
            self.current_item_label
        )

        layout.addWidget(
            progress_group
        )

        # ======================================================
        # RESULTS
        # ======================================================

        result_group = QGroupBox(
            "Processing Result"
        )

        result_layout = QVBoxLayout(
            result_group
        )

        self.result_label = QLabel(
            "No processing performed yet."
        )

        self.result_label.setWordWrap(
            True
        )

        result_layout.addWidget(
            self.result_label
        )

        layout.addWidget(
            result_group
        )

        # ======================================================
        # MAXIMUM ATTENUATION
        # ======================================================

        attenuation_group = QGroupBox(
            "Maximum Attenuation"
        )

        attenuation_layout = QVBoxLayout(
            attenuation_group
        )

        self.attenuation_label = QLabel(
            "No attenuation results yet."
        )

        self.attenuation_label.setWordWrap(
            True
        )

        attenuation_layout.addWidget(
            self.attenuation_label
        )

        layout.addWidget(
            attenuation_group
        )

        layout.addStretch()

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

            self.process_button.setEnabled(
                False
            )

            self.status_label.setText(
                "Status: Ready"
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

        self.update_mode_information()

    # ==========================================================
    # MODE
    # ==========================================================

    def update_mode_information(
        self,
    ):

        mode = (
            self.mode_combo.currentData()
        )

        if mode == "single":

            self.mode_description.setText(
                "Process one selected measurement day "
                "with the interactive attenuation plot."
            )

        elif mode == "month":

            self.mode_description.setText(
                "Process all recognised rain-day folders "
                "inside the selected month. Batch processing "
                "runs in a separate worker process."
            )

        elif mode == "year":

            self.mode_description.setText(
                "Process all month folders inside the "
                "selected year. Overall yearly progress "
                "is reported below."
            )

        self.update_process_button()

    # ==========================================================
    # BUTTON STATE
    # ==========================================================

    def update_process_button(
        self,
    ):

        mode = (
            self.mode_combo.currentData()
        )

        if self.selected_path is None:

            self.process_button.setEnabled(
                False
            )

            return

        if self.selected_format not in (
            "NAR",
            "NARL",
        ):

            self.process_button.setEnabled(
                False
            )

            return

        if mode == "single":

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

        else:

            valid = False

        self.process_button.setEnabled(
            valid
        )

    # ==========================================================
    # START
    # ==========================================================

    def start_processing(
        self,
    ):

        if self.selected_path is None:
            return

        mode = (
            self.mode_combo.currentData()
        )

        self.reset_results()

        if mode == "single":

            self.process_single_day_now()

        elif mode in (
            "month",
            "year",
        ):

            self.process_batch_async(
                mode
            )

    # ==========================================================
    # SINGLE DAY
    # ==========================================================

    def process_single_day_now(
        self,
    ):

        self.set_processing_state(
            True
        )

        self.status_label.setText(
            "Status: Processing single day..."
        )

        self.progress_bar.setValue(
            25
        )

        self.progress_bar.setFormat(
            "Processing..."
        )

        self.current_item_label.setText(
            f"Current: "
            f"{self.selected_name.text()}"
        )

        try:

            result = process_single_day(
                self.selected_path,
                self.selected_format,
            )

            self.progress_bar.setValue(
                100
            )

            self.progress_bar.setFormat(
                "100% — Complete"
            )

            self.display_single_result(
                result
            )

        except Exception as exc:

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(
                "Failed"
            )

            self.display_error(
                exc
            )

        finally:

            self.set_processing_state(
                False
            )

    # ==========================================================
    # BATCH
    # ==========================================================

    def process_batch_async(
        self,
        mode: str,
    ):

        if self.worker is not None:
            return

        self.set_processing_state(
            True
        )

        self.progress_total = 0
        self.progress_completed = 0
        self.progress_failed = 0

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setFormat(
            "Preparing..."
        )

        self.progress_detail_label.setText(
            "Completed: 0 / 0"
        )

        self.current_item_label.setText(
            "Current: Preparing..."
        )

        self.status_label.setText(
            "Status: Starting separate batch worker..."
        )

        self.worker = BatchWorker(
            mode=mode,
            selected_path=self.selected_path,
            dataset_format=self.selected_format,
        )

        self.worker.progress.connect(
            self.handle_progress
        )

        self.worker.completed.connect(
            self.batch_completed
        )

        self.worker.failed.connect(
            self.batch_failed
        )

        self.worker.finished.connect(
            self.worker_finished
        )

        self.worker.start()

    # ==========================================================
    # PROGRESS
    # ==========================================================

    def handle_progress(
        self,
        completed,
        total,
        current_item,
        failed,
        group_name,
        status,
    ):

        self.progress_total = total
        self.progress_completed = completed
        self.progress_failed = failed

        if total > 0:

            percentage = int(
                (
                    completed
                    / total
                )
                * 100
            )

            self.progress_bar.setRange(
                0,
                total,
            )

            self.progress_bar.setValue(
                completed
            )

            self.progress_bar.setFormat(
                f"{percentage}% "
                f"({completed}/{total})"
            )

        else:

            self.progress_bar.setRange(
                0,
                100,
            )

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(
                "Preparing..."
            )

        self.progress_detail_label.setText(
            f"Completed: {completed} / {total}"
            f"    |    Failed: {failed}"
        )

        if current_item:

            self.current_item_label.setText(
                f"Current: {current_item}"
            )

        elif status == "finished":

            self.current_item_label.setText(
                "Current: Complete"
            )

        else:

            self.current_item_label.setText(
                "Current: Updating..."
            )

        if group_name:

            if status == "finished":

                self.status_label.setText(
                    f"Status: Finished — "
                    f"{group_name}"
                )

            else:

                self.status_label.setText(
                    f"Status: Processing — "
                    f"{group_name}"
                )

    # ==========================================================
    # BATCH COMPLETE
    # ==========================================================

    def batch_completed(
        self,
        result,
    ):

        total = result.get(
            "rain_day_count",
            self.progress_total,
        )

        successful = result.get(
            "successful",
            0,
        )

        failed = result.get(
            "failed",
            0,
        )

        self.progress_bar.setRange(
            0,
            max(
                total,
                1,
            ),
        )

        self.progress_bar.setValue(
            max(
                total,
                1,
            )
        )

        self.progress_bar.setFormat(
            "100% — Complete"
        )

        self.status_label.setText(
            "Status: SUCCESS"
        )

        mode = result.get(
            "mode"
        )

        if mode == "month":

            self.result_label.setText(
                "Monthly processing completed.\n\n"
                f"Month: "
                f"{result.get('month_name', '-')}\n"
                f"Rain-day folders: {total}\n"
                f"Successful: {successful}\n"
                f"Failed: {failed}\n\n"
                "Output: Processed_Data"
            )

        elif mode == "year":

            self.result_label.setText(
                "Yearly processing completed.\n\n"
                f"Year: "
                f"{result.get('year', '-')}\n"
                f"Months processed: "
                f"{result.get('month_count', '-')}\n"
                f"Rain-day folders: {total}\n"
                f"Successful: {successful}\n"
                f"Failed: {failed}\n\n"
                "Output: Processed_Data"
            )

        self.attenuation_label.setText(
            "Batch processing completed. "
            "Individual attenuation results are available "
            "inside the generated Processed_Data folders."
        )

        self.progress_detail_label.setText(
            f"Completed: {successful} / {total}"
            f"    |    Failed: {failed}"
        )

        self.current_item_label.setText(
            "Current: Complete"
        )

    # ==========================================================
    # FAILED
    # ==========================================================

    def batch_failed(
        self,
        message,
    ):

        if self.progress_total > 0:

            self.progress_bar.setRange(
                0,
                self.progress_total,
            )

            self.progress_bar.setValue(
                self.progress_completed
            )

            percentage = int(
                (
                    self.progress_completed
                    / self.progress_total
                )
                * 100
            )

            self.progress_bar.setFormat(
                f"{percentage}% — Failed"
            )

        else:

            self.progress_bar.setRange(
                0,
                100,
            )

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(
                "Failed"
            )

        self.status_label.setText(
            "Status: FAILED"
        )

        self.result_label.setText(
            "Batch processing failed:\n\n"
            f"{message}"
        )

        self.attenuation_label.setText(
            "No complete results available."
        )

        self.current_item_label.setText(
            "Current: Failed"
        )

    # ==========================================================
    # WORKER FINISHED
    # ==========================================================

    def worker_finished(
        self,
    ):

        if self.worker is not None:

            self.worker.deleteLater()

        self.worker = None

        self.set_processing_state(
            False
        )

    # ==========================================================
    # SINGLE RESULT
    # ==========================================================

    def display_single_result(
        self,
        result,
    ):

        status = result.get(
            "status",
            "UNKNOWN",
        )

        self.status_label.setText(
            f"Status: {status}"
        )

        self.result_label.setText(
            "Single-day processing completed.\n\n"
            f"Main File:\n"
            f"{result.get('main_file', '-')}\n\n"
            f"Output Folder:\n"
            f"{result.get('output_dir', '-')}"
        )

        maximums = result.get(
            "maximum_attenuation",
            {},
        )

        if not maximums:

            self.attenuation_label.setText(
                "No attenuation results available."
            )

            return

        lines = []

        for channel, value in (
            maximums.items()
        ):

            try:

                lines.append(
                    f"{channel}: "
                    f"{float(value):.3f} dB"
                )

            except (
                TypeError,
                ValueError,
            ):

                lines.append(
                    f"{channel}: {value}"
                )

        self.attenuation_label.setText(
            "\n".join(
                lines
            )
        )

    # ==========================================================
    # ERROR
    # ==========================================================

    def display_error(
        self,
        exc,
    ):

        self.status_label.setText(
            "Status: FAILED"
        )

        self.result_label.setText(
            "Processing failed:\n\n"
            f"{exc}"
        )

        self.attenuation_label.setText(
            "No results available."
        )

        self.current_item_label.setText(
            "Current: Failed"
        )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset_results(
        self,
    ):

        self.status_label.setText(
            "Status: Ready"
        )

        self.result_label.setText(
            "Processing in progress..."
        )

        self.attenuation_label.setText(
            "Waiting for processing results..."
        )

        self.progress_total = 0
        self.progress_completed = 0
        self.progress_failed = 0

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setFormat(
            "Preparing..."
        )

        self.progress_detail_label.setText(
            "Completed: 0 / 0"
        )

        self.current_item_label.setText(
            "Current: Preparing..."
        )

    # ==========================================================
    # PROCESSING STATE
    # ==========================================================

    def set_processing_state(
        self,
        processing: bool,
    ):

        self.mode_combo.setEnabled(
            not processing
        )

        self.process_button.setEnabled(
            False
            if processing
            else self.is_selection_valid()
        )

    def is_selection_valid(
        self,
    ) -> bool:

        if self.selected_path is None:
            return False

        if self.selected_format not in (
            "NAR",
            "NARL",
        ):
            return False

        mode = (
            self.mode_combo.currentData()
        )

        if mode == "single":

            return (
                self.selected_type
                in (
                    "Day",
                    "Rain Day",
                )
            )

        if mode == "month":

            return (
                self.selected_type
                == "Month Folder"
            )

        if mode == "year":

            return (
                self.selected_type
                == "Year Folder"
            )

        return False

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        if self.worker is not None:

            self.worker.stop_process()

            self.worker.quit()

            self.worker.wait(
                2000
            )

        event.accept()