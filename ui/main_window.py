from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
)

from ui.pages.analysis_page import AnalysisPage
from ui.pages.data_explorer_page import DataExplorerPage
from ui.pages.dataset_page import DatasetPage
from ui.pages.home_page import HomePage
from ui.pages.inspection_page import InspectionPage
from ui.pages.plots_page import PlotsPage
from ui.pages.processing_page import ProcessingPage
from ui.pages.reports_page import ReportsPage
from ui.pages.tools_page import ToolsPage

from ui.widgets.detachable_panel import (
    DetachablePanel,
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "DRSP Rain Attenuation Tool"
        )

        self.setMinimumSize(
            800,
            500,
        )

        self.resize(
            1400,
            850,
        )

        self.setup_menu_bar()
        self.setup_ui()
        self.apply_theme()

        self.show_page(
            0,
            "Home",
        )

    # ==========================================================
    # MENU BAR
    # ==========================================================

    def setup_menu_bar(self):

        menu_bar = self.menuBar()

        # ------------------------------------------------------
        # FILE
        # ------------------------------------------------------

        file_menu = menu_bar.addMenu(
            "File"
        )

        file_menu.addAction(
            QAction(
                "New Workspace",
                self,
            )
        )

        file_menu.addAction(
            QAction(
                "Open Dataset",
                self,
            )
        )

        file_menu.addSeparator()

        exit_action = QAction(
            "Exit",
            self,
        )

        exit_action.triggered.connect(
            self.close
        )

        file_menu.addAction(
            exit_action
        )

        # ------------------------------------------------------
        # VIEW
        # ------------------------------------------------------

        view_menu = menu_bar.addMenu(
            "View"
        )

        self.view_console_action = QAction(
            "Hide Console",
            self,
        )

        self.view_console_action.setCheckable(
            True
        )

        self.view_console_action.setChecked(
            True
        )

        self.view_console_action.triggered.connect(
            self.toggle_console
        )

        view_menu.addAction(
            self.view_console_action
        )

        # ------------------------------------------------------
        # ANALYSIS
        # ------------------------------------------------------

        analysis_menu = menu_bar.addMenu(
            "Analysis"
        )

        analysis_menu.addAction(
            QAction(
                "Data Processing",
                self,
            )
        )

        analysis_menu.addAction(
            QAction(
                "Statistics",
                self,
            )
        )

        analysis_menu.addAction(
            QAction(
                "Exceedance Analysis",
                self,
            )
        )

        # ------------------------------------------------------
        # TOOLS
        # ------------------------------------------------------

        tools_menu = menu_bar.addMenu(
            "Tools"
        )

        tools_menu.addAction(
            QAction(
                "Data Inspector",
                self,
            )
        )

        tools_menu.addAction(
            QAction(
                "Data Validator",
                self,
            )
        )

        tools_menu.addSeparator()

        tools_menu.addAction(
            QAction(
                "RF Spectrum Analyzer",
                self,
            )
        )

        # ------------------------------------------------------
        # WINDOW
        # ------------------------------------------------------

        menu_bar.addMenu(
            "Window"
        )

        # ------------------------------------------------------
        # HELP
        # ------------------------------------------------------

        help_menu = menu_bar.addMenu(
            "Help"
        )

        help_menu.addAction(
            QAction(
                "About DRSP Tool",
                self,
            )
        )

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def setup_ui(self):

        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        # ======================================================
        # HORIZONTAL WORKSPACE SPLITTER
        # ======================================================

        self.workspace_splitter = QSplitter(
            Qt.Horizontal
        )

        self.workspace_splitter.setChildrenCollapsible(
            True
        )

        self.workspace_splitter.setHandleWidth(
            8
        )

        self.workspace_splitter.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Ignored,
        )

        self.workspace_splitter.setMinimumSize(
            0,
            0,
        )

        # ------------------------------------------------------
        # NAVIGATION
        # ------------------------------------------------------

        navigation_panel = (
            self.create_navigation_panel()
        )

        # ------------------------------------------------------
        # SCROLLABLE NAVIGATION SIDEBAR
        # ------------------------------------------------------
        # Keep the left navigation visually fixed in width, but allow
        # its contents to scroll vertically when the window/console
        # leaves less vertical space than the navigation needs.
        self.navigation_scroll_area = QScrollArea()

        self.navigation_scroll_area.setObjectName(
            "NavigationScrollArea"
        )

        self.navigation_scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        self.navigation_scroll_area.setWidgetResizable(
            True
        )

        self.navigation_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.navigation_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.navigation_scroll_area.setMinimumSize(
            0,
            0,
        )

        self.navigation_scroll_area.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.navigation_scroll_area.setWidget(
            navigation_panel
        )

        self.navigation_scroll_area.setMinimumWidth(
            0
        )

        self.navigation_scroll_area.setMaximumWidth(
            600
        )

        # ------------------------------------------------------
        # PAGE STACK + GLOBAL WORKSPACE SCROLL AREA
        # ------------------------------------------------------

        self.page_stack = QStackedWidget()

        self.page_stack.setMinimumWidth(
            0
        )

        self.workspace_content_min_height = 680

        self.page_stack.setMinimumHeight(
            self.workspace_content_min_height
        )

        self.page_stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        # Page indexes are intentionally kept stable for the existing
        # workflow. The new Processed Data Explorer is appended at index 8.
        self.pages = [
            HomePage(),
            DatasetPage(),
            InspectionPage(),
            ProcessingPage(),
            AnalysisPage(),
            PlotsPage(),
            ReportsPage(),
            ToolsPage(),
            DataExplorerPage(),
        ]

        for page in self.pages:

            page.setMinimumWidth(
                0
            )

            page.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Preferred,
            )

            self.page_stack.addWidget(
                page
            )

        self.workspace_scroll_area = QScrollArea()

        self.workspace_scroll_area.setObjectName(
            "WorkspaceScrollArea"
        )

        self.workspace_scroll_area.setWidgetResizable(
            True
        )

        self.workspace_scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        self.workspace_scroll_area.setMinimumSize(
            0,
            0,
        )

        self.workspace_scroll_area.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.workspace_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.workspace_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.workspace_scroll_area.setWidget(
            self.page_stack
        )

        self.workspace_splitter.addWidget(
            self.navigation_scroll_area
        )

        self.workspace_splitter.addWidget(
            self.workspace_scroll_area
        )

        self.workspace_splitter.setStretchFactor(
            0,
            0,
        )

        self.workspace_splitter.setStretchFactor(
            1,
            1,
        )

        self.workspace_splitter.setSizes(
            [
                240,
                1160,
            ]
        )

        # ======================================================
        # CONSOLE
        # ======================================================

        self.console_panel = (
            self.create_console_panel()
        )

        self.console_panel.setMinimumHeight(
            55
        )

        self.console_panel.setMaximumHeight(
            16777215
        )

        self.console_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Ignored,
        )

        # ======================================================
        # MAIN VERTICAL SPLITTER
        # ======================================================

        self.main_splitter = QSplitter(
            Qt.Vertical
        )

        self.main_splitter.setChildrenCollapsible(
            True
        )

        self.main_splitter.setHandleWidth(
            10
        )

        self.main_splitter.setMinimumSize(
            0,
            0,
        )

        self.main_splitter.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.main_splitter.addWidget(
            self.workspace_splitter
        )

        self.main_splitter.addWidget(
            self.console_panel
        )

        self.workspace_splitter.setMinimumHeight(
            40
        )

        self.console_panel.setMinimumHeight(
            55
        )

        self.main_splitter.setStretchFactor(
            0,
            1,
        )

        self.main_splitter.setStretchFactor(
            1,
            1,
        )

        self.main_splitter.setCollapsible(
            0,
            True,
        )

        self.main_splitter.setCollapsible(
            1,
            True,
        )

        self.main_splitter.setSizes(
            [
                680,
                170,
            ]
        )

        main_layout.addWidget(
            self.main_splitter
        )

    # ==========================================================
    # NAVIGATION PANEL
    # ==========================================================

    def create_navigation_panel(self):

        panel = QFrame()

        panel.setObjectName(
            "NavigationPanel"
        )

        panel.setMinimumSize(
            0,
            0,
        )

        panel.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Minimum,
        )

        layout = QVBoxLayout(
            panel
        )

        # Make the panel's minimum height follow the complete navigation
        # content so QScrollArea can scroll instead of compressing it.
        layout.setSizeConstraint(
            QVBoxLayout.SetMinimumSize
        )

        layout.setContentsMargins(
            8,
            12,
            8,
            12,
        )

        layout.setSpacing(
            6
        )

        title = QLabel(
            "DRSP"
        )

        title.setObjectName(
            "NavigationTitle"
        )

        subtitle = QLabel(
            "WORKSPACE"
        )

        subtitle.setObjectName(
            "NavigationSubtitle"
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            15
        )

        navigation_items = [
            ("⌂", "Home", 0),
            ("▣", "Dataset", 1),
            ("⌕", "Inspection", 2),
            ("⚙", "Processing", 3),
            ("▥", "Analysis", 4),
            ("◒", "Plots", 5),
            ("▤", "Reports", 6),
            ("⌁", "Tools", 7),
        ]

        self.navigation_buttons = []

        for icon, text, index in (
            navigation_items
        ):

            button = QPushButton(
                f"{icon}   {text}"
            )

            button.setObjectName(
                "NavigationButton"
            )

            button.setMinimumHeight(
                42
            )

            button.clicked.connect(
                lambda checked=False,
                i=index,
                name=text:
                self.show_page(
                    i,
                    name,
                )
            )

            layout.addWidget(
                button
            )

            self.navigation_buttons.append(
                button
            )

        layout.addSpacing(12)

        explorer_label = QLabel("EXPLORER")
        explorer_label.setObjectName("NavigationSectionLabel")
        layout.addWidget(explorer_label)

        processed_button = QPushButton(
            "▱   Processed Data"
        )

        processed_button.setObjectName(
            "NavigationButton"
        )

        processed_button.setMinimumHeight(
            42
        )

        processed_button.clicked.connect(
            lambda checked=False:
            self.show_page(
                8,
                "Processed Data",
            )
        )

        layout.addWidget(processed_button)
        self.navigation_buttons.append(processed_button)

        layout.addStretch()

        version = QLabel(
            "DRSP Rain Attenuation Tool\nv1.0"
        )

        version.setObjectName(
            "VersionLabel"
        )

        layout.addWidget(
            version
        )

        return panel

    # ==========================================================
    # CONSOLE PANEL
    # ==========================================================

    def create_console_panel(self):

        self.console_text = QTextEdit()

        self.console_text.setReadOnly(
            True
        )

        self.console_text.setMinimumSize(
            0,
            0,
        )

        self.console_text.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored,
        )

        self.console_text.append(
            "[DRSP] Application started successfully."
        )

        self.console_text.append(
            "[DRSP] Workspace ready."
        )

        console_status_frame = QFrame()

        console_status_frame.setObjectName(
            "ConsoleStatusBar"
        )

        console_status_layout = QHBoxLayout(
            console_status_frame
        )

        console_status_layout.setContentsMargins(
            8,
            2,
            8,
            2,
        )

        console_status_layout.setSpacing(
            6
        )

        self.console_status_indicator = QLabel(
            "●"
        )

        self.console_status_indicator.setObjectName(
            "ConsoleStatusIndicator"
        )

        self.console_status_label = QLabel(
            "Ready — Home"
        )

        self.console_status_label.setObjectName(
            "ConsoleStatusLabel"
        )

        console_status_layout.addWidget(
            self.console_status_indicator
        )

        console_status_layout.addWidget(
            self.console_status_label
        )

        console_status_layout.addStretch()

        console_content = QWidget()

        console_content.setMinimumSize(
            0,
            0,
        )

        console_content.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored,
        )

        console_layout = QVBoxLayout(
            console_content
        )

        console_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        console_layout.setSpacing(
            0
        )

        console_layout.addWidget(
            self.console_text,
            stretch=1,
        )

        console_layout.addWidget(
            console_status_frame
        )

        panel = DetachablePanel(
            "Console",
            console_content,
        )

        panel.setMinimumSize(
            0,
            55,
        )

        panel.setMaximumHeight(
            16777215
        )

        panel.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored,
        )

        return panel

    # ==========================================================
    # SHOW / HIDE CONSOLE
    # ==========================================================

    def toggle_console(
        self,
        checked: bool,
    ):

        if checked:

            self.console_panel.show()

            self.view_console_action.setText(
                "Hide Console"
            )

            total_height = (
                self.main_splitter.height()
            )

            console_height = max(
                120,
                min(
                    300,
                    int(
                        total_height * 0.22
                    ),
                ),
            )

            self.main_splitter.setSizes(
                [
                    total_height
                    - console_height,
                    console_height,
                ]
            )

        else:

            self.console_panel.hide()

            self.view_console_action.setText(
                "Show Console"
            )

    # ==========================================================
    # PAGE SWITCHING
    # ==========================================================

    def show_page(
        self,
        index,
        page_name=None,
    ):

        if index == 2:

            dataset_page = (
                self.pages[1]
            )

            inspection_page = (
                self.pages[2]
            )

            (
                selected_path,
                selected_type,
                selected_format,
            ) = dataset_page.get_selection()

            inspection_page.set_selected_dataset(
                selected_path,
                selected_type,
                selected_format,
            )

        if index == 3:

            dataset_page = (
                self.pages[1]
            )

            processing_page = (
                self.pages[3]
            )

            (
                selected_path,
                selected_type,
                selected_format,
            ) = dataset_page.get_selection()

            processing_page.set_selected_dataset(
                selected_path,
                selected_type,
                selected_format,
            )

        if index == 8:
            explorer_page = self.pages[8]
            explorer_page.refresh_tree()

        self.page_stack.setCurrentIndex(
            index
        )

        if hasattr(
            self,
            "workspace_scroll_area",
        ):
            self.workspace_scroll_area.verticalScrollBar().setValue(
                0
            )

        if page_name is None:
            page_name = "Home"

        for i, button in enumerate(
            self.navigation_buttons
        ):

            button.setProperty(
                "active",
                i == index,
            )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

            button.update()

        self.console_text.append(
            f"[DRSP] Opened: {page_name}"
        )

        self.console_status_label.setText(
            f"Ready — {page_name}"
        )

    # ==========================================================
    # THEME
    # ==========================================================

    def apply_theme(self):

        self.setStyleSheet(
            """

            QMainWindow {
                background-color: #1e1e1e;
            }

            QMenuBar {
                background-color: #252526;
                color: #cccccc;
                border-bottom: 1px solid #3f3f46;
            }

            QMenuBar::item {
                padding: 6px 12px;
            }

            QMenuBar::item:selected {
                background-color: #37373d;
            }

            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3f3f46;
            }

            QMenu::item:selected {
                background-color: #094771;
            }

            #NavigationScrollArea {
                background-color: #181818;
                border: none;
            }

            #NavigationScrollArea QScrollBar:vertical {
                background-color: #181818;
                width: 10px;
                margin: 0px;
            }

            #NavigationScrollArea QScrollBar::handle:vertical {
                background-color: #4a4a4f;
                min-height: 35px;
                border-radius: 5px;
                margin: 2px;
            }

            #NavigationScrollArea QScrollBar::handle:vertical:hover {
                background-color: #007acc;
            }

            #NavigationScrollArea QScrollBar::add-line:vertical,
            #NavigationScrollArea QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }

            #NavigationScrollArea QScrollBar::add-page:vertical,
            #NavigationScrollArea QScrollBar::sub-page:vertical {
                background: #181818;
            }

            #NavigationPanel {
                background-color: #181818;
            }

            #NavigationTitle {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding-left: 10px;
            }

            #NavigationSubtitle {
                color: #858585;
                font-size: 10px;
                padding-left: 11px;
                letter-spacing: 2px;
            }

            #NavigationSectionLabel {
                color: #666666;
                font-size: 10px;
                font-weight: bold;
                padding-left: 12px;
                letter-spacing: 1px;
            }

            #NavigationButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding-left: 14px;
                border-radius: 4px;
                font-size: 13px;
            }

            #NavigationButton:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }

            #NavigationButton:pressed {
                background-color: #094771;
            }

            #NavigationButton[active="true"] {
                background-color: #2a2d2e;
                color: #ffffff;
                border-left: 3px solid #007acc;
            }

            #VersionLabel {
                color: #666666;
                font-size: 10px;
                padding: 10px;
            }

            #PageTitle {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }

            #PageSubtitle {
                color: #858585;
                font-size: 14px;
            }

            QLabel {
                color: #cccccc;
            }

            QGroupBox {
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QLineEdit,
            QComboBox {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
            }

            QComboBox QAbstractItemView {
                background-color: #252526;
                color: #cccccc;
                selection-background-color: #094771;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #007acc;
            }

            QPushButton {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 7px 14px;
            }

            QPushButton:hover {
                background-color: #37373d;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #094771;
            }

            QPushButton:disabled {
                background-color: #252526;
                color: #666666;
                border-color: #303030;
            }

            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3f3f46;
                alternate-background-color: #2a2a2a;
            }

            QTreeWidget::item {
                padding: 4px;
            }

            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }

            QTreeWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #3a3a3a;
                color: #cccccc;
                border: none;
                padding: 5px;
            }

            QProgressBar {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                text-align: center;
                height: 18px;
            }

            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }

            QTableWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                gridline-color: #3f3f46;
            }

            QTableWidget::item {
                padding: 5px;
            }

            QTableWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
            }

            #DetachablePanel {
                background-color: #252526;
                border: 1px solid #3f3f46;
                border-radius: 4px;
            }

            #DetachablePanelTitleBar {
                background-color: #2d2d30;
                border-bottom: 1px solid #3f3f46;
            }

            #DetachablePanelTitle {
                color: #cccccc;
                font-weight: bold;
                font-size: 12px;
            }

            #DetachablePanelButton {
                background-color: transparent;
                color: #bbbbbb;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 0;
                font-size: 16px;
            }

            #DetachablePanelButton:hover {
                background-color: #404044;
                color: #ffffff;
                border: 1px solid #555555;
            }

            #DetachablePanelButton:pressed {
                background-color: #094771;
            }

            #DetachablePanelContent {
                background-color: #252526;
            }

            QSplitter::handle {
                background-color: #3f3f46;
            }

            QSplitter::handle:hover {
                background-color: #007acc;
            }

            QSplitter::handle:vertical {
                height: 10px;
            }

            QSplitter::handle:horizontal {
                width: 10px;
            }

            #WorkspaceScrollArea {
                background-color: #1e1e1e;
                border: none;
            }

            #WorkspaceScrollArea QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 11px;
                margin: 0px;
            }

            #WorkspaceScrollArea QScrollBar::handle:vertical {
                background-color: #4a4a4f;
                min-height: 40px;
                border-radius: 5px;
                margin: 2px;
            }

            #WorkspaceScrollArea QScrollBar::handle:vertical:hover {
                background-color: #007acc;
            }

            #WorkspaceScrollArea QScrollBar::add-line:vertical,
            #WorkspaceScrollArea QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }

            #WorkspaceScrollArea QScrollBar::add-page:vertical,
            #WorkspaceScrollArea QScrollBar::sub-page:vertical {
                background: #1e1e1e;
            }

            #ConsolePanel {
                background-color: #181818;
            }

            #ConsoleStatusBar {
                background-color: #252526;
                border-top: 1px solid #303030;
            }

            #ConsoleStatusIndicator {
                color: #73c991;
                font-size: 9px;
            }

            #ConsoleStatusLabel {
                color: #858585;
                font-size: 10px;
            }

            #ExplorerPathLabel {
                color: #858585;
                font-family: Consolas;
                font-size: 11px;
            }

            #ExplorerSectionTitle {
                color: #858585;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                padding-left: 3px;
            }

            #ExplorerViewerTitle {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            #ExplorerViewerPath {
                color: #666666;
                font-family: Consolas;
                font-size: 10px;
            }

            #ExplorerEmptyTitle {
                color: #cccccc;
                font-size: 20px;
                font-weight: bold;
            }

            #ExplorerEmptyText {
                color: #777777;
                font-size: 12px;
            }

            QScrollArea {
                border: none;
                background-color: #252526;
            }

            QTextEdit {
                background-color: #111111;
                color: #cccccc;
                border: 1px solid #303030;
                font-family: Consolas;
                font-size: 11px;
            }

            QStatusBar {
                background-color: transparent;
                border: none;
                min-height: 0px;
                max-height: 0px;
            }

            """
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        if hasattr(
            self,
            "console_panel",
        ):
            self.console_panel.close_popout_if_open()

        for page in getattr(
            self,
            "pages",
            [],
        ):

            worker = getattr(
                page,
                "worker",
                None,
            )

            if worker is not None:
                try:
                    if worker.isRunning():
                        worker.quit()
                        worker.wait(1500)
                except Exception:
                    pass

        event.accept()
