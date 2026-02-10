import os

TEXT_PORT = 5557
VOICE_PORT = 5556
BIND_ADDRESS = '0.0.0.0'

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(DATA_DIR, '..', 'users.json')
CHANNELS_FILE = os.path.join(DATA_DIR, '..', 'channels.json')

MAX_VOICE_FRAME = 65536
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 2
MIN_PASSWORD_LEN = 4

DEFAULT_CHANNELS = [
    {"name": "General", "permanent": True}
]
