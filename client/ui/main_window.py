"""Main window: assembles sidebar, chat panel, bottom panel. Manages all connections."""

import time
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QInputDialog, QSlider, QDialog, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont
from client.ui.theme import BG_DARK, BG_MAIN, SEPARATOR, GREEN, RED, TEXT_BRIGHT, ACCENT
from client.ui.sidebar import Sidebar
from client.ui.chat_panel import ChatPanel
from client.ui.bottom_panel import BottomPanel
from client.ui.settings_dialog import SettingsDialog
from client.network.text_client import TextClient
from client.network.voice_client import VoiceClient
from client.audio.engine import AudioEngine
from client.audio.opus_codec import OpusCodec, FRAME_SIZE
from client.audio.voice_modes import VoiceModeManager
from client.config import load_config, save_config


class MainWindow(QMainWindow):
    def __init__(self, host, username, text_client, voice_client, parent=None):
        super().__init__(parent)
        self.host = host
        self.username = username
        self.text_client = text_client
        self.voice_client = voice_client
        self.current_channel = None
        self.ping_time = 0

        # Audio
        self.audio_engine = AudioEngine()
        self.codec = OpusCodec()
        self.voice_mode = VoiceModeManager()
        self.voice_sender_running = False
        self.output_stream = None
        self._restart_output = False

        # Load saved config
        config = load_config()
        self.audio_engine.volume = config.get("volume", {}).get("master", 100)
        self.audio_engine.user_volumes = config.get("volume", {}).get("users", {})
        voice_mode = config.get("audio", {}).get("voice_mode", "ptt")
        self.audio_engine.noise_gate = config.get("audio", {}).get("noise_gate", 200)
        self.voice_mode.va_threshold = config.get("audio", {}).get("va_threshold", 500)

        self._setup_ui()
        self._connect_signals()
        self._start_voice_receiver()

        # Set voice mode
        if voice_mode == "va":
            self.voice_mode.toggle_mode()
            self.bottom_panel.set_voice_mode("va")

    def _setup_ui(self):
        self.setWindowTitle(f"HYBRID - {self.username}")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        self.setStyleSheet(f"background-color: {BG_DARK};")

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.set_username(self.username)
        main_layout.addWidget(self.sidebar)

        # Separator
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {SEPARATOR};")
        main_layout.addWidget(sep)

        # Right side: chat + bottom
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.chat_panel = ChatPanel()
        right_layout.addWidget(self.chat_panel, 1)

        self.bottom_panel = BottomPanel()
        self.bottom_panel.set_username(self.username)
        self.bottom_panel.volume_slider.setValue(self.audio_engine.volume)
        right_layout.addWidget(self.bottom_panel)

        main_layout.addWidget(right, 1)

        # Welcome message
        self.chat_panel.add_system_message(f"Добро пожаловать, {self.username}!")
        self.chat_panel.add_system_message("Выберите канал в боковой панели для начала общения.")

    def _connect_signals(self):
        # Text client signals
        tc = self.text_client
        tc.channel_list_updated.connect(self._on_channel_list)
        tc.channel_users_updated.connect(self._on_channel_users)
        tc.channel_created.connect(self._on_channel_created)
        tc.channel_deleted.connect(self._on_channel_deleted)
        tc.channel_delete_fail.connect(self._on_channel_delete_fail)
        tc.user_joined_channel.connect(self._on_user_joined_channel)
        tc.user_left_channel.connect(self._on_user_left_channel)
        tc.message_received.connect(self._on_message_received)
        tc.typing_indicator.connect(self._on_typing)
        tc.pong_received.connect(self._on_pong)
        tc.system_message.connect(self._on_system_message)
        tc.user_list_updated.connect(self._on_user_list)
        tc.disconnected.connect(self._on_disconnected)

        # Voice client signals
        vc = self.voice_client
        vc.voice_received.connect(self._on_voice_received)
        vc.disconnected.connect(self._on_voice_disconnected)

        # Sidebar signals
        self.sidebar.channel_selected.connect(self._on_channel_selected)
        self.sidebar.channel_create_requested.connect(self._on_create_channel)
        self.sidebar.channel_delete_requested.connect(self._on_delete_channel)
        self.sidebar.user_volume_requested.connect(self._on_user_volume)

        # Chat signals
        self.chat_panel.message_sent.connect(self._on_send_message)
        self.chat_panel.typing.connect(self._on_typing_local)

        # Bottom panel signals
        self.bottom_panel.mic_toggled.connect(self._on_mic_toggle)
        self.bottom_panel.sound_toggled.connect(self._on_sound_toggle)
        self.bottom_panel.settings_clicked.connect(self._on_settings)
        self.bottom_panel.ptt_pressed.connect(self._on_ptt_press)
        self.bottom_panel.ptt_released.connect(self._on_ptt_release)
        self.bottom_panel.voice_mode_toggled.connect(self._on_voice_mode_toggle)
        self.bottom_panel.volume_changed.connect(self._on_volume_change)

    # ==================== VOICE RECEIVER ====================

    def _start_voice_receiver(self):
        """Start the output stream for playing received audio."""
        def receiver_loop():
            try:
                self.output_stream = self.audio_engine.open_output_stream()
            except Exception:
                self.output_stream = None
            # The actual playback happens in _on_voice_received slot

        threading.Thread(target=receiver_loop, daemon=True).start()

    @pyqtSlot(str, bytes)
    def _on_voice_received(self, sender, pcm_data):
        """Play received voice data."""
        if self.audio_engine.sound_muted:
            return
        if not self.output_stream:
            try:
                self.output_stream = self.audio_engine.open_output_stream()
            except Exception:
                return

        # Restart output if needed
        if self._restart_output:
            self._restart_output = False
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except Exception:
                pass
            try:
                self.output_stream = self.audio_engine.open_output_stream()
            except Exception:
                return

        adjusted = self.audio_engine.apply_volume(pcm_data, sender)
        try:
            self.output_stream.write(adjusted)
        except Exception:
            pass

        # Highlight speaking user
        self.sidebar.highlight_speaking(sender)
        QTimer.singleShot(500, lambda s=sender: self.sidebar.clear_speaking(s))

    # ==================== VOICE SENDER ====================

    def _start_voice_sender(self):
        """Start the microphone capture + send loop."""
        if self.voice_sender_running:
            return
        self.voice_sender_running = True

        def sender_loop():
            try:
                stream = self.audio_engine.open_input_stream()
            except Exception:
                self.voice_sender_running = False
                return

            while self.voice_sender_running:
                try:
                    data = stream.read(self.audio_engine.frame_size, exception_on_overflow=False)
                    rms = self.audio_engine.calc_rms(data)

                    if not self.audio_engine.mic_muted and self.voice_mode.should_transmit(rms):
                        if rms > self.audio_engine.noise_gate:
                            self.voice_client.send_voice(data)
                            # Show speaking in sidebar (thread-safe via signal)
                            QTimer.singleShot(0, lambda: self.sidebar.highlight_speaking(self.username))
                            QTimer.singleShot(500, lambda: self.sidebar.clear_speaking(self.username))
                except Exception:
                    break

            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            self.voice_sender_running = False

        threading.Thread(target=sender_loop, daemon=True).start()

    def _stop_voice_sender(self):
        self.voice_sender_running = False

    # ==================== TEXT CLIENT HANDLERS ====================

    @pyqtSlot(list)
    def _on_channel_list(self, channels):
        self.sidebar.update_channels(channels)

    @pyqtSlot(str, list)
    def _on_channel_users(self, channel_name, users):
        self.sidebar.update_channel_users(channel_name, users)

    @pyqtSlot(str)
    def _on_channel_created(self, name):
        self.chat_panel.add_system_message(f"Канал '{name}' создан")

    @pyqtSlot(str)
    def _on_channel_deleted(self, name):
        self.chat_panel.add_system_message(f"Канал '{name}' удалён")
        if self.current_channel == name:
            self.current_channel = None
            self.sidebar.set_active_channel(None)
            self._stop_voice_sender()

    @pyqtSlot(str)
    def _on_channel_delete_fail(self, reason):
        self.chat_panel.add_error_message(f"Не удалось удалить канал: {reason}")

    @pyqtSlot(str, str)
    def _on_user_joined_channel(self, username, channel):
        if username != self.username:
            self.chat_panel.add_system_message(f"{username} присоединился к {channel}")

    @pyqtSlot(str, str)
    def _on_user_left_channel(self, username, channel):
        if username != self.username:
            self.chat_panel.add_system_message(f"{username} покинул {channel}")

    @pyqtSlot(str, str)
    def _on_message_received(self, username, text):
        self.chat_panel.add_other_message(username, text)

    @pyqtSlot(str)
    def _on_typing(self, username):
        self.chat_panel.show_typing(username)

    @pyqtSlot()
    def _on_pong(self):
        ping_ms = int((time.time() - self.ping_time) * 1000)
        self.chat_panel.add_system_message(f"Пинг: {ping_ms} мс")

    @pyqtSlot(str)
    def _on_system_message(self, message):
        self.chat_panel.add_system_message(message)

    @pyqtSlot(list)
    def _on_user_list(self, users):
        pass  # User list is managed via channel users

    @pyqtSlot()
    def _on_disconnected(self):
        self.chat_panel.add_error_message("Потеряно соединение с сервером")
        self.chat_panel.set_status("Отключено", RED)
        self._stop_voice_sender()

    @pyqtSlot()
    def _on_voice_disconnected(self):
        self.chat_panel.add_error_message("Голосовое соединение потеряно")

    # ==================== SIDEBAR HANDLERS ====================

    def _on_channel_selected(self, channel_name):
        if channel_name == self.current_channel:
            # Leave channel
            self.text_client.leave_channel()
            self.current_channel = None
            self.sidebar.set_active_channel(None)
            self.chat_panel.set_channel_name("Нет канала")
            self._stop_voice_sender()
            return

        self.text_client.join_channel(channel_name)
        self.current_channel = channel_name
        self.sidebar.set_active_channel(channel_name)
        self.chat_panel.set_channel_name(channel_name)
        self.chat_panel.add_system_message(f"Вы присоединились к каналу {channel_name}")

        # Start voice sender
        self._start_voice_sender()

    def _on_create_channel(self, name):
        self.text_client.create_channel(name)

    def _on_delete_channel(self, name):
        self.text_client.delete_channel(name)

    def _on_user_volume(self, username):
        """Open per-user volume dialog."""
        current = self.audio_engine.user_volumes.get(username, 100)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Громкость: {username}")
        dialog.setFixedSize(320, 120)
        dialog.setStyleSheet(f"background-color: {BG_DARK};")

        layout = QVBoxLayout(dialog)
        label = QLabel(f"Громкость: {username}")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        label.setStyleSheet(f"color: {TEXT_BRIGHT};")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 200)
        slider.setValue(current)
        val_label = QLabel(f"{current}%")
        val_label.setStyleSheet(f"color: {TEXT_BRIGHT}; font-size: 12px;")
        val_label.setFixedWidth(40)
        val_label.setAlignment(Qt.AlignCenter)

        def on_change(v):
            self.audio_engine.user_volumes[username] = v
            val_label.setText(f"{v}%")

        slider.valueChanged.connect(on_change)

        row = QHBoxLayout()
        row.addWidget(slider, 1)
        row.addWidget(val_label)
        layout.addLayout(row)

        dialog.exec_()

    # ==================== CHAT HANDLERS ====================

    def _on_send_message(self, text):
        if text.startswith("/ping"):
            self.ping_time = time.time()
            self.text_client.send_ping()
        else:
            self.text_client.send_message(text)
            self.chat_panel.add_own_message(self.username, text)

    def _on_typing_local(self):
        self.text_client.send_typing()

    # ==================== BOTTOM PANEL HANDLERS ====================

    def _on_mic_toggle(self, muted):
        self.audio_engine.mic_muted = muted
        if muted:
            self.chat_panel.add_system_message("Микрофон отключён")
        else:
            self.chat_panel.add_system_message("Микрофон включён")

    def _on_sound_toggle(self, muted):
        self.audio_engine.sound_muted = muted
        if muted:
            self.chat_panel.add_system_message("Звук отключён")
        else:
            self.chat_panel.add_system_message("Звук включён")

    def _on_settings(self):
        dialog = SettingsDialog(self.audio_engine, self)
        if dialog.exec_() == QDialog.Accepted:
            self._restart_output = True
            self.chat_panel.add_system_message("Настройки аудио применены")

    def _on_ptt_press(self):
        if self.voice_mode.is_ptt() and self.current_channel:
            self.voice_mode.set_ptt(True)
            self.bottom_panel.set_ptt_speaking(True)
            self.chat_panel.set_status("Вы говорите", GREEN)

    def _on_ptt_release(self):
        if self.voice_mode.is_ptt():
            self.voice_mode.set_ptt(False)
            self.bottom_panel.set_ptt_speaking(False)
            self.chat_panel.set_status("Подключено", GREEN)

    def _on_voice_mode_toggle(self):
        mode = self.voice_mode.toggle_mode()
        self.bottom_panel.set_voice_mode(mode)
        if mode == "va":
            self.chat_panel.add_system_message("Голосовая активация включена")
        else:
            self.chat_panel.add_system_message("Режим Push-to-Talk")

    def _on_volume_change(self, value):
        self.audio_engine.volume = value

    # ==================== CLEANUP ====================

    def closeEvent(self, event):
        """Save config and disconnect."""
        self._stop_voice_sender()

        # Save settings
        config = load_config()
        config["volume"]["master"] = self.audio_engine.volume
        config["volume"]["users"] = self.audio_engine.user_volumes
        config["audio"]["voice_mode"] = self.voice_mode.mode
        config["audio"]["noise_gate"] = self.audio_engine.noise_gate
        config["audio"]["va_threshold"] = self.voice_mode.va_threshold
        save_config(config)

        self.text_client.stop()
        self.voice_client.stop()

        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except Exception:
                pass

        self.audio_engine.terminate()
        event.accept()
