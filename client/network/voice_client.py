"""
Voice socket client running in a QThread.
Handles binary voice frames with Opus decode.
"""

import socket
import struct
import select
from PyQt5.QtCore import QThread, pyqtSignal
from client.protocol import VOICE_PORT
from client.audio.opus_codec import parse_voice_frame, build_voice_frame, OpusCodec


class VoiceClient(QThread):
    # (sender_nickname, pcm_audio_bytes)
    voice_received = pyqtSignal(str, bytes)
    disconnected = pyqtSignal()

    def __init__(self, host, username, port=VOICE_PORT, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.username = username
        self.sock = None
        self.running = False
        self.codec = OpusCodec()

    def connect_to_server(self):
        """Establish voice TCP connection."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # Send username for voice identification
        self.sock.send(self.username.encode('utf-8'))
        self.running = True

    def send_voice(self, pcm_data):
        """Encode and send a voice frame."""
        if not self.sock or not self.running:
            return
        codec_id, encoded = self.codec.encode(pcm_data)
        frame = build_voice_frame(self.username, codec_id, encoded)
        try:
            self.sock.send(frame)
        except Exception:
            pass

    def _recv_exact(self, n):
        """Read exactly n bytes."""
        data = b''
        while len(data) < n and self.running:
            try:
                chunk = self.sock.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception:
                return None
        return data if len(data) == n else None

    def run(self):
        """QThread main loop: receive and decode voice frames."""
        while self.running:
            ready = select.select([self.sock], [], [], 0.3)
            if not ready[0]:
                continue

            try:
                len_data = self._recv_exact(4)
                if not len_data:
                    break
                msg_len = struct.unpack('>I', len_data)[0]
                if msg_len > 65536:
                    break

                payload = self._recv_exact(msg_len)
                if not payload:
                    break

                parsed = parse_voice_frame(payload)
                if not parsed:
                    continue

                nickname, codec_id, audio_data = parsed
                pcm_data = self.codec.decode(codec_id, audio_data)
                self.voice_received.emit(nickname, pcm_data)

            except Exception:
                break

        self.running = False
        self.disconnected.emit()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
