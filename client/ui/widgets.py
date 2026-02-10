"""Reusable custom widgets for the UI."""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from client.ui.theme import (
    BG_SIDEBAR, BG_HOVER, BG_SELECTED, TEXT_NORMAL, TEXT_BRIGHT,
    TEXT_MUTED, GREEN, ACCENT, RED
)


class UserItemWidget(QWidget):
    """A user entry in the channel user list."""
    right_clicked = pyqtSignal(str)  # username

    def __init__(self, username, is_self=False, parent=None):
        super().__init__(parent)
        self.username = username
        self.is_self = is_self
        self.speaking = False
        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.dot = QLabel("\u25CF")
        self.dot.setFont(QFont("Arial", 8))
        self.dot.setStyleSheet(f"color: {TEXT_MUTED};")
        self.dot.setFixedWidth(14)
        layout.addWidget(self.dot)

        self.name_label = QLabel(self.username)
        self.name_label.setFont(QFont("Segoe UI", 12))
        color = TEXT_BRIGHT if self.is_self else TEXT_NORMAL
        self.name_label.setStyleSheet(f"color: {color};")
        layout.addWidget(self.name_label, 1)

        self.setStyleSheet(f"""
            UserItemWidget {{
                background: transparent;
                border-radius: 4px;
            }}
            UserItemWidget:hover {{
                background: {BG_HOVER};
            }}
        """)

    def set_speaking(self, speaking):
        self.speaking = speaking
        if speaking:
            self.dot.setStyleSheet(f"color: {GREEN};")
            self.setStyleSheet(f"""
                UserItemWidget {{
                    background: rgba(67, 181, 129, 0.1);
                    border-radius: 4px;
                }}
            """)
        else:
            self.dot.setStyleSheet(f"color: {TEXT_MUTED};")
            self.setStyleSheet(f"""
                UserItemWidget {{
                    background: transparent;
                    border-radius: 4px;
                }}
                UserItemWidget:hover {{
                    background: {BG_HOVER};
                }}
            """)

    def contextMenuEvent(self, event):
        self.right_clicked.emit(self.username)
        event.accept()


class ChannelItemWidget(QWidget):
    """A voice channel entry in the sidebar."""
    clicked = pyqtSignal(str)  # channel_name
    right_clicked = pyqtSignal(str)  # channel_name

    def __init__(self, channel_name, user_count=0, is_active=False, parent=None):
        super().__init__(parent)
        self.channel_name = channel_name
        self.user_count = user_count
        self.is_active = is_active
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Voice icon
        icon = QLabel("\U0001F50A")
        icon.setFont(QFont("Segoe UI", 10))
        icon.setFixedWidth(20)
        layout.addWidget(icon)

        self.name_label = QLabel(self.channel_name)
        self.name_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.name_label, 1)

        self.count_label = QLabel(str(self.user_count) if self.user_count > 0 else "")
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet(f"color: {TEXT_MUTED};")
        self.count_label.setFixedWidth(24)
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

    def _update_style(self):
        if self.is_active:
            self.setStyleSheet(f"""
                ChannelItemWidget {{
                    background: {BG_SELECTED};
                    border-radius: 4px;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {TEXT_BRIGHT}; font-weight: bold;")
        else:
            self.setStyleSheet(f"""
                ChannelItemWidget {{
                    background: transparent;
                    border-radius: 4px;
                }}
                ChannelItemWidget:hover {{
                    background: {BG_HOVER};
                }}
            """)
            self.name_label.setStyleSheet(f"color: {TEXT_MUTED};")

    def set_active(self, active):
        self.is_active = active
        self._update_style()

    def set_user_count(self, count):
        self.user_count = count
        self.count_label.setText(str(count) if count > 0 else "")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.channel_name)
        event.accept()

    def contextMenuEvent(self, event):
        self.right_clicked.emit(self.channel_name)
        event.accept()
