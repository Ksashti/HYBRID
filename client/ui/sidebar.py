"""Sidebar: server name, channel list, users per channel."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QInputDialog, QMenu, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from client.ui.theme import (
    BG_SIDEBAR, BG_DARK, BG_HOVER, BG_INPUT,
    TEXT_BRIGHT, TEXT_MUTED, TEXT_NORMAL, ACCENT, SEPARATOR
)
from client.ui.widgets import ChannelItemWidget, UserItemWidget


class Sidebar(QWidget):
    channel_selected = pyqtSignal(str)  # channel_name
    channel_create_requested = pyqtSignal(str)  # name
    channel_delete_requested = pyqtSignal(str)  # name
    user_volume_requested = pyqtSignal(str)  # username

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(f"background-color: {BG_SIDEBAR};")
        self.channels = {}  # {name: ChannelItemWidget}
        self.channel_users = {}  # {channel_name: [UserItemWidget]}
        self.current_channel = None
        self.my_username = ""
        self.speaking_users = set()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Server header
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"""
            background-color: {BG_SIDEBAR};
            border-bottom: 1px solid {SEPARATOR};
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        server_name = QLabel("HYBRID")
        server_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        server_name.setStyleSheet(f"color: {TEXT_BRIGHT};")
        h_layout.addWidget(server_name)
        h_layout.addStretch()

        layout.addWidget(header)

        # Channel section header
        section = QWidget()
        section.setStyleSheet(f"background: {BG_SIDEBAR};")
        s_layout = QHBoxLayout(section)
        s_layout.setContentsMargins(16, 12, 8, 4)

        ch_label = QLabel("ГОЛОСОВЫЕ КАНАЛЫ")
        ch_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ch_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        s_layout.addWidget(ch_label, 1)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(20, 20)
        add_btn.setFont(QFont("Segoe UI", 14))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: none;
                font-size: 16px;
            }}
            QPushButton:hover {{ color: {TEXT_BRIGHT}; }}
        """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("Создать канал")
        add_btn.clicked.connect(self._on_create_channel)
        s_layout.addWidget(add_btn)

        layout.addWidget(section)

        # Scrollable channel + users area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {BG_SIDEBAR};
                border: none;
            }}
        """)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.channel_container = QWidget()
        self.channel_container.setStyleSheet(f"background: {BG_SIDEBAR};")
        self.channel_layout = QVBoxLayout(self.channel_container)
        self.channel_layout.setContentsMargins(8, 0, 8, 8)
        self.channel_layout.setSpacing(2)
        self.channel_layout.addStretch()

        scroll.setWidget(self.channel_container)
        layout.addWidget(scroll, 1)

    def set_username(self, username):
        self.my_username = username

    def update_channels(self, channel_names):
        """Rebuild the channel list."""
        # Clear old
        while self.channel_layout.count() > 1:
            item = self.channel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.channels.clear()
        self.channel_users.clear()

        for name in channel_names:
            self._add_channel_widget(name)

    def _add_channel_widget(self, name):
        is_active = (name == self.current_channel)
        ch_widget = ChannelItemWidget(name, is_active=is_active)
        ch_widget.clicked.connect(self._on_channel_click)
        ch_widget.right_clicked.connect(self._on_channel_right_click)

        idx = self.channel_layout.count() - 1  # Before stretch
        self.channel_layout.insertWidget(idx, ch_widget)
        self.channels[name] = ch_widget
        self.channel_users[name] = []

    def update_channel_users(self, channel_name, usernames):
        """Update user list under a channel."""
        # Remove old user widgets for this channel
        if channel_name in self.channel_users:
            for uw in self.channel_users[channel_name]:
                uw.deleteLater()
            self.channel_users[channel_name] = []

        if channel_name not in self.channels:
            return

        # Find channel widget index
        ch_widget = self.channels[channel_name]
        idx = self.channel_layout.indexOf(ch_widget)

        # Update user count
        ch_widget.set_user_count(len(usernames))

        # Add user widgets after channel widget
        for i, username in enumerate(usernames):
            uw = UserItemWidget(username, is_self=(username == self.my_username))
            uw.right_clicked.connect(self._on_user_right_click)
            if username in self.speaking_users:
                uw.set_speaking(True)
            self.channel_layout.insertWidget(idx + 1 + i, uw)
            self.channel_users[channel_name].append(uw)

    def set_active_channel(self, channel_name):
        """Highlight the active channel."""
        old = self.current_channel
        self.current_channel = channel_name
        if old and old in self.channels:
            self.channels[old].set_active(False)
        if channel_name and channel_name in self.channels:
            self.channels[channel_name].set_active(True)

    def highlight_speaking(self, username):
        """Show speaking indicator for a user."""
        self.speaking_users.add(username)
        for ch_users in self.channel_users.values():
            for uw in ch_users:
                if uw.username == username:
                    uw.set_speaking(True)

    def clear_speaking(self, username):
        """Remove speaking indicator."""
        self.speaking_users.discard(username)
        for ch_users in self.channel_users.values():
            for uw in ch_users:
                if uw.username == username:
                    uw.set_speaking(False)

    def _on_channel_click(self, name):
        self.channel_selected.emit(name)

    def _on_channel_right_click(self, name):
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить канал")
        action = menu.exec_(self.cursor().pos())
        if action == delete_action:
            self.channel_delete_requested.emit(name)

    def _on_create_channel(self):
        name, ok = QInputDialog.getText(
            self, "Создать канал", "Имя канала:",
        )
        if ok and name.strip():
            self.channel_create_requested.emit(name.strip())

    def _on_user_right_click(self, username):
        menu = QMenu(self)
        vol_action = menu.addAction(f"Громкость: {username}")
        action = menu.exec_(self.cursor().pos())
        if action == vol_action:
            self.user_volume_requested.emit(username)
