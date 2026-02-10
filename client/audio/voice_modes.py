"""
Voice mode logic: Push-to-Talk (PTT) and Voice Activity Detection (VA).
"""


class VoiceModeManager:
    def __init__(self):
        self.mode = "ptt"  # "ptt" or "va"
        self.ptt_active = False
        self.va_active = False
        self.va_threshold = 500

    def is_ptt(self):
        return self.mode == "ptt"

    def is_va(self):
        return self.mode == "va"

    def toggle_mode(self):
        if self.mode == "ptt":
            self.mode = "va"
            self.va_active = True
        else:
            self.mode = "ptt"
            self.va_active = False
            self.ptt_active = False
        return self.mode

    def set_ptt(self, active):
        """Set PTT state (press/release)."""
        if self.mode == "ptt":
            self.ptt_active = active

    def should_transmit(self, rms=0):
        """Check if audio should be transmitted based on mode and input level."""
        if self.mode == "ptt":
            return self.ptt_active
        elif self.mode == "va":
            return self.va_active and rms > self.va_threshold
        return False
