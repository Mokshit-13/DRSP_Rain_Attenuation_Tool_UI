from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ReportsPage(QWidget):
    """
    Lightweight Reports & Results dashboard.

    This page does not duplicate report-generation logic. It simply explains
    what kinds of outputs the DRSP workflow generates and directs the user to
    the Processed Data Explorer for viewing the actual files.
    """

    def __init__(self):
        super().__init__()

        self.processed_root = Path("Processed_Data").resolve()

        self.setup_ui()
        self.apply_style()
        self.refresh_overview()

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        title = QLabel("Reports & Results")
        title.setObjectName("ReportsPageTitle")

        subtitle = QLabel(
            "All generated outputs can be viewed from the Processed Data "
            "Explorer. This page gives you a quick overview of what the "
            "DRSP workflow produces."
        )
        subtitle.setObjectName("ReportsPageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ------------------------------------------------------
        # EXPLORER BANNER
        # ------------------------------------------------------

        banner = QFrame()
        banner.setObjectName("ReportsExplorerBanner")

        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(16, 14, 16, 14)
        banner_layout.setSpacing(12)

        banner_text_layout = QVBoxLayout()
        banner_text_layout.setContentsMargins(0, 0, 0, 0)
        banner_text_layout.setSpacing(3)

        banner_title = QLabel(
            "Everything generated is available in Processed Data Explorer"
        )
        banner_title.setObjectName("ReportsBannerTitle")

        banner_text = QLabel(
            "Open folders, TXT files, Excel reports, and generated plots "
            "directly from the Explorer."
        )
        banner_text.setObjectName("ReportsBannerText")
        banner_text.setWordWrap(True)

        banner_text_layout.addWidget(banner_title)
        banner_text_layout.addWidget(banner_text)

        banner_layout.addLayout(banner_text_layout, stretch=1)

        self.open_explorer_button = QPushButton(
            "Open Processed Data Explorer"
        )
        self.open_explorer_button.setObjectName(
            "ReportsExplorerButton"
        )
        self.open_explorer_button.clicked.connect(
            self.open_explorer
        )

        banner_layout.addWidget(self.open_explorer_button)

        layout.addWidget(banner)

        # ------------------------------------------------------
        # QUICK OUTPUT COUNTS
        # ------------------------------------------------------

        overview_group = QFrame()
        overview_group.setObjectName("ReportsOverview")

        overview_layout = QGridLayout(overview_group)
        overview_layout.setContentsMargins(12, 12, 12, 12)
        overview_layout.setHorizontalSpacing(10)
        overview_layout.setVerticalSpacing(10)

        self.total_outputs_card = self.create_metric_card(
            "TOTAL OUTPUTS",
            "0",
            "Files generated under Processed_Data",
        )

        self.attenuation_card = self.create_metric_card(
            "ATTENUATION DATA",
            "0",
            "TXT files with per-second attenuation",
        )

        self.plot_card = self.create_metric_card(
            "GENERATED PLOTS",
            "0",
            "PNG attenuation plots",
        )

        self.excel_card = self.create_metric_card(
            "EXCEL REPORTS",
            "0",
            "XLSX analysis / validation outputs",
        )

        self.text_card = self.create_metric_card(
            "TEXT REPORTS",
            "0",
            "TXT report outputs",
        )

        self.day_card = self.create_metric_card(
            "PROCESSED DAYS",
            "0",
            "Day folders containing attenuation output",
        )

        cards = [
            self.total_outputs_card,
            self.attenuation_card,
            self.plot_card,
            self.excel_card,
            self.text_card,
            self.day_card,
        ]

        for position, card in enumerate(cards):
            row = position // 3
            column = position % 3
            overview_layout.addWidget(card, row, column)

        for column in range(3):
            overview_layout.setColumnStretch(column, 1)

        layout.addWidget(overview_group)

        # ------------------------------------------------------
        # WHAT THE TOOL GENERATES
        # ------------------------------------------------------

        section_title = QLabel("WHAT THE TOOL GENERATES")
        section_title.setObjectName("ReportsSectionTitle")

        layout.addWidget(section_title)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(12)
        cards_layout.setVerticalSpacing(12)

        attenuation_info = self.create_info_card(
            "▣",
            "Daily Attenuation Data",
            (
                "Processed rain-event folders contain per-second "
                "attenuation TXT files for the receiver channels."
            ),
            "Typical output: Attenuation_NARL_*.txt",
        )

        plot_info = self.create_info_card(
            "◒",
            "Attenuation Plots",
            (
                "Each processed day can also produce a 2×2 channel "
                "attenuation plot for visual inspection."
            ),
            "Typical output: Attenuation_NARL_*.png",
        )

        validation_info = self.create_info_card(
            "✓",
            "Validation Reports",
            (
                "INF-value validation can generate text and Excel "
                "reports containing affected folders, timestamps, "
                "and summary counts."
            ),
            "Folder: Processed_Data/Validation_Reports/",
        )

        exceedance_info = self.create_info_card(
            "↗",
            "Exceedance Tables",
            (
                "Yearly analysis can generate monthly exceedance "
                "tables in Excel format for attenuation thresholds."
            ),
            "Folder: Processed_Data/Exceedance_Tables/",
        )

        statistics_info = self.create_info_card(
            "▤",
            "Statistics & Analysis",
            (
                "The analysis workflow provides channel statistics, "
                "top attenuation events, exceedance analysis, and "
                "visual results."
            ),
            "Available from Analysis / Plots",
        )

        explorer_info = self.create_info_card(
            "⌁",
            "Everything in One Explorer",
            (
                "The Processed Data Explorer is the place to browse "
                "the actual generated folders and files."
            ),
            "Open Explorer to inspect the real outputs",
        )

        info_cards = [
            attenuation_info,
            plot_info,
            validation_info,
            exceedance_info,
            statistics_info,
            explorer_info,
        ]

        for position, card in enumerate(info_cards):
            row = position // 2
            column = position % 2
            cards_layout.addWidget(card, row, column)

        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)

        layout.addLayout(cards_layout)

        # ------------------------------------------------------
        # STORAGE LOCATION
        # ------------------------------------------------------

        storage = QFrame()
        storage.setObjectName("ReportsStorageFrame")

        storage_layout = QVBoxLayout(storage)
        storage_layout.setContentsMargins(14, 12, 14, 12)
        storage_layout.setSpacing(5)

        storage_title = QLabel("OUTPUT LOCATION")
        storage_title.setObjectName("ReportsStorageTitle")

        self.storage_path_label = QLabel(
            str(self.processed_root)
        )
        self.storage_path_label.setObjectName(
            "ReportsStoragePath"
        )
        self.storage_path_label.setWordWrap(True)
        self.storage_path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        storage_note = QLabel(
            "The Reports page is a summary only — the Explorer contains "
            "the actual files."
        )
        storage_note.setObjectName("ReportsStorageNote")
        storage_note.setWordWrap(True)

        storage_layout.addWidget(storage_title)
        storage_layout.addWidget(self.storage_path_label)
        storage_layout.addWidget(storage_note)

        layout.addWidget(storage)

        layout.addStretch()

    # ==========================================================
    # METRIC CARD
    # ==========================================================

    def create_metric_card(
        self,
        heading: str,
        value: str,
        description: str,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("ReportsMetricCard")
        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)

        heading_label = QLabel(heading)
        heading_label.setObjectName("ReportsMetricHeading")

        value_label = QLabel(value)
        value_label.setObjectName("ReportsMetricValue")

        description_label = QLabel(description)
        description_label.setObjectName("ReportsMetricDescription")
        description_label.setWordWrap(True)

        layout.addWidget(heading_label)
        layout.addWidget(value_label)
        layout.addWidget(description_label)

        card.value_label = value_label

        return card

    # ==========================================================
    # INFORMATION CARD
    # ==========================================================

    def create_info_card(
        self,
        icon: str,
        title: str,
        description: str,
        footer: str,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("ReportsInfoCard")
        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setObjectName("ReportsInfoIcon")

        title_label = QLabel(title)
        title_label.setObjectName("ReportsInfoTitle")
        title_label.setWordWrap(True)

        header.addWidget(icon_label)
        header.addWidget(title_label, stretch=1)

        description_label = QLabel(description)
        description_label.setObjectName("ReportsInfoDescription")
        description_label.setWordWrap(True)

        footer_label = QLabel(footer)
        footer_label.setObjectName("ReportsInfoFooter")
        footer_label.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(description_label)
        layout.addWidget(footer_label)

        return card

    # ==========================================================
    # SCANNING
    # ==========================================================

    def refresh_overview(self):
        """
        Count the currently available generated output files.

        This only scans the filesystem; it does not change any backend
        processing or report-generation behavior.
        """
        root = self.processed_root

        total_outputs = 0
        attenuation_txt = 0
        plot_png = 0
        excel_reports = 0
        text_reports = 0
        processed_days = set()

        if root.exists() and root.is_dir():
            for path in root.rglob("*"):
                if not path.is_file():
                    continue

                total_outputs += 1

                suffix = path.suffix.lower()
                name = path.name.lower()
                parent_parts = {
                    part.lower()
                    for part in path.parts
                }

                if (
                    "attenuation_narl_" in name
                    and suffix == ".txt"
                ):
                    attenuation_txt += 1
                    processed_days.add(
                        str(path.parent.resolve())
                    )

                if (
                    "attenuation_narl_" in name
                    and suffix == ".png"
                ):
                    plot_png += 1

                if suffix == ".xlsx":
                    excel_reports += 1

                if (
                    suffix == ".txt"
                    and (
                        "report" in name
                        or "reports" in name
                        or "validation_reports" in parent_parts
                    )
                ):
                    text_reports += 1

        self.total_outputs_card.value_label.setText(
            str(total_outputs)
        )

        self.attenuation_card.value_label.setText(
            str(attenuation_txt)
        )

        self.plot_card.value_label.setText(
            str(plot_png)
        )

        self.excel_card.value_label.setText(
            str(excel_reports)
        )

        self.text_card.value_label.setText(
            str(text_reports)
        )

        self.day_card.value_label.setText(
            str(len(processed_days))
        )

        self.storage_path_label.setText(
            str(root)
        )

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def open_explorer(self):
        window = self.window()

        if hasattr(window, "show_page"):
            window.show_page(
                8,
                "Processed Data",
            )

    # ==========================================================
    # REFRESH WHEN PAGE IS SHOWN
    # ==========================================================

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_overview()

    # ==========================================================
    # STYLE
    # ==========================================================

    def apply_style(self):
        self.setStyleSheet(
            """
            #ReportsPageTitle {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }

            #ReportsPageSubtitle {
                color: #858585;
                font-size: 14px;
            }

            #ReportsExplorerBanner {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-left: 3px solid #007acc;
                border-radius: 4px;
            }

            #ReportsBannerTitle {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            #ReportsBannerText {
                color: #858585;
                font-size: 11px;
            }

            #ReportsExplorerButton {
                background-color: #094771;
                color: #ffffff;
                border: 1px solid #0e639c;
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
            }

            #ReportsExplorerButton:hover {
                background-color: #0e639c;
            }

            #ReportsExplorerButton:pressed {
                background-color: #1177bb;
            }

            #ReportsOverview {
                background-color: transparent;
                border: none;
            }

            #ReportsMetricCard {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-radius: 4px;
            }

            #ReportsMetricHeading {
                color: #858585;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            #ReportsMetricValue {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }

            #ReportsMetricDescription {
                color: #777777;
                font-size: 10px;
            }

            #ReportsSectionTitle {
                color: #858585;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                padding-left: 2px;
            }

            #ReportsInfoCard {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                min-height: 115px;
            }

            #ReportsInfoIcon {
                color: #007acc;
                font-size: 18px;
                font-weight: bold;
                min-width: 24px;
            }

            #ReportsInfoTitle {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            #ReportsInfoDescription {
                color: #aaaaaa;
                font-size: 11px;
            }

            #ReportsInfoFooter {
                color: #666666;
                font-size: 10px;
                font-family: Consolas;
            }

            #ReportsStorageFrame {
                background-color: #181818;
                border: 1px solid #303030;
                border-radius: 4px;
            }

            #ReportsStorageTitle {
                color: #858585;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            #ReportsStoragePath {
                color: #cccccc;
                font-size: 11px;
                font-family: Consolas;
            }

            #ReportsStorageNote {
                color: #666666;
                font-size: 10px;
            }
            """
        )
