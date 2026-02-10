import threading


class ServerState:
    """Global mutable server state, protected by lock."""

    def __init__(self):
        self.lock = threading.Lock()
        # {socket: {"username": str, "channel": str|None}}
        self.text_clients = {}
        # {socket: {"username": str, "channel": str|None}}
        self.voice_clients = {}

    def add_text_client(self, sock, username):
        with self.lock:
            self.text_clients[sock] = {"username": username, "channel": None}

    def remove_text_client(self, sock):
        with self.lock:
            info = self.text_clients.pop(sock, None)
            return info

    def add_voice_client(self, sock, username):
        with self.lock:
            self.voice_clients[sock] = {"username": username, "channel": None}

    def remove_voice_client(self, sock):
        with self.lock:
            return self.voice_clients.pop(sock, None)

    def set_channel(self, sock, channel_name):
        """Set the channel for a text client and its linked voice client."""
        with self.lock:
            if sock in self.text_clients:
                self.text_clients[sock]["channel"] = channel_name
            # Also update voice client for same username
            username = None
            if sock in self.text_clients:
                username = self.text_clients[sock]["username"]
            if username:
                for vs, vinfo in self.voice_clients.items():
                    if vinfo["username"] == username:
                        vinfo["channel"] = channel_name
                        break

    def get_channel(self, sock):
        with self.lock:
            info = self.text_clients.get(sock)
            if info:
                return info.get("channel")
            return None

    def get_username(self, sock):
        with self.lock:
            info = self.text_clients.get(sock)
            if info:
                return info["username"]
            return None

    def get_all_usernames(self):
        with self.lock:
            return [info["username"] for info in self.text_clients.values()]

    def get_users_in_channel(self, channel_name):
        with self.lock:
            return [
                info["username"]
                for info in self.text_clients.values()
                if info.get("channel") == channel_name
            ]

    def get_text_sockets_in_channel(self, channel_name):
        with self.lock:
            return [
                sock for sock, info in self.text_clients.items()
                if info.get("channel") == channel_name
            ]

    def get_voice_sockets_in_channel(self, channel_name):
        with self.lock:
            return [
                sock for sock, info in self.voice_clients.items()
                if info.get("channel") == channel_name
            ]

    def get_all_text_sockets(self):
        with self.lock:
            return list(self.text_clients.keys())

    def is_username_online(self, username):
        with self.lock:
            return any(info["username"] == username for info in self.text_clients.values())
