import json
import hashlib
import os
import threading
from datetime import datetime
from server.config import USERS_FILE, MAX_USERNAME_LEN, MIN_USERNAME_LEN, MIN_PASSWORD_LEN


class AuthManager:
    def __init__(self, filepath=None):
        self.filepath = filepath or USERS_FILE
        self.lock = threading.Lock()
        self.users = self._load()

    def _load(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("users", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self._save({})
            return {}

    def _save(self, users=None):
        if users is None:
            users = self.users
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump({"users": users}, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _hash_password(password, salt=None):
        """SHA-256 with salt. Using hashlib to avoid bcrypt DLL issues on Windows."""
        if salt is None:
            salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return f"{salt}${hashed}"

    @staticmethod
    def _verify_password(password, stored_hash):
        salt, hashed = stored_hash.split('$', 1)
        check = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return check == hashed

    def register(self, username, password):
        with self.lock:
            if username in self.users:
                return False, "Имя уже занято"
            if len(username) < MIN_USERNAME_LEN or len(username) > MAX_USERNAME_LEN:
                return False, f"Имя должно быть {MIN_USERNAME_LEN}-{MAX_USERNAME_LEN} символов"
            if len(password) < MIN_PASSWORD_LEN:
                return False, f"Пароль минимум {MIN_PASSWORD_LEN} символов"
            self.users[username] = {
                "password_hash": self._hash_password(password),
                "created_at": datetime.now().isoformat()
            }
            self._save()
            return True, None

    def login(self, username, password):
        with self.lock:
            user = self.users.get(username)
            if not user:
                return False, "Пользователь не найден"
            if self._verify_password(password, user["password_hash"]):
                return True, None
            return False, "Неверный пароль"
