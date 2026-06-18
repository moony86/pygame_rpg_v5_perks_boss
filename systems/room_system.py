import random
from enum import Enum, auto
from settings import ROOM_KILLS_REQUIRED, SURVIVAL_ROOM_TIME


class RoomType(Enum):
    COMBAT = auto()
    SURVIVAL = auto()
    ELITE = auto()
    TREASURE = auto()
    CURSE = auto()


class RoomSystem:
    def __init__(self):
        self.room_type = RoomType.COMBAT
        self.room_time = 0.0
        self.target_kills = ROOM_KILLS_REQUIRED
        self.survival_time = SURVIVAL_ROOM_TIME
        self.reward_multiplier = 1

    def choose_next_room(self, room_number):
        if room_number == 1:
            self.room_type = RoomType.COMBAT
        else:
            pool = [RoomType.COMBAT, RoomType.SURVIVAL, RoomType.ELITE, RoomType.TREASURE, RoomType.CURSE]
            weights = [38, 24, 16, 10, 12]
            self.room_type = random.choices(pool, weights=weights, k=1)[0]

        self.room_time = 0.0
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

    def is_clear(self, kills):
        if self.room_type == RoomType.TREASURE:
            return True
        if self.room_type == RoomType.SURVIVAL:
            return self.room_time >= self.survival_time
        return kills >= self.target_kills

    def display_name(self):
        return self.room_type.name.title()
