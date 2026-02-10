"""Settings dialog: audio devices, mic test, noise gate."""

import threading
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSlider, QProgressBar, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from client.ui.theme import (
    BG_DARK, BG_INPUT, BG_HOVER, TEXT_BRIGHT, TEXT_NORMAL,
    TEXT_MUTED, ACCENT, GREEN, YELLOW, RED
)


class SettingsDialog(QDialog):
    def __init__(self, audio_engine, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.testing = False
        self.test_stream = None
        self.setWindowTitle("Настройки")
        self.setFixedSize(450, 420)
        self.setStyleSheet(f"background-color: {BG_DARK};")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Настройки аудио")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_BRIGHT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input device
        layout.addWidget(self._section_label("МИКРОФОН (ВВОД)"))
        self.input_combo = QComboBox()
        for idx, name in self.audio_engine.input_devices:
            self.input_combo.addItem(name, idx)
        # Select current
        for i, (idx, name) in enumerate(self.audio_engine.input_devices):
            if idx == self.audio_engine.selected_input:
                self.input_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.input_combo)

        # Output device
        layout.addWidget(self._section_label("ДИНАМИКИ (ВЫВОД)"))
        self.output_combo = QComboBox()
        for idx, name in self.audio_engine.output_devices:
            self.output_combo.addItem(name, idx)
        for i, (idx, name) in enumerate(self.audio_engine.output_devices):
            if idx == self.audio_engine.selected_output:
                self.output_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.output_combo)

        # Mic test
        layout.addWidget(self._section_label("ПРОВЕРКА МИКРОФОНА"))

        test_row = QHBoxLayout()
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        self.level_bar.setTextVisible(False)
        self.level_bar.setFixedHeight(20)
        self.level_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_INPUT};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {GREEN};
                border-radius: 3px;
            }}
        """)
        test_row.addWidget(self.level_bar, 1)

        self.test_btn = QPushButton("Тест")
        self.test_btn.setFixedSize(70, 28)
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT};
                color: {TEXT_NORMAL};
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {BG_HOVER}; }}
        """)
        self.test_btn.clicked.connect(self._toggle_test)
        test_row.addWidget(self.test_btn)
        layout.addLayout(test_row)

        # Noise gate
        layout.addWidget(self._section_label("ПОРОГ ШУМА"))
        noise_row = QHBoxLayout()
        self.noise_slider = QSlider(Qt.Horizontal)
        self.noise_slider.setRange(0, 1000)
        self.noise_slider.setValue(self.audio_engine.noise_gate)
        noise_row.addWidget(self.noise_slider, 1)
        self.noise_value = QLabel(str(self.audio_engine.noise_gate))
        self.noise_value.setStyleSheet(f"color: {TEXT_NORMAL}; font-size: 12px;")
        self.noise_value.setFixedWidth(40)
        self.noise_slider.valueChanged.connect(lambda v: self.noise_value.setText(str(v)))
        noise_row.addWidget(self.noise_value)
        layout.addLayout(noise_row)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Применить")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #677bc4; }}
        """)
        apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(apply_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT};
                color: {TEXT_NORMAL};
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{ background-color: {BG_HOVER}; }}
        """)
        close_btn.clicked.connect(self._on_close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # Timer for mic level updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_level)

    def _section_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        return label

    def _toggle_test(self):
        if self.testing:
            self.testing = False
            self.test_btn.setText("Тест")
            self.test_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_INPUT};
                    color: {TEXT_NORMAL};
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {BG_HOVER}; }}
            """)
            self.update_timer.stop()
            self.level_bar.setValue(0)
            if self.test_stream:
                try:
                    self.test_stream.stop_stream()
                    self.test_stream.close()
                except Exception:
                    pass
                self.test_stream = None
        else:
            # Get selected input device
            idx = self.input_combo.currentData()
            try:
                self.test_stream = self.audio_engine.audio.open(
                    format=self.audio_engine.format,
                    channels=self.audio_engine.channels,
                    rate=self.audio_engine.sample_rate,
                    input=True,
                    frames_per_buffer=self.audio_engine.frame_size,
                    input_device_index=idx
                )
                self.testing = True
                self.test_btn.setText("Стоп")
                self.test_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {RED};
                        color: {TEXT_BRIGHT};
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }}
                """)
                self.update_timer.start(50)
            except Exception as e:
                self.level_bar.setValue(0)

    def _update_level(self):
        if not self.testing or not self.test_stream:
            return
        try:
            data = self.test_stream.read(self.audio_engine.frame_size, exception_on_overflow=False)
            rms = self.audio_engine.calc_rms(data)
            level = min(int(rms / 80.0), 100)
            self.level_bar.setValue(level)

            if level < 30:
                color = GREEN
            elif level < 70:
                color = YELLOW
            else:
                color = RED
            self.level_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {BG_INPUT};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
        except Exception:
            pass

    def _on_apply(self):
        self.testing = False
        self.update_timer.stop()
        if self.test_stream:
            try:
                self.test_stream.stop_stream()
                self.test_stream.close()
            except Exception:
                pass
            self.test_stream = None

        self.audio_engine.selected_input = self.input_combo.currentData()
        self.audio_engine.selected_output = self.output_combo.currentData()
        self.audio_engine.noise_gate = self.noise_slider.value()
        self.accept()

    def _on_close(self):
        self.testing = False
        self.update_timer.stop()
        if self.test_stream:
            try:
                self.test_stream.stop_stream()
                self.test_stream.close()
            except Exception:
                pass
            self.test_stream = None
        self.reject()

    def closeEvent(self, event):
        self._on_close()
        event.accept()
