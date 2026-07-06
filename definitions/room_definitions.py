from dataclasses import dataclass

from definitions.common import Definition


@dataclass(frozen=True)
class RoomDefinition(Definition):
    title: str
    message: str
    color: tuple[int, int, int]
    spawn_multiplier: float
    enemy_difficulty: float

    def as_info(self):
        return {
            "title": self.title,
            "message": self.message,
            "color": self.color,
            "spawn_multiplier": self.spawn_multiplier,
            "enemy_difficulty": self.enemy_difficulty,
        }


ROOM_DEFINITIONS = {
    "combat": RoomDefinition(
        id="combat",
        display_name="Combat",
        title="COMBAT ROOM",
        message="Clear the waves.",
        color=(220, 55, 55),
        spawn_multiplier=1.0,
        enemy_difficulty=1.0,
    ),
    "survival": RoomDefinition(
        id="survival",
        display_name="Survival",
        title="SURVIVAL ROOM",
        message="Survive the horde.",
        color=(245, 150, 45),
        spawn_multiplier=1.8,
        enemy_difficulty=1.10,
    ),
    "elite": RoomDefinition(
        id="elite",
        display_name="Elite",
        title="ELITE ROOM",
        message="Defeat the elite guard.",
        color=(255, 90, 170),
        spawn_multiplier=0.0,
        enemy_difficulty=1.25,
    ),
    "treasure": RoomDefinition(
        id="treasure",
        display_name="Treasure",
        title="TREASURE ROOM",
        message="Claim your reward.",
        color=(235, 180, 40),
        spawn_multiplier=0.0,
        enemy_difficulty=0.0,
    ),
    "curse": RoomDefinition(
        id="curse",
        display_name="Curse",
        title="CURSE ROOM",
        message="High risk, double reward.",
        color=(150, 70, 220),
        spawn_multiplier=1.65,
        enemy_difficulty=1.20,
    ),
}


def get_room_definition(room_id):
    return ROOM_DEFINITIONS[room_id]


def get_room_info(room_id):
    return get_room_definition(room_id).as_info()
