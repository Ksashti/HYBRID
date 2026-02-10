import socket
import threading
import struct
from server.protocol import (
    send_line, parse_command,
    CMD_REGISTER, CMD_LOGIN, CMD_CREATE_CHANNEL, CMD_DELETE_CHANNEL,
    CMD_JOIN_CHANNEL, CMD_LEAVE_CHANNEL, CMD_MSG, CMD_TYPING, CMD_PING,
    RESP_REG_OK, RESP_REG_FAIL, RESP_AUTH_OK, RESP_AUTH_FAIL,
    EVT_CHANNEL_CREATED, EVT_CHANNEL_DELETED, EVT_CHANNEL_DELETE_FAIL,
    EVT_USER_JOINED_CHANNEL, EVT_USER_LEFT_CHANNEL, EVT_CHANNEL_LIST,
    EVT_CHANNEL_USERS, EVT_USERLIST, EVT_SYSTEM, RESP_PONG,
)


def broadcast_text(state, message, exclude_sock=None, channel=None):
    """Send text message to all authenticated clients, optionally filtered by channel."""
    if channel:
        sockets = state.get_text_sockets_in_channel(channel)
    else:
        sockets = state.get_all_text_sockets()

    for sock in sockets:
        if sock != exclude_sock:
            try:
                send_line(sock, message)
            except Exception:
                pass


def send_userlist(state):
    """Send the online user list to all clients."""
    users = state.get_all_usernames()
    msg = f"{EVT_USERLIST}:{','.join(users)}"
    for sock in state.get_all_text_sockets():
        try:
            send_line(sock, msg)
        except Exception:
            pass


def send_channel_list(state, channel_mgr, sock=None):
    """Send channel list to one client or all."""
    names = channel_mgr.get_channel_names()
    msg = f"{EVT_CHANNEL_LIST}:{','.join(names)}"
    if sock:
        try:
            send_line(sock, msg)
        except Exception:
            pass
    else:
        for s in state.get_all_text_sockets():
            try:
                send_line(s, msg)
            except Exception:
                pass


def send_channel_users(state, channel_name, sock=None):
    """Send user list for a specific channel."""
    users = state.get_users_in_channel(channel_name)
    msg = f"{EVT_CHANNEL_USERS}:{channel_name}:{','.join(users)}"
    if sock:
        try:
            send_line(sock, msg)
        except Exception:
            pass
    else:
        # Send to all clients so everyone sees the update
        for s in state.get_all_text_sockets():
            try:
                send_line(s, msg)
            except Exception:
                pass


def handle_auth(client, auth_mgr, state):
    """Handle authentication phase. Returns username on success, None on failure."""
    buffer = ""
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                return None

            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                cmd, payload = parse_command(line)

                if cmd == CMD_REGISTER:
                    parts = payload.split(":", 1)
                    if len(parts) != 2:
                        send_line(client, f"{RESP_REG_FAIL}:Неверный формат")
                        continue
                    username, password = parts
                    ok, err = auth_mgr.register(username, password)
                    if ok:
                        send_line(client, RESP_REG_OK)
                    else:
                        send_line(client, f"{RESP_REG_FAIL}:{err}")

                elif cmd == CMD_LOGIN:
                    parts = payload.split(":", 1)
                    if len(parts) != 2:
                        send_line(client, f"{RESP_AUTH_FAIL}:Неверный формат")
                        continue
                    username, password = parts
                    if state.is_username_online(username):
                        send_line(client, f"{RESP_AUTH_FAIL}:Уже в сети")
                        continue
                    ok, err = auth_mgr.login(username, password)
                    if ok:
                        send_line(client, RESP_AUTH_OK)
                        return username, buffer
                    else:
                        send_line(client, f"{RESP_AUTH_FAIL}:{err}")

                else:
                    send_line(client, f"{RESP_AUTH_FAIL}:Сначала войдите (LOGIN/REGISTER)")

        except Exception:
            return None


def handle_text_client(client, username, init_buffer, state, auth_mgr, channel_mgr):
    """Handle messages from an authenticated client."""
    buffer = init_buffer
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                break

            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                cmd, payload = parse_command(line)

                if cmd == CMD_MSG:
                    channel = state.get_channel(client)
                    if channel:
                        broadcast_text(state, f"{CMD_MSG}:{username}:{payload}",
                                       exclude_sock=client, channel=channel)

                elif cmd == CMD_TYPING:
                    channel = state.get_channel(client)
                    if channel:
                        broadcast_text(state, f"{CMD_TYPING}:{username}",
                                       exclude_sock=client, channel=channel)

                elif cmd == CMD_PING:
                    send_line(client, RESP_PONG)

                elif cmd == CMD_CREATE_CHANNEL:
                    ok, err = channel_mgr.create_channel(payload)
                    if ok:
                        broadcast_text(state, f"{EVT_CHANNEL_CREATED}:{payload}")
                        send_channel_list(state, channel_mgr)
                    else:
                        send_line(client, f"{EVT_CHANNEL_DELETE_FAIL}:{err}")

                elif cmd == CMD_DELETE_CHANNEL:
                    # Move users from deleted channel to General
                    old_users = state.get_users_in_channel(payload)
                    ok, err = channel_mgr.delete_channel(payload)
                    if ok:
                        # Move affected users to no channel
                        for s in state.get_all_text_sockets():
                            if state.get_channel(s) == payload:
                                state.set_channel(s, None)
                        broadcast_text(state, f"{EVT_CHANNEL_DELETED}:{payload}")
                        send_channel_list(state, channel_mgr)
                    else:
                        send_line(client, f"{EVT_CHANNEL_DELETE_FAIL}:{err}")

                elif cmd == CMD_JOIN_CHANNEL:
                    if not channel_mgr.channel_exists(payload):
                        send_line(client, f"{EVT_SYSTEM}:Канал не найден")
                        continue

                    old_channel = state.get_channel(client)
                    if old_channel:
                        state.set_channel(client, None)
                        broadcast_text(state, f"{EVT_USER_LEFT_CHANNEL}:{username}:{old_channel}")
                        send_channel_users(state, old_channel)

                    state.set_channel(client, payload)
                    broadcast_text(state, f"{EVT_USER_JOINED_CHANNEL}:{username}:{payload}")
                    send_channel_users(state, payload)
                    if old_channel and old_channel != payload:
                        send_channel_users(state, old_channel)

                elif cmd == CMD_LEAVE_CHANNEL:
                    old_channel = state.get_channel(client)
                    if old_channel:
                        state.set_channel(client, None)
                        broadcast_text(state, f"{EVT_USER_LEFT_CHANNEL}:{username}:{old_channel}")
                        send_channel_users(state, old_channel)

                else:
                    send_line(client, f"{EVT_SYSTEM}:Неизвестная команда")

        except Exception:
            break

    # Client disconnected
    old_channel = state.get_channel(client)
    state.remove_text_client(client)
    try:
        client.close()
    except Exception:
        pass

    broadcast_text(state, f"{EVT_SYSTEM}:{username} покинул чат")
    send_userlist(state)
    if old_channel:
        send_channel_users(state, old_channel)
    print(f"{username} отключился")


def accept_text_clients(text_server, state, auth_mgr, channel_mgr):
    """Accept loop for text connections."""
    while True:
        try:
            client, address = text_server.accept()
            print(f"Новое подключение от {address}")

            def client_thread(c=client):
                result = handle_auth(c, auth_mgr, state)
                if result is None:
                    try:
                        c.close()
                    except Exception:
                        pass
                    return

                username, remaining_buffer = result
                state.add_text_client(c, username)
                print(f"{username} вошёл в систему")
                broadcast_text(state, f"{EVT_SYSTEM}:{username} присоединился!", exclude_sock=c)
                send_userlist(state)
                send_channel_list(state, channel_mgr, sock=c)
                handle_text_client(c, username, remaining_buffer, state, auth_mgr, channel_mgr)

            t = threading.Thread(target=client_thread, daemon=True)
            t.start()
        except Exception as e:
            print(f"Ошибка приёма подключения: {e}")
