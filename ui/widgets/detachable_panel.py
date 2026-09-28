from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class DetachablePanel(QFrame):
    """
    Reusable Vivado-style detachable/resizable panel.

    Features
    --------
    - Embedded inside the normal workspace.
    - Dedicated title bar.
    - Detach button.
    - Separate resizable window.
    - Close detached window -> automatically re-dock.
    - Content remains alive while detached.
    """

    def __init__(
        self,
        title: str,
        content: QWidget | None = None,
        parent: QWidget | None = None,
    ):

        super().__init__(parent)

        self.panel_title = title

        self.content_widget: QWidget | None = None

        self.popout_dialog: QDialog | None = None

        self.setObjectName(
            "DetachablePanel"
        )

        self.setMinimumSize(
            0,
            0,
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.setup_ui()

        if content is not None:

            self.set_content(
                content
            )

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        self.main_layout = QVBoxLayout(
            self
        )

        self.main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.main_layout.setSpacing(
            0
        )

        # ------------------------------------------------------
        # TITLE BAR
        # ------------------------------------------------------

        self.title_bar = QFrame()

        self.title_bar.setObjectName(
            "DetachablePanelTitleBar"
        )

        self.title_bar.setMinimumHeight(
            32
        )

        self.title_bar.setMaximumHeight(
            32
        )

        title_layout = QHBoxLayout(
            self.title_bar
        )

        title_layout.setContentsMargins(
            10,
            2,
            5,
            2,
        )

        title_layout.setSpacing(
            5
        )

        self.title_label = QLabel(
            self.panel_title
        )

        self.title_label.setObjectName(
            "DetachablePanelTitle"
        )

        title_layout.addWidget(
            self.title_label
        )

        title_layout.addStretch()

        self.popout_button = QPushButton(
            "⤢"
        )

        self.popout_button.setObjectName(
            "DetachablePanelButton"
        )

        self.popout_button.setFixedSize(
            28,
            26,
        )

        self.popout_button.setToolTip(
            "Open in separate window"
        )

        self.popout_button.clicked.connect(
            self.toggle_popout
        )

        title_layout.addWidget(
            self.popout_button
        )

        self.main_layout.addWidget(
            self.title_bar
        )

        # ------------------------------------------------------
        # CONTENT
        # ------------------------------------------------------

        self.content_frame = QFrame()

        self.content_frame.setObjectName(
            "DetachablePanelContent"
        )

        self.content_frame.setMinimumSize(
            0,
            0,
        )

        self.content_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.content_layout = QVBoxLayout(
            self.content_frame
        )

        self.content_layout.setContentsMargins(
            6,
            6,
            6,
            6,
        )

        self.content_layout.setSpacing(
            0
        )

        self.main_layout.addWidget(
            self.content_frame,
            stretch=1,
        )

    # ==========================================================
    # CONTENT
    # ==========================================================

    def set_content(
        self,
        widget: QWidget,
    ):

        if self.content_widget is not None:

            self.content_layout.removeWidget(
                self.content_widget
            )

            self.content_widget.setParent(
                None
            )

        self.content_widget = widget

        self.content_widget.setParent(
            self.content_frame
        )

        self.content_widget.setMinimumSize(
            0,
            0,
        )

        self.content_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.content_layout.addWidget(
            self.content_widget
        )

    # ==========================================================
    # POP OUT / RESTORE
    # ==========================================================

    def toggle_popout(self):

        if self.popout_dialog is None:

            self.pop_out()

        else:

            self.restore_content()

    def pop_out(self):

        if self.content_widget is None:
            return

        # ------------------------------------------------------
        # Remove content from embedded layout
        # ------------------------------------------------------

        self.content_layout.removeWidget(
            self.content_widget
        )

        # ------------------------------------------------------
        # Create independent window
        # ------------------------------------------------------

        dialog = QDialog(
            self.window()
        )

        dialog.setWindowTitle(
            self.panel_title
        )

        dialog.setWindowFlag(
            Qt.Window
        )

        dialog.setModal(
            False
        )

        dialog.setMinimumSize(
            650,
            400,
        )

        dialog.resize(
            1200,
            700,
        )

        dialog_layout = QVBoxLayout(
            dialog
        )

        dialog_layout.setContentsMargins(
            6,
            6,
            6,
            6,
        )

        dialog_layout.setSpacing(
            0
        )

        # ------------------------------------------------------
        # Put content inside detached window
        # ------------------------------------------------------

        self.content_widget.setParent(
            dialog
        )

        self.content_widget.setMinimumSize(
            0,
            0,
        )

        self.content_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        dialog_layout.addWidget(
            self.content_widget,
            stretch=1,
        )

        self.content_widget.show()

        # ------------------------------------------------------
        # Store dialog reference
        # ------------------------------------------------------

        self.popout_dialog = dialog

        # ------------------------------------------------------
        # Change button
        # ------------------------------------------------------

        self.popout_button.setText(
            "↙"
        )

        self.popout_button.setToolTip(
            "Return to main workspace"
        )

        # ------------------------------------------------------
        # Closing the window -> dock again
        # ------------------------------------------------------

        dialog.finished.connect(
            self.on_popout_closed
        )

        dialog.show()

        dialog.raise_()

        dialog.activateWindow()

    def on_popout_closed(
        self,
        result,
    ):

        del result

        if self.popout_dialog is None:
            return

        self.restore_content()

    def restore_content(self):

        dialog = self.popout_dialog

        if dialog is None:
            return

        if self.content_widget is None:
            return

        # ------------------------------------------------------
        # Remove content from detached window
        # ------------------------------------------------------

        dialog_layout = (
            dialog.layout()
        )

        if dialog_layout is not None:

            dialog_layout.removeWidget(
                self.content_widget
            )

        # ------------------------------------------------------
        # Reparent back to panel
        # ------------------------------------------------------

        self.content_widget.setParent(
            self.content_frame
        )

        self.content_widget.setMinimumSize(
            0,
            0,
        )

        self.content_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.content_layout.addWidget(
            self.content_widget,
            stretch=1,
        )

        self.content_widget.show()

        # ------------------------------------------------------
        # Reset button
        # ------------------------------------------------------

        self.popout_dialog = None

        self.popout_button.setText(
            "⤢"
        )

        self.popout_button.setToolTip(
            "Open in separate window"
        )

        dialog.close()

        dialog.deleteLater()

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def close_popout_if_open(self):

        if self.popout_dialog is not None:

            self.restore_content()