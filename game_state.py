from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    HUB = auto()
    ROOM = auto()
    BOSS = auto()
    PERK_SELECT = auto()
    PAUSED = auto()
    SETTINGS = auto()
    GAME_OVER = auto()
    WIN = auto()
