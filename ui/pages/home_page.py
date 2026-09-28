from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    """
    DRSP Rain Attenuation Tool dashboard.

    The Home page is intentionally a command center rather than another
    processing workspace. It provides:

        - Workspace status
        - Current dataset summary
        - Quick navigation actions
        - Recent console activity
        - Processed-data overview

    It does not duplicate backend processing or analysis logic.
    """

    def __init__(self):
        super().__init__()

        self.processed_root = Path("Processed_Data").resolve()

        self.setup_ui()
        self.apply_home_style()

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        title = QLabel("DRSP Rain Attenuation Tool")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Engineering workspace for rain attenuation processing, "
            "analysis, visualization, reporting, and RF data utilities."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ------------------------------------------------------
        # WORKSPACE + DATASET
        # ------------------------------------------------------

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(12)

        self.workspace_status_card = self.create_workspace_status_card()
        self.dataset_card = self.create_dataset_card()

        top_grid.addWidget(self.workspace_status_card, 0, 0)
        top_grid.addWidget(self.dataset_card, 0, 1)

        top_grid.setColumnStretch(0, 1)
        top_grid.setColumnStretch(1, 1)

        layout.addLayout(top_grid)

        # ------------------------------------------------------
        # QUICK ACTIONS
        # ------------------------------------------------------

        quick_group = QGroupBox("Quick Actions")
        quick_layout = QGridLayout(quick_group)
        quick_layout.setContentsMargins(10, 12, 10, 12)
        quick_layout.setHorizontalSpacing(10)
        quick_layout.setVerticalSpacing(10)

        quick_actions = [
            ("▣", "Dataset", "Select and configure input data.", 1),
            ("⌕", "Inspection", "Inspect raw-data structure and quality.", 2),
            ("⚙", "Processing", "Run attenuation processing workflows.", 3),
            ("◒", "Plots", "Visualize processed attenuation data.", 5),
            ("▤", "Reports", "Review and export analysis reports.", 6),
            ("▱", "Processed Data", "Browse generated files and folders.", 8),
        ]

        for position, (icon, name, description, page_index) in enumerate(
            quick_actions
        ):
            card = self.create_action_card(
                icon,
                name,
                description,
                page_index,
            )

            row = position // 3
            column = position % 3

            quick_layout.addWidget(card, row, column)

        for column in range(3):
            quick_layout.setColumnStretch(column, 1)

        layout.addWidget(quick_group)

        # ------------------------------------------------------
        # LOWER DASHBOARD
        # ------------------------------------------------------

        lower_grid = QGridLayout()
        lower_grid.setHorizontalSpacing(12)
        lower_grid.setVerticalSpacing(12)

        self.activity_card = self.create_activity_card()
        self.data_overview_card = self.create_data_overview_card()

        lower_grid.addWidget(self.activity_card, 0, 0)
        lower_grid.addWidget(self.data_overview_card, 0, 1)

        lower_grid.setColumnStretch(0, 3)
        lower_grid.setColumnStretch(1, 2)

        layout.addLayout(lower_grid, stretch=1)

        # Small footer
        footer = QLabel(
            "DRSP Rain Attenuation Tool  •  Engineering Workspace"
        )
        footer.setObjectName("HomeFooter")
        footer.setAlignment(Qt.AlignRight)

        layout.addWidget(footer)

    # ==========================================================
    # CARD HELPERS
    # ==========================================================

    def make_card_frame(self, object_name: str = "HomeCard") -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )
        return card

    def create_workspace_status_card(self) -> QFrame:
        card = self.make_card_frame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)

        title = QLabel("Workspace Status")
        title.setObjectName("HomeCardTitle")
        layout.addWidget(title)

        self.workspace_ready_label = QLabel("●  Ready")
        self.workspace_ready_label.setObjectName("HomeStatusReady")
        layout.addWidget(self.workspace_ready_label)

        self.workspace_processed_label = QLabel(
            "Processed Data     Checking..."
        )
        self.workspace_reports_label = QLabel(
            "Reports            Checking..."
        )
        self.workspace_analysis_label = QLabel(
            "Analysis           Ready"
        )

        for label in (
            self.workspace_processed_label,
            self.workspace_reports_label,
            self.workspace_analysis_label,
        ):
            label.setObjectName("HomeMetricLabel")
            layout.addWidget(label)

        layout.addStretch()

        return card

    def create_dataset_card(self) -> QFrame:
        card = self.make_card_frame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)

        title = QLabel("Current Dataset")
        title.setObjectName("HomeCardTitle")
        layout.addWidget(title)

        self.dataset_status_label = QLabel("No dataset selected")
        self.dataset_status_label.setObjectName("HomeDatasetStatus")
        self.dataset_status_label.setWordWrap(True)
        layout.addWidget(self.dataset_status_label)

        self.dataset_details_label = QLabel(
            "Choose a dataset from the Dataset workspace."
        )
        self.dataset_details_label.setObjectName("HomeMetricLabel")
        self.dataset_details_label.setWordWrap(True)
        layout.addWidget(self.dataset_details_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        select_button = QPushButton("Select Dataset")
        select_button.setMinimumHeight(34)
        select_button.clicked.connect(
            lambda: self.open_page(1, "Dataset")
        )

        inspect_button = QPushButton("Inspect")
        inspect_button.setMinimumHeight(34)
        inspect_button.clicked.connect(
            lambda: self.open_page(2, "Inspection")
        )

        button_row.addWidget(select_button)
        button_row.addWidget(inspect_button)

        layout.addLayout(button_row)

        return card

    def create_action_card(
        self,
        icon: str,
        name: str,
        description: str,
        page_index: int,
    ) -> QFrame:
        card = self.make_card_frame("HomeActionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setObjectName("HomeActionIcon")
        layout.addWidget(icon_label)

        title = QLabel(name)
        title.setObjectName("HomeActionTitle")
        layout.addWidget(title)

        description_label = QLabel(description)
        description_label.setObjectName("HomeActionDescription")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        button = QPushButton("Open")
        button.setMinimumHeight(30)
        button.clicked.connect(
            lambda checked=False, idx=page_index, text=name:
            self.open_page(idx, text)
        )

        layout.addWidget(button)

        return card

    def create_activity_card(self) -> QFrame:
        card = self.make_card_frame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("Recent Activity")
        title.setObjectName("HomeCardTitle")
        layout.addWidget(title)

        self.activity_label = QLabel(
            "No recent activity."
        )
        self.activity_label.setObjectName("HomeActivity")
        self.activity_label.setWordWrap(False)
        self.activity_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        layout.addWidget(
            self.activity_label,
            stretch=1,
        )

        return card

    def create_data_overview_card(self) -> QFrame:
        card = self.make_card_frame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)

        title = QLabel("Data Overview")
        title.setObjectName("HomeCardTitle")
        layout.addWidget(title)

        self.overview_years_label = QLabel("Years              —")
        self.overview_months_label = QLabel("Months             —")
        self.overview_days_label = QLabel("Processed Days     —")
        self.overview_files_label = QLabel("Attenuation Files  —")
        self.overview_reports_label = QLabel("Reports             —")

        for label in (
            self.overview_years_label,
            self.overview_months_label,
            self.overview_days_label,
            self.overview_files_label,
            self.overview_reports_label,
        ):
            label.setObjectName("HomeMetricLabel")
            layout.addWidget(label)

        layout.addStretch()

        return card

    # ==========================================================
    # REFRESH
    # ==========================================================

    def showEvent(self, event):
        super().showEvent(event)

        self.refresh_dashboard()

    def refresh_dashboard(self):
        self.refresh_dataset()
        self.refresh_workspace_status()
        self.refresh_activity()
        self.refresh_data_overview()

    # ==========================================================
    # CURRENT DATASET
    # ==========================================================

    def refresh_dataset(self):
        dataset_page = self.get_page(1)

        selected_path = None
        selected_type = None
        selected_format = None

        if dataset_page is not None and hasattr(
            dataset_page,
            "get_selection",
        ):
            try:
                (
                    selected_path,
                    selected_type,
                    selected_format,
                ) = dataset_page.get_selection()
            except Exception:
                selected_path = None
                selected_type = None
                selected_format = None

        if selected_path:
            path = Path(selected_path)

            self.dataset_status_label.setText(
                f"●  {path.name}"
            )

            details = []

            if selected_type:
                details.append(
                    f"Type: {selected_type}"
                )

            if selected_format:
                details.append(
                    f"Format: {selected_format}"
                )

            details.append(
                str(path.parent)
            )

            self.dataset_details_label.setText(
                "\n".join(details)
            )
        else:
            self.dataset_status_label.setText(
                "No dataset selected"
            )
            self.dataset_details_label.setText(
                "Choose a dataset from the Dataset workspace."
            )

    # ==========================================================
    # WORKSPACE STATUS
    # ==========================================================

    def refresh_workspace_status(self):
        root_exists = self.processed_root.exists()

        self.workspace_processed_label.setText(
            "Processed Data     "
            + ("Available" if root_exists else "Not Available")
        )

        reports_available = self.has_reports()

        self.workspace_reports_label.setText(
            "Reports            "
            + ("Available" if reports_available else "None Yet")
        )

        self.workspace_ready_label.setText(
            "●  Ready"
        )

    def has_reports(self) -> bool:
        if not self.processed_root.exists():
            return False

        report_names = {
            "Inspection_Reports",
            "Validation_Reports",
            "Exceedence_by_Ratio",
            "Exceedence_by_Total_Seconds",
            "Exceedance_Tables",
            "Statistics",
        }

        for child in self.processed_root.rglob("*"):
            if child.is_dir() and child.name in report_names:
                return True

        return False

    # ==========================================================
    # RECENT ACTIVITY
    # ==========================================================

    def refresh_activity(self):
        window = self.window()

        if not hasattr(window, "console_text"):
            self.activity_label.setText(
                "No recent activity."
            )
            return

        text = window.console_text.toPlainText().strip()

        if not text:
            self.activity_label.setText(
                "No recent activity."
            )
            return

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        lines = lines[-8:]

        if not lines:
            self.activity_label.setText(
                "No recent activity."
            )
            return

        self.activity_label.setText(
            "\n".join(lines)
        )

    # ==========================================================
    # DATA OVERVIEW
    # ==========================================================

    def refresh_data_overview(self):
        root = self.processed_root

        if not root.exists():
            self.set_overview_values(
                0,
                0,
                0,
                0,
                0,
            )
            return

        year_dirs = sorted(
            [
                path
                for path in root.iterdir()
                if path.is_dir() and path.name.isdigit()
            ],
            key=lambda path: path.name,
        )

        month_count = 0
        day_count = 0
        attenuation_file_count = 0

        for year_dir in year_dirs:
            month_dirs = [
                path
                for path in year_dir.iterdir()
                if path.is_dir()
            ]

            month_count += len(month_dirs)

            for month_dir in month_dirs:
                day_dirs = [
                    path
                    for path in month_dir.iterdir()
                    if path.is_dir()
                ]

                day_count += len(day_dirs)

        try:
            attenuation_file_count = sum(
                1
                for path in root.rglob("Attenuation_*.txt")
                if path.is_file()
            )
        except Exception:
            attenuation_file_count = 0

        report_count = self.count_report_files()

        self.set_overview_values(
            len(year_dirs),
            month_count,
            day_count,
            attenuation_file_count,
            report_count,
        )

    def count_report_files(self) -> int:
        root = self.processed_root

        if not root.exists():
            return 0

        report_names = {
            "Inspection_Reports",
            "Validation_Reports",
            "Exceedence_by_Ratio",
            "Exceedence_by_Total_Seconds",
            "Exceedance_Tables",
            "Statistics",
        }

        count = 0

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            try:
                if path.parent.name in report_names:
                    count += 1
            except Exception:
                pass

        return count

    def set_overview_values(
        self,
        years: int,
        months: int,
        days: int,
        attenuation_files: int,
        reports: int,
    ):
        self.overview_years_label.setText(
            f"Years              {years:,}"
        )
        self.overview_months_label.setText(
            f"Months             {months:,}"
        )
        self.overview_days_label.setText(
            f"Processed Days     {days:,}"
        )
        self.overview_files_label.setText(
            f"Attenuation Files  {attenuation_files:,}"
        )
        self.overview_reports_label.setText(
            f"Reports             {reports:,}"
        )

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def get_page(self, index: int):
        window = self.window()

        if not hasattr(window, "pages"):
            return None

        pages = getattr(window, "pages", [])

        if index < 0 or index >= len(pages):
            return None

        return pages[index]

    def open_page(
        self,
        index: int,
        page_name: str,
    ):
        window = self.window()

        if hasattr(window, "show_page"):
            window.show_page(
                index,
                page_name,
            )

    # ==========================================================
    # HOME-SPECIFIC THEME
    # ==========================================================

    def apply_home_style(self):
        self.setStyleSheet(
            """
            #HomeCard {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-radius: 5px;
            }

            #HomeActionCard {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-radius: 5px;
            }

            #HomeActionCard:hover {
                border: 1px solid #007acc;
                background-color: #29292d;
            }

            #HomeCardTitle {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            #HomeStatusReady {
                color: #73c991;
                font-size: 15px;
                font-weight: bold;
            }

            #HomeDatasetStatus {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }

            #HomeMetricLabel {
                color: #b8b8b8;
                font-size: 11px;
            }

            #HomeActionIcon {
                color: #61afef;
                font-size: 20px;
                font-weight: bold;
            }

            #HomeActionTitle {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            #HomeActionDescription {
                color: #9d9d9d;
                font-size: 11px;
            }

            #HomeActivity {
                color: #b8b8b8;
                background-color: #181818;
                border: 1px solid #303030;
                padding: 8px;
                font-family: Consolas;
                font-size: 10px;
            }

            #HomeFooter {
                color: #666666;
                font-size: 10px;
            }
            """
        )
