import pygame
from settings import (
    PLAYER_SPEED,
    PLAYER_MAX_HEALTH,
    PLAYER_INVULNERABLE_TIME,
    DASH_SPEED,
    DASH_DURATION,
    DASH_COOLDOWN,
    PLAYER_SKILL_COOLDOWN,
    SURGE_DURATION,
    GHOST_DURATION,
    GHOST_SPEED_MULTIPLIER,
    BLUE,
)
from systems.asset_loader import load_image, load_sheet_frames
from systems.weapon_system import KnifeWeapon, PistolWeapon, SwordWeapon
from systems.xp_progression import xp_required_for_level
from systems.room_bounds import current_room_bounds, current_room_rect


GUN_SIZE = (32, 32)
GUN_SHOULDER_OFFSET = (11, 10)
GUN_CENTER_REACH = 35
GUN_MUZZLE_REACH = 38
GUN_SHOOT_ANIM_SECONDS = 0.12
KNIFE_SIZE = (42, 42)
KNIFE_ATTACK_ANIM_SECONDS = 0.18
SWORD_SIZE = (58, 58)
SWORD_ATTACK_FRAME_SIZE = (64, 64)
SWORD_ATTACK_FRAME_COUNT = 6
SWORD_ATTACK_ANIM_SECONDS = 0.24
DASH_GHOST_INTERVAL = 0.045
DASH_GHOST_LIFE = 0.22
ENGINEER_BLADE_SPRITE_SIZE = (32, 32)
ENGINEER_BLADE_SPIN_SPEED = 11.0
ENGINEER_BLADE_TRAIL_LIMIT = 5


class Player:
    _sprite_frames = None
    _shadow_frames = None
    _gun_image = None
    _gun_shoot_frames = None
    _knife_image = None
    _knife_frames = None
    _sword_image = None
    _sword_hit_frames = None
    _engineer_blade_image = None
    _engineer_blade_image_loaded = False
    _tea_full_image = None
    _tea_drink_frames = None

    def __init__(self):
        bounds = current_room_bounds()
        self.rect = pygame.Rect(bounds.centerx, bounds.centery, 38, 38)
        self.color = BLUE
        self.anim_time = 0.0
        self.gun_shoot_timer = 0.0
        self.knife_attack_timer = 0.0
        self.sword_attack_timer = 0.0
        self.weapon_cooldown_timer = 0.0
        self.dash_ghosts = []
        self.dash_ghost_emit_timer = 0.0
        self.tea_state = None
        self.tea_drink_timer = 0.0

        self.base_speed = PLAYER_SPEED
        self.speed = PLAYER_SPEED
        self.velocity = pygame.Vector2(0, 0)
        self.move_direction = pygame.Vector2(0, 0)
        self.aim_direction = pygame.Vector2(1, 0)
        self.facing_x = 1

        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.invulnerable_timer = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_next = xp_required_for_level(self.level)
        self.gold = 0

        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.projectile_count = 1
        self.spread_degrees = 0
        self.projectile_speed_bonus = 0
        self.split_damage_multiplier = 1.0
        self.pierce = 0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.75
        self.regen_on_room_clear = 10

        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.skill_cooldown_timer = 0.0
        self.skill_cooldown_multiplier = 1.0
        self.dash_invuln_bonus = 0.0
        self.surge_timer = 0.0
        self.ghost_timer = 0.0
        self.active_skill = "dash"
        self.weapon_damage_multiplier = 1.0
        self.explosive_rounds = False
        self.explosion_radius = 95
        self.explosion_splash_ratio = 1 / 3
        self.knockback_power = 1.0
        self.dash_direction = pygame.Vector2(1, 0)
        self.dash_strike_damage = 0
        self.dash_strike_cooldown_restore = 0.0
        self.dash_strike_hit_ids = set()
        self.engineer_helper_enabled = False
        self.engineer_helper_damage = 0
        self.engineer_helper_cooldown = 1.65
        self.engineer_helper_projectile_speed = 720
        self.engineer_helper_timer = 0.0
        self.engineer_gun_count = 0
        self.engineer_gun_burst_count = 1
        self.engineer_gun_level = 0
        self.engineer_impact_level = 0
        self.engineer_kinetic_level = 0
        self.engineer_overclock_level = 0
        self.engineer_gun_range = 500
        self.engineer_drone_pos = pygame.Vector2(self.rect.center)
        self.engineer_drone_positions = []
        self.engineer_drone_angle = 0.0
        self.engineer_drone_target_id = None
        self.engineer_drone_attack_flash = 0.0
        self.engineer_blade_level = 0
        self.engineer_blade_count = 0
        self.engineer_blade_damage = 0
        self.engineer_blade_radius = 0
        self.engineer_blade_hit_cooldown = 0.60
        self.engineer_blade_orbit_speed = 0.0
        self.engineer_blade_angle = 0.0
        self.engineer_blade_spin_angle = 0.0
        self.engineer_blade_positions = []
        self.engineer_blade_trail = []
        self.engineer_blade_hit_timers = {}
        self.engineer_blade_hit_flash = 0.0
        self.engineer_blade_overdrive_timer = 0.0
        self.engineer_blade_overdrive_cooldown_timer = 0.0
        self.engineer_blade_overdrive_duration = 0.0
        self.engineer_blade_overdrive_cooldown = 0.0
        self.engineer_blade_overdrive_radius_bonus = 0
        self.engineer_blade_overdrive_damage_bonus = 0
        self.engineer_bomber_level = 0
        self.engineer_bomber_count = 0
        self.engineer_bomber_damage = 0
        self.engineer_bomber_radius = 0
        self.engineer_bomber_cooldown = 5.0
        self.engineer_bomber_speed = 0.0
        self.engineer_bomber_max_runs = 0
        self.engineer_bomber_runs_remaining = 0
        self.engineer_bomber_state = "inactive"
        self.engineer_bomber_timer = 0.0
        self.engineer_bomber_pos = pygame.Vector2(self.rect.center)
        self.engineer_bomber_target_pos = pygame.Vector2(self.rect.center)
        self.engineer_bomber_target_id = None
        self.engineer_bomber_explosion_flash = 0.0
        self.engineer_airstrike_unlocked = False
        self.engineer_airstrike_state = "inactive"
        self.engineer_airstrike_timer = 0.0
        self.engineer_airstrike_cooldown = 0.0
        self.engineer_airstrike_cooldown_timer = 0.0
        self.engineer_airstrike_target_pos = pygame.Vector2(self.rect.center)
        self.engineer_airstrike_damage = 0
        self.engineer_airstrike_radius = 0
        self.vampire_kill_heal = 0
        self.vampire_elite_bonus_heal = 0
        self.vampire_blood = 0
        self.vampire_max_blood = 0
        self.vampire_blood_per_kill = 0
        self.vampire_blood_on_hit = 0
        self.vampire_blood_on_boss_hit = 0
        self.vampire_blood_damage_bonus = 0.0
        self.vampire_feed_flash = 0.0
        self.vampire_wound_level = 0
        self.vampire_wound_stacks_per_hit = 0
        self.vampire_wound_max_stacks = 0
        self.vampire_wound_duration = 0.0
        self.vampire_orb_drop_chance = 0.0
        self.vampire_orb_value = 0
        self.vampire_blood_orbs = []
        self.vampire_orb_cap = 16
        self.vampire_orb_attract_radius = 96
        self.vampire_orb_heal = 0
        self.vampire_blood_capacity_bonus = 0
        self.vampire_sustain_level = 0
        self.vampire_feast_unlocked = False
        self.vampire_feast_progress = 0
        self.vampire_feast_threshold = 999
        self.vampire_feast_timer = 0.0
        self.vampire_feast_duration = 0.0
        self.vampire_blood_moon_unlocked = False
        self.vampire_blood_moon_timer = 0.0
        self.vampire_blood_moon_duration = 9.0
        self.vampire_blood_moon_cooldown = 20.0
        self.vampire_blood_moon_cooldown_timer = 0.0
        self.vampire_bat_level = 0
        self.vampire_bat_enabled = False
        self.vampire_bat_state = "inactive"
        self.vampire_bat_timer = 0.0
        self.vampire_bat_search_timer = 0.0
        self.vampire_bat_pos = pygame.Vector2(self.rect.center)
        self.vampire_bat_target_id = None
        self.vampire_bat_target_pos = pygame.Vector2(self.rect.center)
        self.vampire_bat_carried_blood = 0
        self.vampire_bat_chain_kills = 0
        self.vampire_bat_chain_cap = 0
        self.vampire_bat_damage = 0
        self.vampire_bat_speed = 0
        self.vampire_bat_feed_value = 0
        self.vampire_bat_cooldown = 0.0
        self.vampire_trail_level = 0
        self.vampire_trail_enabled = False
        self.vampire_trail_harvest_cap = 0
        self.vampire_trail_harvest_value = 0
        self.vampire_trail_interval = 0.0
        self.vampire_trail_timer = 0.0
        self.vampire_trail_radius = 0
        self.vampire_trail_hit_ids = set()
        self.vampire_trail_harvested_this_dash = 0
        self.ninja_momentum_enabled = False
        self.ninja_momentum = 0.0
        self.ninja_momentum_gain = 0.0
        self.ninja_momentum_max = 0.0
        self.dash_refund_cap = 0.0
        self.dash_refund_this_dash = 0.0
        self.ninja_shuriken_damage = 0
        self.ninja_shuriken_speed = 0

        self.pending_level_ups = 0
        self.last_upgrade_text = ""
        self.perk_counts = {}
        self.perk_choices_made = 0
        self.starter_choice_active = False
        self.starter_build = ""
        self.starter_missing_build = ""
        self.starter_free_reroll_used = False
        self.reroll_tokens = 0
        self.reroll_tokens_earned = 0
        self.reroll_gold_spent = 0
        self.total_rerolls_used = 0
        self.weapons = {
            "pistol": PistolWeapon(),
            "knife": KnifeWeapon(),
            "sword": SwordWeapon(),
        }
        self.active_weapon_key = "pistol"
        self.active_weapon = self.weapons[self.active_weapon_key]

        if Player._sprite_frames is None:
            Player._sprite_frames = load_sheet_frames("hero (1).png", (64, 64), scale=(52, 52))
        if Player._shadow_frames is None:
            Player._shadow_frames = load_sheet_frames("underPlayer1.png", (64, 64), scale=(44, 18))
        if Player._gun_image is None:
            Player._gun_image = load_image("gun.png", size=GUN_SIZE)
        if Player._gun_shoot_frames is None:
            Player._gun_shoot_frames = load_sheet_frames("gun_will_shoting.png", (64, 64), scale=GUN_SIZE)
        if Player._knife_image is None:
            Player._knife_image = load_image("wepone knife.png", size=KNIFE_SIZE)
        if Player._knife_frames is None:
            Player._knife_frames = load_sheet_frames("knife_animation.png", (128, 128), scale=KNIFE_SIZE)
        if Player._sword_image is None:
            Player._sword_image = load_image("soward.png", size=SWORD_SIZE)
        if Player._sword_hit_frames is None:
            Player._sword_hit_frames = load_sheet_frames(
                "sowrd-hit.png",
                SWORD_ATTACK_FRAME_SIZE,
                max_frames=SWORD_ATTACK_FRAME_COUNT,
                scale=SWORD_SIZE,
            )
        if not Player._engineer_blade_image_loaded:
            Player._engineer_blade_image = load_image("blade_drone.png", size=ENGINEER_BLADE_SPRITE_SIZE)
            Player._engineer_blade_image_loaded = True
        if Player._tea_full_image is None:
            Player._tea_full_image = load_image("tea_full.png", size=(32, 32))
        if Player._tea_drink_frames is None:
            Player._tea_drink_frames = load_sheet_frames("tea_drink.png", (32, 32), max_frames=6, scale=(32, 32))

    def reset(self):
        self.rect.center = current_room_bounds().center
        self.velocity.update(0, 0)
        self.move_direction.update(0, 0)
        self.aim_direction.update(1, 0)
        self.facing_x = 1

        self.speed = self.base_speed
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.invulnerable_timer = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_next = xp_required_for_level(self.level)
        self.gold = 0

        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.projectile_count = 1
        self.spread_degrees = 0
        self.projectile_speed_bonus = 0
        self.split_damage_multiplier = 1.0
        self.pierce = 0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.75
        self.regen_on_room_clear = 10

        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.skill_cooldown_timer = 0.0
        self.skill_cooldown_multiplier = 1.0
        self.dash_invuln_bonus = 0.0
        self.surge_timer = 0.0
        self.ghost_timer = 0.0
        self.active_skill = "dash"
        self.weapon_damage_multiplier = 1.0
        self.explosive_rounds = False
        self.explosion_radius = 95
        self.explosion_splash_ratio = 1 / 3
        self.knockback_power = 1.0
        self.dash_direction.update(1, 0)
        self.dash_strike_damage = 0
        self.dash_strike_cooldown_restore = 0.0
        self.dash_strike_hit_ids = set()
        self.engineer_helper_enabled = False
        self.engineer_helper_damage = 0
        self.engineer_helper_cooldown = 1.65
        self.engineer_helper_projectile_speed = 720
        self.engineer_helper_timer = 0.0
        self.engineer_gun_count = 0
        self.engineer_gun_burst_count = 1
        self.engineer_gun_level = 0
        self.engineer_impact_level = 0
        self.engineer_kinetic_level = 0
        self.engineer_overclock_level = 0
        self.engineer_gun_range = 500
        self.engineer_drone_pos.update(self.rect.center)
        self.engineer_drone_positions = []
        self.engineer_drone_angle = 0.0
        self.engineer_drone_target_id = None
        self.engineer_drone_attack_flash = 0.0
        self.engineer_blade_level = 0
        self.engineer_blade_count = 0
        self.engineer_blade_damage = 0
        self.engineer_blade_radius = 0
        self.engineer_blade_hit_cooldown = 0.60
        self.engineer_blade_orbit_speed = 0.0
        self.engineer_blade_angle = 0.0
        self.engineer_blade_spin_angle = 0.0
        self.engineer_blade_positions = []
        self.engineer_blade_trail = []
        self.engineer_blade_hit_timers = {}
        self.engineer_blade_hit_flash = 0.0
        self.engineer_blade_overdrive_timer = 0.0
        self.engineer_blade_overdrive_cooldown_timer = 0.0
        self.engineer_blade_overdrive_duration = 0.0
        self.engineer_blade_overdrive_cooldown = 0.0
        self.engineer_blade_overdrive_radius_bonus = 0
        self.engineer_blade_overdrive_damage_bonus = 0
        self.engineer_bomber_level = 0
        self.engineer_bomber_count = 0
        self.engineer_bomber_damage = 0
        self.engineer_bomber_radius = 0
        self.engineer_bomber_cooldown = 5.0
        self.engineer_bomber_speed = 0.0
        self.engineer_bomber_max_runs = 0
        self.engineer_bomber_runs_remaining = 0
        self.engineer_bomber_state = "inactive"
        self.engineer_bomber_timer = 0.0
        self.engineer_bomber_pos.update(self.rect.center)
        self.engineer_bomber_target_pos.update(self.rect.center)
        self.engineer_bomber_target_id = None
        self.engineer_bomber_explosion_flash = 0.0
        self.engineer_airstrike_unlocked = False
        self.engineer_airstrike_state = "inactive"
        self.engineer_airstrike_timer = 0.0
        self.engineer_airstrike_cooldown = 0.0
        self.engineer_airstrike_cooldown_timer = 0.0
        self.engineer_airstrike_target_pos.update(self.rect.center)
        self.engineer_airstrike_damage = 0
        self.engineer_airstrike_radius = 0
        self.vampire_kill_heal = 0
        self.vampire_elite_bonus_heal = 0
        self.vampire_blood = 0
        self.vampire_max_blood = 0
        self.vampire_blood_per_kill = 0
        self.vampire_blood_on_hit = 0
        self.vampire_blood_on_boss_hit = 0
        self.vampire_blood_damage_bonus = 0.0
        self.vampire_feed_flash = 0.0
        self.vampire_wound_level = 0
        self.vampire_wound_stacks_per_hit = 0
        self.vampire_wound_max_stacks = 0
        self.vampire_wound_duration = 0.0
        self.vampire_orb_drop_chance = 0.0
        self.vampire_orb_value = 0
        self.vampire_blood_orbs.clear()
        self.vampire_orb_cap = 16
        self.vampire_orb_attract_radius = 96
        self.vampire_orb_heal = 0
        self.vampire_blood_capacity_bonus = 0
        self.vampire_sustain_level = 0
        self.vampire_feast_unlocked = False
        self.vampire_feast_progress = 0
        self.vampire_feast_threshold = 999
        self.vampire_feast_timer = 0.0
        self.vampire_feast_duration = 0.0
        self.vampire_blood_moon_unlocked = False
        self.vampire_blood_moon_timer = 0.0
        self.vampire_blood_moon_duration = 9.0
        self.vampire_blood_moon_cooldown = 20.0
        self.vampire_blood_moon_cooldown_timer = 0.0
        self.vampire_bat_level = 0
        self.vampire_bat_enabled = False
        self.vampire_bat_state = "inactive"
        self.vampire_bat_timer = 0.0
        self.vampire_bat_search_timer = 0.0
        self.vampire_bat_pos.update(self.rect.center)
        self.vampire_bat_target_id = None
        self.vampire_bat_target_pos.update(self.rect.center)
        self.vampire_bat_carried_blood = 0
        self.vampire_bat_chain_kills = 0
        self.vampire_bat_chain_cap = 0
        self.vampire_bat_damage = 0
        self.vampire_bat_speed = 0
        self.vampire_bat_feed_value = 0
        self.vampire_bat_cooldown = 0.0
        self.vampire_trail_level = 0
        self.vampire_trail_enabled = False
        self.vampire_trail_harvest_cap = 0
        self.vampire_trail_harvest_value = 0
        self.vampire_trail_interval = 0.0
        self.vampire_trail_timer = 0.0
        self.vampire_trail_radius = 0
        self.vampire_trail_hit_ids.clear()
        self.vampire_trail_harvested_this_dash = 0
        self.ninja_momentum_enabled = False
        self.ninja_momentum = 0.0
        self.ninja_momentum_gain = 0.0
        self.ninja_momentum_max = 0.0
        self.dash_refund_cap = 0.0
        self.dash_refund_this_dash = 0.0
        self.ninja_shuriken_damage = 0
        self.ninja_shuriken_speed = 0

        self.pending_level_ups = 0
        self.last_upgrade_text = ""
        self.perk_counts = {}
        self.perk_choices_made = 0
        self.starter_choice_active = False
        self.starter_build = ""
        self.starter_missing_build = ""
        self.starter_free_reroll_used = False
        self.reroll_tokens = 0
        self.reroll_tokens_earned = 0
        self.reroll_gold_spent = 0
        self.total_rerolls_used = 0
        self.anim_time = 0.0
        self.gun_shoot_timer = 0.0
        self.knife_attack_timer = 0.0
        self.sword_attack_timer = 0.0
        self.weapon_cooldown_timer = 0.0
        self.dash_ghosts.clear()
        self.dash_ghost_emit_timer = 0.0
        self.cancel_tea()
        self.active_weapon_key = "pistol"
        self.active_weapon = self.weapons[self.active_weapon_key]

    def build_power_score(self):
        damage_score = self.damage_bonus / 7
        fire_score = max(0, self.fire_rate_multiplier - 1.0) * 4
        projectile_score = max(0, self.projectile_count - 1) * 1.4
        pierce_score = self.pierce * 0.9
        crit_score = self.crit_chance * 8
        speed_score = max(0, self.speed - self.base_speed) / 35
        hp_score = max(0, self.max_health - PLAYER_MAX_HEALTH) / 35
        return max(0.0, damage_score + fire_score + projectile_score + pierce_score + crit_score + speed_score + hp_score)

    def move_to_hub_spawn(self):
        bounds = current_room_bounds()
        self.rect.center = (bounds.centerx, bounds.centery + 120)

    def move_to_room_spawn(self):
        self.rect.center = current_room_bounds().center

    def handle_movement_input(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if keys[pygame.K_1]:
            self.switch_weapon("pistol")
        if keys[pygame.K_2]:
            self.switch_weapon("knife")
        if keys[pygame.K_3]:
            self.switch_weapon("sword")

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.move_direction = direction
        if abs(direction.x) > 0.1:
            self.facing_x = 1 if direction.x > 0 else -1

        if self.dash_timer > 0:
            self.velocity = self.dash_direction * DASH_SPEED
        else:
            speed = self.speed * (GHOST_SPEED_MULTIPLIER if self.ghost_timer > 0 else 1.0)
            self.velocity = direction * speed

    def try_dash(self):
        return self.try_active_skill() is not None

    def switch_weapon(self, key):
        if key not in self.weapons:
            return
        self.cancel_tea()
        self.active_weapon_key = key
        self.active_weapon = self.weapons[key]
        self.last_upgrade_text = f"Weapon: {self.active_weapon.name}"

    def try_weapon_attack(self):
        if self.tea_state is not None:
            return None
        if self.weapon_cooldown_timer > 0:
            return None
        attack = self.active_weapon.attack(self)
        self.weapon_cooldown_timer = self.active_weapon.cooldown
        return attack

    def try_active_skill(self):
        if self.skill_cooldown_timer > 0 or self.dash_timer > 0:
            return None

        skill = self.active_skill
        self.skill_cooldown_timer = PLAYER_SKILL_COOLDOWN * getattr(self, "skill_cooldown_multiplier", 1.0)

        if skill == "dash":
            if self.move_direction.length_squared() > 0:
                self.dash_direction = self.move_direction.copy()
            else:
                self.dash_direction = self.aim_direction.copy()
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            self.dash_strike_hit_ids.clear()
            self.dash_refund_this_dash = 0.0
            self.invulnerable_timer = max(self.invulnerable_timer, DASH_DURATION + 0.50 + getattr(self, "dash_invuln_bonus", 0.0))
            return "dash"

        if skill == "blast":
            return "blast"

        if skill == "surge":
            self.surge_timer = SURGE_DURATION
            return "surge"

        if skill == "ghost":
            self.ghost_timer = GHOST_DURATION
            self.invulnerable_timer = max(self.invulnerable_timer, GHOST_DURATION)
            return "ghost"

        return None

    def update_aim(self, target_world_pos):
        direction = pygame.Vector2(
            target_world_pos.x - self.rect.centerx,
            target_world_pos.y - self.rect.centery,
        )
        if direction.length_squared() > 0:
            self.aim_direction = direction.normalize()
            if abs(self.aim_direction.x) > 0.1:
                self.facing_x = 1 if self.aim_direction.x > 0 else -1

    def update(self, dt, solid_rects=None):
        if solid_rects is None:
            solid_rects = []

        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        if self.dash_timer > 0:
            self.dash_timer = max(0, self.dash_timer - dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer = max(0, self.dash_cooldown_timer - dt)
        if self.skill_cooldown_timer > 0:
            self.skill_cooldown_timer = max(0, self.skill_cooldown_timer - dt)
        if self.surge_timer > 0:
            self.surge_timer = max(0, self.surge_timer - dt)
        if self.ghost_timer > 0:
            self.ghost_timer = max(0, self.ghost_timer - dt)
        if self.gun_shoot_timer > 0:
            self.gun_shoot_timer = max(0, self.gun_shoot_timer - dt)
        if self.knife_attack_timer > 0:
            self.knife_attack_timer = max(0, self.knife_attack_timer - dt)
        if self.sword_attack_timer > 0:
            self.sword_attack_timer = max(0, self.sword_attack_timer - dt)
        if self.weapon_cooldown_timer > 0:
            self.weapon_cooldown_timer = max(0, self.weapon_cooldown_timer - dt)
        if self.engineer_helper_timer > 0:
            self.engineer_helper_timer = max(0, self.engineer_helper_timer - dt)
        if self.engineer_drone_attack_flash > 0:
            self.engineer_drone_attack_flash = max(0, self.engineer_drone_attack_flash - dt)
        if self.engineer_blade_hit_flash > 0:
            self.engineer_blade_hit_flash = max(0, self.engineer_blade_hit_flash - dt)
        if self.engineer_bomber_explosion_flash > 0:
            self.engineer_bomber_explosion_flash = max(0, self.engineer_bomber_explosion_flash - dt)
        if self.engineer_airstrike_cooldown_timer > 0:
            self.engineer_airstrike_cooldown_timer = max(0, self.engineer_airstrike_cooldown_timer - dt)
        if self.vampire_feed_flash > 0:
            self.vampire_feed_flash = max(0, self.vampire_feed_flash - dt)
        if self.vampire_feast_timer > 0:
            self.vampire_feast_timer = max(0, self.vampire_feast_timer - dt)
        if self.vampire_blood_moon_timer > 0:
            self.vampire_blood_moon_timer = max(0, self.vampire_blood_moon_timer - dt)
        if self.vampire_blood_moon_cooldown_timer > 0:
            self.vampire_blood_moon_cooldown_timer = max(0, self.vampire_blood_moon_cooldown_timer - dt)
        self._update_engineer_drone(dt)
        self._update_engineer_blades(dt)
        self._update_engineer_bomber_visual(dt)
        self._update_ninja_momentum(dt)
        self._update_tea(dt)
        self.anim_time += dt
        self._update_dash_ghosts(dt)

        self.rect.x += round(self.velocity.x * dt)

        for solid in solid_rects:
            if self.rect.colliderect(solid):
                if self.velocity.x > 0:
                    self.rect.right = solid.left
                elif self.velocity.x < 0:
                    self.rect.left = solid.right

        self.rect.y += round(self.velocity.y * dt)

        for solid in solid_rects:
            if self.rect.colliderect(solid):
                if self.velocity.y > 0:
                    self.rect.bottom = solid.top
                elif self.velocity.y < 0:
                    self.rect.top = solid.bottom

        self.rect.clamp_ip(current_room_rect())

    def _update_engineer_drone(self, dt):
        if not self.engineer_helper_enabled:
            self.engineer_drone_pos.update(self.rect.center)
            self.engineer_drone_positions = []
            self.engineer_drone_target_id = None
            return
        self.engineer_drone_angle = (self.engineer_drone_angle + dt * 2.2) % 6.28318
        count = max(1, getattr(self, "engineer_gun_count", 1))
        previous = list(getattr(self, "engineer_drone_positions", []))
        positions = []
        for index in range(count):
            angle = self.engineer_drone_angle + (6.28318 / count) * index
            offset = pygame.Vector2(62, -36).rotate_rad(angle)
            target = pygame.Vector2(self.rect.center) + offset
            if index < len(previous):
                current = previous[index] + (target - previous[index]) * min(1.0, dt * 9.0)
            else:
                current = target
            positions.append(current)
        self.engineer_drone_positions = positions
        self.engineer_drone_pos.update(positions[0])

    def _update_engineer_blades(self, dt):
        self.engineer_blade_hit_timers = {
            enemy_id: max(0.0, timer - dt)
            for enemy_id, timer in self.engineer_blade_hit_timers.items()
            if timer - dt > 0
        }
        if self.engineer_blade_count <= 0:
            self.engineer_blade_positions = []
            self.engineer_blade_trail = []
            self.engineer_blade_overdrive_timer = 0.0
            return
        if self.engineer_blade_overdrive_timer > 0:
            self.engineer_blade_overdrive_timer = max(0.0, self.engineer_blade_overdrive_timer - dt)
            if self.engineer_blade_overdrive_timer <= 0:
                self.engineer_blade_overdrive_cooldown_timer = self.engineer_blade_overdrive_cooldown
        elif self.engineer_blade_overdrive_cooldown > 0:
            self.engineer_blade_overdrive_cooldown_timer = max(0.0, self.engineer_blade_overdrive_cooldown_timer - dt)
            if self.engineer_blade_overdrive_cooldown_timer <= 0:
                self.engineer_blade_overdrive_timer = self.engineer_blade_overdrive_duration
        overdrive = self.engineer_blade_overdrive_timer > 0
        speed = self.engineer_blade_orbit_speed * (1.55 if overdrive else 1.0)
        radius = self.engineer_blade_radius + (self.engineer_blade_overdrive_radius_bonus if overdrive else 0)
        self.engineer_blade_angle = (self.engineer_blade_angle + dt * speed) % 6.28318
        self.engineer_blade_spin_angle = (self.engineer_blade_spin_angle + dt * ENGINEER_BLADE_SPIN_SPEED * (1.35 if overdrive else 1.0)) % 6.28318
        positions = []
        for index in range(self.engineer_blade_count):
            angle = self.engineer_blade_angle + (6.28318 / self.engineer_blade_count) * index
            offset = pygame.Vector2(radius, 0).rotate_rad(angle)
            positions.append(pygame.Vector2(self.rect.center) + offset)
        self.engineer_blade_positions = positions
        if positions:
            self.engineer_blade_trail.append({
                "positions": [pygame.Vector2(pos) for pos in positions],
                "spin_angle": self.engineer_blade_spin_angle,
            })
            self.engineer_blade_trail = self.engineer_blade_trail[-ENGINEER_BLADE_TRAIL_LIMIT:]

    def _update_engineer_bomber_visual(self, dt):
        if self.engineer_bomber_max_runs <= 0:
            self.engineer_bomber_state = "inactive"
            self.engineer_bomber_pos.update(self.rect.center)
            return
        if self.engineer_bomber_state in ("inactive", "ready", "cooldown"):
            launch = self.engineer_bomber_launch_pos()
            self.engineer_bomber_pos += (launch - self.engineer_bomber_pos) * min(1.0, dt * 6.0)

    def engineer_bomber_launch_pos(self):
        return pygame.Vector2(self.rect.center) + pygame.Vector2(-62, -46)

    def reset_engineer_scene_state(self):
        self.engineer_drone_target_id = None
        self.engineer_helper_timer = 0.0
        self.engineer_drone_positions = []
        self.engineer_blade_hit_timers.clear()
        self.engineer_blade_trail = []
        self.engineer_blade_overdrive_timer = 0.0
        self.engineer_blade_overdrive_cooldown_timer = 0.0 if self.engineer_blade_overdrive_cooldown <= 0 else 1.0
        self.engineer_bomber_target_id = None
        self.engineer_bomber_target_pos.update(self.rect.center)
        self.engineer_bomber_pos.update(self.engineer_bomber_launch_pos())
        self.engineer_bomber_runs_remaining = 0
        self.engineer_bomber_timer = 0.0
        self.engineer_bomber_state = "ready" if self.engineer_bomber_max_runs > 0 else "inactive"
        self.engineer_airstrike_state = "ready" if self.engineer_airstrike_unlocked else "inactive"
        self.engineer_airstrike_timer = 0.0
        self.engineer_airstrike_cooldown_timer = 0.0
        self.engineer_airstrike_target_pos.update(self.rect.center)

    def reset_vampire_scene_state(self):
        self.vampire_blood_orbs.clear()
        self.vampire_feast_progress = 0
        self.vampire_feast_timer = 0.0
        self.vampire_blood_moon_timer = 0.0
        self.vampire_blood_moon_cooldown_timer = 0.0
        self.vampire_bat_state = "ready" if self.vampire_bat_enabled else "inactive"
        self.vampire_bat_timer = 0.0
        self.vampire_bat_search_timer = 0.0
        self.vampire_bat_pos.update(self.rect.center)
        self.vampire_bat_target_id = None
        self.vampire_bat_target_pos.update(self.rect.center)
        self.vampire_bat_carried_blood = 0
        self.vampire_bat_chain_kills = 0
        self.vampire_trail_hit_ids.clear()
        self.vampire_trail_harvested_this_dash = 0
        self.vampire_trail_timer = 0.0

    def _update_ninja_momentum(self, dt):
        if not self.ninja_momentum_enabled:
            self.ninja_momentum = 0.0
            return
        cap = max(0.0, self.ninja_momentum_max)
        if cap <= 0:
            self.ninja_momentum = 0.0
            return
        moving = self.move_direction.length_squared() > 0 or self.dash_timer > 0
        if moving:
            self.ninja_momentum = min(cap, self.ninja_momentum + max(0.0, self.ninja_momentum_gain) * dt)
        else:
            self.ninja_momentum = max(0.0, self.ninja_momentum - 0.55 * dt)

    def grant_dash_refund(self, amount):
        cap = max(0.0, getattr(self, "dash_refund_cap", 0.0))
        remaining = max(0.0, cap - getattr(self, "dash_refund_this_dash", 0.0))
        applied = min(max(0.0, amount), remaining)
        if applied <= 0:
            return 0.0
        self.dash_refund_this_dash += applied
        self.skill_cooldown_timer = max(0.0, self.skill_cooldown_timer - applied)
        self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - applied)
        return applied

    def add_blood(self, amount, source="generic"):
        if self.vampire_max_blood <= 0 or amount <= 0:
            return 0
        before = self.vampire_blood
        self.vampire_blood = min(self.vampire_max_blood, self.vampire_blood + int(amount))
        gained = self.vampire_blood - before
        if gained > 0:
            self.vampire_feed_flash = 0.35
            self._advance_vampire_feast(gained)
        return gained

    def _advance_vampire_feast(self, amount):
        if not self.vampire_feast_unlocked:
            return
        self.vampire_feast_progress += int(amount)
        threshold = max(1, self.vampire_feast_threshold)
        if self.vampire_feast_progress < threshold:
            return
        self.vampire_feast_progress = 0
        if self.vampire_blood_moon_unlocked and self.vampire_blood_moon_cooldown_timer <= 0:
            self.vampire_blood_moon_timer = self.vampire_blood_moon_duration
            self.vampire_blood_moon_cooldown_timer = self.vampire_blood_moon_cooldown
        self.vampire_feast_timer = max(self.vampire_feast_timer, self.vampire_feast_duration)

    def vampire_orb_attraction_radius(self):
        radius = getattr(self, "vampire_orb_attract_radius", 96)
        if self.vampire_feast_timer > 0:
            radius += 70
        if self.vampire_blood_moon_timer > 0:
            radius += 90
        return radius + getattr(self, "vampire_blood_capacity_bonus", 0) * 4

    def vampire_bat_rest_cooldown(self):
        cooldown = getattr(self, "vampire_bat_cooldown", 0.0)
        if self.vampire_feast_timer > 0:
            cooldown *= 0.72
        if self.vampire_blood_moon_timer > 0:
            cooldown *= 0.55
        return cooldown

    def _update_dash_ghosts(self, dt):
        for ghost in self.dash_ghosts:
            ghost["life"] -= dt
        self.dash_ghosts = [ghost for ghost in self.dash_ghosts if ghost["life"] > 0]

        if self.dash_timer <= 0:
            self.dash_ghost_emit_timer = 0.0
            return

        self.dash_ghost_emit_timer -= dt
        if self.dash_ghost_emit_timer > 0:
            return

        image = self._current_player_sprite()
        if image is None:
            return

        self.dash_ghosts.append({
            "image": image.copy(),
            "center": self.rect.center,
            "life": DASH_GHOST_LIFE,
            "max_life": DASH_GHOST_LIFE,
        })
        self.dash_ghost_emit_timer = DASH_GHOST_INTERVAL

    def take_damage(self, amount):
        if getattr(self, "dev_god_mode", False):
            return False
        if self.invulnerable_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable_timer = PLAYER_INVULNERABLE_TIME
        return True

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def add_xp(self, amount):
        self.xp += int(amount)
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = xp_required_for_level(self.level)
            self.pending_level_ups += 1
            leveled = True
        return leveled

    def consume_pending_level_up(self):
        if self.pending_level_ups <= 0:
            return False
        self.pending_level_ups -= 1
        return True

    def add_gold(self, amount):
        self.gold += amount

    def spend_gold(self, amount):
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def is_dead(self):
        return self.health <= 0

    def draw(self, surface, camera):
        if self._draw_sprite(surface, camera):
            return

        sr = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        dashing = self.dash_timer > 0 or self.ghost_timer > 0
        invuln  = self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0

        if dashing:
            body_col  = (100, 220, 255)
            head_col  = (140, 235, 255)
            visor_col = (0,  180, 230)
            glow_col  = (80, 200, 255)
        elif invuln:
            body_col  = (120, 170, 255)
            head_col  = (150, 190, 255)
            visor_col = (60,  120, 220)
            glow_col  = (100, 150, 255)
        else:
            body_col  = (42,  110, 200)
            head_col  = (60,  150, 230)
            visor_col = (20,   60, 140)
            glow_col  = (80,  160, 255)

        # --- dash trail ---
        if dashing:
            trail_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(trail_surf, (*glow_col, 40), (4, 4, w + 12, h + 12), border_radius=8)
            surface.blit(trail_surf, (x - 10, y - 10))

        # --- legs ---
        leg_w, leg_h = w // 3 - 1, h // 3
        leg_y = y + h - 2
        pygame.draw.rect(surface, (30, 80, 160),
                         (x + 3, leg_y, leg_w, leg_h), border_radius=3)
        pygame.draw.rect(surface, (30, 80, 160),
                         (x + w - leg_w - 3, leg_y, leg_w, leg_h), border_radius=3)

        # --- body ---
        pygame.draw.rect(surface, body_col, sr, border_radius=6)

        # armour highlight on body top
        highlight = pygame.Rect(x + 3, y + 3, w - 6, h // 3)
        pygame.draw.rect(surface, (*head_col, 80),
                         highlight, border_radius=4)

        # chest detail line
        pygame.draw.line(surface, visor_col,
                         (cx - 4, cy - 2), (cx + 4, cy - 2), 2)

        # --- gun arm pointing toward aim ---
        aim = self.aim_direction
        arm_len  = 14
        gun_len  = 18
        arm_start = pygame.Vector2(cx, cy - 2)
        arm_end   = arm_start + aim * arm_len
        gun_end   = arm_end   + aim * gun_len

        pygame.draw.line(surface, body_col,
                         (round(arm_start.x), round(arm_start.y)),
                         (round(arm_end.x),   round(arm_end.y)), 5)

        # gun barrel
        perp = pygame.Vector2(-aim.y, aim.x)
        g1 = arm_end + perp * 2
        g2 = arm_end - perp * 2
        g3 = gun_end - perp * 2
        g4 = gun_end + perp * 2
        gun_pts = [(round(p.x), round(p.y)) for p in (g1, g2, g3, g4)]
        pygame.draw.polygon(surface, (25, 25, 40), gun_pts)
        pygame.draw.line(surface, (80, 80, 100),
                         (round(arm_end.x), round(arm_end.y)),
                         (round(gun_end.x), round(gun_end.y)), 1)

        # muzzle dot
        pygame.draw.circle(surface, (255, 220, 100),
                           (round(gun_end.x), round(gun_end.y)), 2)

        # --- head (sits above body) ---
        head_w = w - 4
        head_h = h // 2 - 2
        head_x = x + 2
        head_y = y - head_h + 4
        head_rect = pygame.Rect(head_x, head_y, head_w, head_h)
        pygame.draw.rect(surface, head_col, head_rect, border_radius=5)

        # visor bar
        visor_rect = pygame.Rect(head_x + 4, head_y + head_h // 3, head_w - 8, head_h // 3)
        pygame.draw.rect(surface, visor_col, visor_rect, border_radius=2)

        # visor glow dots (eyes)
        eye_y = visor_rect.centery
        pygame.draw.circle(surface, (120, 220, 255), (head_x + 8,  eye_y), 3)
        pygame.draw.circle(surface, (120, 220, 255), (head_x + head_w - 8, eye_y), 3)

        # head top shine
        pygame.draw.rect(surface, (*head_col, 120),
                         pygame.Rect(head_x + 3, head_y + 2, head_w - 6, 3),
                         border_radius=2)

        # --- invuln blink ring ---
        if invuln:
            pygame.draw.circle(surface, (*glow_col, 90),
                               (cx, cy), w // 2 + 6, 2)

    def receive_tea(self):
        self.tea_state = "holding"
        self.tea_drink_timer = 0.0
        self.last_upgrade_text = "Tea acquired"

    def start_drinking_tea(self):
        if self.tea_state != "holding":
            return False
        self.tea_state = "drinking"
        self.tea_drink_timer = 0.0
        self.last_upgrade_text = "Drinking tea"
        return True

    def cancel_tea(self):
        self.tea_state = None
        self.tea_drink_timer = 0.0

    def _update_tea(self, dt):
        if self.tea_state != "drinking":
            return
        self.tea_drink_timer += dt
        frames = Player._tea_drink_frames or []
        duration = 0.75 if frames else 0.55
        if self.tea_drink_timer >= duration:
            self.cancel_tea()
            self.last_upgrade_text = f"Weapon: {self.active_weapon.name}"

    def _draw_sprite(self, surface, camera):
        sprite = self._current_player_sprite()
        if sprite is None:
            return False

        sr = camera.apply_rect(self.rect)
        sprite_rect = sprite.get_rect(center=sr.center)
        self._draw_shadow(surface, sr)
        self._draw_dash_ghosts(surface, camera)

        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0:
            ring_color = (100, 150, 255, 90)
            pygame.draw.circle(surface, ring_color, sr.center, sr.width // 2 + 10, 2)

        surface.blit(sprite, sprite_rect)
        self._draw_sprite_weapon(surface, sr)
        self._draw_engineer_drone(surface, camera)
        self._draw_engineer_blades(surface, camera)
        self._draw_engineer_bomber(surface, camera)
        self._draw_blood_pickups(surface, camera)
        self._draw_blood_bat(surface, camera)
        self._draw_vampire_states(surface, sr)
        self._draw_blood_orb(surface, sr)
        return True

    def _current_player_sprite(self):
        frames = Player._sprite_frames or []
        if not frames:
            return None

        if self.dash_timer > 0 or self.ghost_timer > 0:
            frame_index = 2 if len(frames) > 2 else 0
        else:
            blink_cycle = self.anim_time % 3.2
            frame_index = 3 if blink_cycle > 3.0 and len(frames) > 3 else 0

        sprite = frames[min(frame_index, len(frames) - 1)]
        if self.facing_x < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        return sprite

    def _draw_dash_ghosts(self, surface, camera):
        for ghost in self.dash_ghosts:
            progress = max(0.0, min(1.0, ghost["life"] / ghost["max_life"]))
            image = ghost["image"].copy()
            image.set_alpha(int(95 * progress))
            pos = camera.apply_pos(pygame.Vector2(ghost["center"]))
            rect = image.get_rect(center=(round(pos.x), round(pos.y)))
            surface.blit(image, rect)

    def _draw_shadow(self, surface, screen_rect):
        frames = Player._shadow_frames or []
        if frames:
            shadow = frames[int(self.anim_time * 6) % len(frames)]
        else:
            return
        shadow_rect = shadow.get_rect(center=(screen_rect.centerx, screen_rect.bottom + 6))
        surface.blit(shadow, shadow_rect)

    def _draw_engineer_drone(self, surface, camera):
        if not self.engineer_helper_enabled:
            return
        positions = self.engineer_drone_positions or [self.engineer_drone_pos]
        for index, drone_pos in enumerate(positions):
            pos = camera.apply_pos(drone_pos)
            center = (round(pos.x), round(pos.y))
            flash = self.engineer_drone_attack_flash > 0
            body = (80, 210, 255) if flash else (70, 150, 210)
            core = (255, 245, 160) if flash else (185, 235, 255)
            pygame.draw.circle(surface, (10, 25, 35), center, 13)
            pygame.draw.circle(surface, body, center, 11, 2)
            pygame.draw.circle(surface, core, center, 4)
            pygame.draw.line(surface, (70, 150, 210), (center[0] - 15, center[1]), (center[0] + 15, center[1]), 2)
            pygame.draw.line(surface, (70, 150, 210), (center[0], center[1] - 15), (center[0], center[1] + 15), 2)
            if len(positions) > 1:
                pygame.draw.circle(surface, (255, 245, 160), (center[0] + 8, center[1] - 8), 2 + index)

    def _draw_engineer_blades(self, surface, camera):
        overdrive = self.engineer_blade_overdrive_timer > 0
        blade_image = Player._engineer_blade_image
        if blade_image is not None:
            ghost_count = 4 if overdrive else 2
            trail = self.engineer_blade_trail[:-1][-ghost_count:]
            for trail_index, ghost in enumerate(trail):
                progress = (trail_index + 1) / max(1, len(trail))
                alpha = int((72 if overdrive else 38) * progress)
                self._draw_engineer_blade_sprites(surface, camera, ghost["positions"], ghost["spin_angle"], alpha)
            self._draw_engineer_blade_sprites(surface, camera, self.engineer_blade_positions, self.engineer_blade_spin_angle, 255)
        else:
            for pos in self.engineer_blade_positions:
                screen = camera.apply_pos(pos)
                center = (round(screen.x), round(screen.y))
                color = (255, 230, 85) if overdrive else ((255, 210, 90) if self.engineer_blade_hit_flash > 0 else (180, 225, 245))
                pygame.draw.circle(surface, (25, 35, 45), center, 11)
                pygame.draw.circle(surface, color, center, 10, 2)
                pygame.draw.line(surface, color, (center[0] - 14, center[1]), (center[0] + 14, center[1]), 3)
                pygame.draw.line(surface, color, (center[0], center[1] - 14), (center[0], center[1] + 14), 3)
        if self.engineer_blade_radius:
            player_screen = camera.apply_pos(pygame.Vector2(self.rect.center))
            radius = self.engineer_blade_radius + (self.engineer_blade_overdrive_radius_bonus if overdrive else 0)
            pygame.draw.circle(surface, (255, 210, 90) if overdrive else (80, 130, 150), (round(player_screen.x), round(player_screen.y)), radius, 2 if overdrive else 1)

    def _draw_engineer_blade_sprites(self, surface, camera, positions, spin_angle, alpha):
        image = Player._engineer_blade_image
        if image is None:
            return
        rotated = pygame.transform.rotozoom(image, -spin_angle * 57.2958, 1.0)
        if alpha < 255:
            rotated = rotated.copy()
            rotated.set_alpha(alpha)
        for pos in positions:
            screen = camera.apply_pos(pos)
            rect = rotated.get_rect(center=(round(screen.x), round(screen.y)))
            surface.blit(rotated, rect)

    def _draw_engineer_bomber(self, surface, camera):
        if self.engineer_bomber_max_runs <= 0 or self.engineer_bomber_state == "inactive":
            return
        centers = [self.engineer_bomber_pos]
        if self.engineer_bomber_count > 1 and self.engineer_bomber_state not in ("flying",):
            centers.append(pygame.Vector2(self.rect.center) + pygame.Vector2(62, -46))
        for bomber_pos in centers:
            pos = camera.apply_pos(bomber_pos)
            center = (round(pos.x), round(pos.y))
            if self.engineer_bomber_state == "cooldown":
                ratio = 1.0 - min(1.0, self.engineer_bomber_timer / max(0.01, self.engineer_bomber_cooldown))
                pygame.draw.circle(surface, (45, 30, 22), center, 10)
                pygame.draw.arc(surface, (255, 150, 70), pygame.Rect(center[0] - 13, center[1] - 13, 26, 26), 0, ratio * 6.28318, 3)
                continue
            color = (255, 95, 55) if self.engineer_bomber_state == "flying" else (255, 170, 80)
            pygame.draw.circle(surface, (40, 18, 10), center, 13)
            pygame.draw.polygon(surface, color, [(center[0], center[1] - 13), (center[0] + 13, center[1]), (center[0], center[1] + 13), (center[0] - 13, center[1])])
            pygame.draw.circle(surface, (255, 235, 150), center, 4)
            if self.engineer_bomber_explosion_flash > 0:
                pygame.draw.circle(surface, (255, 120, 45), center, self.engineer_bomber_radius, 3)
        if self.engineer_airstrike_state == "telegraph":
            target = camera.apply_pos(self.engineer_airstrike_target_pos)
            center = (round(target.x), round(target.y))
            pygame.draw.circle(surface, (255, 70, 45), center, self.engineer_airstrike_radius, 3)
            pygame.draw.line(surface, (255, 220, 120), (center[0] - 22, center[1]), (center[0] + 22, center[1]), 3)
            pygame.draw.line(surface, (255, 220, 120), (center[0], center[1] - 22), (center[0], center[1] + 22), 3)

    def _draw_blood_orb(self, surface, screen_rect):
        if self.vampire_max_blood <= 0:
            return
        ratio = self.vampire_blood / max(1, self.vampire_max_blood)
        center = (screen_rect.centerx - 24, screen_rect.top - 12)
        radius = 5 + round(5 * ratio)
        color = (240, 50, 85) if self.vampire_feed_flash > 0 else (150, 25, 45)
        pygame.draw.circle(surface, (30, 0, 8), center, 11)
        pygame.draw.circle(surface, color, center, radius)
        pygame.draw.circle(surface, (255, 170, 185), center, 11, 1)

    def _draw_blood_pickups(self, surface, camera):
        for orb in self.vampire_blood_orbs:
            pos = camera.apply_pos(orb["pos"])
            center = (round(pos.x), round(pos.y))
            pulse = 2 if self.vampire_feast_timer > 0 else 0
            pygame.draw.circle(surface, (40, 0, 12), center, 8 + pulse)
            pygame.draw.circle(surface, (230, 35, 75), center, 5 + pulse)
            pygame.draw.circle(surface, (255, 155, 175), center, 8 + pulse, 1)

    def _draw_blood_bat(self, surface, camera):
        if not self.vampire_bat_enabled or self.vampire_bat_state == "inactive":
            return
        pos = camera.apply_pos(self.vampire_bat_pos)
        center = (round(pos.x), round(pos.y))
        color = (255, 80, 110) if self.vampire_bat_carried_blood > 0 else (130, 25, 55)
        pygame.draw.circle(surface, (25, 0, 10), center, 7)
        pygame.draw.polygon(surface, color, [(center[0] - 16, center[1]), (center[0] - 5, center[1] - 6), (center[0], center[1])])
        pygame.draw.polygon(surface, color, [(center[0] + 16, center[1]), (center[0] + 5, center[1] - 6), (center[0], center[1])])
        pygame.draw.circle(surface, (255, 160, 180), center, 3)

    def _draw_vampire_states(self, surface, screen_rect):
        if self.vampire_blood_moon_timer > 0:
            pygame.draw.circle(surface, (170, 20, 45), screen_rect.center, screen_rect.width // 2 + 24, 3)
            pygame.draw.circle(surface, (255, 90, 120), (screen_rect.centerx + 22, screen_rect.top - 24), 9)
        elif self.vampire_feast_timer > 0:
            pygame.draw.circle(surface, (220, 35, 75), screen_rect.center, screen_rect.width // 2 + 15, 2)

    def _draw_sprite_weapon(self, surface, screen_rect):
        if self._draw_tea_item(surface, screen_rect):
            return

        aim = self.aim_direction
        shoulder = self._weapon_shoulder(screen_rect.center)
        weapon_image = self._current_weapon_image()
        if weapon_image is not None:
            rotated = self._rotated_weapon(weapon_image, aim)
            center = shoulder + aim * GUN_CENTER_REACH
            weapon_rect = rotated.get_rect(center=(round(center.x), round(center.y)))
            surface.blit(rotated, weapon_rect)
            return

        start = shoulder + aim * 3
        end = shoulder + aim * 29
        side = pygame.Vector2(-aim.y, aim.x)
        points = [
            start + side * 3,
            start - side * 3,
            end - side * 2,
            end + side * 2,
        ]
        pygame.draw.polygon(surface, (22, 24, 36), [(round(p.x), round(p.y)) for p in points])
        pygame.draw.circle(surface, (255, 220, 100), (round(end.x), round(end.y)), 2)

    def _draw_tea_item(self, surface, screen_rect):
        if self.tea_state is None:
            return False

        image = None
        if self.tea_state == "drinking":
            frames = Player._tea_drink_frames or []
            if frames:
                progress = min(0.999, self.tea_drink_timer / 0.75)
                frame_index = min(len(frames) - 1, int(progress * len(frames)))
                image = frames[frame_index]
        if image is None:
            image = Player._tea_full_image

        shoulder = self._weapon_shoulder(screen_rect.center)
        offset = self.aim_direction * 26
        center = shoulder + offset
        if image is not None:
            surface.blit(image, image.get_rect(center=(round(center.x), round(center.y))))
        else:
            pygame.draw.circle(surface, (180, 235, 190), (round(center.x), round(center.y)), 10)
            pygame.draw.circle(surface, (90, 55, 30), (round(center.x), round(center.y)), 11, 2)
        return True

    def _weapon_shoulder(self, center):
        return pygame.Vector2(
            center[0] + GUN_SHOULDER_OFFSET[0],
            center[1] + GUN_SHOULDER_OFFSET[1],
        )

    def weapon_muzzle_position(self):
        return self._weapon_shoulder(self.rect.center) + self.aim_direction * GUN_MUZZLE_REACH

    def trigger_gun_shot(self):
        self.gun_shoot_timer = GUN_SHOOT_ANIM_SECONDS

    def trigger_knife_attack(self):
        self.knife_attack_timer = KNIFE_ATTACK_ANIM_SECONDS

    def trigger_sword_attack(self):
        self.sword_attack_timer = SWORD_ATTACK_ANIM_SECONDS

    def _current_weapon_image(self):
        if self.active_weapon_key == "knife":
            return self._current_knife_image()
        if self.active_weapon_key == "sword":
            return self._current_sword_image()
        return self._current_gun_image()

    def _current_knife_image(self):
        frames = Player._knife_frames or []
        if self.knife_attack_timer > 0 and frames:
            progress = 1.0 - (self.knife_attack_timer / KNIFE_ATTACK_ANIM_SECONDS)
            frame_index = min(len(frames) - 1, max(0, int(progress * len(frames))))
            return frames[frame_index]
        return Player._knife_image

    def _current_gun_image(self):
        frames = Player._gun_shoot_frames or []
        if self.gun_shoot_timer > 0 and frames:
            progress = 1.0 - (self.gun_shoot_timer / GUN_SHOOT_ANIM_SECONDS)
            frame_index = min(len(frames) - 1, max(0, int(progress * len(frames))))
            return frames[frame_index]
        return Player._gun_image

    def _current_sword_image(self):
        frames = Player._sword_hit_frames or []
        if self.sword_attack_timer > 0 and frames:
            progress = 1.0 - (self.sword_attack_timer / SWORD_ATTACK_ANIM_SECONDS)
            frame_index = min(len(frames) - 1, max(0, int(progress * len(frames))))
            return frames[frame_index]
        return Player._sword_image

    def _rotated_weapon(self, image, aim):
        aim_angle = aim.as_polar()[1]
        if aim.x < 0:
            image = pygame.transform.flip(image, True, False)
            return pygame.transform.rotate(image, -(aim_angle - 180))
        return pygame.transform.rotate(image, -aim_angle)
