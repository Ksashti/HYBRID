"""Login/Register window."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QTabWidget, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from client.ui.theme import (
    BG_DARK, BG_MAIN, BG_INPUT, BG_SIDEBAR,
    TEXT_BRIGHT, TEXT_MUTED, TEXT_NORMAL, ACCENT, RED
)
from client.config import load_config, save_config


class LoginWindow(QWidget):
    login_success = pyqtSignal(str, str, str, str)  # host, username, password, mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self._setup_ui()
        self._load_saved()

    def _setup_ui(self):
        self.setWindowTitle("HYBRID - Вход")
        self.setFixedSize(420, 520)
        self.setStyleSheet(f"background-color: {BG_DARK};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("HYBRID")
        logo.setFont(QFont("Segoe UI", 28, QFont.Bold))
        logo.setStyleSheet(f"color: {ACCENT};")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        subtitle = QLabel("Голосовой чат")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {TEXT_MUTED};")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(25)

        # Tab widget for Login/Register
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {BG_DARK};
            }}
            QTabBar::tab {{
                background: {BG_SIDEBAR};
                color: {TEXT_MUTED};
                padding: 8px 30px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                color: {TEXT_BRIGHT};
                border-bottom: 2px solid {ACCENT};
            }}
        """)

        self.login_tab = self._create_login_tab()
        self.register_tab = self._create_register_tab()
        self.tabs.addTab(self.login_tab, "Вход")
        self.tabs.addTab(self.register_tab, "Регистрация")
        layout.addWidget(self.tabs)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {RED}; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)

    def _create_field(self, label_text, placeholder="", is_password=False):
        """Create a labeled input field."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vlayout = QVBoxLayout(container)
        vlayout.setContentsMargins(0, 0, 0, 8)
        vlayout.setSpacing(4)

        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label.setStyleSheet(f"color: {TEXT_NORMAL}; font-size: 11px; text-transform: uppercase;")
        vlayout.addWidget(label)

        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 4px;
                padding: 10px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        if is_password:
            field.setEchoMode(QLineEdit.Password)
        vlayout.addWidget(field)

        return container, field

    def _create_login_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background: {BG_DARK};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(0)

        # Server IP
        ip_container, self.login_ip = self._create_field("IP СЕРВЕРА", "Введите IP...")
        layout.addWidget(ip_container)

        # Username
        user_container, self.login_username = self._create_field("ИМЯ ПОЛЬЗОВАТЕЛЯ", "Введите имя...")
        layout.addWidget(user_container)

        # Password
        pass_container, self.login_password = self._create_field("ПАРОЛЬ", "Введите пароль...", True)
        layout.addWidget(pass_container)

        # Remember me
        self.remember_check = QCheckBox("Запомнить меня")
        self.remember_check.setStyleSheet(f"color: {TEXT_NORMAL}; font-size: 12px; padding: 4px 0;")
        layout.addWidget(self.remember_check)
        layout.addSpacing(10)

        # Connect button
        btn = QPushButton("Войти")
        btn.setFixedHeight(40)
        btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #677bc4; }}
            QPushButton:pressed {{ background-color: #5b6eae; }}
        """)
        btn.clicked.connect(self._on_login)
        layout.addWidget(btn)

        # Enter key shortcut
        self.login_password.returnPressed.connect(self._on_login)
        self.login_username.returnPressed.connect(lambda: self.login_password.setFocus())

        layout.addStretch()
        return tab

    def _create_register_tab(self):
        tab = QWidget()
        tab.setStyleSheet(f"background: {BG_DARK};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(0)

        # Server IP
        ip_container, self.reg_ip = self._create_field("IP СЕРВЕРА", "Введите IP...")
        layout.addWidget(ip_container)

        # Username
        user_container, self.reg_username = self._create_field("ИМЯ ПОЛЬЗОВАТЕЛЯ", "Придумайте имя...")
        layout.addWidget(user_container)

        # Password
        pass_container, self.reg_password = self._create_field("ПАРОЛЬ", "Придумайте пароль...", True)
        layout.addWidget(pass_container)

        # Confirm password
        pass2_container, self.reg_password2 = self._create_field("ПОДТВЕРДИТЕ ПАРОЛЬ", "Повторите пароль...", True)
        layout.addWidget(pass2_container)

        layout.addSpacing(10)

        # Register button
        btn = QPushButton("Зарегистрироваться")
        btn.setFixedHeight(40)
        btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {TEXT_BRIGHT};
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #677bc4; }}
            QPushButton:pressed {{ background-color: #5b6eae; }}
        """)
        btn.clicked.connect(self._on_register)
        layout.addWidget(btn)

        self.reg_password2.returnPressed.connect(self._on_register)

        layout.addStretch()
        return tab

    def _load_saved(self):
        """Load saved credentials from config."""
        ip = self.config.get("server_ip", "")
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        remember = self.config.get("remember_me", False)

        self.login_ip.setText(ip)
        self.reg_ip.setText(ip)
        self.login_username.setText(username)
        self.remember_check.setChecked(remember)
        if remember and password:
            self.login_password.setText(password)

    def _on_login(self):
        host = self.login_ip.text().strip()
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not host:
            self.status_label.setText("Введите IP сервера")
            return
        if not username:
            self.status_label.setText("Введите имя пользователя")
            return
        if not password:
            self.status_label.setText("Введите пароль")
            return

        # Save config
        self.config["server_ip"] = host
        self.config["username"] = username
        self.config["remember_me"] = self.remember_check.isChecked()
        if self.remember_check.isChecked():
            self.config["password"] = password
        else:
            self.config["password"] = ""
        save_config(self.config)

        self.status_label.setText("Подключение...")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.login_success.emit(host, username, password, "login")

    def _on_register(self):
        host = self.reg_ip.text().strip()
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        password2 = self.reg_password2.text()

        if not host:
            self.status_label.setText("Введите IP сервера")
            return
        if not username:
            self.status_label.setText("Введите имя пользователя")
            return
        if not password:
            self.status_label.setText("Введите пароль")
            return
        if password != password2:
            self.status_label.setText("Пароли не совпадают")
            return

        self.config["server_ip"] = host
        save_config(self.config)

        self.status_label.setText("Регистрация...")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.login_success.emit(host, username, password, "register")

    def show_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {RED}; font-size: 11px;")

    def show_success(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: #43b581; font-size: 11px;")
