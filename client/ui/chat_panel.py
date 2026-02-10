"""Chat panel: message display, typing indicator, message input."""

import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextBrowser, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor
from client.ui.theme import (
    BG_MAIN, BG_INPUT, BG_HOVER, BG_DARK, SEPARATOR,
    TEXT_BRIGHT, TEXT_MUTED, TEXT_NORMAL, ACCENT, GREEN, RED
)


class ChatPanel(QWidget):
    message_sent = pyqtSignal(str)
    typing = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_MAIN};")
        self.last_typing_time = 0
        self.channel_name = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar with channel name
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet(f"""
            background-color: {BG_MAIN};
            border-bottom: 1px solid {SEPARATOR};
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self.channel_label = QLabel("# General")
        self.channel_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.channel_label.setStyleSheet(f"color: {TEXT_BRIGHT};")
        top_layout.addWidget(self.channel_label)

        top_layout.addStretch()

        self.status_label = QLabel("Подключено")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet(f"color: {GREEN};")
        top_layout.addWidget(self.status_label)

        layout.addWidget(top_bar)

        # Chat display
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {BG_MAIN};
                color: {TEXT_NORMAL};
                border: none;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                padding: 10px 16px;
            }}
        """)
        layout.addWidget(self.chat_display, 1)

        # Typing indicator
        self.typing_label = QLabel("")
        self.typing_label.setFixedHeight(20)
        self.typing_label.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 11px;
            font-style: italic;
            padding-left: 16px;
            background: {BG_MAIN};
        """)
        layout.addWidget(self.typing_label)

        # Input area
        input_container = QWidget()
        input_container.setStyleSheet(f"background: {BG_MAIN};")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 4, 16, 16)
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Написать сообщение...")
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }}
        """)
        self.message_input.returnPressed.connect(self._on_send)
        self.message_input.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.message_input, 1)

        send_btn = QPushButton("Отправить")
        send_btn.setFixedHeight(38)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #677bc4; }}
        """)
        send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(send_btn)

        layout.addWidget(input_container)

    def set_channel_name(self, name):
        self.channel_name = name
        self.channel_label.setText(f"# {name}")

    def set_status(self, text, color=None):
        self.status_label.setText(text)
        if color:
            self.status_label.setStyleSheet(f"color: {color};")

    def add_message(self, text, color=None, bold=False):
        """Add a message to the chat display."""
        if color is None:
            color = TEXT_NORMAL
        weight = "bold" if bold else "normal"
        timestamp = time.strftime("%H:%M")
        html = (
            f'<span style="color: {TEXT_MUTED}; font-size: 11px;">[{timestamp}]</span> '
            f'<span style="color: {color}; font-weight: {weight};">{text}</span>'
        )
        self.chat_display.append(html)

    def add_own_message(self, username, text):
        self.add_message(f"[{username}]: {text}", ACCENT, bold=True)

    def add_other_message(self, username, text):
        self.add_message(f"[{username}]: {text}", TEXT_NORMAL)

    def add_system_message(self, text):
        self.add_message(text, GREEN)

    def add_error_message(self, text):
        self.add_message(text, RED)

    def show_typing(self, username):
        self.typing_label.setText(f"{username} печатает...")
        QTimer.singleShot(3000, lambda: self.typing_label.setText(""))

    def _on_send(self):
        text = self.message_input.text().strip()
        if text:
            self.message_sent.emit(text)
            self.message_input.clear()

    def _on_text_changed(self):
        now = time.time()
        if now - self.last_typing_time > 2:
            self.last_typing_time = now
            self.typing.emit()

    def clear_chat(self):
        self.chat_display.clear()
