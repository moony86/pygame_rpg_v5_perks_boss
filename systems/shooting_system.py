import math
import random

from settings import (
    PROJECTILE_DAMAGE,
    PROJECTILE_SPEED,
    SHOOT_COOLDOWN,
)

from entities.projectile import Projectile


def rotate_vector(vec, degrees):
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)

    return vec.__class__(
        vec.x * cos_a - vec.y * sin_a,
        vec.x * sin_a + vec.y * cos_a,
    )


def crit_stats(player):
    crit_chance = max(0.0, player.crit_chance)
    overflow_bonus = max(0.0, crit_chance - 1.0)
    effective_chance = min(1.0, crit_chance)
    effective_multiplier = player.crit_multiplier + overflow_bonus
    return effective_chance, effective_multiplier


class ShootingSystem:
    def __init__(self):
        self.shoot_timer = 0.0

    def reset(self):
        self.shoot_timer = 0.0

    def update(self, dt):
        self.shoot_timer = max(0, self.shoot_timer - dt)

    def try_shoot(self, player, projectiles, audio=None):
        if self.shoot_timer > 0:
            return False

        base_damage = PROJECTILE_DAMAGE + player.damage_bonus
        speed = PROJECTILE_SPEED + player.projectile_speed_bonus
        count = player.projectile_count
        crit_chance, crit_multiplier = crit_stats(player)

        if count <= 1:
            angles = [0]
        else:
            total = player.spread_degrees
            start = -total / 2
            step = total / max(1, count - 1)
            angles = [start + i * step for i in range(count)]

        for angle in angles:
            direction = rotate_vector(player.aim_direction, angle)
            critical = random.random() < crit_chance
            damage = int(base_damage * (crit_multiplier if critical else 1))

            projectiles.append(
                Projectile(
                    player.rect.centerx,
                    player.rect.centery,
                    direction,
                    damage,
                    speed=speed,
                    pierce=player.pierce,
                    critical=critical,
                )
            )

        if audio:
            audio.play("shoot")

        self.shoot_timer = max(0.055, SHOOT_COOLDOWN / player.fire_rate_multiplier)
        return True
