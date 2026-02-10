"""Discord-inspired dark theme for PyQt5."""

# Color palette
BG_DARK = "#202225"
BG_MAIN = "#36393f"
BG_SIDEBAR = "#2f3136"
BG_INPUT = "#40444b"
BG_HOVER = "#4f545c"
BG_SELECTED = "#42464d"
TEXT_NORMAL = "#dcddde"
TEXT_BRIGHT = "#ffffff"
TEXT_MUTED = "#72767d"
ACCENT = "#7289da"
ACCENT_HOVER = "#677bc4"
GREEN = "#43b581"
RED = "#f04747"
YELLOW = "#faa61a"
SEPARATOR = "#2c2f33"

STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: """ + BG_DARK + """;
    color: """ + TEXT_NORMAL + """;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QLabel {
    color: """ + TEXT_NORMAL + """;
    background: transparent;
}

QLineEdit {
    background-color: """ + BG_INPUT + """;
    color: """ + TEXT_BRIGHT + """;
    border: none;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: """ + ACCENT + """;
}

QLineEdit:focus {
    border: 1px solid """ + ACCENT + """;
}

QPushButton {
    background-color: """ + ACCENT + """;
    color: """ + TEXT_BRIGHT + """;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: """ + ACCENT_HOVER + """;
}

QPushButton:pressed {
    background-color: #5b6eae;
}

QPushButton:disabled {
    background-color: """ + BG_HOVER + """;
    color: """ + TEXT_MUTED + """;
}

QPushButton[class="secondary"] {
    background-color: """ + BG_INPUT + """;
    color: """ + TEXT_NORMAL + """;
}

QPushButton[class="secondary"]:hover {
    background-color: """ + BG_HOVER + """;
}

QPushButton[class="danger"] {
    background-color: """ + RED + """;
}

QPushButton[class="danger"]:hover {
    background-color: #d84040;
}

QPushButton[class="icon"] {
    background: transparent;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 16px;
}

QPushButton[class="icon"]:hover {
    background-color: """ + BG_HOVER + """;
}

QTextBrowser, QTextEdit {
    background-color: """ + BG_MAIN + """;
    color: """ + TEXT_NORMAL + """;
    border: none;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    padding: 10px 15px;
    selection-background-color: """ + ACCENT + """;
}

QScrollBar:vertical {
    background: """ + BG_MAIN + """;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: """ + BG_DARK + """;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: """ + BG_HOVER + """;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 0;
}

QCheckBox {
    color: """ + TEXT_NORMAL + """;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 2px solid """ + BG_HOVER + """;
    background: """ + BG_INPUT + """;
}

QCheckBox::indicator:checked {
    background: """ + ACCENT + """;
    border-color: """ + ACCENT + """;
}

QComboBox {
    background-color: """ + BG_INPUT + """;
    color: """ + TEXT_BRIGHT + """;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 13px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: """ + BG_INPUT + """;
    color: """ + TEXT_BRIGHT + """;
    border: 1px solid """ + BG_HOVER + """;
    selection-background-color: """ + ACCENT + """;
}

QSlider::groove:horizontal {
    background: """ + BG_INPUT + """;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: """ + ACCENT + """;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -4px 0;
}

QSlider::handle:horizontal:hover {
    background: """ + ACCENT_HOVER + """;
}

QTabWidget::pane {
    border: none;
    background: """ + BG_DARK + """;
}

QTabBar::tab {
    background: """ + BG_SIDEBAR + """;
    color: """ + TEXT_MUTED + """;
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: """ + TEXT_BRIGHT + """;
    border-bottom: 2px solid """ + ACCENT + """;
}

QTabBar::tab:hover {
    color: """ + TEXT_NORMAL + """;
}

QMenu {
    background-color: """ + BG_INPUT + """;
    color: """ + TEXT_BRIGHT + """;
    border: 1px solid """ + BG_HOVER + """;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: """ + ACCENT + """;
}

QMenu::separator {
    height: 1px;
    background: """ + BG_HOVER + """;
    margin: 4px 8px;
}

QProgressBar {
    background-color: """ + BG_INPUT + """;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: """ + GREEN + """;
    border-radius: 3px;
}
"""
