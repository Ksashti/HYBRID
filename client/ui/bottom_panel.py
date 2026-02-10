"""Bottom panel: user info, mute mic, mute sound, voice controls, settings."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from client.ui.theme import (
    BG_DARK, BG_INPUT, BG_HOVER, SEPARATOR,
    TEXT_BRIGHT, TEXT_MUTED, TEXT_NORMAL, ACCENT, GREEN, RED
)


class BottomPanel(QWidget):
    mic_toggled = pyqtSignal(bool)  # True = muted
    sound_toggled = pyqtSignal(bool)  # True = muted
    settings_clicked = pyqtSignal()
    ptt_pressed = pyqtSignal()
    ptt_released = pyqtSignal()
    voice_mode_toggled = pyqtSignal()
    volume_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mic_muted = False
        self.sound_muted = False
        self.voice_mode = "ptt"
        self.setFixedHeight(64)
        self.setStyleSheet(f"""
            background-color: {BG_DARK};
            border-top: 1px solid {SEPARATOR};
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # User avatar (colored circle with initial)
        self.avatar = QLabel("")
        self.avatar.setFixedSize(36, 36)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.avatar.setStyleSheet(f"""
            background-color: {ACCENT};
            color: {TEXT_BRIGHT};
            border-radius: 18px;
        """)
        layout.addWidget(self.avatar)

        # Username
        self.username_label = QLabel("")
        self.username_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.username_label.setStyleSheet(f"color: {TEXT_BRIGHT};")
        layout.addWidget(self.username_label)

        layout.addStretch()

        # PTT / Voice activity button
        self.ptt_btn = QPushButton("PTT")
        self.ptt_btn.setMinimumSize(90, 36)
        self.ptt_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.ptt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {RED};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 6px;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: #d84040; }}
        """)
        self.ptt_btn.pressed.connect(self.ptt_pressed.emit)
        self.ptt_btn.released.connect(self.ptt_released.emit)
        layout.addWidget(self.ptt_btn)

        # Voice mode toggle
        self.mode_btn = QPushButton("PTT")
        self.mode_btn.setMinimumSize(50, 36)
        self.mode_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT};
                color: {TEXT_NORMAL};
                border: none;
                border-radius: 6px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background-color: {BG_HOVER}; }}
        """)
        self.mode_btn.clicked.connect(self._on_mode_toggle)
        layout.addWidget(self.mode_btn)

        # Separator
        sep = QWidget()
        sep.setFixedSize(1, 28)
        sep.setStyleSheet(f"background: {SEPARATOR};")
        layout.addWidget(sep)

        # Mute mic button
        self.mic_btn = QPushButton("\U0001F3A4")
        self.mic_btn.setFixedSize(42, 36)
        self.mic_btn.setFont(QFont("Segoe UI", 16))
        self.mic_btn.setToolTip("Отключить микрофон")
        self._style_icon_btn(self.mic_btn, active=True)
        self.mic_btn.clicked.connect(self._on_mic_toggle)
        layout.addWidget(self.mic_btn)

        # Mute sound button
        self.sound_btn = QPushButton("\U0001F50A")
        self.sound_btn.setFixedSize(42, 36)
        self.sound_btn.setFont(QFont("Segoe UI", 16))
        self.sound_btn.setToolTip("Отключить звук")
        self._style_icon_btn(self.sound_btn, active=True)
        self.sound_btn.clicked.connect(self._on_sound_toggle)
        layout.addWidget(self.sound_btn)

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setFixedHeight(20)
        self.volume_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {BG_INPUT};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {TEXT_NORMAL};
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -4px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: {TEXT_BRIGHT};
            }}
        """)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        layout.addWidget(self.volume_slider)

        # Settings
        settings_btn = QPushButton("\u2699")
        settings_btn.setFixedSize(42, 36)
        settings_btn.setFont(QFont("Segoe UI", 18))
        settings_btn.setToolTip("Настройки")
        self._style_icon_btn(settings_btn, active=True)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)

    def _style_icon_btn(self, btn, active=True):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_NORMAL};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: {BG_HOVER};
                    color: {TEXT_BRIGHT};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {RED};
                    color: {TEXT_BRIGHT};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: #d84040;
                }}
            """)

    def set_username(self, username):
        self.username_label.setText(username)
        if username:
            self.avatar.setText(username[0].upper())

    def _on_mic_toggle(self):
        self.mic_muted = not self.mic_muted
        if self.mic_muted:
            self.mic_btn.setText("\U0001F507")  # muted icon
            self.mic_btn.setToolTip("Включить микрофон")
            self._style_icon_btn(self.mic_btn, active=False)
        else:
            self.mic_btn.setText("\U0001F3A4")
            self.mic_btn.setToolTip("Отключить микрофон")
            self._style_icon_btn(self.mic_btn, active=True)
        self.mic_toggled.emit(self.mic_muted)

    def _on_sound_toggle(self):
        self.sound_muted = not self.sound_muted
        if self.sound_muted:
            self.sound_btn.setText("\U0001F507")
            self.sound_btn.setToolTip("Включить звук")
            self._style_icon_btn(self.sound_btn, active=False)
        else:
            self.sound_btn.setText("\U0001F50A")
            self.sound_btn.setToolTip("Отключить звук")
            self._style_icon_btn(self.sound_btn, active=True)
        self.sound_toggled.emit(self.sound_muted)

    def _on_mode_toggle(self):
        self.voice_mode_toggled.emit()

    def set_voice_mode(self, mode):
        """Update display for PTT or VA mode."""
        self.voice_mode = mode
        if mode == "ptt":
            self.mode_btn.setText("PTT")
            self.mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_INPUT};
                    color: {TEXT_NORMAL};
                    border: none;
                    border-radius: 6px;
                    padding: 0 8px;
                }}
                QPushButton:hover {{ background-color: {BG_HOVER}; }}
            """)
            self.ptt_btn.setText("PTT")
            self.ptt_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {RED};
                    color: {TEXT_BRIGHT};
                    border: none;
                    border-radius: 6px;
                    padding: 0 12px;
                }}
                QPushButton:hover {{ background-color: #d84040; }}
            """)
        else:
            self.mode_btn.setText("VA")
            self.mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GREEN};
                    color: {TEXT_BRIGHT};
                    border: none;
                    border-radius: 6px;
                    padding: 0 8px;
                }}
            """)
            self.ptt_btn.setText("VA ВКЛ")
            self.ptt_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GREEN};
                    color: {TEXT_BRIGHT};
                    border: none;
                    border-radius: 6px;
                    padding: 0 12px;
                }}
            """)

    def set_ptt_speaking(self, speaking):
        """Visual feedback when speaking in PTT mode."""
        if self.voice_mode == "ptt":
            if speaking:
                self.ptt_btn.setText("ГОВОРИТЕ...")
                self.ptt_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {GREEN};
                        color: {TEXT_BRIGHT};
                        border: none;
                        border-radius: 6px;
                        padding: 0 12px;
                    }}
                """)
            else:
                self.ptt_btn.setText("PTT")
                self.ptt_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {RED};
                        color: {TEXT_BRIGHT};
                        border: none;
                        border-radius: 6px;
                        padding: 0 12px;
                    }}
                """)
