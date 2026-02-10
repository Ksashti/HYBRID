"""
Opus codec wrapper for HYBRID VoiceChat.
Uses opuslib (ctypes binding to libopus).
Falls back to raw PCM if opuslib/libopus not available.
"""

import struct
import sys
import os
import ctypes

def _ensure_opus_dll():
    """Locate and preload opus.dll so opuslib can find it."""
    # In frozen (PyInstaller) builds
    if getattr(sys, 'frozen', False):
        os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

    # Try loading from pyogg package (it bundles opus.dll on Windows)
    try:
        import pyogg
        pyogg_dir = os.path.dirname(pyogg.__file__)
        opus_dll_path = os.path.join(pyogg_dir, 'opus.dll')
        if os.path.exists(opus_dll_path):
            ctypes.cdll.LoadLibrary(opus_dll_path)
            return True
    except Exception:
        pass

    # Try system PATH
    try:
        ctypes.cdll.LoadLibrary('opus')
        return True
    except Exception:
        pass

    return False

_ensure_opus_dll()

OPUS_AVAILABLE = False
try:
    import opuslib
    OPUS_AVAILABLE = True
except Exception:
    pass

# Audio constants
SAMPLE_RATE = 48000
CHANNELS = 1
FRAME_SIZE = 960  # 20ms at 48kHz
BITRATE = 64000
CODEC_ID_OPUS = 0x01
CODEC_ID_RAW = 0x00


class OpusCodec:
    """Opus encode/decode. Falls back to passthrough if opuslib unavailable."""

    def __init__(self):
        self.available = OPUS_AVAILABLE
        self.encoder = None
        self.decoder = None

        if self.available:
            try:
                self.encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_VOIP)
                self.encoder.bitrate = BITRATE
                self.decoder = opuslib.Decoder(SAMPLE_RATE, CHANNELS)
            except Exception:
                self.available = False
                self.encoder = None
                self.decoder = None

    @property
    def codec_id(self):
        return CODEC_ID_OPUS if self.available else CODEC_ID_RAW

    def encode(self, pcm_data):
        """Encode raw PCM bytes to Opus. Returns (codec_id, encoded_bytes)."""
        if self.available and self.encoder:
            try:
                opus_data = self.encoder.encode(pcm_data, FRAME_SIZE)
                return CODEC_ID_OPUS, opus_data
            except Exception:
                pass
        return CODEC_ID_RAW, pcm_data

    def decode(self, codec_id, data):
        """Decode Opus or raw PCM back to raw PCM bytes."""
        if codec_id == CODEC_ID_OPUS and self.available and self.decoder:
            try:
                return self.decoder.decode(data, FRAME_SIZE)
            except Exception:
                return data
        return data


def build_voice_frame(nickname, codec_id, audio_data):
    """Build a binary voice frame for transmission.

    Format:
        [4B BE] total_payload_length
        [2B BE] nick_length
        [NB]    nick_bytes
        [1B]    codec_id
        [2B BE] audio_data_length
        [NB]    audio_data
    """
    nick_bytes = nickname.encode('utf-8')
    payload = (
        struct.pack('>H', len(nick_bytes)) +
        nick_bytes +
        struct.pack('B', codec_id) +
        struct.pack('>H', len(audio_data)) +
        audio_data
    )
    return struct.pack('>I', len(payload)) + payload


def parse_voice_frame(payload):
    """Parse voice frame payload (without the 4-byte length prefix).

    Returns: (nickname, codec_id, audio_data) or None on error.
    """
    try:
        if len(payload) < 5:
            return None
        nick_len = struct.unpack('>H', payload[:2])[0]
        offset = 2
        if len(payload) < offset + nick_len + 3:
            return None
        nickname = payload[offset:offset + nick_len].decode('utf-8')
        offset += nick_len
        codec_id = payload[offset]
        offset += 1
        audio_len = struct.unpack('>H', payload[offset:offset + 2])[0]
        offset += 2
        audio_data = payload[offset:offset + audio_len]
        return nickname, codec_id, audio_data
    except Exception:
        return None
