import json
import os
import sys

DEFAULT_SERVER_IP = "192.168.1.101"

def _get_config_dir():
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~')
    config_dir = os.path.join(base, 'HYBRID')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

CONFIG_FILE = os.path.join(_get_config_dir(), 'config.json')


def load_config():
    """Load config from disk. Returns dict with defaults if file missing."""
    defaults = {
        "server_ip": DEFAULT_SERVER_IP,
        "username": "",
        "password": "",
        "remember_me": False,
        "audio": {
            "input_device": "",
            "output_device": "",
            "noise_gate": 200,
            "va_threshold": 500,
            "voice_mode": "ptt"
        },
        "volume": {
            "master": 100,
            "users": {}
        }
    }
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Merge with defaults
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
                elif isinstance(val, dict):
                    for k2, v2 in val.items():
                        if k2 not in data[key]:
                            data[key][k2] = v2
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults


def save_config(config):
    """Save config to disk."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
