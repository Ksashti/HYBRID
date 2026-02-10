"""
Audio engine: device enumeration, stream management, mute flags.
Ports the Windows MME ctypes logic from the old client_gui.py.
"""

import struct
import sys
import ctypes
import pyaudio
from client.audio.opus_codec import SAMPLE_RATE, CHANNELS, FRAME_SIZE

FORMAT = pyaudio.paInt16
NOISE_GATE_DEFAULT = 200


class AudioEngine:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.sample_rate = SAMPLE_RATE
        self.channels = CHANNELS
        self.frame_size = FRAME_SIZE
        self.format = FORMAT

        self.input_devices = []
        self.output_devices = []
        self.selected_input = None
        self.selected_output = None

        self.mic_muted = False
        self.sound_muted = False
        self.noise_gate = NOISE_GATE_DEFAULT
        self.volume = 100
        self.user_volumes = {}  # {username: 0-200}

        self._enumerate_devices()

    def _get_winmm_names(self):
        """Get proper Unicode device names via Windows MME API."""
        input_names = {}
        output_names = {}

        if sys.platform != 'win32':
            return input_names, output_names

        try:
            winmm = ctypes.windll.winmm
            WAVE_MAPPER = 0xFFFFFFFF

            class WAVEINCAPSW(ctypes.Structure):
                _fields_ = [
                    ('wMid', ctypes.c_ushort),
                    ('wPid', ctypes.c_ushort),
                    ('vDriverVersion', ctypes.c_uint),
                    ('szPname', ctypes.c_wchar * 32),
                    ('dwFormats', ctypes.c_uint),
                    ('wChannels', ctypes.c_ushort),
                    ('wReserved1', ctypes.c_ushort),
                ]

            class WAVEOUTCAPSW(ctypes.Structure):
                _fields_ = [
                    ('wMid', ctypes.c_ushort),
                    ('wPid', ctypes.c_ushort),
                    ('vDriverVersion', ctypes.c_uint),
                    ('szPname', ctypes.c_wchar * 32),
                    ('dwFormats', ctypes.c_uint),
                    ('wChannels', ctypes.c_ushort),
                    ('wReserved1', ctypes.c_ushort),
                    ('dwSupport', ctypes.c_uint),
                ]

            caps = WAVEINCAPSW()
            if winmm.waveInGetDevCapsW(WAVE_MAPPER, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                input_names[-1] = caps.szPname

            for i in range(winmm.waveInGetNumDevs()):
                caps = WAVEINCAPSW()
                if winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    input_names[i] = caps.szPname

            caps = WAVEOUTCAPSW()
            if winmm.waveOutGetDevCapsW(WAVE_MAPPER, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                output_names[-1] = caps.szPname

            for i in range(winmm.waveOutGetNumDevs()):
                caps = WAVEOUTCAPSW()
                if winmm.waveOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    output_names[i] = caps.szPname
        except Exception:
            pass
        return input_names, output_names

    def _enumerate_devices(self):
        """Enumerate audio devices with proper Unicode names."""
        self.input_devices = []
        self.output_devices = []

        win_in, win_out = self._get_winmm_names()

        try:
            default_host = self.audio.get_default_host_api_info()['index']
        except Exception:
            default_host = 0

        try:
            host_info = self.audio.get_host_api_info_by_index(default_host)
        except Exception:
            return

        pa_inputs = []
        pa_outputs = []
        for local_idx in range(host_info['deviceCount']):
            try:
                info = self.audio.get_device_info_by_host_api_device_index(default_host, local_idx)
                if info['maxInputChannels'] > 0:
                    pa_inputs.append(info)
                if info['maxOutputChannels'] > 0:
                    pa_outputs.append(info)
            except Exception:
                pass

        num_win_in = len([k for k in win_in if k >= 0])
        num_win_out = len([k for k in win_out if k >= 0])
        in_offset = 1 if len(pa_inputs) == num_win_in + 1 else 0
        out_offset = 1 if len(pa_outputs) == num_win_out + 1 else 0

        seen_input = set()
        seen_output = set()

        for i, info in enumerate(pa_inputs):
            global_idx = info['index']
            win_idx = i - in_offset
            name = win_in.get(win_idx, info['name'])
            if name not in seen_input:
                self.input_devices.append((global_idx, name))
                seen_input.add(name)

        for i, info in enumerate(pa_outputs):
            global_idx = info['index']
            win_idx = i - out_offset
            name = win_out.get(win_idx, info['name'])
            if name not in seen_output:
                self.output_devices.append((global_idx, name))
                seen_output.add(name)

        if self.input_devices:
            self.selected_input = self.input_devices[0][0]
        if self.output_devices:
            self.selected_output = self.output_devices[0][0]

    def open_input_stream(self):
        """Open microphone stream."""
        return self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.frame_size,
            input_device_index=self.selected_input
        )

    def open_output_stream(self):
        """Open speaker stream."""
        return self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.frame_size,
            output_device_index=self.selected_output
        )

    @staticmethod
    def calc_rms(data):
        """Compute RMS level of 16-bit PCM audio."""
        count = len(data) // 2
        if count == 0:
            return 0
        total = 0
        for i in range(0, len(data) - 1, 2):
            sample = struct.unpack('<h', data[i:i + 2])[0]
            total += sample * sample
        return (total / count) ** 0.5

    def apply_volume(self, audio_data, sender=None):
        """Apply master + per-user volume to PCM audio data."""
        user_vol = self.user_volumes.get(sender, 100) if sender else 100
        vol = (self.volume / 100.0) * (user_vol / 100.0)

        if vol == 1.0:
            return audio_data

        adjusted = bytearray()
        for i in range(0, len(audio_data) - 1, 2):
            sample = struct.unpack('<h', audio_data[i:i + 2])[0]
            sample = int(sample * vol)
            sample = max(-32768, min(32767, sample))
            adjusted.extend(struct.pack('<h', sample))
        return bytes(adjusted)

    def terminate(self):
        """Clean up PyAudio."""
        self.audio.terminate()
