import pygame
import math

from entities.enemy import Enemy, EnemyType
from entities.enemy_bullet import EnemyBullet
from systems.world_utils import rotate_vector


class BossAttackSystem:
    def handle_action(self, action, enemies, enemy_bullets, effects=None, audio=None, player=None):
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

        if distance < 250 and phase >= 2:
            self._boss_dash_attack(action, player_pos, phase, threat, enemies, effects)
        elif distance > 500:
            self._boss_gravity_well(action, phase, threat, damage_multiplier, enemy_bullets, effects, player)
        elif action["type"] == "boss_cone":
            self._boss_burst_cone(action, base, phase, threat, damage_multiplier, enemy_bullets, player)
        elif action["type"] == "boss_ring":
            self._boss_ring(action, phase, threat, damage_multiplier, enemy_bullets, effects, audio)
        else:
            self._boss_summon_leap(action, base, phase, threat, enemies, effects)

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
        step = 40 if phase == 1 else (30 if phase == 2 else 24)
        damage = int((18 + phase * 2) * damage_multiplier)
        for angle in range(0, 360, step):
            vec = rotate_vector(pygame.Vector2(1, 0), angle)
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], vec, damage, speed=95 + phase * 25))

        if player is not None:
            toward_player = pygame.Vector2(player.rect.center) - pygame.Vector2(action["x"], action["y"])
            if toward_player.length_squared() > 0:
                toward_player = toward_player.normalize()
                enemy_bullets.append(EnemyBullet(
                    action["x"], action["y"], toward_player, int(14 * damage_multiplier),
                    speed=260 + phase * 45, homing_target=player, turn_rate=0.85 + phase * 0.25,
                ))

        if effects:
            effects.ring((action["x"], action["y"]), radius=210 + phase * 20, life=0.6, width=10)

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
        step = 18 if phase == 1 else (14 if phase == 2 else 12)
        speed = 285 + phase * 55 + min(90, threat * 8)
        damage = int((14 + phase * 2) * damage_multiplier)
        for angle in range(0, 360, step):
            enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle), damage, speed=speed))

        if phase >= 2:
            for angle in range(0, 360, step * 2):
                enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle + step // 2), damage, speed=speed * 0.72))

        if effects:
            effects.ring((action["x"], action["y"]), radius=160 + phase * 18, life=0.45, width=6)
        if audio:
            audio.play("boss")

    def _boss_summon_leap(self, action, base, phase, threat, enemies, effects):
        boss_pos = pygame.Vector2(action["x"], action["y"])
        summon_count = 2 if phase == 1 else 3
        spread = 90 if summon_count == 2 else 120
        types = [EnemyType.CHASER, EnemyType.HUNTER, EnemyType.BRUTE]
        for i in range(summon_count):
            offset = -spread / 2 + (spread / max(1, summon_count - 1)) * i
            pos = boss_pos + rotate_vector(base, offset) * (120 + i * 18)
            enemy_type = types[i % len(types)]
            enemies.append(Enemy(pos.x, pos.y, enemy_type, difficulty=max(1.0, threat * 0.72)))

        if effects:
            effects.ring((action["x"], action["y"]), radius=120, life=0.45, width=8)
