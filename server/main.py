import socket
import threading
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import TEXT_PORT, VOICE_PORT, BIND_ADDRESS
from server.state import ServerState
from server.auth import AuthManager
from server.channels import ChannelManager
from server.text_handler import accept_text_clients
from server.voice_handler import accept_voice_clients


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith('172.'):
            try:
                hostname_ip = socket.gethostbyname(socket.gethostname())
                if hostname_ip.startswith('192.168.') or hostname_ip.startswith('10.'):
                    return hostname_ip
            except Exception:
                pass
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "не удалось определить"


def main():
    state = ServerState()
    auth_mgr = AuthManager()
    channel_mgr = ChannelManager()

    text_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    text_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    text_server.bind((BIND_ADDRESS, TEXT_PORT))
    text_server.listen()

    voice_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    voice_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    voice_server.bind((BIND_ADDRESS, VOICE_PORT))
    voice_server.listen()

    local_ip = get_local_ip()
    print("=" * 50)
    print("  HYBRID Server v2.0")
    print("=" * 50)
    print(f"  Текстовый сервер: порт {TEXT_PORT}")
    print(f"  Голосовой сервер: порт {VOICE_PORT}")
    print(f"  Локальный IP: {local_ip}")
    print(f"  Каналы: {', '.join(channel_mgr.get_channel_names())}")
    print(f"  Зарегистрировано пользователей: {len(auth_mgr.users)}")
    print("=" * 50)
    print("Ожидание подключений...\n")

    text_thread = threading.Thread(
        target=accept_text_clients,
        args=(text_server, state, auth_mgr, channel_mgr),
        daemon=True
    )
    voice_thread = threading.Thread(
        target=accept_voice_clients,
        args=(voice_server, state),
        daemon=True
    )

    text_thread.start()
    voice_thread.start()

    try:
        text_thread.join()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")


if __name__ == "__main__":
    main()
