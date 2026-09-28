from __future__ import annotations

from pathlib import Path

import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QSizePolicy,
)

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from ui.widgets.detachable_panel import DetachablePanel


class PlotsPage(QWidget):
    """
    Engineering-style plotting workspace for processed rain attenuation data.

    This page reads already-generated attenuation TXT files and does not
    change the underlying attenuation-processing algorithm.

    Features
    --------
    - All Channels — 2x2 view
    - Single Channel view
    - Channel Comparison view
    - Interactive Matplotlib navigation/zoom toolbar
    - Detachable Plot Workspace
    - Detachable Plot Summary
    - Channel statistics table
    - PNG export
    - PDF export

    Expected processed file columns:
        Time, Att_Channel-1, Att_Channel-2, ...
    """

    ATTENUATION_COLUMNS = [
        "Att_Channel-1",
        "Att_Channel-2",
        "Att_Channel-3",
        "Att_Channel-4",
    ]

    def __init__(self):
        super().__init__()

        self.loaded_file: Path | None = None
        self.dataframe: pd.DataFrame | None = None
        self.available_channels: list[str] = []

        self.figure = Figure(
            figsize=(10, 6),
            tight_layout=False,
        )
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.toolbar = NavigationToolbar(
            self.canvas,
            self,
        )
        self.toolbar.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.setup_ui()
        self.clear_plot()

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(10)

        title = QLabel("Plots")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Visualize processed rain attenuation data with interactive "
            "engineering plots."
        )
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ------------------------------------------------------
        # DATA SELECTION
        # ------------------------------------------------------

        selection_group = QGroupBox("Plot Data Selection")
        selection_layout = QGridLayout(selection_group)
        selection_layout.setHorizontalSpacing(10)
        selection_layout.setVerticalSpacing(8)

        selection_layout.addWidget(
            QLabel("Processed File:"),
            0,
            0,
        )

        self.file_label = QLabel(
            "No attenuation file selected"
        )
        self.file_label.setWordWrap(True)
        selection_layout.addWidget(
            self.file_label,
            0,
            1,
        )

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(
            self.browse_file
        )
        selection_layout.addWidget(
            self.browse_button,
            0,
            2,
        )

        selection_layout.addWidget(
            QLabel("Plot Type:"),
            1,
            0,
        )

        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItem(
            "All Channels — 2×2",
            "all",
        )
        self.plot_type_combo.addItem(
            "Single Channel",
            "single",
        )
        self.plot_type_combo.addItem(
            "Channel Comparison",
            "comparison",
        )
        self.plot_type_combo.currentIndexChanged.connect(
            self.update_control_state
        )
        selection_layout.addWidget(
            self.plot_type_combo,
            1,
            1,
        )

        selection_layout.addWidget(
            QLabel("Channel:"),
            2,
            0,
        )

        self.channel_combo = QComboBox()
        self.channel_combo.setEnabled(False)
        selection_layout.addWidget(
            self.channel_combo,
            2,
            1,
        )

        layout.addWidget(selection_group)

        # ------------------------------------------------------
        # ACTIONS
        # ------------------------------------------------------

        action_layout = QHBoxLayout()

        self.generate_button = QPushButton("Generate Plot")
        self.generate_button.setMinimumHeight(38)
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(
            self.generate_plot
        )
        action_layout.addWidget(
            self.generate_button
        )

        self.export_png_button = QPushButton("Export PNG")
        self.export_png_button.setMinimumHeight(38)
        self.export_png_button.setEnabled(False)
        self.export_png_button.clicked.connect(
            self.export_png
        )
        action_layout.addWidget(
            self.export_png_button
        )

        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.setMinimumHeight(38)
        self.export_pdf_button.setEnabled(False)
        self.export_pdf_button.clicked.connect(
            self.export_pdf
        )
        action_layout.addWidget(
            self.export_pdf_button
        )

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # ------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------

        summary_group = QGroupBox("Plot Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_label = QLabel(
            "Load a processed attenuation file to begin."
        )
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(
            self.summary_label
        )

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels(
            [
                "Channel",
                "Samples",
                "Minimum (dB)",
                "Maximum (dB)",
                "Mean (dB)",
            ]
        )
        self.summary_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.summary_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.summary_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.summary_table.setMinimumHeight(130)
        summary_layout.addWidget(
            self.summary_table
        )

        self.summary_panel = DetachablePanel(
            "Plot Summary",
            summary_group,
        )
        layout.addWidget(
            self.summary_panel
        )

        # ------------------------------------------------------
        # PLOT WORKSPACE
        # ------------------------------------------------------

        plot_content = QWidget()
        plot_content.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        plot_layout = QVBoxLayout(plot_content)
        plot_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        plot_layout.setSpacing(0)

        plot_layout.addWidget(
            self.toolbar
        )
        plot_layout.addWidget(
            self.canvas,
            stretch=1,
        )

        self.plot_panel = DetachablePanel(
            "Plot Workspace",
            plot_content,
        )
        layout.addWidget(
            self.plot_panel,
            stretch=1,
        )

        self.update_control_state()

    # ==========================================================
    # FILE BROWSE
    # ==========================================================

    def browse_file(self):
        default_directory = str(
            Path("Processed_Data").resolve()
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Processed Attenuation File",
            default_directory,
            "Attenuation TXT (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        self.load_file(
            Path(file_path)
        )

    # ==========================================================
    # LOAD FILE
    # ==========================================================

    def load_file(self, path: Path):
        try:
            dataframe = pd.read_csv(
                path,
                sep="\t",
            )

            dataframe.columns = [
                str(column).strip()
                for column in dataframe.columns
            ]

            if "Time" not in dataframe.columns:
                raise ValueError(
                    "Selected file does not contain a 'Time' column."
                )

            channels = [
                channel
                for channel in self.ATTENUATION_COLUMNS
                if channel in dataframe.columns
            ]

            if not channels:
                raise ValueError(
                    "Selected file does not contain any supported "
                    "attenuation channels."
                )

            for channel in channels:
                dataframe[channel] = pd.to_numeric(
                    dataframe[channel],
                    errors="coerce",
                )

            # Processed attenuation files normally contain HH:MM:SS.
            # Using pandas' general parser here also tolerates files that
            # happen to contain a date prefix without changing normal cases.
            dataframe["Time"] = pd.to_datetime(
                dataframe["Time"].astype(str).str.strip(),
                errors="coerce",
            )

            dataframe = dataframe.dropna(
                subset=["Time"]
            ).reset_index(drop=True)

            if dataframe.empty:
                raise ValueError(
                    "The selected file contains no valid time samples."
                )

            self.loaded_file = path
            self.dataframe = dataframe
            self.available_channels = channels

            self.channel_combo.clear()
            for channel in channels:
                self.channel_combo.addItem(
                    channel,
                    channel,
                )

            self.file_label.setText(
                str(path)
            )

            self.summary_label.setText(
                f"Loaded {len(dataframe):,} samples | "
                f"Channels: {', '.join(channels)}"
            )

            self.populate_summary()
            self.generate_plot()

            self.log_console(
                f"[DRSP] Plot data loaded: {path}"
            )

        except Exception as exc:
            self.loaded_file = None
            self.dataframe = None
            self.available_channels = []
            self.channel_combo.clear()
            self.summary_table.setRowCount(0)

            self.generate_button.setEnabled(False)
            self.export_png_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)

            self.summary_label.setText(
                f"Failed to load plot data:\n{exc}"
            )

            self.clear_plot()

    # ==========================================================
    # CONTROL STATE
    # ==========================================================

    def update_control_state(self):
        has_data = self.dataframe is not None
        is_single = (
            self.plot_type_combo.currentData()
            == "single"
        )

        self.channel_combo.setEnabled(
            has_data and is_single
        )

        self.generate_button.setEnabled(
            has_data
        )

        if not has_data:
            self.export_png_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def populate_summary(self):
        if self.dataframe is None:
            self.summary_table.setRowCount(0)
            return

        self.summary_table.setRowCount(
            len(self.available_channels)
        )

        for row_index, channel in enumerate(
            self.available_channels
        ):
            series = self.dataframe[channel].dropna()

            values = [
                channel,
                f"{len(series):,}",
                (
                    f"{series.min():.4f}"
                    if not series.empty
                    else "-"
                ),
                (
                    f"{series.max():.4f}"
                    if not series.empty
                    else "-"
                ),
                (
                    f"{series.mean():.4f}"
                    if not series.empty
                    else "-"
                ),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(
                    str(value)
                )
                item.setTextAlignment(
                    Qt.AlignCenter
                )
                self.summary_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    # ==========================================================
    # PLOT GENERATION
    # ==========================================================

    def generate_plot(self):
        if self.dataframe is None:
            return

        try:
            plot_type = (
                self.plot_type_combo.currentData()
            )

            self.figure.clear()

            if plot_type == "all":
                self.draw_all_channels()

            elif plot_type == "single":
                self.draw_single_channel()

            elif plot_type == "comparison":
                self.draw_comparison()

            else:
                raise ValueError(
                    f"Unsupported plot type: {plot_type}"
                )

            self.figure.tight_layout(
                rect=(0, 0, 1, 0.96)
            )
            self.canvas.draw_idle()

            self.export_png_button.setEnabled(True)
            self.export_pdf_button.setEnabled(True)

            self.log_console(
                "[DRSP] Plot generated: "
                f"{self.plot_type_combo.currentText()}"
            )

        except Exception as exc:
            self.figure.clear()

            axis = self.figure.add_subplot(111)
            axis.text(
                0.5,
                0.5,
                f"Plot generation failed:\n{exc}",
                ha="center",
                va="center",
            )
            axis.set_axis_off()

            self.canvas.draw_idle()

            self.export_png_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)

            self.log_console(
                f"[DRSP] Plot generation failed: {exc}"
            )

    # ==========================================================
    # PLOT TYPES
    # ==========================================================

    def draw_all_channels(self):
        axes = self.figure.subplots(
            2,
            2,
        )
        axes_flat = list(
            axes.flat
        )

        for index, channel in enumerate(
            self.available_channels[:4]
        ):
            axis = axes_flat[index]
            axis.plot(
                self.dataframe["Time"],
                self.dataframe[channel],
                linewidth=0.8,
            )

            axis.set_title(
                channel.replace(
                    "Att_Channel-",
                    "Channel ",
                )
            )
            axis.set_xlabel("Time")
            axis.set_ylabel("Attenuation (dB)")
            axis.grid(
                True,
                alpha=0.3,
            )

        for index in range(
            len(self.available_channels),
            4,
        ):
            axes_flat[index].set_axis_off()

        self.figure.suptitle(
            "Rain Attenuation — All Channels",
            fontsize=13,
        )

    def draw_single_channel(self):
        channel = (
            self.channel_combo.currentData()
        )

        if not channel:
            channel = self.available_channels[0]

        axis = self.figure.add_subplot(111)

        axis.plot(
            self.dataframe["Time"],
            self.dataframe[channel],
            linewidth=1.0,
        )

        axis.set_title(
            f"Rain Attenuation — {channel}"
        )
        axis.set_xlabel("Time")
        axis.set_ylabel("Attenuation (dB)")
        axis.grid(
            True,
            alpha=0.3,
        )

    def draw_comparison(self):
        axis = self.figure.add_subplot(111)

        for channel in self.available_channels:
            axis.plot(
                self.dataframe["Time"],
                self.dataframe[channel],
                linewidth=0.9,
                label=channel.replace(
                    "Att_Channel-",
                    "CH",
                ),
            )

        axis.set_title(
            "Rain Attenuation — Channel Comparison"
        )
        axis.set_xlabel("Time")
        axis.set_ylabel("Attenuation (dB)")
        axis.grid(
            True,
            alpha=0.3,
        )
        axis.legend()

    def clear_plot(self):
        self.figure.clear()

        axis = self.figure.add_subplot(111)
        axis.text(
            0.5,
            0.5,
            "Select a processed attenuation TXT file\n"
            "to begin plotting.",
            ha="center",
            va="center",
        )
        axis.set_axis_off()

        self.canvas.draw_idle()

    # ==========================================================
    # EXPORT
    # ==========================================================

    def export_png(self):
        self.export_figure(
            "png"
        )

    def export_pdf(self):
        self.export_figure(
            "pdf"
        )

    def export_figure(
        self,
        extension: str,
    ):
        if (
            self.dataframe is None
            or self.loaded_file is None
        ):
            return

        default_name = (
            f"{self.loaded_file.stem}_"
            f"{self.plot_type_combo.currentData()}."
            f"{extension}"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Plot as {extension.upper()}",
            default_name,
            f"{extension.upper()} Files (*.{extension});;"
            "All Files (*)",
        )

        if not file_path:
            return

        try:
            self.figure.savefig(
                file_path,
                dpi=300,
                bbox_inches="tight",
            )

            self.summary_label.setText(
                f"Plot exported successfully:\n{file_path}"
            )

            self.log_console(
                f"[DRSP] Plot exported: {file_path}"
            )

        except Exception as exc:
            self.summary_label.setText(
                f"Plot export failed:\n{exc}"
            )

            self.log_console(
                f"[DRSP] Plot export failed: {exc}"
            )

    # ==========================================================
    # CONSOLE
    # ==========================================================

    def log_console(
        self,
        message: str,
    ):
        window = self.window()

        if hasattr(
            window,
            "console_text",
        ):
            window.console_text.append(
                message
            )

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def closeEvent(self, event):
        self.plot_panel.close_popout_if_open()
        self.summary_panel.close_popout_if_open()
        event.accept()
