"""HYBRID VoiceChat Client - Entry point."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from client.ui.theme import STYLESHEET
from client.ui.login_window import LoginWindow
from client.ui.main_window import MainWindow
from client.network.text_client import TextClient
from client.network.voice_client import VoiceClient
from client.protocol import TEXT_PORT, VOICE_PORT


class HybridApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLESHEET)
        self.app.setApplicationName("HYBRID")

        self.login_window = None
        self.main_window = None
        self.text_client = None
        self.voice_client = None
        self.username = None
        self.host = None

    def run(self):
        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self._on_login_attempt)
        self.login_window.show()
        sys.exit(self.app.exec_())

    def _on_login_attempt(self, host, username, password, mode):
        """Handle login/register attempt from the login window."""
        self.host = host
        self.username = username

        try:
            # Create text client and connect
            self.text_client = TextClient(host, TEXT_PORT)
            self.text_client.connect_to_server()

            # Connect auth signals
            self.text_client.auth_ok.connect(
                lambda: self._on_auth_ok(host, username, password)
            )
            self.text_client.auth_fail.connect(self._on_auth_fail)
            self.text_client.reg_ok.connect(
                lambda: self._on_reg_ok(host, username, password)
            )
            self.text_client.reg_fail.connect(self._on_reg_fail)

            # Start receiving thread
            self.text_client.start()

            # Send auth command
            if mode == "login":
                self.text_client.login(username, password)
            else:
                self.text_client.register(username, password)

        except Exception as e:
            self.login_window.show_error(f"Не удалось подключиться: {e}")
            if self.text_client:
                self.text_client.stop()
                self.text_client = None

    def _on_auth_ok(self, host, username, password):
        """Authentication succeeded. Connect voice and open main window."""
        try:
            self.voice_client = VoiceClient(host, username, VOICE_PORT)
            self.voice_client.connect_to_server()
            self.voice_client.start()
        except Exception as e:
            self.login_window.show_error(f"Голосовое подключение не удалось: {e}")
            return

        # Disconnect auth signals to avoid duplicate handling
        try:
            self.text_client.auth_ok.disconnect()
            self.text_client.auth_fail.disconnect()
            self.text_client.reg_ok.disconnect()
            self.text_client.reg_fail.disconnect()
        except Exception:
            pass

        # Open main window
        self.login_window.hide()
        self.main_window = MainWindow(host, username, self.text_client, self.voice_client)
        self.main_window.show()

    def _on_auth_fail(self, reason):
        self.login_window.show_error(f"Ошибка входа: {reason}")
        if self.text_client:
            self.text_client.stop()
            self.text_client = None

    def _on_reg_ok(self, host, username, password):
        """Registration succeeded. Now login."""
        self.login_window.show_success("Регистрация успешна! Входим...")
        # Auto-login after registration
        try:
            self.text_client.stop()
        except Exception:
            pass

        # Small delay then login
        QTimer.singleShot(500, lambda: self._on_login_attempt(host, username, password, "login"))

    def _on_reg_fail(self, reason):
        self.login_window.show_error(f"Ошибка регистрации: {reason}")
        if self.text_client:
            self.text_client.stop()
            self.text_client = None


def main():
    app = HybridApp()
    app.run()


if __name__ == "__main__":
    main()
