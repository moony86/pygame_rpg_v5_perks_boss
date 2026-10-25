from pathlib import Path
import sys
import pygame

from config import CONFIG
from systems.class_audio import CUES

SOUND_FILES = {
    **{cue:cue+'.wav' for values in CUES.values() for cue in (values['shoot'], values['impact'])},
    "shoot": "shoot.wav",
    "hit": "hit.wav",
    "enemy_death": "enemy_death.wav",
    "dash": "dash.wav",
    "level_up": "level_up.wav",
    "room_clear": "room_clear.wav",
    "boss_spawn": "boss_spawn.wav",
    "boss_phase": "boss_phase.wav",
    "boss_death": "boss_death.wav",
    "coin_pickup": "coin_pickup.wav",
    "xp_pickup": "xp_pickup.wav",
    "peckcard": "peckcard.wav",
    "wave_start": "wave_start.wav",
    "wave_clear": "wave_clear.wav",
    "portal_open": "portal_open.wav",
    "upgrade_buy": "upgrade_buy.wav",
    "menu_select": "menu_select.wav",
    "tea_drink": "tea_drink.wav",
    **{key:key+'.wav' for key in ('heal_pickup','boost_pickup','time_stop_pickup',
       'time_stop_tick','time_stop_tock','time_stop_end','boss_warning','boss_exposed',
       'boss_guard','boss_eye_break','boss_eye_heal','boss_parry_ready','ninja_parry','player_hurt','low_health')},
}

CUE_CHANNELS={'player_hurt':2,'low_health':2,'time_stop_pickup':0,'time_stop_end':0,'time_stop_tick':1,'time_stop_tock':1,
              'heal_pickup':2,'boost_pickup':2,'boss_warning':3,'boss_parry_ready':3,
              'boss_exposed':4,'boss_eye_break':5,'ninja_parry':5,'boss_eye_heal':4,'boss_guard':4}
CUE_GAINS={'time_stop_tick':.40,'time_stop_tock':.40,'time_stop_pickup':.80,
           'player_hurt':.80,'low_health':.50,
           'time_stop_end':.70,'heal_pickup':.85,'boost_pickup':.85,'boss_guard':.30,
           'boss_eye_heal':.35,'boss_warning':.75,'boss_parry_ready':.85,'ninja_parry':.90}
CUE_GAINS.update({cue:values['gain'] for values in CUES.values()
                  for cue in (values['shoot'], values['impact'])})


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


class AudioSystem:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self.current_music = None
        self._time_active = False
        self._tick_timer = 0.
        self._tick_index = 0
        self._low_timer = 0.

        self.sounds_path = resource_path(Path("assets") / "sounds")
        self.music_path = resource_path(Path("assets") / "music")

        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(max(20,pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(6)
            self.enabled = True
        except Exception as error:
            print(f"[Audio] Disabled: {error}")
            return

        self.load_sounds()

    def load_sounds(self):
        for name, filename in SOUND_FILES.items():
            path = self.sounds_path / filename

            if not path.exists():
                print(f"[Audio] Missing sound: {path}")
                continue

            try:
                sound = pygame.mixer.Sound(str(path))
                volume = CONFIG["master_volume"] * CONFIG["sfx_volume"] * CONFIG["sound_volumes"].get(name, CUE_GAINS.get(name,1.0))
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
            if name in CUE_CHANNELS:
                pygame.mixer.Channel(CUE_CHANNELS[name]).play(sound)
            else:
                sound.play()

    def reset_context(self):
        self._time_active=False
        self._low_timer=0.
        self._tick_timer=0.
        self._tick_index=0
        if self.enabled:
            for index in (0,1):
                pygame.mixer.Channel(index).stop()

    def update_context(self, player, state_name, dt):
        if state_name not in ('HUB','ROOM','BOSS'):
            self.reset_context()  # Pause/menu/death must never leave a ticking clock.
            return
        active=getattr(player,'enemy_time_stop_timer',0)>0
        if 0<player.health/max(1,player.max_health)<=.25:
            self._low_timer-=dt
            if self._low_timer<=0:
                # Never interrupt an important pickup/hurt cue with a heartbeat.
                if not self.enabled or not pygame.mixer.Channel(2).get_busy():
                    self.play('low_health')
                    self._low_timer=1.2
        else:
            self._low_timer=0.
        if active:
            if not self._time_active:
                self._tick_timer=.20
                self._tick_index=0
            self._tick_timer-=dt
            if self._tick_timer<=0:
                self.play('time_stop_tick' if self._tick_index%2==0 else 'time_stop_tock')
                self._tick_index+=1
                self._tick_timer+=.38
        elif self._time_active:
            if self.enabled:
                pygame.mixer.Channel(1).stop()
            self.play('time_stop_end')
        self._time_active=active

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
                * CONFIG["sound_volumes"].get(name, CUE_GAINS.get(name,1.0))
            )
            sound.set_volume(volume)

        if self.enabled:
            pygame.mixer.music.set_volume(
                CONFIG["master_volume"] * CONFIG["music_volume"]
            )
