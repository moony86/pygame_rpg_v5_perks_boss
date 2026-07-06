import math
import random

from settings import (
    PROJECTILE_DAMAGE,
    PROJECTILE_SPEED,
    SHOOT_COOLDOWN,
    PROJECTILE_KNOCKBACK,
    SURGE_DAMAGE_MULTIPLIER,
    SURGE_FIRE_RATE_MULTIPLIER,
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
        self.last_fire_interval = None

    def reset(self):
        self.shoot_timer = 0.0
        self.last_fire_interval = None

    def update(self, dt):
        self.shoot_timer = max(0, self.shoot_timer - dt)

    def try_shoot(self, player, projectiles, audio=None):
        fire_multiplier = player.fire_rate_multiplier * (SURGE_FIRE_RATE_MULTIPLIER if getattr(player, "surge_timer", 0) > 0 else 1.0)
        fire_interval = max(0.055, SHOOT_COOLDOWN / fire_multiplier)
        if self.last_fire_interval is None:
            self.last_fire_interval = fire_interval
        elif abs(fire_interval - self.last_fire_interval) > 0.0001:
            self.shoot_timer = min(self.shoot_timer, fire_interval)
            self.last_fire_interval = fire_interval

        if self.shoot_timer > 0:
            return False

        surge_damage = SURGE_DAMAGE_MULTIPLIER if getattr(player, "surge_timer", 0) > 0 else 1.0
        blood_bonus = 1.0
        if getattr(player, "vampire_blood", 0) > 0:
            blood_bonus += min(0.35, getattr(player, "vampire_blood", 0) * getattr(player, "vampire_blood_damage_bonus", 0.0))
        blood_moon_bonus = 1.15 if getattr(player, "vampire_blood_moon_timer", 0) > 0 else 1.0
        base_damage = int((PROJECTILE_DAMAGE + player.damage_bonus) * getattr(player, "weapon_damage_multiplier", 1.0) * surge_damage * blood_bonus * blood_moon_bonus)
        speed = PROJECTILE_SPEED + player.projectile_speed_bonus
        count = player.projectile_count
        split_damage_scale = getattr(player, "split_damage_multiplier", 1.0)
        if count > 1:
            split_damage_scale *= max(0.50, 1.0 - (count - 1) * 0.10)
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
            damage = max(1, int(base_damage * split_damage_scale * (crit_multiplier if critical else 1)))
            muzzle = player.weapon_muzzle_position()

            projectiles.append(
                Projectile(
                    muzzle.x,
                    muzzle.y,
                    direction,
                    damage,
                    speed=speed,
                    pierce=player.pierce,
                    critical=critical,
                    knockback=PROJECTILE_KNOCKBACK * getattr(player, "knockback_power", 1.0),
                    explosive=getattr(player, "explosive_rounds", False),
                    explosion_radius=getattr(player, "explosion_radius", 95),
                    explosion_splash_ratio=getattr(player, "explosion_splash_ratio", 1 / 3),
                )
            )

        if hasattr(player, "trigger_gun_shot"):
            player.trigger_gun_shot()

        if audio:
            audio.play("shoot")

        self.shoot_timer = fire_interval
        return True
