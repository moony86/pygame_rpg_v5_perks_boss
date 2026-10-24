import pygame
import math

from entities.enemy import Enemy, EnemyType
from entities.enemy_bullet import EnemyBullet
from systems.room_bounds import current_room_bounds
from systems.world_utils import rotate_vector

BOSS_CLOSE_DASH_DISTANCE = 210
BOSS_FAR_GRAVITY_DISTANCE = 720
BOSS_GRAVITY_SAFE_RADIUS = 185
BOSS_GRAVITY_RING_RADIUS = 330


class BossAttackSystem:
    def handle_action(self, action, enemies, enemy_bullets, effects=None, audio=None, player=None, enemy_factory=None):
        boss_pos = pygame.Vector2(action["x"], action["y"])
        base = pygame.Vector2(action.get("direction", pygame.Vector2(1, 0)))
        if base.length_squared() == 0:
            base = pygame.Vector2(1, 0)
        else:
            base = base.normalize()

        player_pos = pygame.Vector2(player.rect.center) if player is not None else boss_pos + base * 400
        distance = boss_pos.distance_to(player_pos)
        phase = action.get("phase", 1)
        threat = max(1.0, action.get("difficulty", 1.0))
        damage_multiplier = action.get("damage_multiplier", 1.0)

        if distance < BOSS_CLOSE_DASH_DISTANCE and phase >= 2:
            self._boss_dash_attack(action, player_pos, phase, threat, enemies, effects)
        elif distance > BOSS_FAR_GRAVITY_DISTANCE:
            self._boss_gravity_well(action, phase, threat, damage_multiplier, enemy_bullets, effects, player)
        elif action["type"] == "boss_cone":
            self._boss_burst_cone(action, base, phase, threat, damage_multiplier, enemy_bullets, player)
        elif action["type"] == "boss_ring":
            self._boss_ring(action, phase, threat, damage_multiplier, enemy_bullets, effects, audio)
        elif action["type"] == "boss_laser":
            self._boss_laser(action, base, phase, threat, damage_multiplier, enemy_bullets, effects)
        else:
            self._boss_summon_leap(action, base, phase, threat, enemies, effects, enemy_factory)

    def _boss_burst_cone(self, action, base, phase, threat, damage_multiplier, enemy_bullets, player=None):
        count = 4 + min(2, phase)
        spread = 42 + phase * 8
        start = -spread / 2
        step = spread / max(1, count - 1)
        damage = int((15 + phase * 2) * damage_multiplier)
        for i in range(count):
            offset = start + i * step
            speed = 390 + i * 42 + phase * 30
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(base, offset), damage, speed=speed))

        if phase >= 2 and player is not None:
            enemy_bullets.append(EnemyBullet(
                action["x"], action["y"], base, int(12 * damage_multiplier),
                speed=330 + phase * 35, homing_target=player, turn_rate=1.0 + phase * 0.35,
            ))

    def _boss_gravity_well(self, action, phase, threat, damage_multiplier, enemy_bullets, effects, player=None):
        bounds = current_room_bounds()
        target = pygame.Vector2(player.rect.center) if player is not None else pygame.Vector2(bounds.center)
        target.x, target.y = bounds.clamp_center(target, 220, 180)
        damage = int((16 + phase * 2) * damage_multiplier)
        lanes = 8 + phase * 2
        gap_index = int((pygame.Vector2(action["x"], action["y"]).angle_to(pygame.Vector2(1, 0)) // 45) % lanes)
        for i in range(lanes):
            if i in (gap_index, (gap_index + lanes // 2) % lanes):
                continue
            angle = i * (360 / lanes)
            spawn = target + rotate_vector(pygame.Vector2(1, 0), angle) * BOSS_GRAVITY_RING_RADIUS
            spawn.x, spawn.y = bounds.clamp_center(spawn, 18, 18)
            direction = target - spawn
            if direction.length_squared() <= 0:
                direction = rotate_vector(pygame.Vector2(1, 0), angle + 90)
            enemy_bullets.append(EnemyBullet(
                spawn.x,
                spawn.y,
                direction.normalize(),
                damage,
                speed=145 + phase * 28,
            ))

        if player is not None:
            toward_player = target - pygame.Vector2(action["x"], action["y"])
            if toward_player.length_squared() > 0:
                enemy_bullets.append(EnemyBullet(
                    action["x"], action["y"], toward_player.normalize(), int(12 * damage_multiplier),
                    speed=300 + phase * 35, homing_target=player, turn_rate=0.45 + phase * 0.16,
                ))
        if effects:
            effects.ring(target, radius=BOSS_GRAVITY_SAFE_RADIUS, life=0.68, width=4)
            effects.ring(target, radius=BOSS_GRAVITY_RING_RADIUS, life=0.68, width=8)

    def _boss_dash_attack(self, action, player_pos, phase, threat, enemies, effects):
        for enemy in enemies:
            if enemy.type == EnemyType.BOSS:
                direction = player_pos - pygame.Vector2(action["x"], action["y"])
                if direction.length_squared() == 0:
                    direction = pygame.Vector2(1, 0)
                enemy.leap_velocity = direction.normalize() * (820 + phase * 190 + threat * 22)
                enemy.leap_timer = 0.42 + phase * 0.04
                break
        if effects:
            effects.ring((action["x"], action["y"]), radius=90, life=0.3, width=20)

    def _boss_ring(self, action, phase, threat, damage_multiplier, enemy_bullets, effects, audio):
        step = 20 if phase == 1 else (18 if phase == 2 else 16)
        speed = 255 + phase * 48 + min(70, threat * 6)
        damage = int((14 + phase * 2) * damage_multiplier)
        for angle in range(0, 360, step):
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle), damage, speed=speed))

        if phase >= 2:
            for angle in range(0, 360, step * 2):
                enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle + step // 2), damage, speed=speed * 0.72))

        if effects:
            effects.ring((action["x"], action["y"]), radius=135 + phase * 16, life=0.45, width=6)
        if audio:
            audio.play("boss_phase")

    def _boss_laser(self, action, base, phase, threat, damage_multiplier, enemy_bullets, effects):
        damage = int((18 + phase * 3) * damage_multiplier)
        for angle in range(-30, 31, 15):
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(base, angle), damage, speed=500 + phase * 35))
        if effects:
            effects.ring((action["x"], action["y"]), radius=115 + phase * 18, life=0.38, width=5)

    def _boss_summon_leap(self, action, base, phase, threat, enemies, effects, enemy_factory=None):
        boss_pos = pygame.Vector2(action["x"], action["y"])
        summon_count = 2 if phase == 1 else 3
        spread = 90 if summon_count == 2 else 120
        types = [EnemyType.CHASER, EnemyType.HUNTER, EnemyType.BRUTE]
        for i in range(summon_count):
            offset = -spread / 2 + (spread / max(1, summon_count - 1)) * i
            pos = boss_pos + rotate_vector(base, offset) * (120 + i * 18)
            bounds = current_room_bounds()
            pos.x, pos.y = bounds.clamp_center(pos, 90, 90)
            enemy_type = types[i % len(types)]
            difficulty = max(1.0, threat * 0.72)
            if enemy_factory is not None:
                enemies.append(enemy_factory(pos.x, pos.y, enemy_type, difficulty))
            else:
                enemies.append(Enemy(pos.x, pos.y, enemy_type, difficulty=difficulty))

        if effects:
            effects.ring((action["x"], action["y"]), radius=120, life=0.45, width=8)
