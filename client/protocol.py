# Protocol v2 constants and helpers (client-side)

# Ports
TEXT_PORT = 5557
VOICE_PORT = 5556

# Auth commands (client -> server)
CMD_REGISTER = "REGISTER"
CMD_LOGIN = "LOGIN"

# Auth responses (server -> client)
RESP_REG_OK = "REG_OK"
RESP_REG_FAIL = "REG_FAIL"
RESP_AUTH_OK = "AUTH_OK"
RESP_AUTH_FAIL = "AUTH_FAIL"

# Channel commands (client -> server)
CMD_CREATE_CHANNEL = "CREATE_CHANNEL"
CMD_DELETE_CHANNEL = "DELETE_CHANNEL"
CMD_JOIN_CHANNEL = "JOIN_CHANNEL"
CMD_LEAVE_CHANNEL = "LEAVE_CHANNEL"

# Channel events (server -> client)
EVT_CHANNEL_CREATED = "CHANNEL_CREATED"
EVT_CHANNEL_DELETED = "CHANNEL_DELETED"
EVT_CHANNEL_DELETE_FAIL = "CHANNEL_DELETE_FAIL"
EVT_USER_JOINED_CHANNEL = "USER_JOINED_CHANNEL"
EVT_USER_LEFT_CHANNEL = "USER_LEFT_CHANNEL"
EVT_CHANNEL_LIST = "CHANNEL_LIST"
EVT_CHANNEL_USERS = "CHANNEL_USERS"

# Chat
CMD_MSG = "MSG"
CMD_TYPING = "TYPING"
CMD_PING = "PING"
RESP_PONG = "PONG"
EVT_USERLIST = "USERLIST"
EVT_SYSTEM = "SYSTEM"

# Voice codec IDs
CODEC_OPUS = 0x01


def send_line(sock, message):
    """Send a newline-delimited UTF-8 message."""
    sock.send((message + "\n").encode('utf-8'))


def parse_command(line):
    """Parse a protocol line into (command, payload)."""
    if ':' in line:
        cmd, _, payload = line.partition(':')
        return cmd, payload
    return line, ''
