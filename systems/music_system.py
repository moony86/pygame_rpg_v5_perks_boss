from pathlib import Path

import pygame

from config import CONFIG
from systems.audio_system import resource_path


MUSIC_TRACKS = {
    "hub": "hub.ogg",
    "room": "combat.ogg",
    "boss": "boss_01.ogg",
}
MUSIC_FALLBACKS = {"boss": "boss.ogg"}


class MusicSystem:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.current_key = None
        self.music_path = resource_path(Path("assets") / "music")

    def play_music(self, key, fade_ms=500):
        if not self.enabled or not CONFIG.get("music_enabled", True):
            return False
        if key == self.current_key:
            return True

        filename = MUSIC_TRACKS.get(key)
        if filename is None:
            return False

        for candidate in (filename, MUSIC_FALLBACKS.get(key)):
            if candidate is None:
                continue
            path = self.music_path / candidate
            if not path.exists():
                continue
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(CONFIG["master_volume"] * CONFIG["music_volume"])
                pygame.mixer.music.play(loops=-1, fade_ms=max(0, int(fade_ms)))
                self.current_key = key
                return True
            except pygame.error:
                continue
        return False

    def stop_music(self, fade_ms=500):
        if not self.enabled:
            self.current_key = None
            return False
        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(int(fade_ms))
            else:
                pygame.mixer.music.stop()
            self.current_key = None
            return True
        except pygame.error:
            self.current_key = None
            return False

    def apply_volume(self):
        if not self.enabled:
            return
        pygame.mixer.music.set_volume(CONFIG["master_volume"] * CONFIG["music_volume"])
