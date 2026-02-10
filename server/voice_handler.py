import socket
import threading
import struct
from server.protocol import CODEC_OPUS


def recv_exact(sock, n):
    """Read exactly n bytes from socket."""
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def broadcast_voice(framed_data, sender_sock, state):
    """Broadcast voice frame to all voice clients in the same channel as sender."""
    sender_info = state.voice_clients.get(sender_sock)
    if not sender_info or not sender_info.get("channel"):
        return

    channel = sender_info["channel"]
    targets = state.get_voice_sockets_in_channel(channel)

    for sock in targets:
        if sock != sender_sock:
            try:
                sock.send(framed_data)
            except Exception:
                pass


def handle_voice_client(voice_client, state):
    """Handle voice data from a single client."""
    while True:
        try:
            len_data = recv_exact(voice_client, 4)
            if not len_data:
                break
            msg_len = struct.unpack('>I', len_data)[0]
            if msg_len > 65536:
                break
            voice_data = recv_exact(voice_client, msg_len)
            if not voice_data:
                break

            # Reframe: prepend the length header back for broadcasting
            framed = struct.pack('>I', msg_len) + voice_data
            broadcast_voice(framed, voice_client, state)
        except Exception:
            break

    state.remove_voice_client(voice_client)
    try:
        voice_client.close()
    except Exception:
        pass


def accept_voice_clients(voice_server, state):
    """Accept loop for voice connections."""
    while True:
        try:
            voice_client, address = voice_server.accept()
            # Set TCP_NODELAY for lower latency
            voice_client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            try:
                nick_data = voice_client.recv(1024).decode('utf-8').strip()
            except Exception:
                nick_data = ""

            state.add_voice_client(voice_client, nick_data)
            print(f"Голосовое подключение от {address} ({nick_data})")

            t = threading.Thread(target=handle_voice_client, args=(voice_client, state), daemon=True)
            t.start()
        except Exception as e:
            print(f"Ошибка голосового подключения: {e}")
