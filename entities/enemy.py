import pygame
from enum import Enum, auto

from settings import (
    ENEMY_SPEED,
    ENEMY_HEALTH,
    RED,
    PURPLE,
    CYAN,
    ORANGE,
    PINK,
    RANGED_ATTACK_RANGE,
    RANGED_WINDUP_TIME,
    RANGED_ATTACK_COOLDOWN,
    JUMPER_ATTACK_RANGE,
    JUMPER_WINDUP_TIME,
    JUMPER_LEAP_TIME,
    JUMPER_ATTACK_COOLDOWN,
    BOSS_HEALTH,
    BOSS_SPEED,
)


class EnemyType(Enum):
    CHASER = auto()
    RANGED = auto()
    JUMPER = auto()
    ELITE = auto()
    BOSS = auto()


class Enemy:
    def __init__(self, x, y, enemy_type=EnemyType.CHASER, difficulty=1.0):
        self.type = enemy_type

        if self.type == EnemyType.BOSS:
            self.phase = 1
            self.shield = 150
            self.max_shield = 150
            self.rage = False

            self.rect = pygame.Rect(x, y, 92, 92)
            self.speed = BOSS_SPEED
            self.max_health = BOSS_HEALTH

        elif self.type == EnemyType.ELITE:
            self.rect = pygame.Rect(x, y, 58, 58)
            self.speed = ENEMY_SPEED * 0.82 * difficulty
            self.max_health = int(ENEMY_HEALTH * difficulty * 5.0)

        else:
            self.rect = pygame.Rect(x, y, 34, 34)
            base_speed = ENEMY_SPEED

            if self.type == EnemyType.RANGED:
                base_speed *= 0.72
            elif self.type == EnemyType.JUMPER:
                base_speed *= 0.88

            self.speed = base_speed * difficulty
            self.max_health = int(ENEMY_HEALTH * difficulty)

            if self.type == EnemyType.RANGED:
                self.max_health = int(self.max_health * 0.75)
            elif self.type == EnemyType.JUMPER:
                self.max_health = int(self.max_health * 1.25)

        self.health = self.max_health
        self.alive = True
        self.hit_flash = 0.0

        self.attack_cooldown = 1.0
        self.windup_timer = 0.0
        self.windup_direction = pygame.Vector2(0, 0)
        self.windup_action = None

        self.leap_timer = 0.0
        self.leap_velocity = pygame.Vector2(0, 0)

        self.boss_attack_index = 0

    def update(self, dt, player_rect):
        if not self.alive:
            return None

        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt)

        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)

        if self.windup_timer > 0:
            self.windup_timer = max(0, self.windup_timer - dt)

            if self.windup_timer <= 0:
                return self._finish_windup()

            return None

        if self.leap_timer > 0:
            self.leap_timer = max(0, self.leap_timer - dt)
            self.rect.x += round(self.leap_velocity.x * dt)
            self.rect.y += round(self.leap_velocity.y * dt)
            return None

        to_player = pygame.Vector2(
            player_rect.centerx - self.rect.centerx,
            player_rect.centery - self.rect.centery,
        )

        distance = to_player.length()
        direction = to_player.normalize() if distance > 0 else pygame.Vector2(0, 0)

        if self.type == EnemyType.RANGED:
            self._update_ranged(distance, direction, dt)
        elif self.type == EnemyType.JUMPER:
            self._update_jumper(distance, direction, dt)
        elif self.type == EnemyType.ELITE:
            self._update_elite(distance, direction, dt)
        elif self.type == EnemyType.BOSS:
            self._update_boss(distance, direction, dt)
        else:
            self._move(direction, dt)

        return None

    def _start_windup(self, seconds, direction, action):
        self.windup_timer = seconds
        self.windup_direction = direction.copy()
        self.windup_action = action

    def _update_ranged(self, distance, direction, dt):
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0:
            self._start_windup(RANGED_WINDUP_TIME, direction, "enemy_shoot")
            self.attack_cooldown = RANGED_ATTACK_COOLDOWN
            return

        if distance < 240:
            self._move(-direction, dt)
        elif distance > 380:
            self._move(direction, dt)

    def _update_jumper(self, distance, direction, dt):
        if distance <= JUMPER_ATTACK_RANGE and self.attack_cooldown <= 0:
            self._start_windup(JUMPER_WINDUP_TIME, direction, "enemy_jump")
            self.attack_cooldown = JUMPER_ATTACK_COOLDOWN
            return

        self._move(direction, dt)

    def _update_elite(self, distance, direction, dt):
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0:
            self._start_windup(0.85, direction, "elite_burst")
            self.attack_cooldown = 2.4
            return

        self._move(direction, dt)

    def _update_boss(self, distance, direction, dt):
        if self.phase == 2 and self.health <= self.max_health * 0.35:
            self.phase = 3
            self.rage = True

        if self.attack_cooldown <= 0:
            if self.phase == 1:
                attacks = [
                    "boss_cone",
                    "boss_ring",
                ]
            elif self.phase == 2:
                attacks = [
                    "boss_cone",
                    "boss_ring",
                    "boss_summon_leap",
                ]
            else:
                attacks = [
                    "boss_ring",
                    "boss_cone",
                    "boss_summon_leap",
                    "boss_ring",
                ]

            action = attacks[self.boss_attack_index % len(attacks)]
            self.boss_attack_index += 1

            if self.phase == 1:
                windup = 0.95
                cooldown = 2.2
            elif self.phase == 2:
                windup = 0.80
                cooldown = 1.8
            else:
                windup = 0.65
                cooldown = 1.35

            self._start_windup(windup, direction, action)
            self.attack_cooldown = cooldown
            return

        if distance > 270:
            self._move(direction, dt)
        elif distance < 150:
            self._move(-direction, dt)

    def _finish_windup(self):
        action = self.windup_action
        self.windup_action = None

        if action == "enemy_jump":
            self.leap_timer = JUMPER_LEAP_TIME
            self.leap_velocity = self.windup_direction * 730
            return {"type": "enemy_jump"}

        return {
            "type": action,
            "x": self.rect.centerx,
            "y": self.rect.centery,
            "direction": self.windup_direction.copy(),
            "phase": self.phase if self.type == EnemyType.BOSS else 1,
        }

    def _move(self, direction, dt):
        self.rect.x += round(direction.x * self.speed * dt)
        self.rect.y += round(direction.y * self.speed * dt)

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash = 0.08

        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True

        return False

    def draw(self, surface, camera):
        if self.type == EnemyType.RANGED:
            base_color = PURPLE
        elif self.type == EnemyType.JUMPER:
            base_color = CYAN
        elif self.type == EnemyType.ELITE:
            base_color = PINK
        elif self.type == EnemyType.BOSS:
            base_color = ORANGE
        else:
            base_color = RED

        screen_rect = camera.apply_rect(self.rect)
        color = (255, 140, 140) if self.hit_flash > 0 else base_color

        pygame.draw.rect(surface, color, screen_rect, border_radius=7)

        if self.type == EnemyType.BOSS:
            if self.phase == 1:
                pygame.draw.circle(
                    surface,
                    (80, 180, 255),
                    screen_rect.center,
                    58,
                    4,
                )
            elif self.phase == 3:
                pygame.draw.circle(
                    surface,
                    (255, 60, 60),
                    screen_rect.center,
                    62,
                    5,
                )

        bar_w = self.rect.width
        ratio = max(0, self.health / self.max_health)

        bg = pygame.Rect(self.rect.x, self.rect.y - 9, bar_w, 5)
        fg = pygame.Rect(self.rect.x, self.rect.y - 9, int(bar_w * ratio), 5)

        pygame.draw.rect(surface, (80, 0, 0), camera.apply_rect(bg))
        pygame.draw.rect(surface, (255, 80, 80), camera.apply_rect(fg))

        if self.type == EnemyType.BOSS and self.phase == 1:
            shield_ratio = max(0, self.shield / self.max_shield)

            shield_bg = pygame.Rect(self.rect.x, self.rect.y - 17, bar_w, 5)
            shield_fg = pygame.Rect(
                self.rect.x,
                self.rect.y - 17,
                int(bar_w * shield_ratio),
                5,
            )

            pygame.draw.rect(surface, (20, 60, 100), camera.apply_rect(shield_bg))
            pygame.draw.rect(surface, (80, 180, 255), camera.apply_rect(shield_fg))

        if self.windup_timer > 0 and self.windup_direction.length_squared() > 0:
            start = camera.apply_pos(pygame.Vector2(self.rect.center))
            action = self.windup_action or ""

            if "ring" in action:
                pygame.draw.circle(
                    surface,
                    (255, 120, 40),
                    (round(start.x), round(start.y)),
                    120,
                    4,
                )

            elif "summon" in action:
                end = start + self.windup_direction * 290
                pygame.draw.line(surface, (255, 120, 40), start, end, 9)
                pygame.draw.circle(
                    surface,
                    (255, 120, 40),
                    (round(start.x), round(start.y)),
                    32,
                    2,
                )

            else:
                length = 650 if self.type == EnemyType.BOSS else 520
                width = 7 if self.type in (EnemyType.BOSS, EnemyType.ELITE) else 3
                end = start + self.windup_direction * length

                pygame.draw.line(surface, (255, 120, 40), start, end, width)
                pygame.draw.circle(
                    surface,
                    (255, 120, 40),
                    (round(start.x), round(start.y)),
                    22,
                    2,
                )
