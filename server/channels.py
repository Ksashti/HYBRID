import json
import threading
from server.config import CHANNELS_FILE, DEFAULT_CHANNELS


class ChannelManager:
    def __init__(self, filepath=None):
        self.filepath = filepath or CHANNELS_FILE
        self.lock = threading.Lock()
        self.channels = self._load()

    def _load(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                channels = data.get("channels", [])
                if not channels:
                    channels = list(DEFAULT_CHANNELS)
                    self._save(channels)
                return channels
        except (FileNotFoundError, json.JSONDecodeError):
            channels = list(DEFAULT_CHANNELS)
            self._save(channels)
            return channels

    def _save(self, channels=None):
        if channels is None:
            channels = self.channels
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump({"channels": channels}, f, indent=2, ensure_ascii=False)

    def create_channel(self, name):
        with self.lock:
            name = name.strip()
            if not name:
                return False, "Имя канала не может быть пустым"
            if len(name) > 32:
                return False, "Имя канала максимум 32 символа"
            if any(ch["name"] == name for ch in self.channels):
                return False, "Канал уже существует"
            self.channels.append({"name": name, "permanent": False})
            self._save()
            return True, None

    def delete_channel(self, name):
        with self.lock:
            ch = next((c for c in self.channels if c["name"] == name), None)
            if not ch:
                return False, "Канал не найден"
            if ch.get("permanent"):
                return False, "Нельзя удалить постоянный канал"
            self.channels.remove(ch)
            self._save()
            return True, None

    def get_channel_names(self):
        with self.lock:
            return [ch["name"] for ch in self.channels]

    def channel_exists(self, name):
        with self.lock:
            return any(ch["name"] == name for ch in self.channels)
