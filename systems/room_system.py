import random
from enum import Enum, auto

from settings import ROOM_KILLS_REQUIRED, SURVIVAL_ROOM_TIME


class RoomType(Enum):
    COMBAT = auto()
    SURVIVAL = auto()
    ELITE = auto()
    TREASURE = auto()
    CURSE = auto()


ROOM_INFO = {
    RoomType.COMBAT: {
        "title": "COMBAT ROOM",
        "message": "Clear the waves.",
        "color": (220, 55, 55),
        "spawn_multiplier": 1.0,
        "enemy_difficulty": 1.0,
    },
    RoomType.SURVIVAL: {
        "title": "SURVIVAL ROOM",
        "message": "Survive the horde.",
        "color": (245, 150, 45),
        "spawn_multiplier": 1.8,
        "enemy_difficulty": 1.10,
    },
    RoomType.ELITE: {
        "title": "ELITE ROOM",
        "message": "Defeat the elite guard.",
        "color": (255, 90, 170),
        "spawn_multiplier": 0.0,
        "enemy_difficulty": 1.25,
    },
    RoomType.TREASURE: {
        "title": "TREASURE ROOM",
        "message": "Claim your reward.",
        "color": (235, 180, 40),
        "spawn_multiplier": 0.0,
        "enemy_difficulty": 0.0,
    },
    RoomType.CURSE: {
        "title": "CURSE ROOM",
        "message": "High risk, double reward.",
        "color": (150, 70, 220),
        "spawn_multiplier": 1.65,
        "enemy_difficulty": 1.20,
    },
}


class RoomSystem:
    def __init__(self):
        self.room_type = None
        self.room_time = 0.0
        self.banner_timer = 2.2
        self.reward_multiplier = 1

        self.target_kills = 0
        self.survival_time = SURVIVAL_ROOM_TIME

    def choose_next_room(self, room_number):
        """
        Current compatible progression.

        Important:
        Boss is handled outside this file by game/scene logic.
        This system only chooses normal rooms.
        """

        room_plan = {
            1: RoomType.COMBAT,
            2: RoomType.COMBAT,
            3: RoomType.TREASURE,
            4: RoomType.ELITE,

            6: RoomType.COMBAT,
            7: RoomType.SURVIVAL,
            8: RoomType.TREASURE,
            9: RoomType.CURSE,
        }

        self.room_type = room_plan.get(room_number, RoomType.COMBAT)

        self.room_time = 0.0
        self.banner_timer = 2.2
        self.reward_multiplier = 2 if self.room_type == RoomType.CURSE else 1

        if self.room_type == RoomType.COMBAT:
            self.target_kills = 18 + room_number * 4

        elif self.room_type == RoomType.CURSE:
            self.target_kills = 24 + room_number * 5

        elif self.room_type == RoomType.ELITE:
            self.target_kills = 1

        elif self.room_type == RoomType.TREASURE:
            self.target_kills = 0

        elif self.room_type == RoomType.SURVIVAL:
            # game.py currently displays Survival as Horde using target_kills.
            # Keep this non-zero until game.py is changed to display Time instead.
            self.target_kills = 120 + room_number * 20

        self.survival_time = 28 + room_number * 3

        return self.room_type

    def update(self, dt):
        self.room_time += dt

        if self.banner_timer > 0:
            self.banner_timer = max(0, self.banner_timer - dt)

    def is_clear(self, kills):
        """
        Legacy compatibility.

        game.py currently does not rely on this for portal opening,
        but keep it to avoid breaking older references.
        """

        if self.room_type == RoomType.TREASURE:
            return True

        if self.room_type == RoomType.SURVIVAL:
            return self.room_time >= self.survival_time

        return kills >= self.target_kills

    def display_name(self):
        if self.room_type is None:
            return ""

        return self.room_type.name.title()

    def info(self):
        return ROOM_INFO[self.room_type]

    def spawn_multiplier(self):
        return self.info()["spawn_multiplier"]

    def enemy_difficulty_multiplier(self):
        return self.info()["enemy_difficulty"]