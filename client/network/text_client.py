"""
Text socket client running in a QThread.
Emits signals for all protocol events.
"""

import socket
from PyQt5.QtCore import QThread, pyqtSignal
from client.protocol import (
    send_line, parse_command,
    RESP_REG_OK, RESP_REG_FAIL, RESP_AUTH_OK, RESP_AUTH_FAIL,
    EVT_CHANNEL_CREATED, EVT_CHANNEL_DELETED, EVT_CHANNEL_DELETE_FAIL,
    EVT_USER_JOINED_CHANNEL, EVT_USER_LEFT_CHANNEL, EVT_CHANNEL_LIST,
    EVT_CHANNEL_USERS, EVT_USERLIST, EVT_SYSTEM,
    CMD_MSG, CMD_TYPING, CMD_PING, RESP_PONG,
    CMD_LOGIN, CMD_REGISTER, CMD_CREATE_CHANNEL, CMD_DELETE_CHANNEL,
    CMD_JOIN_CHANNEL, CMD_LEAVE_CHANNEL,
    TEXT_PORT,
)


class TextClient(QThread):
    # Auth signals
    auth_ok = pyqtSignal()
    auth_fail = pyqtSignal(str)  # reason
    reg_ok = pyqtSignal()
    reg_fail = pyqtSignal(str)  # reason

    # Channel signals
    channel_list_updated = pyqtSignal(list)  # [channel_names]
    channel_created = pyqtSignal(str)  # channel_name
    channel_deleted = pyqtSignal(str)  # channel_name
    channel_delete_fail = pyqtSignal(str)  # reason
    channel_users_updated = pyqtSignal(str, list)  # channel_name, [usernames]
    user_joined_channel = pyqtSignal(str, str)  # username, channel_name
    user_left_channel = pyqtSignal(str, str)  # username, channel_name

    # Chat signals
    message_received = pyqtSignal(str, str)  # username, text
    typing_indicator = pyqtSignal(str)  # username
    pong_received = pyqtSignal()
    system_message = pyqtSignal(str)  # message
    user_list_updated = pyqtSignal(list)  # [usernames]

    # Connection
    disconnected = pyqtSignal()

    def __init__(self, host, port=TEXT_PORT, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.sock = None
        self.running = False

    def connect_to_server(self):
        """Establish TCP connection. Call before start()."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True

    def send(self, message):
        """Send a text protocol message."""
        if self.sock:
            try:
                send_line(self.sock, message)
            except Exception:
                pass

    def login(self, username, password):
        self.send(f"{CMD_LOGIN}:{username}:{password}")

    def register(self, username, password):
        self.send(f"{CMD_REGISTER}:{username}:{password}")

    def send_message(self, text):
        self.send(f"{CMD_MSG}:{text}")

    def send_typing(self):
        self.send(CMD_TYPING)

    def send_ping(self):
        self.send(CMD_PING)

    def join_channel(self, channel_name):
        self.send(f"{CMD_JOIN_CHANNEL}:{channel_name}")

    def leave_channel(self):
        self.send(CMD_LEAVE_CHANNEL)

    def create_channel(self, name):
        self.send(f"{CMD_CREATE_CHANNEL}:{name}")

    def delete_channel(self, name):
        self.send(f"{CMD_DELETE_CHANNEL}:{name}")

    def run(self):
        """QThread main loop: read and dispatch protocol messages."""
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096).decode('utf-8')
                if not data:
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self._dispatch(line)

            except Exception:
                break

        self.running = False
        self.disconnected.emit()

    def _dispatch(self, line):
        """Route a protocol line to the appropriate signal."""
        cmd, payload = parse_command(line)

        if cmd == RESP_AUTH_OK:
            self.auth_ok.emit()
        elif cmd == RESP_AUTH_FAIL:
            self.auth_fail.emit(payload)
        elif cmd == RESP_REG_OK:
            self.reg_ok.emit()
        elif cmd == RESP_REG_FAIL:
            self.reg_fail.emit(payload)
        elif cmd == EVT_CHANNEL_LIST:
            channels = payload.split(",") if payload else []
            self.channel_list_updated.emit(channels)
        elif cmd == EVT_CHANNEL_CREATED:
            self.channel_created.emit(payload)
        elif cmd == EVT_CHANNEL_DELETED:
            self.channel_deleted.emit(payload)
        elif cmd == EVT_CHANNEL_DELETE_FAIL:
            self.channel_delete_fail.emit(payload)
        elif cmd == EVT_CHANNEL_USERS:
            # Format: channel_name:user1,user2
            parts = payload.split(":", 1)
            if len(parts) == 2:
                ch_name = parts[0]
                users = parts[1].split(",") if parts[1] else []
                self.channel_users_updated.emit(ch_name, users)
        elif cmd == EVT_USER_JOINED_CHANNEL:
            parts = payload.split(":", 1)
            if len(parts) == 2:
                self.user_joined_channel.emit(parts[0], parts[1])
        elif cmd == EVT_USER_LEFT_CHANNEL:
            parts = payload.split(":", 1)
            if len(parts) == 2:
                self.user_left_channel.emit(parts[0], parts[1])
        elif cmd == CMD_MSG:
            parts = payload.split(":", 1)
            if len(parts) == 2:
                self.message_received.emit(parts[0], parts[1])
        elif cmd == CMD_TYPING:
            self.typing_indicator.emit(payload)
        elif cmd == RESP_PONG:
            self.pong_received.emit()
        elif cmd == EVT_SYSTEM:
            self.system_message.emit(payload)
        elif cmd == EVT_USERLIST:
            users = payload.split(",") if payload else []
            self.user_list_updated.emit(users)

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
