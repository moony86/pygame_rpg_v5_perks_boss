from collections import Counter, defaultdict
from time import perf_counter
import math

import pygame

from entities.enemy import EnemyType
from systems.room_bounds import current_room_bounds, current_room_rect


HORDE_GRID_CELL_SIZE = 96
HORDE_FLOW_CELL_SIZE = 160
HORDE_REAL_CAP = 320
LOD0_DISTANCE = 420
LOD1_DISTANCE = 900
LOD1_INTERVAL = 3
LOD2_INTERVAL = 8
HORDE_SPAWN_MARGIN = 760


class SpatialHashGrid:
    def __init__(self, cell_size=HORDE_GRID_CELL_SIZE):
        self.cell_size = cell_size
        self.cells = defaultdict(list)
        self.object_cells = {}
        self.query_checks = 0

    def rebuild(self, objects):
        self.clear()
        for obj in objects:
            if getattr(obj, "alive", True):
                self.insert(obj)

    def clear(self):
        self.cells.clear()
        self.object_cells.clear()
        self.query_checks = 0

    def insert(self, obj):
        rect = getattr(obj, "rect", None)
        if rect is None:
            return
        cells = tuple(self._cells_for_rect(rect))
        self.object_cells[id(obj)] = cells
        for cell in cells:
            self.cells[cell].append(obj)

    def nearby_rect(self, rect, padding=0):
        expanded = rect.inflate(padding * 2, padding * 2)
        seen = set()
        result = []
        for cell in self._cells_for_rect(expanded):
            for obj in self.cells.get(cell, ()):
                obj_id = id(obj)
                if obj_id in seen:
                    continue
                seen.add(obj_id)
                result.append(obj)
        self.query_checks += len(result)
        return result

    def nearby_point(self, pos, radius):
        rect = pygame.Rect(round(pos[0] - radius), round(pos[1] - radius), radius * 2, radius * 2)
        radius_sq = radius * radius
        return [
            obj for obj in self.nearby_rect(rect)
            if pygame.Vector2(obj.rect.center).distance_squared_to(pos) <= radius_sq
        ]

    def _cells_for_rect(self, rect):
        min_x = max(0, rect.left // self.cell_size)
        max_x = max(0, rect.right // self.cell_size)
        min_y = max(0, rect.top // self.cell_size)
        max_y = max(0, rect.bottom // self.cell_size)
        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                yield (cx, cy)


class InfluenceMap:
    def __init__(self, cell_size=HORDE_FLOW_CELL_SIZE, map_size=None):
        self.cell_size = cell_size
        self.map_size = map_size if map_size is not None else current_room_bounds().width
        self.columns = math.ceil(self.map_size / cell_size)
        self.rows = math.ceil(self.map_size / cell_size)
        self.values = {}
        self.target_cell = (0, 0)
        self.danger_cells = set()

    def rebuild(self, player_rect, danger_points=()):
        self.values.clear()
        self.danger_cells.clear()
        self.target_cell = self.world_to_cell(player_rect.center)
        self.values[self.target_cell] = 3
        for pos, radius in danger_points:
            center = self.world_to_cell(pos)
            reach = max(1, math.ceil(radius / self.cell_size))
            for cy in range(center[1] - reach, center[1] + reach + 1):
                for cx in range(center[0] - reach, center[0] + reach + 1):
                    if 0 <= cx < self.columns and 0 <= cy < self.rows:
                        self.values[(cx, cy)] = max(self.values.get((cx, cy), 0), 1)
                        self.danger_cells.add((cx, cy))

    def world_to_cell(self, pos):
        return (
            max(0, min(self.columns - 1, int(pos[0] // self.cell_size))),
            max(0, min(self.rows - 1, int(pos[1] // self.cell_size))),
        )

    def cell_value(self, cell):
        return self.values.get(cell, 0)

    def direction_at(self, pos, fallback_target):
        cell = self.world_to_cell(pos)
        current = self.cell_value(cell)
        best_cell = cell
        best_score = -999999.0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                candidate = (cell[0] + dx, cell[1] + dy)
                if not (0 <= candidate[0] < self.columns and 0 <= candidate[1] < self.rows):
                    continue
                center = self.cell_center(candidate)
                distance = pygame.Vector2(center).distance_to(fallback_target)
                value = self.cell_value(candidate)
                score = -distance + value * 220.0
                if current == 1 and candidate not in self.danger_cells:
                    score += 160.0
                if value == 1:
                    score -= 120.0
                if score > best_score:
                    best_score = score
                    best_cell = candidate
        target = pygame.Vector2(self.cell_center(best_cell))
        direction = target - pygame.Vector2(pos)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(fallback_target) - pygame.Vector2(pos)
        return direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(0, 0)

    def cell_center(self, cell):
        return (
            cell[0] * self.cell_size + self.cell_size * 0.5,
            cell[1] * self.cell_size + self.cell_size * 0.5,
        )


class HordeSystem:
    def __init__(self, real_cap=HORDE_REAL_CAP):
        self.enabled = False
        self.real_cap = real_cap
        self.pending = Counter()
        self.spatial_grid = SpatialHashGrid()
        self.flow = InfluenceMap()
        self.frame_index = 0
        self.last_lod_counts = {"LOD0": 0, "LOD1": 0, "LOD2": 0}
        self.last_metrics = {
            "real": 0,
            "virtual": 0,
            "lod0": 0,
            "lod1": 0,
            "lod2": 0,
            "projectile_checks": 0,
            "enemy_update_ms": 0.0,
            "combat_collision_ms": 0.0,
            "draw_ms": 0.0,
        }

    def spawn_test(self, game, count, enemy_type=EnemyType.CHASER):
        self.clear(game)
        self.enabled = True
        self.pending[enemy_type] = max(0, int(count))
        self.activate_pending(game)
        self.update_debug_metrics(game)

    def clear(self, game):
        horde_enemies = [enemy for enemy in getattr(game, "enemies", []) if getattr(enemy, "horde_test_enemy", False)]
        for enemy in horde_enemies:
            enemy.alive = False
        if horde_enemies and hasattr(game, "enemy_pool"):
            game.enemy_pool.release_many(horde_enemies)
        game.enemies = [enemy for enemy in getattr(game, "enemies", []) if not getattr(enemy, "horde_test_enemy", False)]
        self.pending.clear()
        self.spatial_grid.clear()
        self.enabled = False
        self.last_lod_counts = {"LOD0": 0, "LOD1": 0, "LOD2": 0}
        self.update_debug_metrics(game)

    def activate_pending(self, game):
        if not self.enabled:
            return []
        real_count = sum(1 for enemy in game.enemies if getattr(enemy, "horde_test_enemy", False) and enemy.alive)
        capacity = max(0, self.real_cap - real_count)
        if capacity <= 0 or not self.pending:
            return []
        spawned = []
        for enemy_type in list(self.pending):
            while self.pending[enemy_type] > 0 and capacity > 0:
                x, y = self._offscreen_spawn(game)
                enemy = game.enemy_pool.acquire(x, y, enemy_type, 1.0)
                enemy.horde_test_enemy = True
                enemy.horde_lod = 2
                enemy.horde_update_bucket = (len(spawned) + real_count) % LOD2_INTERVAL
                spawned.append(enemy)
                self.pending[enemy_type] -= 1
                capacity -= 1
            if self.pending[enemy_type] <= 0:
                del self.pending[enemy_type]
            if capacity <= 0:
                break
        game.enemies.extend(spawned)
        return spawned

    def update_influence(self, game):
        danger = []
        player = getattr(game, "player", None)
        if player is not None:
            for pos in getattr(player, "engineer_blade_positions", [])[:8]:
                danger.append((pos, 52))
            air_pos = getattr(player, "engineer_airstrike_target_pos", None)
            if getattr(player, "engineer_airstrike_state", "") == "telegraph" and air_pos is not None:
                danger.append((air_pos, getattr(player, "engineer_airstrike_radius", 150)))
        self.flow.rebuild(game.player.rect, danger)

    def update_enemies(self, game, dt, handle_action):
        start = perf_counter()
        self.frame_index += 1
        self.activate_pending(game)
        self.update_influence(game)
        counts = {"LOD0": 0, "LOD1": 0, "LOD2": 0}
        player_center = pygame.Vector2(game.player.rect.center)
        for enemy in game.enemies:
            if not getattr(enemy, "alive", True):
                continue
            if getattr(enemy, "type", None) == EnemyType.BOSS or not getattr(enemy, "horde_test_enemy", False):
                setattr(enemy, "horde_lod", 0)
                action = enemy.update(dt, game.player.rect, game.collision.get_colliders())
                if action:
                    handle_action(action, game)
                continue
            distance_sq = pygame.Vector2(enemy.rect.center).distance_squared_to(player_center)
            if distance_sq <= LOD0_DISTANCE * LOD0_DISTANCE:
                lod = 0
                interval = 1
            elif distance_sq <= LOD1_DISTANCE * LOD1_DISTANCE:
                lod = 1
                interval = LOD1_INTERVAL
            else:
                lod = 2
                interval = LOD2_INTERVAL
            setattr(enemy, "horde_lod", lod)
            counts[f"LOD{lod}"] += 1
            bucket = getattr(enemy, "horde_update_bucket", id(enemy) % interval)
            if lod > 0 and (self.frame_index + bucket) % interval != 0:
                self._tick_timers(enemy, dt)
                continue
            scaled_dt = dt * interval if lod > 0 else dt
            if lod == 0:
                action = enemy.update(scaled_dt, game.player.rect, game.collision.get_colliders())
                if action:
                    handle_action(action, game)
            else:
                self._simple_flow_move(enemy, game.player.rect, scaled_dt, lod)
        self.last_lod_counts = counts
        self.last_metrics["enemy_update_ms"] = (perf_counter() - start) * 1000.0
        self.update_debug_metrics(game)

    def rebuild_spatial_grid(self, enemies):
        self.spatial_grid.rebuild(enemies)
        return self.spatial_grid

    def update_debug_metrics(self, game):
        self.last_metrics.update({
            "real": sum(1 for enemy in getattr(game, "enemies", []) if getattr(enemy, "horde_test_enemy", False) and getattr(enemy, "alive", True)),
            "virtual": sum(self.pending.values()),
            "lod0": self.last_lod_counts.get("LOD0", 0),
            "lod1": self.last_lod_counts.get("LOD1", 0),
            "lod2": self.last_lod_counts.get("LOD2", 0),
            "projectile_checks": self.spatial_grid.query_checks,
        })

    def set_combat_ms(self, milliseconds):
        self.last_metrics["combat_collision_ms"] = milliseconds

    def set_draw_ms(self, milliseconds):
        self.last_metrics["draw_ms"] = milliseconds

    def _simple_flow_move(self, enemy, player_rect, dt, lod):
        self._tick_timers(enemy, dt)
        direction = self.flow.direction_at(enemy.rect.center, player_rect.center)
        speed_scale = 0.82 if lod == 1 else 0.68
        speed = getattr(enemy, "speed", 160)
        enemy.rect.x += round(direction.x * speed * speed_scale * dt)
        enemy.rect.y += round(direction.y * speed * speed_scale * dt)
        enemy.rect.clamp_ip(current_room_rect())
        enemy._anim = getattr(enemy, "_anim", 0.0) + dt

    def _tick_timers(self, enemy, dt):
        for attr in ("hit_flash", "knockback_timer", "attack_cooldown", "anti_kite_timer", "chaser_burst_timer", "chaser_burst_cooldown"):
            value = getattr(enemy, attr, 0.0)
            if value > 0:
                setattr(enemy, attr, max(0.0, value - dt))

    def _offscreen_spawn(self, game):
        bounds = current_room_bounds()
        player = pygame.Vector2(game.player.rect.center)
        angle = (len(game.enemies) * 137.5 + sum(self.pending.values()) * 19.0) % 360
        radius = HORDE_SPAWN_MARGIN + (len(game.enemies) % 7) * 34
        pos = player + pygame.Vector2(radius, 0).rotate(angle)
        if bounds.left + 80 <= pos.x <= bounds.right - 80 and bounds.top + 80 <= pos.y <= bounds.bottom - 80:
            return round(pos.x), round(pos.y)
        pos.x = max(bounds.left + 80, min(bounds.right - 80, pos.x))
        pos.y = max(bounds.top + 80, min(bounds.bottom - 80, pos.y))
        return round(pos.x), round(pos.y)
