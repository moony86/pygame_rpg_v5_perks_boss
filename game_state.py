from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    HUB = auto()
    ROOM = auto()
    BOSS = auto()
    PERK_SELECT = auto()
    GAME_OVER = auto()
    WIN = auto()
