from dataclasses import dataclass, replace
import random

import pygame

from definitions.prototype_room_definitions import (
    PROTOTYPE_DOORS,
    PROTOTYPE_OBSTACLES,
    PROTOTYPE_REWARD_GOLD,
    PROTOTYPE_REWARD_XP,
    PROTOTYPE_ROOM_HEIGHT,
    PROTOTYPE_ROOM_WIDTH,
    PROTOTYPE_SPAWN_PLAN,
    PrototypeSpawn,
)
from entities.enemy import EnemyType
from game_state import GameState
from settings import PERK_PICK_LIMIT
from systems.room_bounds import reset_room_bounds
from systems.room_system import RoomType

OPPOSITE_DOOR = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}

DOOR_STEP = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}

MOVEMENT_PICKUP_RESPAWN = 12.0
MOVEMENT_PICKUP_PLAYER_CLEARANCE = 260
STAGE_PRECOMBAT_GRACE = 1.8
STAGE_ROOM_REWARD_XP = {
    1: 220,
    2: 170,
    4: 160,
    5: 150,
    6: 150,
    7: 170,
}


@dataclass(frozen=True)
class StageRoom:
    index: int
    room_type: RoomType
    label: str
    spawn_plan: tuple = ()
    active_cap: int = 10
    release_threshold: int = 4
    reward_xp: int = PROTOTYPE_REWARD_XP
    reward_gold: int = PROTOTYPE_REWARD_GOLD
    boss: bool = False


@dataclass
class StageMapNode:
    room: StageRoom
    grid_pos: tuple[int, int]
    neighbors: dict
    discovered: bool = False
    entered: bool = False
    cleared: bool = False


def _scaled_plan(index, room_type):
    target_count = 34 + index * 5
    if room_type == RoomType.ELITE:
        target_count += 10
    plan = []
    source = list(PROTOTYPE_SPAWN_PLAN)
    while len(plan) < target_count:
        slot = len(plan)
        item = source[slot % len(source)]
        enemy_type = item.enemy_type
        if room_type == RoomType.ELITE and len(plan) in (8, 19, 30, 43, 55):
            enemy_type = EnemyType.ELITE
        delay = (slot // 4) * 5.2 + (slot % 4) * 0.45 + 0.2
        plan.append(PrototypeSpawn(delay, item.door_id, enemy_type))
    return tuple(plan)


def _base_stage_rooms():
    types = (
        RoomType.COMBAT,
        RoomType.COMBAT,
        RoomType.TREASURE,
        RoomType.ELITE,
        RoomType.COMBAT,
        RoomType.COMBAT,
        RoomType.ELITE,
    )
    rooms = []
    for index, room_type in enumerate(types, start=1):
        if room_type == RoomType.TREASURE:
            rooms.append(StageRoom(index, room_type, "Treasure", active_cap=0, reward_xp=60, reward_gold=120))
        else:
            active_cap = min(15, 9 + index)
            release_threshold = min(active_cap - 2, max(3, active_cap // 2))
            reward_xp = STAGE_ROOM_REWARD_XP.get(index, PROTOTYPE_REWARD_XP)
            rooms.append(StageRoom(index, room_type, room_type.name.title(), _scaled_plan(index, room_type), active_cap, release_threshold, reward_xp=reward_xp))
    rooms.append(StageRoom(8, RoomType.ELITE, "Boss", active_cap=1, reward_xp=320, reward_gold=180, boss=True))
    return tuple(rooms)


def build_stage_one():
    return tuple(node.room for node in build_stage_map())


def build_stage_map(seed=None, room_count=8):
    rng = random.Random(seed)
    positions = [(0, 0)]
    occupied = {(0, 0)}
    edges = []
    while len(positions) < room_count:
        base = rng.choice(positions)
        directions = list(DOOR_STEP.items())
        rng.shuffle(directions)
        for door_id, step in directions:
            candidate = (base[0] + step[0], base[1] + step[1])
            if candidate in occupied:
                continue
            occupied.add(candidate)
            positions.append(candidate)
            edges.append((base, candidate, door_id))
            break

    distances = _stage_distances((0, 0), edges)
    boss_pos = max(positions, key=lambda pos: (distances.get(pos, 0), abs(pos[0]) + abs(pos[1]), pos))
    ordered_positions = sorted(
        positions,
        key=lambda pos: (distances.get(pos, 0), 1 if pos == boss_pos else 0, pos[1], pos[0]),
    )
    ordered_positions = [pos for pos in ordered_positions if pos != boss_pos] + [boss_pos]

    base_rooms = list(_base_stage_rooms())
    nodes = {}
    for index, pos in enumerate(ordered_positions, start=1):
        source = base_rooms[min(index - 1, len(base_rooms) - 1)]
        if pos == boss_pos:
            room = replace(source, index=index, room_type=RoomType.ELITE, label="Boss", active_cap=1, reward_xp=320, reward_gold=180, boss=True)
        elif source.boss:
            room = replace(source, index=index, boss=False, label=source.room_type.name.title())
        else:
            room = replace(source, index=index)
        nodes[pos] = StageMapNode(room=room, grid_pos=pos, neighbors={})

    for a, b, door_id in edges:
        nodes[a].neighbors[door_id] = b
        nodes[b].neighbors[OPPOSITE_DOOR[door_id]] = a

    nodes[(0, 0)].discovered = True
    return tuple(nodes[pos] for pos in ordered_positions)


def _stage_distances(start, edges):
    graph = {}
    for a, b, _door_id in edges:
        graph.setdefault(a, []).append(b)
        graph.setdefault(b, []).append(a)
    distances = {start: 0}
    queue = [start]
    while queue:
        current = queue.pop(0)
        for neighbor in graph.get(current, ()):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


class StageSystem:
    def __init__(self, game):
        self.game = game
        self.stage_number = 1
        self.nodes = build_stage_map()
        self.rooms = tuple(node.room for node in self.nodes)
        self.node_by_pos = {node.grid_pos: node for node in self.nodes}
        self.active = False
        self.completed = False
        self.room_index = 0
        self.current_pos = (0, 0)
        self.entry_door = None

    @property
    def current_room(self):
        node = self.current_node
        return node.room if node else None

    @property
    def current_node(self):
        if not self.active:
            return None
        return self.node_by_pos.get(self.current_pos)

    def start_stage(self):
        self.nodes = build_stage_map()
        self.rooms = tuple(node.room for node in self.nodes)
        self.node_by_pos = {node.grid_pos: node for node in self.nodes}
        self.active = True
        self.completed = False
        self.room_index = 0
        self.current_pos = (0, 0)
        self.entry_door = None
        self.game.room_number = self.current_room.index
        self.game.show_wave_notice("BUILDING STAGE MAP")
        self._enter_current_room()

    def _enter_current_room(self):
        node = self.current_node
        if node is None:
            self.complete_stage()
            return
        room = node.room
        node.discovered = True
        node.entered = True
        self.game.room_number = room.index
        self.room_index = room.index - 1
        self.game.prototype_room.enter(stage_room=room, entry_door=self.entry_door, already_cleared=node.cleared)
        self.game.message = f"Stage {self.stage_number} - Room {room.index}/{len(self.rooms)}: {room.label}"

    def advance_after_exit(self):
        if not self.active:
            return False
        return self.try_complete_or_use_center_exit()

    def try_complete_or_use_center_exit(self):
        node = self.current_node
        if node and node.room.boss and node.cleared:
            self.complete_stage()
            return True
        return False

    def try_use_door(self, player_rect):
        node = self.current_node
        if node is None or not node.cleared:
            return False
        for door in PROTOTYPE_DOORS:
            target_pos = node.neighbors.get(door.id)
            if target_pos is None:
                continue
            door_rect = self.door_rect(door.id)
            if player_rect.colliderect(door_rect):
                self.current_pos = target_pos
                self.entry_door = OPPOSITE_DOOR[door.id]
                target = self.node_by_pos[target_pos]
                target.discovered = True
                self._enter_current_room()
                return True
        return False

    def mark_current_room_cleared(self):
        node = self.current_node
        if node is None:
            return
        node.cleared = True
        for target_pos in node.neighbors.values():
            self.node_by_pos[target_pos].discovered = True

    def door_rect(self, door_id):
        door = next(item for item in PROTOTYPE_DOORS if item.id == door_id)
        rect = pygame.Rect(0, 0, 94, 94)
        rect.center = (door.x, door.y)
        return rect

    def open_doors(self):
        node = self.current_node
        if node is None:
            return []
        return [(door_id, target_pos, self.door_rect(door_id)) for door_id, target_pos in node.neighbors.items()]

    def complete_stage(self):
        self.active = False
        self.completed = True
        self._reset_player_progress_preserve_gold()
        reset_room_bounds()
        from systems.scene_system import enter_hub
        enter_hub(self.game)
        self.game.message = f"Stage {self.stage_number} complete. Gold preserved; build reset."
        self.game.show_wave_notice("STAGE CLEAR")

    def _reset_player_progress_preserve_gold(self):
        player = self.game.player
        gold = player.gold
        active_skill = getattr(player, "active_skill", "dash")
        player.reset()
        player.gold = gold
        player.active_skill = active_skill
        player.pending_level_ups = 0
        player.perk_counts.clear()
        player.perk_choices_made = 0
        self.game.upgrades.reset()
        self.game.room_completion_xp_awarded.clear()

    def legacy_route_available(self):
        return True

    def spawn_movement_pickups(self):
        self.game.movement_pickups = []
        room = self.current_room
        if room is None or room.boss:
            return
        player_center = pygame.Vector2(self.game.player.rect.center)
        bounds = pygame.Rect(0, 0, PROTOTYPE_ROOM_WIDTH, PROTOTYPE_ROOM_HEIGHT)
        obstacles = getattr(self.game, "room_obstacles", [])
        for obstacle in obstacles[:2]:
            rect = pygame.Rect(0, 0, 34, 34)
            candidates = (
                (obstacle.centerx, obstacle.top - 70),
                (obstacle.centerx, obstacle.bottom + 70),
                (obstacle.left - 70, obstacle.centery),
                (obstacle.right + 70, obstacle.centery),
            )
            chosen = None
            for center in candidates:
                rect.center = center
                if not bounds.contains(rect):
                    continue
                if any(rect.inflate(22, 22).colliderect(other) for other in obstacles):
                    continue
                if pygame.Vector2(rect.center).distance_to(player_center) < MOVEMENT_PICKUP_PLAYER_CLEARANCE:
                    continue
                chosen = rect.copy()
                break
            if chosen is None:
                continue
            self.game.movement_pickups.append({
                "type": "dash_refresh",
                "rect": chosen,
                "spawn_rect": chosen.copy(),
                "duration": 1.8,
                "alive": True,
                "respawn_timer": 0.0,
                "respawn_delay": MOVEMENT_PICKUP_RESPAWN,
            })
