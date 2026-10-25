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
    GOLD,
    YELLOW,
)
from systems.asset_loader import load_image, load_sheet_frames
from systems.object_catalog import sprite as visual_sprite, definition as visual_definition
from systems.room_bounds import current_room_bounds, current_room_rect

CHASER_BURST_MIN_DISTANCE = 150
CHASER_BURST_MAX_DISTANCE = 560
CHASER_BURST_THRESHOLD = 1.15
CHASER_BURST_DURATION = 0.42
CHASER_BURST_COOLDOWN = 2.05
CHASER_BURST_SPEED_MULTIPLIER = 1.42


class EnemyType(Enum):
    CHASER  = auto()
    CHASER_FAST = auto()
    CHASER_TANK = auto()
    RANGED  = auto()
    RANGED_THREE = auto()
    RANGED_FIVE = auto()
    RANGED_RAIN = auto()
    JUMPER  = auto()
    JUMPER_FAST = auto()
    JUMPER_HEAVY = auto()
    HUNTER  = auto()
    BRUTE   = auto()
    ELITE   = auto()
    BOSS    = auto()
    LOOT    = auto()


class Enemy:
    _chaser_idle_image = None
    _chaser_walk_frames = None

    _ranged_idle_image = None
    _ranged_body_frames = None
    _ranged_weapon_frames = None
    _phase_font = None

    def __init__(self, x, y, enemy_type=EnemyType.CHASER, difficulty=1.0):
        self.is_boss_eye = False
        self.is_boss_guard = False
        self.guardian_owner_id = None
        self.encounter = None
        self.type = enemy_type
        self.difficulty = max(1.0, difficulty)
        self.health_scale = self.difficulty ** 1.45
        self.speed_scale = min(1.55, 0.85 + self.difficulty * 0.14)
        self.damage_multiplier = min(3.8, 1.0 + self.difficulty * 0.28)
        self.attack_speed_multiplier = min(2.80, 1.0 + self.difficulty * 0.22)

        ranged_types = (EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.RANGED_FIVE, EnemyType.RANGED_RAIN)
        jumper_types = (EnemyType.JUMPER, EnemyType.JUMPER_FAST, EnemyType.JUMPER_HEAVY)

        if self.type == EnemyType.LOOT:
            self.rect       = pygame.Rect(x, y, 48, 54)
            self.speed      = ENEMY_SPEED * 2.15
            self.max_health = int(ENEMY_HEALTH * 4.1)
            self.damage_multiplier = 0.0

        elif self.type == EnemyType.BOSS:
            self.phase       = 1
            self.max_shield  = int(650 + BOSS_HEALTH * (0.25 + self.difficulty * 0.32))
            self.shield      = self.max_shield
            self.rage        = False
            self.rect        = pygame.Rect(x, y, 104, 112)
            self.speed       = BOSS_SPEED * min(2.35, 1.0 + self.difficulty * 0.13)
            self.max_health  = int(BOSS_HEALTH * (2.35 + self.difficulty * 1.85))

        elif self.type == EnemyType.ELITE:
            self.rect       = pygame.Rect(x, y, 70, 80)
            self.speed      = ENEMY_SPEED * 0.82 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 4.9)

        elif self.type == EnemyType.HUNTER:
            self.rect       = pygame.Rect(x, y, 50, 60)
            self.speed      = ENEMY_SPEED * 1.18 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 1.15)

        elif self.type == EnemyType.BRUTE:
            self.rect       = pygame.Rect(x, y, 66, 76)
            self.speed      = ENEMY_SPEED * 0.95 * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale * 2.4)
            self.damage_multiplier *= 1.25

        else:
            self.rect      = pygame.Rect(x, y, 46, 56)
            base_speed     = ENEMY_SPEED

            if self.type in ranged_types:
                base_speed *= 0.72
            elif self.type in jumper_types:
                base_speed *= 0.88
            elif self.type == EnemyType.CHASER_FAST:
                base_speed *= 1.28
            elif self.type == EnemyType.CHASER_TANK:
                base_speed *= 0.78

            self.speed      = base_speed * self.speed_scale
            self.max_health = int(ENEMY_HEALTH * self.health_scale)

            if self.type in ranged_types:
                ranged_health = {
                    EnemyType.RANGED: 0.76,
                    EnemyType.RANGED_THREE: 0.86,
                    EnemyType.RANGED_FIVE: 0.98,
                    EnemyType.RANGED_RAIN: 1.10,
                }[self.type]
                self.max_health = int(self.max_health * ranged_health)
            elif self.type in jumper_types:
                jumper_health = {
                    EnemyType.JUMPER: 1.25,
                    EnemyType.JUMPER_FAST: 1.05,
                    EnemyType.JUMPER_HEAVY: 1.65,
                }[self.type]
                self.max_health = int(self.max_health * jumper_health)
            elif self.type == EnemyType.CHASER_FAST:
                self.max_health = int(self.max_health * 0.78)
            elif self.type == EnemyType.CHASER_TANK:
                self.max_health = int(self.max_health * 1.65)
                self.damage_multiplier *= 1.12

        self.health    = self.max_health
        self.alive     = True
        self.hit_flash = 0.0
        self.knockback_timer = 0.0

        self.attack_cooldown  = 1.0
        self.windup_timer     = 0.0
        self.windup_direction = pygame.Vector2(0, 0)
        self.windup_action    = None
        self.ranged_windup_total = 0.0
        self.ranged_release_timer = 0.0

        self.leap_timer    = 0.0
        self.leap_velocity = pygame.Vector2(0, 0)
        self.jumper_windup_total = 0.
        self.jumper_flight_total = 0.
        self.jumper_landing_timer = 0.
        self.brute_windup_total = 0.
        self.brute_stop_timer = 0.
        self.brute_stride = 0.
        self.brute_moving = False
        self.brute_slam_pending = 0.
        self.champion_block_timer = 0.
        self.last_damage = 0
        self.champion_owner = None
        self.escort_spawned = False
        self.escort_guards = []
        self.escort_had_guards = False
        self.escort_broken = False
        self.elite_state = 'chase'
        self.elite_timer = 0.
        self.elite_move_remaining = 0.
        self.visual_stride = 0.
        self.visual_moving = False
        self.visual_windup_total = 0.
        self.visual_release_timer = 0.

        self.boss_attack_index = 0
        self.elite_attack_index = 0
        self.last_player_center = None
        self.estimated_player_velocity = pygame.Vector2(0, 0)
        self.anti_kite_timer = 0.0
        self.chase_pressure_timer = 0.0
        self.chaser_burst_timer = 0.0
        self.chaser_burst_cooldown = 0.35 + ((int(x) + int(y)) % 7) * 0.11
        self.path_commit_timer = 0.0
        self.path_commit_direction = pygame.Vector2(0, 0)

        # animation tick (used for oscillating effects)
        self._anim = 0.0
        if self.type == EnemyType.BOSS:
            from systems.boss_encounter import BossEncounter
            self.encounter = BossEncounter(self)

        if Enemy._chaser_idle_image is None:
            Enemy._chaser_idle_image = load_image("enamyIdle.png", size=(36, 36))
        if Enemy._chaser_walk_frames is None:
            Enemy._chaser_walk_frames = load_sheet_frames("enamy1.png", (32, 32), scale=(36, 36))
            
        if Enemy._ranged_body_frames is None:
            Enemy._ranged_body_frames = load_sheet_frames("enamyRange.png", (64, 64), scale=(42, 42))
        if Enemy._ranged_idle_image is None and Enemy._ranged_body_frames:
            Enemy._ranged_idle_image = Enemy._ranged_body_frames[0]
        if Enemy._ranged_weapon_frames is None:
            Enemy._ranged_weapon_frames = load_sheet_frames("enamyRangeWepaon.png", (64, 64), scale=(32, 32))

    # ------------------------------------------------------------------ #
    #  UPDATE LOGIC  (unchanged from original)                            #
    # ------------------------------------------------------------------ #

    def update(self, dt, player_rect, solid_rects=None):
        self.solid_rects = solid_rects or ()
        self.player_rect = player_rect
        if not self.alive:
            return None

        self._anim += dt
        self.ranged_release_timer = max(0., self.ranged_release_timer-dt)
        self.jumper_landing_timer = max(0., self.jumper_landing_timer-dt)
        self.brute_stop_timer = max(0., self.brute_stop_timer-dt)
        self.champion_block_timer = max(0., self.champion_block_timer-dt)
        self.brute_moving = False
        self.visual_release_timer=max(0.,self.visual_release_timer-dt)
        self.visual_moving=False

        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt)
        if self.knockback_timer > 0:
            self.knockback_timer = max(0, self.knockback_timer - dt)
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if self.anti_kite_timer > 0:
            self.anti_kite_timer = max(0, self.anti_kite_timer - dt)
        if self.chaser_burst_timer > 0:
            self.chaser_burst_timer = max(0, self.chaser_burst_timer - dt)
        if self.chaser_burst_cooldown > 0:
            self.chaser_burst_cooldown = max(0, self.chaser_burst_cooldown - dt)
        if self.path_commit_timer > 0:
            self.path_commit_timer = max(0, self.path_commit_timer - dt)

        if self.is_boss_eye:
            return None
        if self.encounter is not None:
            return self.encounter.update(dt, player_rect)

        if self.type == EnemyType.ELITE:
            from systems.champion_encounters import update_elite
            return update_elite(self, dt, player_rect)
        if self.brute_slam_pending > 0:
            self.brute_slam_pending = max(0., self.brute_slam_pending-dt)
            if self.brute_slam_pending == 0:
                return {'type': 'champion_slam', 'enemy': self, 'radius': 110}
            return None
        if self.type == EnemyType.BRUTE and self.brute_stop_timer > 0:
            return None

        if self.windup_timer > 0:
            self.windup_timer = max(0, self.windup_timer - dt)
            if self.windup_timer <= 0:
                return self._finish_windup()
            return None

        if self.leap_timer > 0:
            old_rect = self.rect.copy()
            self.leap_timer = max(0, self.leap_timer - dt)
            self._move_vector(self.leap_velocity * dt, ignore_solids=self.type != EnemyType.BRUTE)
            self.rect.clamp_ip(current_room_rect())
            if self.leap_timer <= 0:
                self._resolve_leap_landing(old_rect)
                from systems.jumper_presentation import is_jumper
                if is_jumper(self):
                    self.jumper_landing_timer = .22
                elif self.type == EnemyType.BRUTE:
                    self.brute_stop_timer = 1.15
                    self.brute_slam_pending = .28
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

        ranged_types = (EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.RANGED_FIVE, EnemyType.RANGED_RAIN)
        jumper_types = (EnemyType.JUMPER, EnemyType.JUMPER_FAST, EnemyType.JUMPER_HEAVY)

        if self.type == EnemyType.LOOT:
            self._update_loot(distance, direction, dt)
        elif self.type in (EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.RANGED_FIVE, EnemyType.RANGED_RAIN):
            self._update_ranged(distance, direction, dt)
        elif self.type in (EnemyType.JUMPER, EnemyType.JUMPER_FAST, EnemyType.JUMPER_HEAVY):
            self._update_jumper(distance, direction, dt)
        elif self.type == EnemyType.HUNTER:
            self._update_hunter(distance, direction, dt)
        elif self.type == EnemyType.BRUTE:
            self._update_brute(distance, direction, dt)
        elif self.type == EnemyType.ELITE:
            self._update_elite(distance, direction, dt)
        elif self.type == EnemyType.BOSS:
            self._update_boss(distance, direction, dt)
        elif self.type == EnemyType.CHASER:
            self._update_chaser(distance, direction, dt)
        else:
            self._move(direction, dt)

        return None

    def _start_windup(self, seconds, direction, action):
        self.visual_windup_total = seconds
        self.visual_release_timer = 0.
        self.windup_timer     = seconds
        self.windup_direction = direction.copy()
        self.windup_action    = action
        if action == 'enemy_jump':
            self.jumper_windup_total = seconds
        if action == 'brute_charge':
            self.brute_windup_total = seconds
            self.brute_stop_timer = 0.
        if action in ('enemy_shoot', 'enemy_rain'):
            self.ranged_windup_total = seconds
            self.ranged_release_timer = 0.

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
        bounds = current_room_bounds()
        center_pull = pygame.Vector2(bounds.centerx - self.rect.centerx, bounds.centery - self.rect.centery)
        flee = -direction if distance > 0 else pygame.Vector2(1, 0).rotate(self._anim * 90)
        side = pygame.Vector2(-direction.y, direction.x) if distance > 0 else pygame.Vector2(0, 1)
        weave = side * math.sin(self._anim * 5.2) * 0.85
        edge_pull = pygame.Vector2(0, 0)
        edge_margin = 260
        if (
            self.rect.left < bounds.left + edge_margin
            or self.rect.right > bounds.right - edge_margin
            or self.rect.top < bounds.top + edge_margin
            or self.rect.bottom > bounds.bottom - edge_margin
        ):
            if center_pull.length_squared() > 0:
                edge_pull = center_pull.normalize() * 1.25
        panic = 1.22 if distance < 230 else 1.0
        move_dir = flee * panic + weave + edge_pull
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)
            self.rect.clamp_ip(current_room_rect())

    def _update_chaser(self, distance, direction, dt):
        if distance <= 0:
            return

        if self.chaser_burst_timer > 0:
            if not self._has_line_of_sight():
                self.chaser_burst_timer = 0.0
                self.chase_pressure_timer = 0.0
                self._move(self._obstacle_seek_direction(direction), dt)
                return
            old_speed = self.speed
            self.speed *= CHASER_BURST_SPEED_MULTIPLIER
            self._move(direction, dt)
            self.speed = old_speed
            return

        has_sight = self._has_line_of_sight()
        can_pressure = CHASER_BURST_MIN_DISTANCE < distance < CHASER_BURST_MAX_DISTANCE and has_sight
        if can_pressure:
            self.chase_pressure_timer += dt
        else:
            self.chase_pressure_timer = max(0.0, self.chase_pressure_timer - dt * 1.5)

        if (
            can_pressure
            and self.chase_pressure_timer >= CHASER_BURST_THRESHOLD
            and self.chaser_burst_cooldown <= 0
        ):
            self.chase_pressure_timer = 0.0
            self.chaser_burst_timer = CHASER_BURST_DURATION
            self.chaser_burst_cooldown = CHASER_BURST_COOLDOWN + ((self.rect.centerx + self.rect.centery) % 5) * 0.08

        self._move(direction if has_sight else self._obstacle_seek_direction(direction), dt)

    def _update_ranged(self, distance, direction, dt):
        has_sight = self._has_line_of_sight()
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0 and has_sight:
            if self.type == EnemyType.RANGED_RAIN:
                aim = self._predictive_direction(0.45, 40)
                self._start_windup(max(0.35, RANGED_WINDUP_TIME * 0.70), aim, "enemy_rain")
                self.attack_cooldown = max(1.05, RANGED_ATTACK_COOLDOWN * 0.92 / self.attack_speed_multiplier)
            else:
                aim = self._predictive_direction(0.72, 120)
                self._start_windup(max(0.24, RANGED_WINDUP_TIME * 0.55), aim, "enemy_shoot")
                cooldown_scale = 0.64 if self.type == EnemyType.RANGED else (0.70 if self.type == EnemyType.RANGED_THREE else 0.78)
                self.attack_cooldown = max(0.42, RANGED_ATTACK_COOLDOWN * cooldown_scale / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 2.3) * 0.75
        if not has_sight:
            move_dir = self._obstacle_seek_direction(direction)
        elif distance < 115:
            move_dir = -direction + strafe * 0.35
        elif distance > 285:
            move_dir = direction + strafe * 0.35
        else:
            move_dir = direction * 0.38 + strafe
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)

    def _update_jumper(self, distance, direction, dt):
        attack_range = JUMPER_ATTACK_RANGE + (60 if self.type == EnemyType.JUMPER_HEAVY else 0)
        if distance <= attack_range and self.attack_cooldown <= 0:
            aim = self._predictive_direction(0.48, 80)
            self._start_windup(max(0.24, JUMPER_WINDUP_TIME * (0.48 if self.type == EnemyType.JUMPER_FAST else 0.68 if self.type == EnemyType.JUMPER_HEAVY else 0.58)), aim, "enemy_jump")
            cooldown_scale = 0.50 if self.type == EnemyType.JUMPER_FAST else (0.82 if self.type == EnemyType.JUMPER_HEAVY else 0.62)
            self.attack_cooldown = max(0.78, JUMPER_ATTACK_COOLDOWN * cooldown_scale / self.attack_speed_multiplier)
            return
        self._move(direction, dt)

    def _update_hunter(self, distance, direction, dt):
        has_sight = self._has_line_of_sight()
        if distance <= RANGED_ATTACK_RANGE + 170 and self.attack_cooldown <= 0 and has_sight:
            aim = self._predictive_direction(0.82, 110)
            self._start_windup(0.32, aim, "hunter_homing")
            self.attack_cooldown = max(0.78, 1.15 / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.cos(self._anim * 2.8) * 0.85
        if not has_sight:
            move_dir = self._obstacle_seek_direction(direction)
        elif distance < 105:
            move_dir = -direction + strafe * 0.4
        elif distance > 230:
            move_dir = direction + strafe * 0.25
        else:
            move_dir = direction * 0.45 + strafe
        if move_dir.length_squared() > 0:
            self._move(move_dir.normalize(), dt)

    def _update_brute(self, distance, direction, dt):
        has_sight = self._has_line_of_sight()
        if distance <= 340 and self.attack_cooldown <= 0 and has_sight:
            aim = self._predictive_direction(0.42, 55)
            self._start_windup(0.46, aim, "brute_charge")
            self.attack_cooldown = max(1.05, 1.95 / self.attack_speed_multiplier)
            return
        if distance > 95:
            flank = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 1.7) * 0.45
            move_dir = (direction if has_sight else self._obstacle_seek_direction(direction)) + flank
            if move_dir.length_squared() > 0:
                move_dir = move_dir.normalize()
            self._move(move_dir, dt)

    def _update_elite(self, distance, direction, dt):
        has_sight = self._has_line_of_sight()
        if distance <= RANGED_ATTACK_RANGE and self.attack_cooldown <= 0 and has_sight:
            attacks = ["elite_cross", "elite_burst", "elite_laser", "enemy_jump"]
            action = attacks[self.elite_attack_index % len(attacks)]
            self.elite_attack_index += 1
            aim = self._predictive_direction(0.65, 90)
            windup = 0.52 if action == "elite_cross" else (0.82 if action == "elite_laser" else 0.68)
            self._start_windup(windup, aim, action)
            self.attack_cooldown = max(1.05, 2.25 / self.attack_speed_multiplier)
            return

        strafe = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 1.9) * 0.5
        if not has_sight:
            move_dir = self._obstacle_seek_direction(direction)
        elif distance > 145:
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
                attacks = ["boss_cone", "boss_ring", "boss_laser"]
            elif self.phase == 2:
                attacks = ["boss_cone", "boss_ring", "boss_summon_leap", "boss_laser"]
            else:
                attacks = ["boss_ring", "boss_laser", "boss_cone", "boss_summon_leap"]

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
            pressure = 1.0
            if distance > 560:
                pressure = 1.35 if self.phase == 1 else 1.62
            flank = pygame.Vector2(-direction.y, direction.x) * math.sin(self._anim * 2.1) * 0.28
            move_dir = direction + flank
            if move_dir.length_squared() > 0:
                old_speed = self.speed
                self.speed *= pressure
                self._move(move_dir.normalize(), dt)
                self.speed = old_speed
        elif distance < 150:
            self._move(-direction, dt)

    def _finish_windup(self):
        action            = self.windup_action
        self.windup_action = None
        if action and self.type.name in ('HUNTER','ELITE','BOSS'):
            self.visual_release_timer=.24
        if action in ('enemy_shoot', 'enemy_rain'):
            from systems.ranged_presentation import RELEASE_SECONDS, RECOVERY_SECONDS
            self.ranged_release_timer = RELEASE_SECONDS + RECOVERY_SECONDS

        if action == "enemy_jump":
            jump_speed = 820 * min(1.9, self.speed_scale / 1.32)
            if self.type == EnemyType.JUMPER_FAST:
                jump_speed *= 1.20
            elif self.type == EnemyType.JUMPER_HEAVY:
                jump_speed *= 0.92
            self.leap_timer = JUMPER_LEAP_TIME * (0.88 if self.type == EnemyType.JUMPER_FAST else 1.15 if self.type == EnemyType.JUMPER_HEAVY else 1.0)
            self.leap_velocity = self.windup_direction * jump_speed
            self.jumper_flight_total = self.leap_timer
            return {"type": "enemy_jump"}

        if action == "brute_charge":
            if not self._has_line_of_sight():
                self.attack_cooldown = min(self.attack_cooldown, 0.35)
                return None
            self.leap_timer = 0.42
            self.leap_velocity = self.windup_direction * 720
            return {"type": "brute_charge"}

        if action == "enemy_rain":
            target = self.last_player_center or pygame.Vector2(self.rect.center)
            return {
                "type": "enemy_rain",
                "x": self.rect.centerx,
                "y": self.rect.centery,
                "target_x": target.x,
                "target_y": target.y,
                "direction": self.windup_direction.copy(),
                "difficulty": self.difficulty,
                "damage_multiplier": self.damage_multiplier,
                "owner_id": id(self),
            }

        shot_count = {
            EnemyType.RANGED: 2,
            EnemyType.RANGED_THREE: 3,
            EnemyType.RANGED_FIVE: 5,
        }.get(self.type, 1)

        return {
            "type":      action,
            "x":         self.rect.centerx,
            "y":         self.rect.centery,
            "direction": self.windup_direction.copy(),
            "phase":     self.phase if self.type == EnemyType.BOSS else 1,
            "difficulty": self.difficulty,
            "damage_multiplier": self.damage_multiplier,
            "owner_id": id(self),
            "shot_count": shot_count,
        }

    def _move(self, direction, dt):
        if direction.x != 0:
            self.facing_left = direction.x < 0
        blocked = self._move_vector(direction * self.speed * dt)
        if blocked and direction.length_squared() > 0:
            self.path_commit_timer = 0.0
            side = pygame.Vector2(-direction.y, direction.x)
            if math.sin(self._anim * 3.0 + self.rect.centerx * 0.01) < 0:
                side = -side
            self._move_vector(side * self.speed * dt * 0.85)

    def _move_vector(self, movement, ignore_solids=False):
        previous_center=self.rect.center
        dx = round(movement.x)
        dy = round(movement.y)
        solid_rects = () if ignore_solids else getattr(self, "solid_rects", ())
        blocked = False
        self.rect.x += dx
        for solid in solid_rects:
            if self.rect.colliderect(solid):
                blocked = True
                if dx > 0:
                    self.rect.right = solid.left
                elif dx < 0:
                    self.rect.left = solid.right
        self.rect.y += dy
        for solid in solid_rects:
            if self.rect.colliderect(solid):
                blocked = True
                if dy > 0:
                    self.rect.bottom = solid.top
                elif dy < 0:
                    self.rect.top = solid.bottom
        distance=pygame.Vector2(self.rect.center).distance_to(previous_center)
        self.visual_stride+=distance*.12
        self.visual_moving=self.visual_moving or distance>0
        if self.type == EnemyType.BRUTE:
            self.brute_stride+=distance*.12
            self.brute_moving=self.brute_moving or distance>0
        return blocked

    def _collides_solid(self, rect):
        return any(rect.colliderect(solid) for solid in getattr(self, "solid_rects", ()))

    def _resolve_leap_landing(self, fallback_rect):
        if not self._collides_solid(self.rect):
            return
        intended = pygame.Vector2(self.rect.center)
        bounds = current_room_rect()
        candidates = [fallback_rect.copy()]
        for solid in getattr(self, "solid_rects", ()):
            if not self.rect.colliderect(solid.inflate(2, 2)):
                continue
            for center in (
                (solid.left - self.rect.width // 2 - 2, intended.y),
                (solid.right + self.rect.width // 2 + 2, intended.y),
                (intended.x, solid.top - self.rect.height // 2 - 2),
                (intended.x, solid.bottom + self.rect.height // 2 + 2),
            ):
                candidate = self.rect.copy()
                candidate.center = (round(center[0]), round(center[1]))
                candidate.clamp_ip(bounds)
                candidates.append(candidate)
        valid = [candidate for candidate in candidates if not self._collides_solid(candidate)]
        if valid:
            self.rect = min(valid, key=lambda rect: pygame.Vector2(rect.center).distance_squared_to(intended))
        else:
            self.rect = fallback_rect.copy()
        self.leap_velocity = pygame.Vector2(0, 0)

    def _has_line_of_sight(self):
        player_rect = getattr(self, "player_rect", None)
        if player_rect is None:
            return True
        start = pygame.Vector2(self.rect.center)
        end = pygame.Vector2(player_rect.center)
        for solid in getattr(self, "solid_rects", ()):
            if solid.clipline(start, end):
                return False
        return True

    def _obstacle_seek_direction(self, direction):
        if direction.length_squared() == 0:
            return direction
        if self.path_commit_timer > 0 and self.path_commit_direction.length_squared() > 0:
            return self.path_commit_direction
        side = pygame.Vector2(-direction.y, direction.x)
        if abs(direction.x) > abs(direction.y):
            side *= 1 if (self.rect.centery % 2 == 0) else -1
        else:
            side *= 1 if (self.rect.centerx % 2 == 0) else -1
        committed = (direction * 0.45 + side * 0.95).normalize()
        self.path_commit_direction = committed
        self.path_commit_timer = 0.55
        return committed

    def take_damage(self, amount, reflected=False):
        if self.encounter is not None:
            return self.encounter.damage(amount, reflected=reflected)
        if self.type == EnemyType.BRUTE and not (self.windup_action == 'brute_charge' or self.brute_stop_timer > 0):
            self.last_damage = 0
            self.champion_block_timer = .16
            return False
        if self.type == EnemyType.ELITE:
            from systems.champion_encounters import guards_alive
            if guards_alive(self):
                amount *= .25
        self.last_damage = max(0, amount)
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
        if self.encounter is not None:
            self.encounter.draw(surface,camera)
        key = 'boss_healing_eye' if self.is_boss_eye else 'enemy_' + self.type.name.lower()
        if self.type == EnemyType.BOSS and self.phase > 1:
            key = 'enemy_boss_phase_' + str(self.phase)
        art = visual_sprite(key, frame=int(self._anim*visual_definition(key)['fps']))
        if art is not None:
            sr = camera.apply_rect(self.rect)
            shadow = pygame.Rect(0,0,max(16,sr.width),max(5,sr.height//5))
            shadow.center = (sr.centerx,sr.bottom)
            pygame.draw.ellipse(surface,(4,7,12),shadow)
            if self.encounter is not None:
                sr.y-=round(self.encounter.lift)
            # The new authored enemy sprites face left, like the legacy set.
            from systems.ranged_presentation import is_ranged, pose as ranged_pose, draw_cast
            ranged = is_ranged(self)
            from systems.jumper_presentation import is_jumper, pose as jumper_pose, draw_ground
            jumper = is_jumper(self)
            if jumper:
                draw_ground(surface,sr.center,self)
            brute = self.type == EnemyType.BRUTE
            if brute:
                from systems.brute_presentation import pose as brute_pose, draw_ground as brute_ground
                brute_ground(surface,sr.center,self)
            facing_left = getattr(self,'facing_left',False)
            if ranged and (self.windup_timer > 0 or self.ranged_release_timer > 0) and abs(self.windup_direction.x)>.1:
                facing_left=self.windup_direction.x<0
            if jumper and abs(self.windup_direction.x)>.1 and (self.windup_timer>0 or self.leap_timer>0):
                facing_left=self.windup_direction.x<0
            if brute and abs(self.windup_direction.x)>.1 and (self.windup_timer>0 or self.leap_timer>0):
                facing_left=self.windup_direction.x<0
            if self.type.name in ('HUNTER','ELITE','BOSS') and abs(self.windup_direction.x)>.1 and (self.windup_timer>0 or self.visual_release_timer>0):
                facing_left=self.windup_direction.x<0
            if not facing_left:
                art = pygame.transform.flip(art,True,False)
            if self.hit_flash > 0:
                art = art.copy()
                art.fill((145,145,145,0),special_flags=pygame.BLEND_RGB_ADD)
            offset = (0, 0)
            if self.type == EnemyType.CHASER:
                from systems.chaser_presentation import pose
                art, offset, _ = pose(self, art)
            if ranged:
                art, offset, cast_state, progress, aim = ranged_pose(self, art)
            if jumper:
                art, offset, _ = jumper_pose(self,art)
            if brute:
                art, offset, _ = brute_pose(self,art)
            from systems.actor_presentation import REMAINING, enemy_pose
            if self.type.name in REMAINING:
                art, offset, _ = enemy_pose(self,art)
            surface.blit(art,art.get_rect(center=(sr.centerx+offset[0],sr.centery+offset[1])))
            if self.type in (EnemyType.BRUTE, EnemyType.ELITE):
                from systems.champion_encounters import draw
                draw(self, surface, camera)
            if ranged:
                draw_cast(surface,sr.center,aim,cast_state,progress)
            if self.type.name in ('HUNTER','ELITE','BOSS') and self.windup_direction.length_squared()>0:
                from systems.shot_presentation import draw_charge
                charging=self.windup_timer>0
                release=self.visual_release_timer>0 and self.leap_timer<=0
                if charging or release:
                    amount=max(.1,1-self.windup_timer/max(.001,self.visual_windup_total)) if charging else self.visual_release_timer/.24
                    direction=self.windup_direction.normalize()
                    draw_charge(surface,pygame.Vector2(sr.center)+direction*(sr.width*.4),direction,amount,
                                'fire' if self.type==EnemyType.BOSS else 'magic',release=release)
            self._draw_health_bar(surface,camera)
            if self.type == EnemyType.BOSS:
                if Enemy._phase_font is None:
                    Enemy._phase_font = pygame.font.Font(None,22)
                label = Enemy._phase_font.render('PHASE '+str(self.phase),True,(255,185,110))
                surface.blit(label,label.get_rect(center=(sr.centerx,sr.top-40)))
            self._draw_vampire_wounds(surface,camera)
            self._draw_windup_indicator(surface,camera)
            return
        self._draw_shadow_glow(surface, camera)
        if self.type in (EnemyType.CHASER, EnemyType.CHASER_FAST, EnemyType.CHASER_TANK):
            
            self._draw_chaser(surface, camera)
            
        elif self.hit_flash > 0:
            self._draw_flash(surface, camera)
        elif self.type in (EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.RANGED_FIVE, EnemyType.RANGED_RAIN):
            self._draw_ranged(surface, camera)
        elif self.type in (EnemyType.JUMPER, EnemyType.JUMPER_FAST, EnemyType.JUMPER_HEAVY):
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
        self._draw_vampire_wounds(surface, camera)
        self._draw_windup_indicator(surface, camera)

    def _draw_shadow_glow(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        shadow_extra = 10
        shadow_h = max(5, sr.height // 5)
        shadow_col = (0, 0, 0)
        if self.type == EnemyType.BRUTE:
            shadow_extra = 22
            shadow_h = max(8, sr.height // 4)
        elif self.type == EnemyType.BOSS:
            shadow_extra = 34
            shadow_h = max(12, sr.height // 4)
        elif self.type == EnemyType.ELITE:
            shadow_extra = 18
        elif self.type == EnemyType.LOOT:
            shadow_col = (38, 28, 0)
        shadow = pygame.Rect(0, 0, max(12, sr.width + shadow_extra), shadow_h)
        shadow.center = (sr.centerx + 2, sr.bottom - 2)
        pygame.draw.ellipse(surface, shadow_col, shadow)

        ranged_types = (EnemyType.RANGED, EnemyType.RANGED_THREE, EnemyType.RANGED_FIVE, EnemyType.RANGED_RAIN)
        if self.type in (EnemyType.CHASER, EnemyType.CHASER_FAST, EnemyType.CHASER_TANK):
            rim_col = (255, 105, 105)
            if self.type == EnemyType.CHASER_FAST:
                rim_col = (255, 145, 80)
            elif self.type == EnemyType.CHASER_TANK:
                rim_col = (210, 95, 95)
            pygame.draw.line(surface, rim_col, sr.topleft, (sr.right - 2, sr.top), 1)
            pygame.draw.line(surface, (95, 8, 8), (sr.left, sr.bottom - 2), (sr.right - 2, sr.bottom - 2), 1)
        elif self.type in ranged_types:
            windup_ratio = min(1.0, max(0.0, self.windup_timer / max(0.01, RANGED_WINDUP_TIME)))
            pulse = 2 + int(3 * math.sin(self._anim * 12))
            glow_radius = max(sr.width, sr.height) // 2 + pulse + int(8 * windup_ratio)
            glow_col = (115, 175, 255) if self.type == EnemyType.RANGED_RAIN else (185, 125, 255)
            pygame.draw.circle(surface, glow_col, sr.center, glow_radius, 1 + int(2 * windup_ratio))
            if self.windup_timer > 0:
                pygame.draw.line(surface, (220, 245, 255), (sr.left + 5, sr.top - 3), (sr.right - 5, sr.top - 3), 2)
        elif self.type == EnemyType.HUNTER:
            side_x = sr.left + 5 if getattr(self, "facing_left", False) else sr.right - 5
            pygame.draw.line(surface, (255, 130, 235), (side_x, sr.top + 5), (side_x, sr.bottom - 7), 2)
            pygame.draw.rect(surface, (170, 55, 210), sr.inflate(5, 5), 1, border_radius=8)
        elif self.type == EnemyType.BRUTE:
            pygame.draw.rect(surface, (55, 34, 18), sr.inflate(10, 8), 3, border_radius=8)
            pygame.draw.line(surface, (235, 185, 95), (sr.left + 7, sr.top + 3), (sr.right - 8, sr.top + 3), 2)

        if self.hit_flash > 0 or self.type in (EnemyType.ELITE, EnemyType.BOSS, EnemyType.LOOT):
            glow_col = (255, 90, 90)
            if self.type == EnemyType.ELITE:
                glow_col = GOLD
            elif self.type == EnemyType.BOSS:
                glow_col = (255, 85, 45)
            elif self.type == EnemyType.LOOT:
                glow_col = (255, 220, 80)
            inflate = 8
            width = 2
            if self.type == EnemyType.ELITE:
                inflate = 12 + int(2 * abs(math.sin(self._anim * 4)))
                width = 3
            elif self.type == EnemyType.BOSS:
                inflate = 18 + int(4 * abs(math.sin(self._anim * 3)))
                width = 4
            glow_rect = sr.inflate(inflate, inflate)
            pygame.draw.rect(surface, glow_col, glow_rect, width, border_radius=8)
            if self.type == EnemyType.BOSS:
                pygame.draw.line(surface, (255, 170, 70), (sr.left - 8, sr.top - 8), (sr.right + 8, sr.top - 8), 2)

    # ---- hit flash (all types) ----------------------------------------
    def _draw_flash(self, surface, camera):
        sr = camera.apply_rect(self.rect)
        pygame.draw.rect(surface, (255, 140, 140), sr, border_radius=7)

    # ---- CHASER --------------------------------------------------------
    def _draw_chaser(self, surface, camera):
        if self._draw_chaser_sprite(surface, camera):
            return
    
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height
    
        body_col = (180, 30, 30)
        spike_col = (220, 50, 50)
    
        if self.type == EnemyType.CHASER_FAST:
            body_col, spike_col = (220, 70, 40), (255, 120, 60)
        elif self.type == EnemyType.CHASER_TANK:
            body_col, spike_col = (125, 35, 35), (210, 80, 80)
    
        pygame.draw.rect(surface, body_col, sr, border_radius=4)
        pygame.draw.line(surface, (255, 120, 120), (x + 4, y + 4), (x + w - 5, y + 4), 2)
        pygame.draw.line(surface, (90, 8, 8), (x + 3, y + h - 4), (x + w - 4, y + h - 4), 2)
    
        spike_size = 7
        for sx, sy in [(x, y), (x + w - spike_size, y)]:
            pygame.draw.polygon(surface, spike_col, [
                (sx, sy + spike_size),
                (sx + spike_size // 2, sy - 4),
                (sx + spike_size, sy + spike_size),
            ])
    
        eye_rect = pygame.Rect(x + 4, y + 7, w - 8, 7)
        pygame.draw.rect(surface, (20, 0, 0), eye_rect, border_radius=2)
        pygame.draw.rect(surface, (255, 30, 30), pygame.Rect(x + 6, y + 9, 6, 3), border_radius=1)
        pygame.draw.rect(surface, (255, 30, 30), pygame.Rect(x + w - 12, y + 9, 6, 3), border_radius=1)
    
        for fx in [x + 3, x + w - 10]:
            pygame.draw.rect(
                surface,
                (140, 20, 20),
                pygame.Rect(fx, y + h - 5, 7, 5),
                border_radius=2,
            )
    def _draw_chaser_sprite(self, surface, camera):
        frames = Enemy._chaser_walk_frames or []
        image = None
        if frames:
            image = frames[int(self._anim * 8) % len(frames)]
        else:
            image = Enemy._chaser_idle_image

        if image is None:
            return False
            
        facing_left = getattr(self, 'facing_left', False)
        if self.leap_timer > 0 and self.leap_velocity.x != 0:
            facing_left = self.leap_velocity.x < 0

        sr = camera.apply_rect(self.rect)
        scaled_image = pygame.transform.scale(image, (sr.width, sr.height))
        
        if not facing_left:
            scaled_image = pygame.transform.flip(scaled_image, True, False)
        
        if self.hit_flash > 0:
            scaled_image.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(scaled_image, scaled_image.get_rect(center=sr.center))
        return True

    # ---- RANGED --------------------------------------------------------
    def _draw_ranged(self, surface, camera):
        if self.type == EnemyType.RANGED and self._draw_ranged_sprite(surface, camera):
            return

        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        robe_col = {
            EnemyType.RANGED: (85, 45, 135),
            EnemyType.RANGED_THREE: (115, 55, 175),
            EnemyType.RANGED_FIVE: (150, 55, 210),
            EnemyType.RANGED_RAIN: (55, 80, 150),
        }.get(self.type, (90, 50, 150))
        hood_col = tuple(max(0, c - 28) for c in robe_col)
        orb_col = (120, 190, 255) if self.type == EnemyType.RANGED_RAIN else (180, 120, 255)

        pygame.draw.rect(surface, robe_col, sr, border_radius=8)
        pygame.draw.line(surface, (170, 110, 230), (x + 4, y + 5), (x + w - 5, y + 5), 2)

        hood_pts = [
            (x + 2, y + 6),
            (cx,    y - 7),
            (x + w - 2, y + 6),
        ]
        pygame.draw.polygon(surface, hood_col, hood_pts)

        staff_x = x - 5
        pygame.draw.line(surface, (55, 30, 100),
                         (staff_x, y - 2), (staff_x, y + h + 2), 3)
        orb_pulse = 5 + int(2 * math.sin(self._anim * 4))
        if self.windup_timer > 0:
            orb_pulse += 3
        pygame.draw.circle(surface, orb_col, (staff_x, y - 2), orb_pulse, 2)
        pygame.draw.circle(surface, (220, 190, 255), (staff_x, y - 2), orb_pulse // 2)

        eye_y = y + h // 3
        pygame.draw.circle(surface, (200, 150, 255), (cx - 5, eye_y), 4)
        pygame.draw.circle(surface, (200, 150, 255), (cx + 5, eye_y), 4)
        pygame.draw.circle(surface, (240, 220, 255), (cx - 5, eye_y), 2)
        pygame.draw.circle(surface, (240, 220, 255), (cx + 5, eye_y), 2)

    def _draw_ranged_sprite(self, surface, camera):
        body_frames = Enemy._ranged_body_frames or []
        if not body_frames:
            return False

        sr = camera.apply_rect(self.rect)
        body = body_frames[int(self._anim * 7) % len(body_frames)]
        aim = self._ranged_aim_direction()

        if aim.x < 0:
            body = pygame.transform.flip(body, True, False)

        surface.blit(body, body.get_rect(center=sr.center))

        weapon_frames = Enemy._ranged_weapon_frames or []
        if weapon_frames:
            weapon = weapon_frames[int(self._anim * 9) % len(weapon_frames)]
            weapon = self._rotate_sprite_weapon(weapon, aim)
            weapon_center = pygame.Vector2(sr.center) + aim * 23
            weapon_rect = weapon.get_rect(center=(round(weapon_center.x), round(weapon_center.y)))
            surface.blit(weapon, weapon_rect)

        return True

    def _ranged_aim_direction(self):
        if self.windup_direction.length_squared() > 0:
            return self.windup_direction.normalize()

        if self.last_player_center is not None:
            direction = pygame.Vector2(self.last_player_center) - pygame.Vector2(self.rect.center)
            if direction.length_squared() > 0:
                return direction.normalize()

        return pygame.Vector2(-1 if getattr(self, "facing_left", False) else 1, 0)

    def _rotate_sprite_weapon(self, image, aim):
        angle = aim.as_polar()[1]
        if aim.x < 0:
            image = pygame.transform.flip(image, True, False)
            return pygame.transform.rotate(image, -(angle - 180))
        return pygame.transform.rotate(image, -angle)

    # ---- JUMPER --------------------------------------------------------
    def _draw_jumper(self, surface, camera):
        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        leaping = self.leap_timer > 0
        base_body = {
            EnemyType.JUMPER: (0, 180, 180),
            EnemyType.JUMPER_FAST: (40, 230, 160),
            EnemyType.JUMPER_HEAVY: (20, 120, 210),
        }.get(self.type, (0, 180, 180))
        col_body = tuple(min(255, c + 50) for c in base_body) if leaping else base_body

        # body – teal compact block
        pygame.draw.rect(surface, col_body, sr, border_radius=6)
        pygame.draw.line(surface, (120, 255, 230), (x + 5, y + 4), (x + w - 6, y + 4), 2)

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
        pygame.draw.line(surface, (255, 150, 235), (x + 5, y + 4), (x + w - 6, y + 4), 2)
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
        pygame.draw.line(surface, (230, 190, 105), (x + 6, y + 4), (x + w - 7, y + 4), 2)
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
        pulse = int(2 + 2 * math.sin(self._anim * 5))
        pygame.draw.rect(surface, (255, 120, 195), sr.inflate(6 + pulse, 6 + pulse), 2, border_radius=8)

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
        pygame.draw.line(surface, (255, 250, 170), (x + 6, y + 5), (x + w - 7, y + 5), 2)
        pygame.draw.rect(surface, (110, 70, 10), pygame.Rect(x + 5, y + 7, w - 10, h - 12), border_radius=5)
        pygame.draw.circle(surface, YELLOW, (cx - 7, cy - 2), 4)
        pygame.draw.circle(surface, YELLOW, (cx + 7, cy - 2), 4)
        pygame.draw.rect(surface, (255, 235, 120), pygame.Rect(x + 7, y + h - 10, w - 14, 4), border_radius=2)
        glimmer = int(self._anim * 6) % 4
        sparkle_points = ((x + 8, y + 9), (x + w - 10, y + 15), (cx, y + h - 14), (x + w - 15, y + h - 8))
        sx, sy = sparkle_points[glimmer]
        pygame.draw.line(surface, (255, 255, 210), (sx - 4, sy), (sx + 4, sy), 1)
        pygame.draw.line(surface, (255, 255, 210), (sx, sy - 4), (sx, sy + 4), 1)

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

        if Enemy._phase_font is None:
            Enemy._phase_font = pygame.font.SysFont("Arial", 15, bold=True)
        phase_font = Enemy._phase_font
        phase_shadow = phase_font.render(phase_label_text, True, (0, 0, 0))
        phase_label = phase_font.render(phase_label_text, True, phase_label_color)
        phase_pos = phase_label.get_rect(center=(cx, y - 18))
        surface.blit(phase_shadow, (phase_pos.x + 1, phase_pos.y + 1))
        surface.blit(phase_label, phase_pos)

        # massive body
        pygame.draw.rect(surface, body_col, sr, border_radius=8)
        pygame.draw.rect(surface, (255, 150, 80), sr.inflate(8, 8), 2, border_radius=10)
        pygame.draw.line(surface, (255, 230, 150), (x + 10, y + 5), (x + w - 11, y + 5), 3)

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
        if self.encounter is not None:
            return  # One readable encounter health bar, not two competing boss bars.
        bar_w = self.rect.width
        ratio = max(0, self.health / self.max_health)

        bg = pygame.Rect(self.rect.x, self.rect.y - 9, bar_w, 5)
        fg = pygame.Rect(self.rect.x, self.rect.y - 9, int(bar_w * ratio), 5)

        pygame.draw.rect(surface, (60, 0, 0),    camera.apply_rect(bg))
        pygame.draw.rect(surface, (220, 60, 60), camera.apply_rect(fg))

        # boss shield bar
        if self.type == EnemyType.BOSS and self.phase == 1 and self.encounter is None:
            sh_ratio = max(0, self.shield / self.max_shield)
            sh_bg = pygame.Rect(self.rect.x, self.rect.y - 17, bar_w, 5)
            sh_fg = pygame.Rect(self.rect.x, self.rect.y - 17, int(bar_w * sh_ratio), 5)
            pygame.draw.rect(surface, (20, 60, 100),  camera.apply_rect(sh_bg))
            pygame.draw.rect(surface, (80, 180, 255), camera.apply_rect(sh_fg))

    def _draw_vampire_wounds(self, surface, camera):
        stacks = int(getattr(self, "vampire_wound_stacks", 0))
        if stacks <= 0:
            return
        sr = camera.apply_rect(self.rect)
        y = sr.top - 15
        start_x = sr.centerx - (stacks - 1) * 5
        for index in range(stacks):
            center = (start_x + index * 10, y)
            pygame.draw.circle(surface, (45, 0, 12), center, 5)
            pygame.draw.circle(surface, (235, 40, 80), center, 3)

    # ---- windup indicator ---------------------------------------------
    def _draw_windup_indicator(self, surface, camera):
        if self.encounter is not None:
            return  # Encounter draws pattern-matched tells, including cyan parry cues.
        if self.windup_timer <= 0 or self.windup_direction.length_squared() == 0:
            return

        start  = camera.apply_pos(pygame.Vector2(self.rect.center))
        action = self.windup_action or ""
        if self.type == EnemyType.HUNTER:
            from systems.ranged_presentation import draw_telegraph
            draw_telegraph(surface,start,self.windup_direction,self.windup_telegraph_length(),
                           self.windup_timer,self.visual_windup_total,self._anim,
                           palette=((220,70,150),(255,165,210)))
            return
        if action == 'brute_charge' and self.type == EnemyType.BRUTE:
            from systems.ranged_presentation import draw_telegraph
            draw_telegraph(surface,start,self.windup_direction,self.windup_telegraph_length(),
                           self.windup_timer,self.brute_windup_total,self._anim,
                           palette=((210,130,50),(255,220,140)))
            return
        if action in ('enemy_shoot', 'enemy_rain') or (action=='enemy_jump' and self.type in (EnemyType.JUMPER,EnemyType.JUMPER_FAST,EnemyType.JUMPER_HEAVY)):
            from systems.ranged_presentation import draw_telegraph
            draw_telegraph(surface, start, self.windup_direction,
                           self.windup_telegraph_length(), self.windup_timer,
                           self.jumper_windup_total if action=='enemy_jump' else self.ranged_windup_total, self._anim)
            return

        if "ring" in action:
            pygame.draw.circle(surface, (255, 120, 40),
                               (round(start.x), round(start.y)), 120, 3)

        elif "summon" in action:
            from systems.ranged_presentation import draw_telegraph
            draw_telegraph(surface,start,self.windup_direction,290,self.windup_timer,
                           self.visual_windup_total,self._anim,palette=((230,80,65),(255,190,140)))

        else:
            length = self.windup_telegraph_length()
            from systems.ranged_presentation import draw_telegraph
            colors=((230,80,65),(255,190,140)) if self.type==EnemyType.BOSS else ((205,150,60),(255,230,170))
            draw_telegraph(surface,start,self.windup_direction,length,self.windup_timer,
                           self.visual_windup_total,self._anim,palette=colors)

    def windup_telegraph_length(self):
        action = self.windup_action or ""
        if self.type == EnemyType.BOSS:
            return 650
        if action in ("enemy_shoot", "enemy_rain"):
            return RANGED_ATTACK_RANGE
        if action == "hunter_homing":
            return RANGED_ATTACK_RANGE + 170
        if action == "enemy_jump":
            if self.type == EnemyType.JUMPER_HEAVY:
                return JUMPER_ATTACK_RANGE + 60
            return JUMPER_ATTACK_RANGE
        if action == "brute_charge":
            return 560
        if self.type == EnemyType.ELITE:
            return RANGED_ATTACK_RANGE
        return 520
