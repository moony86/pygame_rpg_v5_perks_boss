import pygame

from definitions.prototype_room_definitions import (
    PROTOTYPE_ACTIVE_ENEMY_CAP,
    PROTOTYPE_DOORS,
    PROTOTYPE_OBSTACLES,
    PROTOTYPE_REWARD_GOLD,
    PROTOTYPE_REWARD_XP,
    PROTOTYPE_ROOM_HEIGHT,
    PROTOTYPE_ROOM_WIDTH,
    PROTOTYPE_SPAWN_PLAN,
    PROTOTYPE_TELEGRAPH_TIME,
    prototype_door_map,
)
from entities.enemy import EnemyType
from game_state import GameState
from systems.room_bounds import RoomBounds, reset_room_bounds, set_room_bounds
from systems.room_system import RoomType

STAGE_PRECOMBAT_GRACE = 1.8
SPAWN_ACCELERATION_LOOKAHEAD = 3.0


class PrototypeCombatRoom:
    def __init__(self, game):
        self.game = game
        self.bounds = RoomBounds(0, 0, PROTOTYPE_ROOM_WIDTH, PROTOTYPE_ROOM_HEIGHT)
        self.active = False
        self.elapsed = 0.0
        self.spawn_index = 0
        self.pending = []
        self.cleared = False
        self.total_spawns = len(PROTOTYPE_SPAWN_PLAN)
        self.doors = prototype_door_map()
        self.stage_room = None
        self.spawn_plan = PROTOTYPE_SPAWN_PLAN
        self.active_cap = PROTOTYPE_ACTIVE_ENEMY_CAP
        self.release_threshold = 4
        self.reward_xp = PROTOTYPE_REWARD_XP
        self.reward_gold = PROTOTYPE_REWARD_GOLD

    def enter(self, stage_room=None, entry_door=None, already_cleared=False):
        set_room_bounds(self.bounds)
        game = self.game
        self.stage_room = stage_room
        self.spawn_plan = getattr(stage_room, "spawn_plan", PROTOTYPE_SPAWN_PLAN) if stage_room else PROTOTYPE_SPAWN_PLAN
        self.active_cap = getattr(stage_room, "active_cap", PROTOTYPE_ACTIVE_ENEMY_CAP) if stage_room else PROTOTYPE_ACTIVE_ENEMY_CAP
        self.release_threshold = getattr(stage_room, "release_threshold", 4) if stage_room else 4
        self.reward_xp = getattr(stage_room, "reward_xp", PROTOTYPE_REWARD_XP) if stage_room else PROTOTYPE_REWARD_XP
        self.reward_gold = getattr(stage_room, "reward_gold", PROTOTYPE_REWARD_GOLD) if stage_room else PROTOTYPE_REWARD_GOLD
        self.total_spawns = len(self.spawn_plan)
        game.state = GameState.ROOM
        game.rooms.room_type = getattr(stage_room, "room_type", RoomType.COMBAT) if stage_room else RoomType.COMBAT
        game.rooms.room_time = 0.0
        game.rooms.banner_timer = 1.2
        game.rooms.reward_multiplier = 1
        game.rooms.target_kills = self.total_spawns if self.total_spawns else 1
        game.room_kills = 0
        game.room_exit_open = False
        game.collision.clear()
        game.room_obstacles = [obstacle.rect() for obstacle in PROTOTYPE_OBSTACLES]
        for obstacle in game.room_obstacles:
            game.collision.add_rect(obstacle)
        game.horde.clear(game)
        game.enemy_pool.release_many(game.enemies)
        game.enemies.clear()
        game.projectiles.clear()
        game.enemy_bullets.clear()
        game.loot.reset()
        game.effects.reset()
        game.room_flow.clear_scene()
        game.player.cancel_tea()
        game.player.rect.center = self.bounds.center
        game.player.reset_engineer_scene_state()
        game.player.reset_vampire_scene_state()
        game.camera.reset(game.player.rect)
        game.dialogue.close()
        self.active = True
        self.elapsed = -STAGE_PRECOMBAT_GRACE if stage_room and self.total_spawns else 0.0
        self.spawn_index = 0
        self.pending = []
        self.cleared = False
        if already_cleared:
            self.spawn_index = len(self.spawn_plan)
            self.pending = []
            self.cleared = True
            game.room_exit_open = bool(stage_room and getattr(stage_room, "boss", False))
        if hasattr(game, "stage"):
            game.stage.spawn_movement_pickups()
        if stage_room and getattr(stage_room, "boss", False) and not already_cleared:
            self._spawn_stage_boss()
        elif stage_room and game.rooms.room_type == RoomType.TREASURE and not already_cleared:
            self._spawn_treasure_room()
        self._place_player_for_entry(entry_door)
        game.message = "Prototype small combat room: door spawns active." if stage_room is None else f"Stage room: {stage_room.label}"
        game.show_wave_notice("PROTOTYPE ROOM" if stage_room is None else "GET READY")
        game.events.emit("state_room")

    def exit_to_hub(self):
        self.active = False
        self.pending.clear()
        reset_room_bounds()
        from systems.scene_system import enter_hub
        enter_hub(self.game)

    def update(self, dt):
        if not self.active or self.cleared:
            return
        game = self.game
        self.elapsed += dt
        game.rooms.update(dt)

        active_count = sum(1 for enemy in game.enemies if enemy.alive)
        accelerated = self.stage_room is not None and active_count <= self.release_threshold

        while self.spawn_index < len(self.spawn_plan):
            item = self.spawn_plan[self.spawn_index]
            if item.delay > self.elapsed and not (accelerated and item.delay <= self.elapsed + SPAWN_ACCELERATION_LOOKAHEAD):
                break
            self.pending.append({
                "door_id": item.door_id,
                "enemy_type": item.enemy_type,
                "timer": PROTOTYPE_TELEGRAPH_TIME,
            })
            self.spawn_index += 1

        kept = []
        for entry in self.pending:
            entry["timer"] = max(0.0, entry["timer"] - dt)
            if entry["timer"] > 0 or active_count >= self.active_cap:
                kept.append(entry)
                continue
            door = self.doors[entry["door_id"]]
            enemy = game.enemy_pool.acquire(door.x, door.y, entry["enemy_type"], difficulty=1.0)
            enemy.prototype_room_enemy = True
            game.enemies.append(enemy)
            active_count += 1
            game.effects.ring(enemy.rect.center, color=(255, 190, 70), radius=42, life=0.20, width=4)
        self.pending = kept

    def ready_to_clear(self):
        return (
            self.active
            and not self.cleared
            and self.spawn_index >= len(self.spawn_plan)
            and not self.pending
            and not any(enemy.alive for enemy in self.game.enemies)
        )

    def open_exit(self):
        if self.cleared:
            return
        game = self.game
        self.cleared = True
        stage = getattr(game, "stage", None)
        if stage and stage.active:
            stage.mark_current_room_cleared()
            if self.stage_room and getattr(self.stage_room, "boss", False):
                game.room_exit_open = True
                game.room_exit_rect.center = (self.bounds.centerx, self.bounds.centery - 180)
            else:
                game.room_exit_open = False
        else:
            game.room_exit_open = True
            game.room_exit_rect.center = (self.bounds.centerx, self.bounds.centery - 180)
        game.loot.spawn_xp((self.bounds.centerx - 28, self.bounds.centery - 120), self.reward_xp)
        game.loot.spawn_gold((self.bounds.centerx + 28, self.bounds.centery - 120), self.reward_gold)
        game.events.emit("room_cleared")
        game.audio.play("portal_open")
        game.feel.room_clear()
        ring_center = game.room_exit_rect.center if game.room_exit_open else self.bounds.center
        game.effects.ring(ring_center, radius=150, life=0.8, width=5)
        if stage and stage.active and not getattr(self.stage_room, "boss", False):
            game.message = "Room cleared. Doors unlocked. Press E on a doorway."
        else:
            game.message = "Prototype cleared. Reward spawned. Press E on the exit portal."
        game.show_wave_notice("PROTOTYPE CLEAR" if self.stage_room is None else "ROOM CLEAR")

    def draw_stage_doors(self, surface, camera, font):
        stage = getattr(self.game, "stage", None)
        if not stage or not stage.active:
            return
        node = stage.current_node
        if node is None:
            return
        unlocked = node.cleared
        for door_id, target_pos, rect in stage.open_doors():
            screen_rect = camera.apply_rect(rect)
            target = stage.node_by_pos[target_pos]
            color = (80, 170, 255) if unlocked else (70, 80, 95)
            if target.cleared:
                color = (90, 220, 150) if unlocked else (70, 100, 85)
            elif target.discovered:
                color = (255, 210, 90) if unlocked else (95, 85, 55)
            pygame.draw.rect(surface, color, screen_rect, 3, border_radius=10)
            label = "E" if unlocked else "LOCK"
            text = font.render(label, True, color)
            surface.blit(text, text.get_rect(center=screen_rect.center))

    def _place_player_for_entry(self, entry_door):
        if entry_door not in self.doors:
            return
        door = self.doors[entry_door]
        offsets = {
            "north": (0, 120),
            "south": (0, -120),
            "east": (-120, 0),
            "west": (120, 0),
        }
        dx, dy = offsets.get(entry_door, (0, 0))
        self.game.player.rect.center = (door.x + dx, door.y + dy)
        self.game.camera.reset(self.game.player.rect)

    def draw_telegraphs(self, surface, camera, font):
        if not self.active:
            return
        for door in PROTOTYPE_DOORS:
            pos = camera.apply_pos(pygame.Vector2(door.x, door.y))
            pygame.draw.circle(surface, (40, 90, 130), (round(pos.x), round(pos.y)), 24, 2)
        for entry in self.pending:
            door = self.doors[entry["door_id"]]
            pos = camera.apply_pos(pygame.Vector2(door.x, door.y))
            progress = 1.0 - entry["timer"] / max(0.01, PROTOTYPE_TELEGRAPH_TIME)
            radius = 28 + int(progress * 26)
            color = (255, 190, 70) if entry["timer"] > 0.18 else (255, 90, 60)
            pygame.draw.circle(surface, color, (round(pos.x), round(pos.y)), radius, 4)
            label = font.render("!", True, color)
            surface.blit(label, label.get_rect(center=(round(pos.x), round(pos.y))))

    def debug_snapshot(self):
        return {
            "active": self.active,
            "bounds": (self.bounds.width, self.bounds.height),
            "elapsed": round(self.elapsed, 2),
            "spawn_index": self.spawn_index,
            "pending": len(self.pending),
            "active_cap": self.active_cap,
            "obstacles": len(getattr(self.game, "room_obstacles", [])),
            "cleared": self.cleared,
        }

    def _spawn_treasure_room(self):
        game = self.game
        bounds = self.bounds
        for x, y in ((bounds.centerx - 120, bounds.centery - 130), (bounds.centerx + 120, bounds.centery - 130)):
            loot = game.enemy_pool.acquire(x, y, EnemyType.LOOT, difficulty=1.0)
            loot.prototype_room_enemy = True
            game.enemies.append(loot)
        self.spawn_index = len(self.spawn_plan)

    def _spawn_stage_boss(self):
        game = self.game
        boss = game.enemy_pool.acquire(self.bounds.centerx, self.bounds.centery - 220, EnemyType.BOSS, difficulty=1.8)
        boss.prototype_room_enemy = True
        game.enemies.append(boss)
        self.spawn_index = len(self.spawn_plan)
        game.events.emit("boss_spawned")
