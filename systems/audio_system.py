import math
import pygame


class AudioSystem:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            import numpy as np
            self.np = np
            self.enabled = True
            self._build_sounds()
        except Exception:
            self.enabled = False

    def _tone(self, freq=440, duration=0.08, volume=0.25, wave="sine"):
        np = self.np
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        if wave == "square":
            audio = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave == "noise":
            audio = np.random.uniform(-1, 1, len(t))
        else:
            audio = np.sin(2 * np.pi * freq * t)

        envelope = np.linspace(1, 0, len(t))
        audio = audio * envelope * volume
        arr = (audio * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(arr)

    def _build_sounds(self):
        self.sounds["shoot"] = self._tone(720, 0.045, 0.18, "square")
        self.sounds["hit"] = self._tone(210, 0.05, 0.20, "noise")
        self.sounds["death"] = self._tone(120, 0.12, 0.25, "square")
        self.sounds["level"] = self._tone(880, 0.18, 0.25, "sine")
        self.sounds["room"] = self._tone(520, 0.25, 0.22, "sine")
        self.sounds["boss"] = self._tone(90, 0.35, 0.35, "square")
        self.sounds["dash"] = self._tone(480, 0.09, 0.22, "noise")
        self.sounds["select"] = self._tone(620, 0.06, 0.18, "sine")

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.play()
