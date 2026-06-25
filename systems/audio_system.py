from pathlib import Path
import sys
import pygame

from config import CONFIG


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


class AudioSystem:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self.current_music = None

        self.sounds_path = resource_path(Path("assets") / "sounds")
        self.music_path = resource_path(Path("assets") / "music")

        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception as error:
            print(f"[Audio] Disabled: {error}")
            return

        self.load_sounds()

    def load_sounds(self):
        sound_files = {
            "shoot": "shoot.wav",
            "hit": "hit.wav",
            "enemy_death": "enemy_death.wav",
            "dash": "dash.wav",
            "level_up": "level_up.wav",
            "room_clear": "room_clear.wav",
            "boss_spawn": "boss_spawn.wav",
            "boss_phase": "boss_phase.wav",
            "menu_select": "menu_select.wav",
        }

        for name, filename in sound_files.items():
            path = self.sounds_path / filename

            if not path.exists():
                print(f"[Audio] Missing sound: {path}")
                continue

            try:
                sound = pygame.mixer.Sound(str(path))
                volume = CONFIG["master_volume"] * CONFIG["sfx_volume"] * CONFIG["sound_volumes"].get(name, 1.0)
                sound.set_volume(volume)
                self.sounds[name] = sound
            except Exception as error:
                print(f"[Audio] Failed loading {path}: {error}")

    def play(self, name):
        if not self.enabled:
            return

        if not CONFIG["sfx_enabled"]:
            return

        sound = self.sounds.get(name)

        if sound:
            sound.play()

    def play_music(self, name, loops=-1):
        if not self.enabled:
            return

        if not CONFIG["music_enabled"]:
            return

        if self.current_music == name:
            return

        path = self.music_path / name

        if not path.exists():
            print(f"[Audio] Missing music: {path}")
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(CONFIG["master_volume"] * CONFIG["music_volume"])
            pygame.mixer.music.play(loops)
            self.current_music = name
        except Exception as error:
            print(f"[Audio] Failed playing music {path}: {error}")

    def stop_music(self):
        if not self.enabled:
            return

        pygame.mixer.music.stop()
        self.current_music = None

    def apply_volumes(self):
        for name, sound in self.sounds.items():
            volume = (
                CONFIG["master_volume"]
                * CONFIG["sfx_volume"]
                * CONFIG["sound_volumes"].get(name, 1.0)
            )
            sound.set_volume(volume)

        if self.enabled:
            pygame.mixer.music.set_volume(
                CONFIG["master_volume"] * CONFIG["music_volume"]
            )
