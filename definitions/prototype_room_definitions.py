from dataclasses import dataclass

import pygame

from entities.enemy import EnemyType


@dataclass(frozen=True)
class PrototypeDoor:
    id: str
    x: int
    y: int
    facing: str


@dataclass(frozen=True)
class PrototypeSpawn:
    delay: float
    door_id: str
    enemy_type: EnemyType


@dataclass(frozen=True)
class PrototypeObstacle:
    id: str
    x: int
    y: int
    width: int
    height: int

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


@dataclass(frozen=True)
class PrototypePickupPoint:
    id: str
    x: int
    y: int
    kind: str = 'dash_refresh'


@dataclass(frozen=True)
class PrototypeRoomLayout:
    id: str
    doors: tuple
    obstacles: tuple
    movement_pickups: tuple = ()


PROTOTYPE_ROOM_WIDTH = 1920
PROTOTYPE_ROOM_HEIGHT = 1080
PROTOTYPE_ACTIVE_ENEMY_CAP = 10
PROTOTYPE_TELEGRAPH_TIME = 0.60
PROTOTYPE_REWARD_XP = 120
PROTOTYPE_REWARD_GOLD = 80


PROTOTYPE_DOORS = (
    PrototypeDoor("north", 960, 78, "south"),
    PrototypeDoor("east", 1842, 540, "west"),
    PrototypeDoor("south", 960, 1002, "north"),
    PrototypeDoor("west", 78, 540, "east"),
)


PROTOTYPE_OBSTACLES = (
    PrototypeObstacle("west_cover", 470, 330, 140, 300),
    PrototypeObstacle("center_cover", 820, 585, 280, 110),
    PrototypeObstacle("east_cover", 1310, 450, 140, 300),
)


DEFAULT_MOVEMENT_PICKUPS = (
    PrototypePickupPoint("west_pickup", 650, 540),
    PrototypePickupPoint("east_pickup", 1270, 540),
)


DEFAULT_PROTOTYPE_LAYOUT = PrototypeRoomLayout(
    "default_cross_cover",
    PROTOTYPE_DOORS,
    PROTOTYPE_OBSTACLES,
    DEFAULT_MOVEMENT_PICKUPS,
)


COMBAT_LAYOUT_VARIANTS = (
    DEFAULT_PROTOTYPE_LAYOUT,
    PrototypeRoomLayout(
        "split_lanes",
        (
            PrototypeDoor("north", 820, 78, "south"),
            PrototypeDoor("east", 1842, 430, "west"),
            PrototypeDoor("south", 1100, 1002, "north"),
            PrototypeDoor("west", 78, 650, "east"),
        ),
        (
            PrototypeObstacle("north_left_cover", 540, 250, 240, 110),
            PrototypeObstacle("south_right_cover", 1140, 720, 240, 110),
            PrototypeObstacle("center_pillar", 895, 450, 130, 190),
        ),
        (
            PrototypePickupPoint("north_lane_pickup", 910, 300),
            PrototypePickupPoint("south_lane_pickup", 1010, 780),
        ),
    ),
    PrototypeRoomLayout(
        "offset_columns",
        (
            PrototypeDoor("north", 1060, 78, "south"),
            PrototypeDoor("east", 1842, 620, "west"),
            PrototypeDoor("south", 860, 1002, "north"),
            PrototypeDoor("west", 78, 460, "east"),
        ),
        (
            PrototypeObstacle("west_column", 430, 435, 120, 260),
            PrototypeObstacle("mid_column", 900, 255, 120, 260),
            PrototypeObstacle("east_column", 1370, 565, 120, 260),
        ),
        (
            PrototypePickupPoint("upper_mid_pickup", 1060, 430),
            PrototypePickupPoint("lower_mid_pickup", 760, 660),
        ),
    ),
)


PROTOTYPE_SPAWN_PLAN = (
    PrototypeSpawn(0.20, "north", EnemyType.CHASER),
    PrototypeSpawn(0.65, "west", EnemyType.CHASER),
    PrototypeSpawn(1.10, "east", EnemyType.RANGED),
    PrototypeSpawn(1.55, "south", EnemyType.CHASER),
    PrototypeSpawn(6.00, "north", EnemyType.JUMPER),
    PrototypeSpawn(6.45, "west", EnemyType.CHASER_FAST),
    PrototypeSpawn(6.90, "east", EnemyType.RANGED),
    PrototypeSpawn(7.35, "south", EnemyType.CHASER),
    PrototypeSpawn(12.00, "north", EnemyType.RANGED_THREE),
    PrototypeSpawn(12.45, "east", EnemyType.JUMPER),
    PrototypeSpawn(12.90, "west", EnemyType.CHASER_TANK),
    PrototypeSpawn(13.35, "south", EnemyType.HUNTER),
    PrototypeSpawn(19.00, "west", EnemyType.CHASER),
    PrototypeSpawn(19.45, "north", EnemyType.CHASER_FAST),
    PrototypeSpawn(19.90, "south", EnemyType.RANGED),
    PrototypeSpawn(20.35, "east", EnemyType.CHASER),
    PrototypeSpawn(26.00, "north", EnemyType.JUMPER),
    PrototypeSpawn(26.45, "east", EnemyType.RANGED_THREE),
    PrototypeSpawn(26.90, "south", EnemyType.CHASER),
    PrototypeSpawn(27.35, "west", EnemyType.CHASER_TANK),
    PrototypeSpawn(34.00, "south", EnemyType.HUNTER),
    PrototypeSpawn(34.45, "west", EnemyType.CHASER_FAST),
    PrototypeSpawn(34.90, "east", EnemyType.RANGED),
    PrototypeSpawn(35.35, "north", EnemyType.CHASER),
    PrototypeSpawn(42.00, "east", EnemyType.JUMPER),
    PrototypeSpawn(42.45, "south", EnemyType.RANGED_THREE),
    PrototypeSpawn(42.90, "north", EnemyType.CHASER),
    PrototypeSpawn(43.35, "west", EnemyType.CHASER),
    PrototypeSpawn(51.00, "north", EnemyType.CHASER_TANK),
    PrototypeSpawn(51.45, "east", EnemyType.CHASER_FAST),
    PrototypeSpawn(51.90, "west", EnemyType.RANGED),
    PrototypeSpawn(52.35, "south", EnemyType.CHASER),
    PrototypeSpawn(61.00, "west", EnemyType.HUNTER),
    PrototypeSpawn(61.45, "south", EnemyType.JUMPER),
    PrototypeSpawn(61.90, "east", EnemyType.RANGED_THREE),
    PrototypeSpawn(62.35, "north", EnemyType.CHASER_FAST),
    PrototypeSpawn(72.00, "north", EnemyType.CHASER_TANK),
    PrototypeSpawn(72.45, "south", EnemyType.HUNTER),
    PrototypeSpawn(72.90, "west", EnemyType.RANGED),
    PrototypeSpawn(73.35, "east", EnemyType.JUMPER),
)


def prototype_door_map(layout=None):
    source = layout.doors if layout else PROTOTYPE_DOORS
    return {door.id: door for door in source}
