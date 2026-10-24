from dataclasses import dataclass, replace
import random

import pygame

from definitions.prototype_room_definitions import (
    COMBAT_LAYOUT_VARIANTS,
    DEFAULT_PROTOTYPE_LAYOUT,
    PROTOTYPE_DOORS,
    PROTOTYPE_OBSTACLES,
    PROTOTYPE_REWARD_GOLD,
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
from systems.xp_budget import stage_room_completion_xp
from systems.stage_document import playable_nodes
from systems.object_catalog import definition as object_definition

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


@dataclass(frozen=True)
class StageRoom:
    index: int
    room_type: RoomType
    label: str
    spawn_plan: tuple = ()
    active_cap: int = 10
    release_threshold: int = 4
    reward_xp: int = 0
    reward_gold: int = PROTOTYPE_REWARD_GOLD
    boss: bool = False
    layout: object = DEFAULT_PROTOTYPE_LAYOUT


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
        enemy_type = _stage_enemy_type(index, room_type, item.enemy_type, slot)
        if room_type == RoomType.ELITE and len(plan) in (8, 19, 30, 43, 55):
            enemy_type = EnemyType.ELITE
        delay = (slot // 4) * 5.2 + (slot % 4) * 0.45 + 0.2
        plan.append(PrototypeSpawn(delay, item.door_id, enemy_type))
    return tuple(plan)


def _stage_enemy_type(index, room_type, base_type, slot):
    if room_type == RoomType.TREASURE:
        return base_type
    if index <= 2:
        return base_type

    late_cycle = slot % 12
    if index >= 3 and base_type == EnemyType.CHASER and late_cycle in (2, 7):
        return EnemyType.CHASER_FAST
    if index >= 4 and base_type == EnemyType.RANGED and late_cycle in (1, 6):
        return EnemyType.RANGED_THREE
    if index >= 5 and base_type in (EnemyType.CHASER, EnemyType.CHASER_FAST) and late_cycle in (3, 9):
        return EnemyType.HUNTER
    if index >= 5 and base_type == EnemyType.JUMPER and late_cycle in (0, 8):
        return EnemyType.JUMPER_FAST
    if index >= 6 and base_type in (EnemyType.RANGED, EnemyType.RANGED_THREE) and late_cycle in (4, 10):
        return EnemyType.RANGED_FIVE
    if index >= 6 and base_type == EnemyType.CHASER_TANK and late_cycle in (5, 11):
        return EnemyType.BRUTE
    if index >= 7 and base_type == EnemyType.JUMPER and late_cycle in (2, 6):
        return EnemyType.JUMPER_HEAVY
    if index >= 7 and base_type in (EnemyType.RANGED, EnemyType.RANGED_THREE) and late_cycle == 0:
        return EnemyType.RANGED_RAIN
    return base_type


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
        layout = COMBAT_LAYOUT_VARIANTS[(index - 1) % len(COMBAT_LAYOUT_VARIANTS)]
        if room_type == RoomType.TREASURE:
            reward_xp = stage_room_completion_xp(index, room_type)
            rooms.append(StageRoom(index, room_type, "Treasure", active_cap=0, reward_xp=reward_xp, reward_gold=120, layout=layout))
        else:
            active_cap = min(15, 9 + index)
            release_threshold = min(active_cap - 2, max(3, active_cap // 2))
            reward_xp = stage_room_completion_xp(index, room_type)
            rooms.append(StageRoom(index, room_type, room_type.name.title(), _scaled_plan(index, room_type), active_cap, release_threshold, reward_xp=reward_xp, layout=layout))
    rooms.append(StageRoom(8, RoomType.ELITE, "Boss", active_cap=1, reward_xp=stage_room_completion_xp(8, RoomType.ELITE, boss=True), reward_gold=180, boss=True, layout=DEFAULT_PROTOTYPE_LAYOUT))
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
            room = replace(source, index=index, room_type=RoomType.ELITE, label="Boss", active_cap=1, reward_xp=stage_room_completion_xp(index, RoomType.ELITE, boss=True), reward_gold=180, boss=True)
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
        self.nodes = playable_nodes(build_stage_map)
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
        self.nodes = playable_nodes(build_stage_map)
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
        self.game.message = ""

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
        for door in self.current_doors():
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
        door = next(item for item in self.current_doors() if item.id == door_id)
        rect = pygame.Rect(0, 0, 94, 94)
        rect.center = (door.x, door.y)
        return rect

    def current_doors(self):
        room = self.current_room
        layout = getattr(room, "layout", DEFAULT_PROTOTYPE_LAYOUT) if room else DEFAULT_PROTOTYPE_LAYOUT
        return layout.doors

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

    def spawn_movement_pickups(self):
        self.game.movement_pickups = []
        room = self.current_room
        if room is None or room.boss:
            return
        player_center = pygame.Vector2(self.game.player.rect.center)
        bounds = pygame.Rect(0, 0, PROTOTYPE_ROOM_WIDTH, PROTOTYPE_ROOM_HEIGHT)
        obstacles = getattr(self.game, "room_obstacles", [])
        layout = getattr(room, "layout", DEFAULT_PROTOTYPE_LAYOUT)
        for point in getattr(layout, "movement_pickups", ()):
            rect = pygame.Rect(0, 0, 34, 34)
            rect.center = (point.x, point.y)
            if not bounds.contains(rect):
                continue
            if any(rect.inflate(22, 22).colliderect(other) for other in obstacles):
                continue
            if pygame.Vector2(rect.center).distance_to(player_center) < MOVEMENT_PICKUP_PLAYER_CLEARANCE:
                continue
            self._add_movement_pickup(rect, getattr(point, 'kind', 'dash_refresh'))
        if self.game.movement_pickups:
            return
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
            self._add_movement_pickup(chosen)

    def _add_movement_pickup(self, rect, kind='dash_refresh'):
        config = object_definition(kind)
        self.game.movement_pickups.append({
            "type": kind,
            "rect": rect.copy(),
            "spawn_rect": rect.copy(),
            "duration": config.get('duration', 1.8),
            "value": config.get('medium', config.get('duration', 1.8)),
            "alive": True,
            "respawn_timer": 0.0,
            "respawn_delay": config['respawn'],
        })
