import pygame
import math
import random
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
    MAP_SIZE,
    GOLD,
    YELLOW,
)


class EnemyType(Enum):
    CHASER  = auto()
    RANGED  = auto()
    JUMPER  = auto()
    HUNTER  = auto()
    BRUTE   = auto()
    ELITE   = auto()
    BOSS    = auto()
    LOOT    = auto()


class Enemy:
    def __init__(self, x, y, enemy_type=EnemyType.CHASER, difficulty=1.0):
        self.type = enemy_type
        self.difficulty = max(1.0, difficulty)
        self.health_scale = self.difficulty ** 1.35
        self.speed_scale = min(3.15, 0.85 + self.difficulty * 0.42)
        self.damage_multiplier = min(3.4, 1.0 + self.difficulty * 0.16)
        self.attack_speed_multiplier = min(2.35, 1.0 + self.difficulty * 0.11)

        if self.type == EnemyType.LOOT:
            self.rect       = pygame.Rect(x, y, 36, 36)
            self.speed      = ENEMY_SPEED * 2.15
            self.max_health = int(ENEMY_HEALTH * 4.1)
            self.damage_multiplier = 0.0

        elif self.type == EnemyType.BOSS:
            self.phase       = 1
            self.max_shield  = int(650 + BOSS_HEALTH * (0.25 + self.difficulty * 0.32))
            self.shield      = self.max_shield
            self.rage        = False
            self.rect        = pygame.Rect(x, y, 92, 92)
            self.speed       = BOSS_SPEED * min(2.35, 1.0 + self.difficulty * 0.13)
            self.max_health  = int(BOSS_HEALTH * (2.35 + self.difficulty * 1.85))

        elif self.type == EnemyType.ELITE:
            self.rect       = pygame.Rect(x, y, 58, 58)
            self.speed      = ENEMY_SPEED * 0.82 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 4.2)

        elif self.type == EnemyType.HUNTER:
            self.rect       = pygame.Rect(x, y, 38, 38)
            self.speed      = ENEMY_SPEED * 1.18 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 1.15)

        elif self.type == EnemyType.BRUTE:
            self.rect       = pygame.Rect(x, y, 52, 52)
            self.speed      = ENEMY_SPEED * 0.95 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 2.4)
            self.damage_multiplier *= 1.25

        else:
            self.rect      = pygame.Rect(x, y, 34, 34)
            base_speed     = ENEMY_SPEED

            if self.type == EnemyType.RANGED:
                base_speed *= 0.72
            elif self.type == EnemyType.JUMPER:
                base_speed *= 0.88

            self.speed      = base_speed * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale)

            if self.type == EnemyType.RANGED:
                self.max_health = int(self.max_health * 0.82)
            elif self.type == EnemyType.JUMPER:
                self.max_health = int(self.max_health * 1.35)

        self.health    = self.max_health
        self.alive     = True
        self.hit_flash = 0.0

        self.attack_cooldown  = 1.0
        self.windup_timer     = 0.0
        self.windup_direction = pygame.Vector2(0, 0)
        self.windup_action    = None

        self.leap_timer    = 0.0
        self.leap_velocity = pygame.Vector2(0, 0)

        self.boss_attack_index = 0
        self.last_player_center = None
        self.estimated_player_velocity = pygame.Vector2(0, 0)

        # animation tick (used for oscillating effects)
        self._anim = 0.0

    # ------------------------------------------------------------------ #
    #  UPDATE LOGIC  (unchanged from original)                            #
    # ------------------------------------------------------------------ #

    def update(self, dt, player_rect):
        if not self.alive:
            return None

        self._anim += dt

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

        player_center = pygame.Vector2(player_rect.center)
        if self.last_player_center is not None and dt > 0:
            instant_velocity = (player_center - self.last_player_center) / dt
            self.estimated_player_velocity = self.estimated_player_velocity.lerp(instant_velocity, 0.35)
        self.last_player_center = player_center.copy()

        to_player = pygame.Vector2(
            player_rect.centerx - self.rect.centerx,
            player_rect.centery - self.rect.centery,
        )
        distance  = to_player.length()
        direction = to_player.normalize() if distance > 0 else pygame.Vector2(0, 0)

        if self.type == EnemyType.LOOT:
            self._update_loot(distance, direction, dt)
        elif self.type == EnemyType.RANGED:
            self._update_ranged(distance, direction, dt)
        elif self.type == EnemyType.JUMPER:
            self._update_jumper(distance, direction, dt)
        elif self.type == EnemyType.HUNTER:
            self._update_hunter(distance, direction, dt)
        elif self.type == EnemyType.BRUTE:
            self._update_brute(distance, direction, dt)
        elif self.type == EnemyType.ELITE:
            self._update_elite(distance, direction, dt)
        elif self.type == EnemyType.BOSS:
            self._update_boss(distance, direction, dt)
        else:
            self._move(direction, dt)

        return None

    def _start_windup(self, seconds, direction, action):
        self.windup_timer     = seconds
        self.windup_direction = direction.copy()
        self.windup_action    = action

    def _predictive_direction(self, lead_time, offset_strength=0.0):
        target = (self.last_player_center or pygame.Vector2(self.rect.center)) + self.estimated_player_velocity * lead_time
        if offset_strength > 0:
            to_target = target - pygame.Vector2(self.rect.center)
            if to_target.length_squared() > 0:
                side = pygame.Vector2(-to_target.y, to_target.x).normalize()
                target += side * random.uniform(-offset_strength, offset_strength)
        aim = target - pygame.Vector2(self.rect.center)
        if aim.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return aim.normalize()

    def _update_loot(self, distance, direction, dt):
        center_pull = pygame.Vector2(MAP_SIZE / 2 - self.rect.centerx, MAP_SIZE / 2 - self.rect.centery)
        flee = -direction if distance > 0 else pygame.Vector2(1, 0).rotate(self._anim * 90)
        side = pygame.Vector2(-direction.y, direction.x) if distance > 0 else pygame.Vector2(0, 1)
        weave = side * math.sin(self._anim * 5.2) * 0.85
        edge_pull = pygame.Vector2(0, 0)
        edge_margin = 260
        if self.rect.left < edge_margin or self.rect.right > MAP_SIZE - edge_margin or self.rect.top < edge_margin or self.rect.bottom > MAP_SIZE - edge_margin:
            if center_pull.length_squared() > 0:
                edge_pull = center_pull.normalize() * 1.25
        panic = 1.22 if distance < 230 else 1.0
        move_dir = flee * panic + weave + edge_pull
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)
            self.rect.clamp_ip(pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE))

    def _update_ranged(self, distance, direction, dt):
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.72, 120)
            self._start_windup(max(0.24, RANGED_WINDUP_TIME * 0.55), aim, "enemy_shoot")
            self.attack_cooldown = max(0.42, RANGED_ATTACK_COOLDOWN * 0.58 / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 2.3) * 0.75
        if distance < 115:
            move_dir = -direction + strafe * 0.35
        elif distance > 285:
            move_dir = direction + strafe * 0.35
        else:
            move_dir = direction * 0.38 + strafe
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)

    def _update_jumper(self, distance, direction, dt):
        if distance <= JUMPER_ATTACK_RANGE and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.48, 80)
            self._start_windup(max(0.28, JUMPER_WINDUP_TIME * 0.58), aim, "enemy_jump")
            self.attack_cooldown = max(0.85, JUMPER_ATTACK_COOLDOWN * 0.62 / self.attack_speed_multiplier)
            return
        self._move(direction, dt)

    def _update_hunter(self, distance, direction, dt):
        if distance <= RANGED_ATTACK_RANGE + 170 and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.82, 110)
            self._start_windup(0.32, aim, "hunter_homing")
            self.attack_cooldown = max(0.78, 1.15 / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.cos(self._anim * 2.8) * 0.85
        if distance < 105:
            move_dir = -direction + strafe * 0.4
        elif distance > 230:
            move_dir = direction + strafe * 0.25
        else:
            move_dir = direction * 0.45 + strafe
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)

    def _update_brute(self, distance, direction, dt):
        if distance <= 560 and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.42, 55)
            self._start_windup(0.46, aim, "brute_charge")
            self.attack_cooldown = max(1.05, 1.95 / self.attack_speed_multiplier)
            return
        if distance > 95:
            flank = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 1.7) * 0.45
            move_dir = direction + flank
            if move_dir.length_squared() > 0:
                move_dir = move_dir.normalize()
            self._move(move_dir, dt)

    def _update_elite(self, distance, direction, dt):
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.65, 110)
            self._start_windup(0.68, aim, "elite_burst")
            self.attack_cooldown = max(0.72, 1.55 / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 1.9) * 0.5
        if distance > 145:
            move_dir = direction + strafe
        else:
            move_dir = -direction * 0.35 + strafe
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)

    def _update_boss(self, distance, direction, dt):
        if self.phase == 2 and self.health <= self.max_health * 0.35:
            self.phase = 3
            self.rage  = True

        if self.attack_cooldown <= 0:
            if self.phase == 1:
                attacks = ["boss_cone", "boss_ring"]
            elif self.phase == 2:
                attacks = ["boss_cone", "boss_ring", "boss_summon_leap"]
            else:
                attacks = ["boss_ring", "boss_cone", "boss_summon_leap", "boss_ring"]

            action = attacks[self.boss_attack_index % len(attacks)]
            self.boss_attack_index += 1

            if self.phase == 1:
                windup, cooldown = 0.95, 2.2 / self.attack_speed_multiplier
            elif self.phase == 2:
                windup, cooldown = 0.80, 1.8 / self.attack_speed_multiplier
            else:
                windup, cooldown = 0.65, 1.35 / self.attack_speed_multiplier

            aim = self._predictive_direction(0.65 if self.phase == 1 else 0.85, 120 if self.phase >= 2 else 70)
            self._start_windup(windup, aim, action)
            self.attack_cooldown = cooldown
            return

        if distance > 270:
            self._move(direction, dt)
        elif distance < 150:
            self._move(-direction, dt)

    def _finish_windup(self):
        action            = self.windup_action
        self.windup_action = None

        if action == "enemy_jump":
            self.leap_timer    = JUMPER_LEAP_TIME
            self.leap_velocity = self.windup_direction * (820 * min(1.9, self.speed_scale / 1.32))
            return {"type": "enemy_jump"}

        if action == "brute_charge":
            self.leap_timer = 0.42
            self.leap_velocity = self.windup_direction * (660 * min(1.65, self.speed_scale / 1.45))
            return {"type": "brute_charge"}

        return {
            "type":      action,
            "x":         self.rect.centerx,
            "y":         self.rect.centery,
            "direction": self.windup_direction.copy(),
            "phase":     self.phase if self.type == EnemyType.BOSS else 1,
            "difficulty": self.difficulty,
            "damage_multiplier": self.damage_multiplier,
            "owner_id": id(self),
        }

    def _move(self, direction, dt):
        self.rect.x += round(direction.x * self.speed * dt)
        self.rect.y += round(direction.y * self.speed * dt)

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash = 0.08
        if self.health <= 0:
            self.health = 0
            self.alive  = False
            return True
        return False

    # ------------------------------------------------------------------ #
    #  DRAW                                                                #
    # ------------------------------------------------------------------ #

    def draw(self, surface, camera):
        if self.hit_flash > 0:
            self._draw_flash(surface, camera)
        elif self.type == EnemyType.CHASER:
            self._draw_chaser(surface, camera)
        elif self.type == EnemyType.RANGED:
            self._draw_ranged(surface, camera)
        elif self.type == EnemyType.JUMPER:
            self._draw_jumper(surface, camera)
        elif self.type == EnemyType.HUNTER:
            self._draw_hunter(surface, camera)
        elif self.type == EnemyType.BRUTE:
            self._draw_brute(surface, camera)
        elif self.type == EnemyType.ELITE:
            self._draw_elite(surface, camera)
        elif self.type == EnemyType.BOSS:
            self._draw_boss(surface, camera)
        elif self.type == EnemyType.LOOT:
            self._draw_loot(surface, camera)

        self._draw_health_bar(surface, camera)
        self._draw_windup_indicator(surface, camera)

    # ---- hit flash (all types) ----------------------------------------
    def _draw_flash(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        pygame.draw.rect(surface, (255, 140, 140), sr, border_radius=7)

    # ---- CHASER --------------------------------------------------------
    def _draw_chaser(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        # body – dark red blocky rectangle
        pygame.draw.rect(surface, (180, 30, 30), sr, border_radius=4)

        # shoulder spikes (top corners)
        spike_size = 7
        for sx, sy in [(x, y), (x + w - spike_size, y)]:
            pygame.draw.polygon(surface, (220, 50, 50), [
                (sx, sy + spike_size),
                (sx + spike_size // 2, sy - 4),
                (sx + spike_size, sy + spike_size),
            ])

        # angry eye slit
        eye_rect = pygame.Rect(x + 4, y + 7, w - 8, 7)
        pygame.draw.rect(surface, (20, 0, 0), eye_rect, border_radius=2)
        pygame.draw.rect(surface, (255, 30, 30), pygame.Rect(x + 6, y + 9, 6, 3), border_radius=1)
        pygame.draw.rect(surface, (255, 30, 30), pygame.Rect(x + w - 12, y + 9, 6, 3), border_radius=1)

        # claw feet
        for fx in [x + 3, x + w - 10]:
            pygame.draw.rect(surface, (140, 20, 20),
                             pygame.Rect(fx, y + h - 5, 7, 5), border_radius=2)

    # ---- RANGED --------------------------------------------------------
    def _draw_ranged(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        # robe body – tall rounded purple
        pygame.draw.rect(surface, (90, 50, 150), sr, border_radius=8)

        # hood top
        hood_pts = [
            (x + 2, y + 6),
            (cx,    y - 7),
            (x + w - 2, y + 6),
        ]
        pygame.draw.polygon(surface, (70, 35, 125), hood_pts)

        # glowing orb staff (left side)
        staff_x = x - 5
        pygame.draw.line(surface, (55, 30, 100),
                         (staff_x, y - 2), (staff_x, y + h + 2), 3)
        orb_pulse = 5 + int(2 * math.sin(self._anim * 4))
        pygame.draw.circle(surface, (180, 120, 255), (staff_x, y - 2), orb_pulse, 2)
        pygame.draw.circle(surface, (220, 190, 255), (staff_x, y - 2), orb_pulse // 2)

        # glowing eyes
        eye_y = y + h // 3
        pygame.draw.circle(surface, (200, 150, 255), (cx - 5, eye_y), 4)
        pygame.draw.circle(surface, (200, 150, 255), (cx + 5, eye_y), 4)
        pygame.draw.circle(surface, (240, 220, 255), (cx - 5, eye_y), 2)
        pygame.draw.circle(surface, (240, 220, 255), (cx + 5, eye_y), 2)

    # ---- JUMPER --------------------------------------------------------
    def _draw_jumper(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        leaping = self.leap_timer > 0
        col_body = (0, 180, 180) if not leaping else (0, 230, 230)

        # body – teal compact block
        pygame.draw.rect(surface, col_body, sr, border_radius=6)

        # coiled spring legs (when idle) or extended (when leaping)
        spring_col = (0, 130, 130)
        if leaping:
            # extended legs downward
            for lx in [x + 4, x + w - 10]:
                pygame.draw.rect(surface, spring_col,
                                 pygame.Rect(lx, y + h, 6, 14), border_radius=2)
                pygame.draw.rect(surface, (0, 200, 200),
                                 pygame.Rect(lx, y + h + 11, 6, 3), border_radius=1)
        else:
            # coiled dashes
            for lx in [x + 4, x + w - 10]:
                for row in range(3):
                    pygame.draw.rect(surface, spring_col,
                                     pygame.Rect(lx, y + h - 6 + row * 2, 6, 1))

        # visor slit
        visor = pygame.Rect(x + 4, y + h // 3 - 2, w - 8, 6)
        pygame.draw.rect(surface, (0, 30, 40), visor, border_radius=2)
        pygame.draw.rect(surface, (0, 255, 220),
                         pygame.Rect(x + 4, y + h // 3 - 1, w - 8, 2), border_radius=1)

        # antenna
        pygame.draw.line(surface, (0, 160, 160),
                         (cx, y), (cx, y - 8), 2)
        pygame.draw.circle(surface, (80, 255, 220), (cx, y - 9), 3)

    # ---- HUNTER --------------------------------------------------------
    def _draw_hunter(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        pygame.draw.rect(surface, (130, 30, 120), sr, border_radius=7)
        pygame.draw.rect(surface, (255, 70, 210), pygame.Rect(x + 5, y + 7, w - 10, 7), border_radius=2)
        pygame.draw.circle(surface, (255, 120, 230), (cx, cy), 8, 2)
        pygame.draw.line(surface, (255, 70, 210), (cx - 14, cy + 11), (cx + 14, cy + 11), 3)

        pulse = int(4 + 2 * math.sin(self._anim * 5))
        pygame.draw.circle(surface, (255, 70, 210), (cx, cy), w // 2 + pulse, 1)

    # ---- BRUTE ---------------------------------------------------------
    def _draw_brute(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        charging = self.leap_timer > 0 or self.windup_action == "brute_charge"
        body_col = (120, 95, 55) if not charging else (210, 145, 55)
        plate_col = (210, 175, 90)
        pygame.draw.rect(surface, body_col, sr, border_radius=5)
        pygame.draw.rect(surface, plate_col, pygame.Rect(x + 5, y + 5, w - 10, 10), border_radius=2)
        pygame.draw.rect(surface, (75, 50, 30), pygame.Rect(x + 8, y + h - 13, w - 16, 8), border_radius=2)
        pygame.draw.circle(surface, (255, 230, 120), (cx - 9, y + 23), 4)
        pygame.draw.circle(surface, (255, 230, 120), (cx + 9, y + 23), 4)
        if charging:
            pygame.draw.circle(surface, (255, 170, 60), (cx, cy), w // 2 + 6, 3)

    # ---- ELITE ---------------------------------------------------------
    def _draw_elite(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        # armoured body – pink/magenta with plates
        pygame.draw.rect(surface, (180, 50, 120), sr, border_radius=6)

        # shoulder armour plates
        plate_h = h // 3
        for px in [x - 6, x + w]:
            pygame.draw.rect(surface, (210, 80, 150),
                             pygame.Rect(px, y + 4, 8, plate_h), border_radius=3)

        # chest cross detail
        pygame.draw.line(surface, (220, 120, 180), (cx, y + 6), (cx, y + h - 6), 2)
        pygame.draw.line(surface, (220, 120, 180), (x + 6, cy), (x + w - 6, cy), 2)

        # visor - T shape
        pygame.draw.rect(surface, (40, 0, 30),
                         pygame.Rect(x + 8, y + 10, w - 16, 8), border_radius=2)
        pygame.draw.rect(surface, (255, 100, 200),
                         pygame.Rect(x + 8, y + 11, w - 16, 3), border_radius=1)

        # knee guards
        for kx in [x + 5, x + w - 13]:
            pygame.draw.rect(surface, (210, 80, 150),
                             pygame.Rect(kx, y + h - 8, 8, 6), border_radius=2)

    # ---- LOOT ---------------------------------------------------------
    def _draw_loot(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        pulse = int(3 + 2 * math.sin(self._anim * 9))
        pygame.draw.circle(surface, (100, 70, 10), (cx, cy), w // 2 + 8 + pulse, 2)
        pygame.draw.rect(surface, GOLD, sr, border_radius=8)
        pygame.draw.rect(surface, (110, 70, 10), pygame.Rect(x + 5, y + 7, w - 10, h - 12), border_radius=5)
        pygame.draw.circle(surface, YELLOW, (cx - 7, cy - 2), 4)
        pygame.draw.circle(surface, YELLOW, (cx + 7, cy - 2), 4)
        pygame.draw.rect(surface, (255, 235, 120), pygame.Rect(x + 7, y + h - 10, w - 14, 4), border_radius=2)

    # ---- BOSS ----------------------------------------------------------
    def _draw_boss(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        rage = self.phase == 3

        body_col   = (200, 80, 10) if not rage else (220, 40, 40)
        accent_col = (240, 120, 30) if not rage else (255, 80, 20)
        eye_col    = (255, 60, 0)  if not rage else (255, 0, 0)

        # phase glow ring
        phase_label_text = "PHASE 1" if self.phase == 1 else ("PHASE 2" if self.phase == 2 else "RAGE")
        phase_label_color = (80, 180, 255) if self.phase == 1 else ((255, 170, 40) if self.phase == 2 else (255, 60, 60))

        if self.phase == 1:
            pygame.draw.circle(surface, (80, 180, 255), (cx, cy), w // 2 + 10, 3)
        elif self.phase == 2:
            pygame.draw.circle(surface, (255, 170, 40), (cx, cy), w // 2 + 8, 4)
            pygame.draw.circle(surface, (255, 110, 20), (cx, cy), w // 2 + 16, 2)
        elif rage:
            pulse = int(3 + 2 * math.sin(self._anim * 6))
            pygame.draw.circle(surface, (255, 60, 60), (cx, cy), w // 2 + pulse, 4)

        phase_font = pygame.font.SysFont("Arial", 15, bold=True)
        phase_shadow = phase_font.render(phase_label_text, True, (0, 0, 0))
        phase_label = phase_font.render(phase_label_text, True, phase_label_color)
        phase_pos = phase_label.get_rect(center=(cx, y - 18))
        surface.blit(phase_shadow, (phase_pos.x + 1, phase_pos.y + 1))
        surface.blit(phase_label, phase_pos)

        # massive body
        pygame.draw.rect(surface, body_col, sr, border_radius=8)

        # shoulder pauldrons
        p_w, p_h = w // 4, h // 5
        pygame.draw.rect(surface, accent_col,
                         pygame.Rect(x - p_w + 2, y + 8, p_w, p_h), border_radius=4)
        pygame.draw.rect(surface, accent_col,
                         pygame.Rect(x + w - 4,   y + 8, p_w, p_h), border_radius=4)

        # armour chest plate
        chest = pygame.Rect(x + w // 5, y + h // 4, w * 3 // 5, h // 2)
        pygame.draw.rect(surface, accent_col, chest, border_radius=4)

        # chest rune lines
        pygame.draw.line(surface, body_col, (cx, chest.top + 4), (cx, chest.bottom - 4), 2)
        pygame.draw.line(surface, body_col,
                         (chest.left + 4, cy - 2), (chest.right - 4, cy - 2), 2)

        # crown spikes on top
        n_spikes = 5
        spike_base_y = y
        for i in range(n_spikes):
            sx = x + (w // (n_spikes + 1)) * (i + 1)
            spike_h = 14 if i % 2 == 0 else 9
            pygame.draw.polygon(surface, accent_col, [
                (sx - 5, spike_base_y),
                (sx,     spike_base_y - spike_h),
                (sx + 5, spike_base_y),
            ])

        # glowing rectangular eyes
        eye_h, eye_w = h // 8, w // 5
        eye_y = y + h // 5
        for ex in [x + w // 5, x + w - w // 5 - eye_w]:
            pygame.draw.rect(surface, (40, 0, 0),
                             pygame.Rect(ex - 1, eye_y - 1, eye_w + 2, eye_h + 2),
                             border_radius=2)
            pygame.draw.rect(surface, eye_col,
                             pygame.Rect(ex, eye_y, eye_w, eye_h), border_radius=2)
            # inner glow
            pygame.draw.rect(surface, (255, 180, 100),
                             pygame.Rect(ex + 2, eye_y + 2, eye_w - 4, eye_h - 4),
                             border_radius=1)

        # heavy legs
        leg_w = w // 4
        for lx in [x + 4, x + w - leg_w - 4]:
            pygame.draw.rect(surface, (160, 60, 5),
                             pygame.Rect(lx, y + h - 2, leg_w, h // 4 + 4), border_radius=4)

        # scar / battle damage detail
        pygame.draw.line(surface, (100, 20, 0),
                         (cx - 8, y + h // 5 - 4), (cx - 2, y + h // 5 + 8), 2)

        # phase 1 shield bar (drawn separately in _draw_health_bar)
        # rage aura particles
        if rage:
            t = self._anim
            for i in range(4):
                angle = t * 2.5 + i * (math.pi / 2)
                px = cx + int(math.cos(angle) * (w // 2 + 16))
                py = cy + int(math.sin(angle) * (h // 2 + 16))
                pygame.draw.circle(surface, (255, 80, 20), (px, py), 4)

    # ---- health bar ---------------------------------------------------
    def _draw_health_bar(self, surface, camera):
        bar_w = self.rect.width
        ratio = max(0, self.health / self.max_health)

        bg = pygame.Rect(self.rect.x, self.rect.y - 9, bar_w, 5)
        fg = pygame.Rect(self.rect.x, self.rect.y - 9, int(bar_w * ratio), 5)

        pygame.draw.rect(surface, (60, 0, 0),    camera.apply_rect(bg))
        pygame.draw.rect(surface, (220, 60, 60), camera.apply_rect(fg))

        # boss shield bar
        if self.type == EnemyType.BOSS and self.phase == 1:
            sh_ratio = max(0, self.shield / self.max_shield)
            sh_bg = pygame.Rect(self.rect.x, self.rect.y - 17, bar_w, 5)
            sh_fg = pygame.Rect(self.rect.x, self.rect.y - 17, int(bar_w * sh_ratio), 5)
            pygame.draw.rect(surface, (20, 60, 100),  camera.apply_rect(sh_bg))
            pygame.draw.rect(surface, (80, 180, 255), camera.apply_rect(sh_fg))

    # ---- windup indicator ---------------------------------------------
    def _draw_windup_indicator(self, surface, camera):
        if self.windup_timer <= 0 or self.windup_direction.length_squared() == 0:
            return

        start  = camera.apply_pos(pygame.Vector2(self.rect.center))
        action = self.windup_action or ""

        if "ring" in action:
            pygame.draw.circle(surface, (255, 120, 40),
                               (round(start.x), round(start.y)), 120, 3)

        elif "summon" in action:
            end = start + self.windup_direction * 290
            pygame.draw.line(surface, (255, 120, 40), start, end, 8)
            pygame.draw.circle(surface, (255, 120, 40),
                               (round(start.x), round(start.y)), 30, 2)

        else:
            length = 650 if self.type == EnemyType.BOSS else 520
            width  = 7 if self.type in (EnemyType.BOSS, EnemyType.ELITE) else 3
            end    = start + self.windup_direction * length
            pygame.draw.line(surface, (255, 120, 40), start, end, width)
            pygame.draw.circle(surface, (255, 120, 40),
                               (round(start.x), round(start.y)), 20, 2)
