import pygame

from settings import (
    BOSS_DAMAGE,
    ENEMY_BULLET_DAMAGE,
)

from entities.enemy import Enemy, EnemyType
from entities.enemy_bullet import EnemyBullet
from systems.world_utils import rotate_vector


class BossAttackSystem:
    def handle_action(self, action, enemies, enemy_bullets, effects=None, audio=None):
        base = action["direction"]
        phase = action.get("phase", 1)

        if action["type"] == "boss_cone":
            self._boss_cone(action, base, phase, enemy_bullets)

        elif action["type"] == "boss_ring":
            self._boss_ring(action, phase, enemy_bullets, effects, audio)

        elif action["type"] == "boss_summon_leap":
            self._boss_summon_leap(action, base, phase, enemies, effects)

    def _boss_cone(self, action, base, phase, enemy_bullets):
        angles = [-24, -12, 0, 12, 24]

        if phase == 2:
            angles = [-36, -24, -12, 0, 12, 24, 36]

        for angle in angles:
            enemy_bullets.append(
                EnemyBullet(
                    action["x"],
                    action["y"],
                    rotate_vector(base, angle),
                    14 if phase == 1 else BOSS_DAMAGE,
                )
            )

    def _boss_ring(self, action, phase, enemy_bullets, effects, audio):
        step = 30 if phase == 1 else 20

        for angle in range(0, 360, step):
            enemy_bullets.append(
                EnemyBullet(
                    action["x"],
                    action["y"],
                    rotate_vector(pygame.Vector2(1, 0), angle),
                    12 if phase == 1 else 16,
                    speed=240 if phase == 1 else 290,
                )
            )

        if audio:
            audio.play("boss")

        if effects:
            effects.ring(
                (action["x"], action["y"]),
                radius=160,
                life=0.45,
                width=5,
            )

    def _boss_summon_leap(self, action, base, phase, enemies, effects):
        boss_pos = pygame.Vector2(action["x"], action["y"])

        for angle in [-90, 0, 90]:
            pos = boss_pos + rotate_vector(base, angle) * 120
            enemies.append(
                Enemy(
                    pos.x,
                    pos.y,
                    EnemyType.CHASER,
                    difficulty=1.8 if phase == 1 else 2.2,
                )
            )

        for enemy in enemies:
            if enemy.type == EnemyType.BOSS:
                enemy.leap_timer = 0.34
                enemy.leap_velocity = base * (680 if phase == 1 else 820)
                break

        if effects:
            effects.ring(boss_pos, radius=120, life=0.35, width=4)
