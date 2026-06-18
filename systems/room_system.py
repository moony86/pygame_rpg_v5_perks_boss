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
        "message": "Kill all enemies.",
        "color": (220, 55, 55),
        "spawn_multiplier": 1.0,
        "enemy_difficulty": 1.0,
    },
    RoomType.SURVIVAL: {
        "title": "SURVIVAL ROOM",
        "message": "Survive until the timer ends.",
        "color": (245, 150, 45),
        "spawn_multiplier": 1.45,
        "enemy_difficulty": 1.15,
    },
    RoomType.ELITE: {
        "title": "ELITE ROOM",
        "message": "Defeat the elite enemy.",
        "color": (255, 90, 170),
        "spawn_multiplier": 0.0,
        "enemy_difficulty": 1.4,
    },
    RoomType.TREASURE: {
        "title": "TREASURE ROOM",
        "message": "Free reward. No combat.",
        "color": (235, 180, 40),
        "spawn_multiplier": 0.0,
        "enemy_difficulty": 0.0,
    },
    RoomType.CURSE: {
        "title": "CURSE ROOM",
        "message": "Enemies are stronger. Rewards are doubled.",
        "color": (150, 70, 220),
        "spawn_multiplier": 1.75,
        "enemy_difficulty": 1.35,
    },
}


class RoomSystem:
    def __init__(self):
        self.room_type = RoomType.COMBAT
        self.room_time = 0.0
        self.target_kills = ROOM_KILLS_REQUIRED
        self.survival_time = SURVIVAL_ROOM_TIME
        self.reward_multiplier = 1
        self.banner_timer = 0.0

    def choose_next_room(self, room_number):
        if room_number == 1:
            self.room_type = RoomType.COMBAT
        else:
            pool = [
                RoomType.COMBAT,
                RoomType.SURVIVAL,
                RoomType.ELITE,
                RoomType.TREASURE,
                RoomType.CURSE,
            ]
            weights = [35, 25, 16, 10, 14]
            self.room_type = random.choices(pool, weights=weights, k=1)[0]

        self.room_time = 0.0
        self.banner_timer = 2.2
        self.reward_multiplier = 2 if self.room_type == RoomType.CURSE else 1

        if self.room_type == RoomType.COMBAT:
            self.target_kills = ROOM_KILLS_REQUIRED + room_number * 2
        elif self.room_type == RoomType.CURSE:
            self.target_kills = ROOM_KILLS_REQUIRED + room_number * 3
        elif self.room_type == RoomType.ELITE:
            self.target_kills = 1
        elif self.room_type == RoomType.TREASURE:
            self.target_kills = 0
        else:
            self.target_kills = 999

        self.survival_time = SURVIVAL_ROOM_TIME + room_number * 4
        return self.room_type

    def update(self, dt):
        self.room_time += dt
        if self.banner_timer > 0:
            self.banner_timer = max(0, self.banner_timer - dt)

    def is_clear(self, kills):
        if self.room_type == RoomType.TREASURE:
            return True
        if self.room_type == RoomType.SURVIVAL:
            return self.room_time >= self.survival_time
        return kills >= self.target_kills

    def display_name(self):
        return self.room_type.name.title()

    def info(self):
        return ROOM_INFO[self.room_type]

    def spawn_multiplier(self):
        return self.info()["spawn_multiplier"]

    def enemy_difficulty_multiplier(self):
        return self.info()["enemy_difficulty"]
