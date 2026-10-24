import json
import os
import sys
from pathlib import Path

CONFIG = {
    "master_volume": 0.5,
    "sfx_volume": 0.3,
    "music_volume": 0.2,
    "sfx_enabled": True,
    "music_enabled": True,
    "show_fps": True,
    "screen_shake": True,
    "aim_assist": True,
    "reduced_flashes": False,

    "sound_volumes": {
        "shoot": 0.22,
        "hit": 0.45,
        "enemy_death": 0.55,
        "dash": 0.45,
        "level_up": 0.65,
        "room_clear": 0.65,
        "boss_spawn": 0.75,
        "boss_phase": 0.75,
        "boss_death": 0.75,
        "peckcard": 0.55,
        "wave_start": 0.50,
        "wave_clear": 0.60,
        "portal_open": 0.65,
        "upgrade_buy": 0.50,
        "coin_pickup": 0.35,
        "xp_pickup": 0.30,
        "tea_drink": 0.45,
        "menu_select": 0.35,
    },
}

USER_KEYS = ('master_volume','sfx_volume','music_volume','screen_shake','aim_assist','reduced_flashes')


def settings_path():
    override = os.environ.get('BLUECUBE_SETTINGS_PATH')
    if override:
        return Path(override)
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.config'))) / 'BlueCube' / 'settings.json'


def load_preferences():
    if sys.platform == 'emscripten':
        return  # Browser is an internal QA harness, not a supported player build.
    try:
        data = json.loads(settings_path().read_text(encoding='utf-8'))
        for key in USER_KEYS:
            value = data.get(key)
            if key.endswith('_volume') and isinstance(value, (int,float)) and not isinstance(value,bool):
                if 0 <= value <= 1:
                    CONFIG[key] = float(value)
            elif not key.endswith('_volume') and isinstance(value,bool):
                CONFIG[key] = value
    except (OSError, ValueError, AttributeError):
        pass


def save_preferences():
    if sys.platform == 'emscripten':
        return True
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({k:CONFIG[k] for k in USER_KEYS},indent=2),encoding='utf-8')
        temporary.replace(path)
        return True
    except OSError:
        return False


load_preferences()
