import pygame

from settings import ENEMY_BULLET_DAMAGE
from entities.enemy_bullet import EnemyBullet, FallingEnemyBullet
from systems.world_utils import rotate_vector


class CombatActionResolver:
    def handle(self, action, game):
        action_type = action["type"]

        if action_type == 'boss_trial':
            action['encounter'].arena_solids=tuple(game.collision.get_colliders())
            action['encounter'].resolve(action,game.enemies,game.enemy_bullets,game.effects,game.audio,game.player)
            return

        if action_type == "enemy_shoot":
            base_damage = int(ENEMY_BULLET_DAMAGE * action.get("damage_multiplier", 1.0))
            speed = 410 + int(action.get("difficulty", 1.0) * 12)
            shot_count = action.get("shot_count", 2)
            patterns = {
                2: [(-11, 0.9), (11, 0.9)],
                3: [(-18, 0.82), (0, 1.0), (18, 0.82)],
                5: [(-28, 0.65), (-14, 0.85), (0, 1.0), (14, 0.85), (28, 0.65)],
            }
            for angle, damage_scale in patterns.get(shot_count, patterns[2]):
                damage = max(1, int(base_damage * damage_scale))
                game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=speed, owner_id=action.get("owner_id")))

        elif action_type == "enemy_rain":
            base_damage = int((ENEMY_BULLET_DAMAGE + 3) * action.get("damage_multiplier", 1.0))
            target = pygame.Vector2(action.get("target_x", action["x"]), action.get("target_y", action["y"]))
            difficulty = action.get("difficulty", 1.0)
            offsets = [(0, 0), (-55, -20), (55, 20), (-20, 55)]
            if difficulty >= 4.5:
                offsets.append((25, -65))
            for index, (ox, oy) in enumerate(offsets):
                game.enemy_bullets.append(FallingEnemyBullet(target.x + ox, target.y + oy, base_damage, delay=0.62 + index * 0.10, owner_id=action.get("owner_id")))

        elif action_type == "elite_cross":
            difficulty = action.get("difficulty", 1.0)
            damage = int((ENEMY_BULLET_DAMAGE + 2) * action.get("damage_multiplier", 1.0))
            speed = 390 + int(difficulty * 10)
            for angle in (0, 90, 180, 270):
                game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=speed, owner_id=action.get("owner_id")))

        elif action_type == "elite_laser":
            damage = int((ENEMY_BULLET_DAMAGE + 4) * action.get("damage_multiplier", 1.0))
            base = action["direction"]
            for angle in (-30, -20, -10, 0, 10, 20, 30):
                game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(base, angle), damage, speed=560, owner_id=action.get("owner_id")))
            game.effects.ring((action["x"], action["y"]), radius=95, life=0.32, width=4)

        elif action_type == "elite_burst":
            difficulty = action.get("difficulty", 1.0)
            base_damage = int((ENEMY_BULLET_DAMAGE + 2) * action.get("damage_multiplier", 1.0))
            fan_speed = 470 + int(difficulty * 16)
            ring_speed = 330 + int(difficulty * 10)
            for angle, damage_scale in [(-34, 0.75), (-18, 0.9), (0, 1.0), (18, 0.9), (34, 0.75)]:
                damage = max(1, int(base_damage * damage_scale))
                game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=fan_speed, owner_id=action.get("owner_id")))
            for angle in range(0, 360, 60):
                damage = max(1, int(base_damage * 0.55))
                game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=ring_speed, owner_id=action.get("owner_id")))

        elif action_type == "hunter_homing":
            damage = int((ENEMY_BULLET_DAMAGE + 1) * action.get("damage_multiplier", 1.0))
            speed = 330 + int(action.get("difficulty", 1.0) * 12)
            game.enemy_bullets.append(EnemyBullet(action["x"], action["y"], action["direction"], damage, speed=speed, homing_target=game.player, turn_rate=1.55, owner_id=action.get("owner_id")))

        elif action_type in ("boss_cone", "boss_ring", "boss_summon_leap", "boss_laser"):
            game.boss_attacks.handle_action(
                action,
                game.enemies,
                game.enemy_bullets,
                game.effects,
                game.audio,
                player=game.player,
                enemy_factory=game.enemy_pool.acquire,
            )
