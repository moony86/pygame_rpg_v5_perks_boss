import os
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

from settings import (
    ENEMY_CONTACT_COOLDOWN,
    ENEMY_DAMAGE,
    ENEMY_XP_REWARD,
    ENEMY_SPAWN_SAFE_RADIUS,
    DEV_TOOLS_ENABLED,
    JUMPER_ATTACK_RANGE,
    MAP_SIZE,
    PROJECTILE_DAMAGE,
    RANGED_ATTACK_RANGE,
    ROOMS_TO_BOSS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from game_state import GameState
from entities.enemy import EnemyType
from entities.player import Player
from entities.enemy import Enemy
from entities.enemy_bullet import EnemyBullet
from entities.pickup import Pickup
from systems.combat_system import CombatSystem
from systems.effects import EffectsSystem
from systems.dev_tools import DevTools
from systems.perk_system import (
    OFFICIAL_STARTER_BUILDS,
    PERK_EFFECTS,
    PERK_REROLL_GOLD_COST,
    STARTER_BUILD_CARDS,
    PerkSystem,
)
from entities.projectile import Projectile
from systems.shooting_system import ShootingSystem
from ui.hud import hud_occupied_rects, vampire_hud_data, vampire_hud_rect, vampire_hud_visible
from systems.room_system import ROOM_PLAN, RoomSystem, RoomType, room_type_for_number
from systems.spawn_system import SpawnSystem, SPAWN_BODY_SIZE
from systems.wave_system import WaveSystem
from systems.wave_system import BUILD_POWER_INFLUENCE_BY_ROOM, DEFAULT_BUILD_POWER_INFLUENCE, ROOM_1_GROUP_HARD_CAP, ROOM_1_GROUP_SATURATION_CAP
from systems.definition_registry import definition_registry
from systems.loot_system import LootSystem
from ui.perk_screen import _build_badge_text
from states.combat_state import collect_exit_loot
from systems.room_flow import RoomFlowSystem
from systems.xp_progression import cumulative_xp_for_level, xp_required_for_level
from systems.xp_budget import (
    STAGE_COMPLETION_XP,
    STAGE_EXPECTED_ENEMY_XP,
    STAGE_ROOM_TARGET_LEVELS,
    award_stage_room_completion_xp,
    award_room_completion_xp,
    expected_stage_cumulative_xp_after_boss,
    expected_stage_cumulative_xp_after_room,
)
from states.hub_state import handle_hub_events, should_enter_boss
from systems.boss_attack_system import BOSS_CLOSE_DASH_DISTANCE, BOSS_FAR_GRAVITY_DISTANCE, BossAttackSystem
from systems.room_bounds import HUB_ROOM_BOUNDS, current_room_bounds
from systems.scene_system import enter_boss, enter_hub
from systems.audio_system import SOUND_FILES
from systems.dialogue_system import DIALOGUE_BOTTOM_MARGIN, DIALOGUE_HEIGHT, DIALOGUE_WIDTH_RATIO
from systems.music_system import MUSIC_TRACKS, MusicSystem
from ui.dev_panel import CATEGORIES, DevPanel
from systems.horde_system import SpatialHashGrid, HordeSystem
from systems.sprite_animation import (
    SpriteSheetAnimation,
    animation_spec,
    detected_frame_count,
    load_animation_frames,
    sprite_animation_report,
)


class FakeCamera:
    def __init__(self, x, y):
        self.offset = pygame.Vector2(x, y)


class FakePlayer:
    def reset(self):
        self.__init__(self.rect.copy())

    def __init__(self, rect):
        self.rect = rect
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.xp = 0
        self.xp_to_next = xp_required_for_level(self.level)
        self.gold = 0
        self.pending_level_ups = 0
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
        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.projectile_count = 1
        self.spread_degrees = 0
        self.projectile_speed_bonus = 0
        self.split_damage_multiplier = 1.0
        self.pierce = 0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.75
        self.explosive_rounds = False
        self.explosion_radius = 95
        self.explosion_splash_ratio = 1 / 3
        self.regen_on_room_clear = 10
        self.max_health = 100
        self.health = 100
        self.speed = 400
        self.dash_cooldown_timer = 0.0
        self.skill_cooldown_multiplier = 1.0
        self.dash_invuln_bonus = 0.0
        self.knockback_power = 1.0
        self.move_direction = pygame.Vector2(0, 0)
        self.aim_direction = pygame.Vector2(1, 0)
        self.weapon_damage_multiplier = 1.0
        self.surge_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.skill_cooldown_timer = 0.0
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
        self.engineer_drone_pos = pygame.Vector2(rect.center)
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
        self.engineer_bomber_pos = pygame.Vector2(rect.center)
        self.engineer_bomber_target_pos = pygame.Vector2(rect.center)
        self.engineer_bomber_target_id = None
        self.engineer_bomber_explosion_flash = 0.0
        self.engineer_airstrike_unlocked = False
        self.engineer_airstrike_state = "inactive"
        self.engineer_airstrike_timer = 0.0
        self.engineer_airstrike_cooldown = 0.0
        self.engineer_airstrike_cooldown_timer = 0.0
        self.engineer_airstrike_target_pos = pygame.Vector2(rect.center)
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
        self.vampire_bat_pos = pygame.Vector2(rect.center)
        self.vampire_bat_target_id = None
        self.vampire_bat_target_pos = pygame.Vector2(rect.center)
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
        self.last_upgrade_text = ""
        self.active_weapon = SimpleNamespace(name="Test Gun")

    def build_power_score(self):
        return 0.0

    def add_xp(self, amount):
        self.xp += int(amount)
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = xp_required_for_level(self.level)
            self.pending_level_ups += 1

    def add_gold(self, amount):
        self.gold += amount

    def spend_gold(self, amount):
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return True

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def grant_dash_refund(self, amount):
        remaining = max(0.0, self.dash_refund_cap - self.dash_refund_this_dash)
        applied = min(max(0.0, amount), remaining)
        self.dash_refund_this_dash += applied
        self.skill_cooldown_timer = max(0.0, self.skill_cooldown_timer - applied)
        self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - applied)
        return applied

    def add_blood(self, amount, source="generic"):
        before = self.vampire_blood
        self.vampire_blood = min(self.vampire_max_blood, self.vampire_blood + int(amount))
        gained = self.vampire_blood - before
        if gained > 0:
            self._advance_vampire_feast(gained)
        return gained

    def _advance_vampire_feast(self, amount):
        if not self.vampire_feast_unlocked:
            return
        self.vampire_feast_progress += int(amount)
        if self.vampire_feast_progress >= self.vampire_feast_threshold:
            self.vampire_feast_progress = 0
            if self.vampire_blood_moon_unlocked and self.vampire_blood_moon_cooldown_timer <= 0:
                self.vampire_blood_moon_timer = self.vampire_blood_moon_duration
                self.vampire_blood_moon_cooldown_timer = self.vampire_blood_moon_cooldown
            self.vampire_feast_timer = max(self.vampire_feast_timer, self.vampire_feast_duration)

    def vampire_orb_attraction_radius(self):
        radius = self.vampire_orb_attract_radius
        if self.vampire_feast_timer > 0:
            radius += 70
        if self.vampire_blood_moon_timer > 0:
            radius += 90
        return radius

    def vampire_bat_rest_cooldown(self):
        cooldown = self.vampire_bat_cooldown
        if self.vampire_feast_timer > 0:
            cooldown *= 0.72
        if self.vampire_blood_moon_timer > 0:
            cooldown *= 0.55
        return cooldown

    def weapon_muzzle_position(self):
        return pygame.Vector2(self.rect.center) + self.aim_direction * 38

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
        self.engineer_bomber_state = "ready" if self.engineer_bomber_max_runs > 0 else "inactive"
        self.engineer_bomber_timer = 0.0
        self.engineer_airstrike_state = "ready" if self.engineer_airstrike_unlocked else "inactive"
        self.engineer_airstrike_timer = 0.0
        self.engineer_airstrike_cooldown_timer = 0.0


class FakeEnemy:
    def __init__(self, rect, health=30, enemy_type=EnemyType.CHASER):
        self.rect = rect
        self.health = health
        self.max_health = health
        self.type = enemy_type
        self.alive = True
        self.damage_multiplier = 1.0
        self.knockback_timer = 0.0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.alive = False
            return True
        return False


class FakeProjectile:
    def __init__(self, rect, damage=10):
        self.rect = rect
        self.damage = damage
        self.alive = True
        self.critical = False
        self.direction = pygame.Vector2(1, 0)
        self.knockback = 0
        self.explosive = False
        self.hit_ids = set()

    def can_hit(self, enemy):
        return id(enemy) not in self.hit_ids

    def register_hit(self, enemy):
        self.hit_ids.add(id(enemy))
        self.alive = False


class FakeEvents:
    def __init__(self):
        self.subscriptions = []
        self.emitted = []

    def subscribe(self, event_name, callback):
        self.subscriptions.append((event_name, callback))

    def emit(self, event_name, data=None):
        self.emitted.append((event_name, data))


class FakeClock:
    def get_fps(self):
        return 60.0


class FakeDevGame:
    def __init__(self):
        self.events = FakeEvents()
        self.player = FakePlayer(pygame.Rect(300, 300, 38, 38))
        self.perks = PerkSystem()
        self.clock = FakeClock()
        self.state = SimpleNamespace(name="ROOM")
        self.rooms = SimpleNamespace(room_type=SimpleNamespace(name="COMBAT"))
        self.room_number = 1
        self.camera = SimpleNamespace(offset=pygame.Vector2(0, 0))
        self.enemies = []
        self.projectiles = []
        self.enemy_bullets = []
        self.npcs = []
        self.room_exit_open = False
        self.music = SimpleNamespace(current_key="room")


class FakeToolPanel:
    def __init__(self):
        self.calls = 0

    def handle_event(self, event):
        self.calls += 1
        return True


class FakeWaveDesigner:
    def __init__(self):
        self.visible = False
        self.exported = False

    def toggle(self):
        self.visible = not self.visible

    def export(self):
        self.exported = True


class FakeAssetPipeline:
    def __init__(self):
        self.assets = []
        self.filter_type = "all"
        self.message = "ready"
        self.reported = False

    def export_report(self):
        self.reported = True


class FakeAssetBrowser:
    def __init__(self):
        self.visible = False
        self.pipeline = FakeAssetPipeline()
        self.calls = 0

    def toggle(self):
        self.visible = not self.visible

    def handle_event(self, event):
        self.calls += 1
        return True


class FakeAudio:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


class FakeMusic:
    def __init__(self):
        self.stopped = []

    def stop_music(self, fade_ms=0):
        self.stopped.append(fade_ms)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def check_room_system():
    rooms = RoomSystem()
    expected = ROOM_PLAN

    for room_number, room_type in expected.items():
        assert_true(room_type_for_number(room_number) == room_type, f"room plan helper mismatch for room {room_number}")
        selected = rooms.choose_next_room(room_number)
        assert_true(selected == room_type, f"room {room_number} selected {selected}, expected {room_type}")
        assert_true(rooms.target_kills >= 0, f"room {room_number} did not initialize target_kills")
        assert_true(rooms.survival_time > 0, f"room {room_number} did not initialize survival_time")

    rooms.choose_next_room(10)
    assert_true(rooms.reward_multiplier == 2, "curse room reward_multiplier should be 2")

    rooms.choose_next_room(1)
    assert_true(rooms.reward_multiplier == 1, "non-curse room reward_multiplier should be 1")


def check_spawn_system():
    spawn = SpawnSystem()
    camera = FakeCamera(1800, 1800)
    player_rect = pygame.Rect(2300, 2300, 38, 38)
    player_center = pygame.Vector2(player_rect.center)
    visible_rect = pygame.Rect(camera.offset.x, camera.offset.y, SCREEN_WIDTH, SCREEN_HEIGHT)

    for _ in range(25):
        x, y = spawn.get_spawn_position(camera, player_rect)
        assert_true(0 <= x <= MAP_SIZE - SPAWN_BODY_SIZE, f"spawn x outside map: {x}")
        assert_true(0 <= y <= MAP_SIZE - SPAWN_BODY_SIZE, f"spawn y outside map: {y}")

        center = pygame.Vector2(x + SPAWN_BODY_SIZE / 2, y + SPAWN_BODY_SIZE / 2)
        distance = center.distance_to(player_center)
        assert_true(distance >= ENEMY_SPAWN_SAFE_RADIUS, f"spawn too close to player: {distance:.1f}")
        assert_true(not visible_rect.collidepoint(center.x, center.y), "spawn center inside visible camera rect")


def check_wave_system():
    waves = WaveSystem()
    player = FakePlayer(pygame.Rect(0, 0, 38, 38))
    waves.reset(1, RoomType.COMBAT, player)

    assert_true(waves.active, "wave reset should activate waves")
    assert_true(waves.wave_state in ("group_spawning", "spawning", "done"), f"unexpected wave_state after reset: {waves.wave_state}")
    assert_true(len(waves.waves) > 0, "combat room should create waves")
    assert_true(all(wave.get("groups") for wave in waves.waves), "room 1 combat waves should use encounter groups")
    assert_true(len(waves.waves) == 1, "room 1 grouped ownership should keep all room 1 groups inside one grouped wave")
    assert_true(sum(wave.get("count", 0) for wave in waves.waves) == 65, "room 1 grouped design should preserve near-current enemy count")
    assert_true(waves.waves[0].get("spawn_queue") == [], "grouped wave should not use old wave spawn_queue")
    assert_true(waves.wave_mode == "grouped", "room 1 wave should report grouped mode")
    assert_true(not waves.legacy_clearing_gate_active, "legacy clearing gate should not own active grouped spawning")
    assert_true(waves.build_power_influence == BUILD_POWER_INFLUENCE_BY_ROOM[1], "room 1 should use reduced build power influence")
    sample_chaser = Enemy(0, 0, EnemyType.CHASER, difficulty=waves.waves[0]["enemy_difficulty_override"])
    sample_ranged = Enemy(0, 0, EnemyType.RANGED, difficulty=waves.waves[0]["enemy_difficulty_override"])
    chaser_stk = (sample_chaser.max_health + PROJECTILE_DAMAGE - 1) // PROJECTILE_DAMAGE
    ranged_stk = (sample_ranged.max_health + PROJECTILE_DAMAGE - 1) // PROJECTILE_DAMAGE
    assert_true(2 <= chaser_stk <= 3, f"room 1 chaser should be 2-3 base pistol shots, got {chaser_stk}")
    assert_true(2 <= ranged_stk <= 3, f"room 1 ranged should be 2-3 base pistol shots, got {ranged_stk}")

    created = []

    def spawn_position():
        return (100, 100)

    def enemy_factory(x, y, enemy_type, difficulty):
        enemy = SimpleNamespace(x=x, y=y, enemy_type=enemy_type, difficulty=difficulty, alive=True)
        created.append(enemy)
        return enemy

    guard = 0
    living = []
    saw_burst = False
    saw_group_release_with_living_enemies = False
    max_alive = 0
    while not waves.all_waves_spawned() and guard < 2000:
        before_group = waves.current_group_id
        spawned = waves.update(0.25, spawn_position, len(living), enemy_factory, living_enemies=living, player_rect=player.rect)
        saw_burst = saw_burst or len(spawned) > 1
        living.extend(spawned)
        max_alive = max(max_alive, len(living))
        if before_group != waves.current_group_id and living:
            saw_group_release_with_living_enemies = True
        if living and guard % 4 == 3:
            living.pop(0)
        if waves.wave_state == "clearing":
            living.clear()
        guard += 1

    assert_true(waves.all_waves_spawned(), "waves did not finish in controlled scenario")
    assert_true(len(created) > 0, "wave update did not create any enemies")
    assert_true(saw_burst, "room 1 grouped waves should spawn bursts, not pure single drip")
    assert_true(saw_group_release_with_living_enemies, "room 1 groups should release before full room clear")
    assert_true(max_alive <= ROOM_1_GROUP_HARD_CAP, f"room 1 grouped waves should respect hard cap, saw {max_alive}")
    assert_true(all(hasattr(enemy, "wave_group_id") for enemy in created), "grouped enemies should be tagged for debug tracking")
    assert_true(250 <= len(created) * 5 <= 400, "room 1 enemy XP should stay within requested range")
    assert_true(STAGE_EXPECTED_ENEMY_XP[1] == 780, "stage room 1 budget should use the current 39 enemy spawn plan at 20 XP")

    expected_release = WaveSystem()
    expected_release.reset(1, RoomType.COMBAT, player)
    expected_group = expected_release.waves[0]["groups"][0]
    expected_living = []
    for index in range(ROOM_1_GROUP_SATURATION_CAP):
        enemy = SimpleNamespace(alive=True, rect=pygame.Rect(index * 4, 0, 34, 34), enemy_type=EnemyType.CHASER)
        expected_living.append(enemy)
        expected_group["living_ids"].add(id(enemy))
    expected_group["state"] = "clearing"
    expected_group["spawned_count"] = expected_group["count"]
    expected_group["elapsed"] = expected_group["expected_clear_time"]
    expected_release.update(0.1, spawn_position, len(expected_living), enemy_factory, living_enemies=expected_living, player_rect=player.rect)
    assert_true(expected_release.current_group_id == "r1w1b", "group should release after expected clear time even when nearby enemies remain")
    assert_true(expected_release.next_group_release_reason == "expected_time", "expected clear time should be the release reason")

    early_release = WaveSystem()
    early_release.reset(1, RoomType.COMBAT, player)
    early_group = early_release.waves[0]["groups"][0]
    early_enemy = SimpleNamespace(alive=True, rect=pygame.Rect(0, 0, 34, 34), enemy_type=EnemyType.CHASER)
    early_group["living_ids"].add(id(early_enemy))
    early_group["state"] = "clearing"
    early_group["spawned_count"] = early_group["count"]
    early_group["elapsed"] = 0.5
    early_release.update(0.1, spawn_position, 1, enemy_factory, living_enemies=[early_enemy], player_rect=player.rect)
    assert_true(early_release.current_group_id == "r1w1b", "group should release early when living count is below threshold")
    assert_true(early_release.next_group_release_reason == "early_clear", "early clear should be the release reason")

    hard_block = WaveSystem()
    hard_block.reset(1, RoomType.COMBAT, player)
    hard_group = hard_block.waves[0]["groups"][0]
    hard_living = []
    for index in range(ROOM_1_GROUP_HARD_CAP):
        enemy = SimpleNamespace(alive=True, rect=pygame.Rect(2300 + index * 4, 2300, 34, 34), enemy_type=EnemyType.CHASER)
        hard_living.append(enemy)
        hard_group["living_ids"].add(id(enemy))
    hard_group["state"] = "clearing"
    hard_group["spawned_count"] = hard_group["count"]
    hard_group["elapsed"] = hard_group["expected_clear_time"]
    hard_block.update(0.1, spawn_position, len(hard_living), enemy_factory, living_enemies=hard_living, player_rect=player.rect)
    assert_true(hard_block.current_group_id == "r1w1a", "group should not release at hard cap")
    assert_true(hard_block.release_blocked_reason == "blocked_by_hard_cap", "hard cap should be the blocked reason")

    no_kill = WaveSystem()
    no_kill.reset(1, RoomType.COMBAT, player)
    no_kill_created = []
    no_kill_living = []

    def no_kill_factory(x, y, enemy_type, difficulty):
        enemy = SimpleNamespace(
            x=x,
            y=y,
            rect=pygame.Rect(x, y, 34, 34),
            enemy_type=enemy_type,
            difficulty=difficulty,
            alive=True,
        )
        no_kill_created.append(enemy)
        return enemy

    started_groups = {no_kill.current_group_id}
    blocked_seen = False
    guard = 0
    while guard < 600 and no_kill.wave_state != "group_clearing":
        current_group = no_kill.waves[0]["groups"][no_kill.current_group_index]
        dt = max(0.25, current_group.get("expected_clear_time", 4.0) + 0.25)
        spawned = no_kill.update(dt, spawn_position, len(no_kill_living), no_kill_factory, living_enemies=no_kill_living, player_rect=player.rect)
        no_kill_living.extend(spawned)
        started_groups.add(no_kill.current_group_id)
        if no_kill.release_blocked_reason == "blocked_by_hard_cap":
            blocked_seen = True
            no_kill_living = no_kill_living[:ROOM_1_GROUP_HARD_CAP - 2]
        guard += 1

    assert_true("r1w2a" in started_groups, "group 2 wave pressure should start without clearing first 15 enemies")
    assert_true("r1w3c" in started_groups, f"all room 1 groups should be able to start, got {started_groups}")
    assert_true(blocked_seen, "no-kill simulation should hit hard cap before release resumes")
    assert_true(no_kill.wave_state == "group_clearing", "grouped wave should enter grouped clearing only after all groups are done")
    assert_true(no_kill.wave_state != "done", "grouped wave should not complete while wave enemies are still alive")
    no_kill_living.clear()
    no_kill.update(0.25, spawn_position, 0, no_kill_factory, living_enemies=no_kill_living, player_rect=player.rect)
    assert_true(no_kill.wave_state == "done", "grouped wave should complete after all groups spawned and wave enemies cleared")

    room_two = WaveSystem()
    room_two.reset(2, RoomType.COMBAT, player)
    assert_true(not any(wave.get("groups") for wave in room_two.waves), "rooms 2-8 should keep existing non-group wave data in this pass")
    assert_true(room_two.build_power_influence == BUILD_POWER_INFLUENCE_BY_ROOM[2], "room 2 should use low build power influence")
    for room_number, room_type in (
        (3, RoomType.TREASURE),
        (4, RoomType.ELITE),
        (5, RoomType.COMBAT),
        (6, RoomType.COMBAT),
        (7, RoomType.COMBAT),
        (8, RoomType.ELITE),
    ):
        later_room = WaveSystem()
        later_room.reset(room_number, room_type, player)
        assert_true(not any(wave.get("groups") for wave in later_room.waves), f"room {room_number} should keep existing non-group wave data")
    room_seven = WaveSystem()
    room_seven.reset(7, RoomType.COMBAT, player)
    assert_true(room_seven.build_power_influence == DEFAULT_BUILD_POWER_INFLUENCE, "room 7+ should restore full build power influence")


def check_room_flow_system():
    flow = RoomFlowSystem()
    flow.start_for_room(RoomType.COMBAT)
    assert_true(flow.countdown_active, "combat room should start countdown")
    assert_true(flow.countdown_label() == "3", f"countdown should start at 3, got {flow.countdown_label()}")
    assert_true(not flow.room_can_advance(), "room should not advance during countdown")

    finished = flow.update_countdown(1.0)
    assert_true(not finished, "countdown should not finish after one second")
    assert_true(flow.countdown_label() == "2", f"countdown should show 2 after one second, got {flow.countdown_label()}")

    finished = flow.update_countdown(2.0)
    assert_true(finished, "countdown should finish after three total seconds")
    assert_true(flow.room_can_advance(), "room should advance after countdown")

    flow.start_for_room(RoomType.TREASURE)
    assert_true(flow.room_can_advance(), "treasure room should not use countdown")


def check_xp_progression():
    assert_true(cumulative_xp_for_level(20) == 9675, "Level 20 cumulative XP should be 9,675")
    assert_true(cumulative_xp_for_level(25) == 16945, "Level 25 cumulative XP should be 16,945")

    player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    assert_true(player.xp_to_next == 100, "level 1 should require 100 XP")
    player.add_xp(cumulative_xp_for_level(20))
    assert_true(player.level == 20, f"large XP gain should reach level 20, got {player.level}")
    assert_true(player.pending_level_ups == 19, f"one pending perk per level expected 19, got {player.pending_level_ups}")
    assert_true(player.xp == 0, f"exact cumulative level 20 XP should leave no overflow, got {player.xp}")
    assert_true(player.xp_to_next == xp_required_for_level(20), "level 20 next requirement should use centralized helper")

    player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    player.add_xp(cumulative_xp_for_level(25) + 123)
    assert_true(player.level == 25, f"large XP gain should cross multiple levels to level 25, got {player.level}")
    assert_true(player.pending_level_ups == 24, f"one pending perk per level expected 24, got {player.pending_level_ups}")
    assert_true(player.xp == 123, f"XP overflow should be preserved, got {player.xp}")


def check_horde_system():
    grid = SpatialHashGrid(cell_size=64)
    near = FakeEnemy(pygame.Rect(100, 100, 30, 30), health=20)
    far = FakeEnemy(pygame.Rect(500, 500, 30, 30), health=20)
    grid.rebuild([near, far])
    nearby = grid.nearby_rect(pygame.Rect(90, 90, 80, 80))
    assert_true(near in nearby and far not in nearby, "spatial grid should return only nearby enemies")
    assert_true(len(nearby) == len({id(enemy) for enemy in nearby}), "spatial grid queries should de-duplicate objects")

    combat = CombatSystem()
    player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    projectile = FakeProjectile(pygame.Rect(105, 105, 8, 8), damage=10)
    grid.rebuild([near, far])
    kills, _boss = combat.update(0.0, player, [projectile], [near, far], [], spatial_grid=grid)
    assert_true(near.health == 10 and far.health == 20 and kills == 0, "grid-backed projectile collision should hit nearby enemies only")
    assert_true(grid.query_checks < 2, "projectile collision should avoid checking every enemy when grid is available")

    lod_game = SimpleNamespace(
        player=FakePlayer(pygame.Rect(1000, 1000, 38, 38)),
        enemies=[],
        enemy_pool=SimpleNamespace(
            acquire=lambda x, y, enemy_type, difficulty=1.0: FakeEnemy(pygame.Rect(x, y, 34, 34), health=30, enemy_type=enemy_type),
            release_many=lambda enemies: None,
        ),
    )
    horde = HordeSystem(real_cap=2)
    horde.spawn_test(lod_game, 5)
    assert_true(len(lod_game.enemies) == 2 and sum(horde.pending.values()) == 3, "horde should keep excess enemies virtual when real cap is full")
    assert_true(lod_game.player.xp == 0 and lod_game.player.gold == 0, "virtual horde enemies should not grant rewards before activation")
    first_pos = pygame.Vector2(lod_game.enemies[0].rect.center)
    for _ in range(10):
        horde.update_enemies(lod_game, 0.05, lambda action, game: None)
    assert_true(pygame.Vector2(lod_game.enemies[0].rect.center).distance_to(first_pos) > 0, "LOD flow movement should move enemies without teleporting")
    lod_game.enemies[0].alive = False
    lod_game.enemies = [enemy for enemy in lod_game.enemies if enemy.alive]
    horde.activate_pending(lod_game)
    assert_true(len(lod_game.enemies) == 2 and sum(horde.pending.values()) == 2, "virtual horde should activate safely when real capacity opens")
    horde.clear(lod_game)
    assert_true(not horde.enabled and not lod_game.enemies and not horde.pending, "horde test should clear real and virtual enemies")

    reward_enemy = FakeEnemy(pygame.Rect(120, 100, 34, 34), health=8)
    reward_projectile = FakeProjectile(pygame.Rect(120, 100, 10, 10), damage=20)
    kills, _boss = combat.update(0.0, player, [reward_projectile], [reward_enemy], [])
    xp_after = player.xp
    gold_after = player.gold
    kills_again, _boss = combat.update(0.0, player, [reward_projectile], [reward_enemy], [])
    assert_true(kills == 1 and kills_again == 0 and player.xp == xp_after and player.gold == gold_after, "enemy rewards should be granted once after death")

    from game import Game
    game = Game()
    game.state = GameState.ROOM
    assert_true(game.horde is None, "normal Game startup should not instantiate HordeSystem")
    if DEV_TOOLS_ENABLED:
        game.dev_tools.spawn_horde_test(100)
        assert_true(game.horde.enabled and len(game.enemies) == 100, "F12/dev horde spawn should create real horde enemies")
    else:
        result = game.dev_tools.spawn_horde_test(100)
        assert_true(result is False and game.horde is None and len(game.enemies) == 0, "demo build should block dev horde spawner")
        game.ensure_horde().spawn_test(game, 100)
    for build_keys in (
        ("impact_drive", "kinetic_rounds", "overclock", "blade_drone", "bomber_drone"),
        ("sanguine_rounds", "vital_core", "blood_bat", "blood_trail"),
        ("phantom_step", "shadow_shuriken", "scout_boots"),
        ("rapid_fire", "power_rounds", "hollow_point", "split_shot", "needle_rounds", "critical_spark", "explosive_rounds"),
    ):
        for key in build_keys:
            if key in PERK_EFFECTS:
                grant_perk_picks(game.player, key, 4)
        horde = game.ensure_horde()
        horde.update_enemies(game, 0.05, game.combat_actions.handle)
        horde_grid = horde.rebuild_spatial_grid(game.enemies)
        game.combat.update(0.05, game.player, game.projectiles, game.enemies, game.enemy_bullets, effects=game.effects, spatial_grid=horde_grid)
    if DEV_TOOLS_ENABLED:
        game.dev_tools.clear_horde_test()
    else:
        game.horde.clear(game)
    assert_true(game.horde is not None and not game.horde.enabled and len(game.enemies) == 0, "horde clear should remove horde enemies")


def check_room_xp_budget():
    assert_true(STAGE_EXPECTED_ENEMY_XP[1] == 780, "stage room 1 enemy XP should come from 39 current spawns")
    assert_true(STAGE_EXPECTED_ENEMY_XP[4] == 1680, "stage elite room 4 should include elite kill XP")
    assert_true(STAGE_EXPECTED_ENEMY_XP[7] == 1980, "stage elite room 7 should include all five elite slots")
    assert_true(STAGE_EXPECTED_ENEMY_XP[8] == 600, "stage boss enemy XP should use the live boss kill reward")
    assert_true(STAGE_COMPLETION_XP[1] == 0, "stage room 1 enemy XP should satisfy its stage target without completion XP")
    assert_true(STAGE_COMPLETION_XP[2] == 20, "stage room 2 completion XP should top up the stage-relative curve")
    assert_true(STAGE_COMPLETION_XP[4] == 90, "stage room 4 completion XP should use current elite-room XP math")
    assert_true(STAGE_COMPLETION_XP[8] == 385, "stage boss completion XP should target Level 19 within the Stage")

    level_after_room_6 = FakePlayer(pygame.Rect(300, 300, 38, 38))
    level_after_room_6.add_xp(expected_stage_cumulative_xp_after_room(6))
    assert_true(level_after_room_6.level == STAGE_ROOM_TARGET_LEVELS[6], f"budget simulation should reach stage target Level {STAGE_ROOM_TARGET_LEVELS[6]} around room 6, got {level_after_room_6.level}")

    level_after_room_8 = FakePlayer(pygame.Rect(300, 300, 38, 38))
    level_after_room_8.add_xp(expected_stage_cumulative_xp_after_room(8))
    assert_true(level_after_room_8.level == STAGE_ROOM_TARGET_LEVELS[8], f"budget simulation should reach stage boss target Level {STAGE_ROOM_TARGET_LEVELS[8]}, got {level_after_room_8.level}")

    level_after_boss = FakePlayer(pygame.Rect(300, 300, 38, 38))
    level_after_boss.add_xp(expected_stage_cumulative_xp_after_boss())
    assert_true(level_after_boss.level == STAGE_ROOM_TARGET_LEVELS[8], f"budget simulation should end the Stage at Level {STAGE_ROOM_TARGET_LEVELS[8]}, got {level_after_boss.level}")

    game = SimpleNamespace(
        room_number=4,
        player=FakePlayer(pygame.Rect(300, 300, 38, 38)),
        loot=LootSystem(),
        events=FakeEvents(),
    )
    awarded = award_room_completion_xp(game, (100, 100))
    assert_true(awarded == STAGE_COMPLETION_XP[4], f"legacy room completion XP wrapper mismatch: {awarded}")
    assert_true(sum(pickup.value for pickup in game.loot.pickups if pickup.pickup_type == "xp") == awarded, "room completion XP should spawn exact XP pickups")
    pickup_count = len([pickup for pickup in game.loot.pickups if pickup.pickup_type == "xp"])
    assert_true(pickup_count > 0, "room completion XP should spawn visible XP pickups")

    duplicate = award_room_completion_xp(game, (100, 100))
    assert_true(duplicate == 0, "room completion XP should not duplicate for the same room")
    assert_true(sum(pickup.value for pickup in game.loot.pickups if pickup.pickup_type == "xp") == awarded, "duplicate room XP call should not add pickups")

    stage_room = SimpleNamespace(index=8, room_type=RoomType.ELITE, boss=True)
    stage_game = SimpleNamespace(
        stage=SimpleNamespace(active=True, stage_number=3),
        player=FakePlayer(pygame.Rect(300, 300, 38, 38)),
        loot=LootSystem(),
        events=FakeEvents(),
        room_completion_xp_awarded=set(),
    )
    stage_awarded = award_stage_room_completion_xp(stage_game, stage_room, (120, 120))
    assert_true(stage_awarded == STAGE_COMPLETION_XP[8], f"stage boss completion XP mismatch: {stage_awarded}")
    assert_true(award_stage_room_completion_xp(stage_game, stage_room, (120, 120)) == 0, "stage completion XP should not duplicate within the same Stage room")

    assert_true(not should_enter_boss(6), "boss should not trigger at room 6")
    assert_true(not should_enter_boss(ROOMS_TO_BOSS), f"boss should not trigger before room {ROOMS_TO_BOSS} is cleared")
    assert_true(should_enter_boss(ROOMS_TO_BOSS + 1), f"boss should trigger from room progression after room {ROOMS_TO_BOSS}")


def check_stage_route_verification():
    route = SimpleNamespace(room_number=1)
    visited = []
    for expected_room in range(1, ROOMS_TO_BOSS + 1):
        assert_true(route.room_number == expected_room, f"route should enter room {expected_room}, got {route.room_number}")
        assert_true(not should_enter_boss(route.room_number), f"boss should not appear before room {expected_room} is cleared")
        visited.append(route.room_number)
        route.room_number += 1

    assert_true(visited == list(range(1, ROOMS_TO_BOSS + 1)), f"route should visit rooms 1-{ROOMS_TO_BOSS}, got {visited}")
    assert_true(route.room_number == ROOMS_TO_BOSS + 1, f"clearing room {ROOMS_TO_BOSS} should advance route to boss gate")
    assert_true(should_enter_boss(route.room_number), f"boss should appear only after room {ROOMS_TO_BOSS}")

    high_level_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    high_level_player.level = 99
    for room_number in range(1, ROOMS_TO_BOSS + 1):
        assert_true(not should_enter_boss(room_number), f"level {high_level_player.level} should not trigger boss early at room {room_number}")

    boss_enemy = FakeEnemy(pygame.Rect(100, 100, 34, 34), health=200, enemy_type=EnemyType.BOSS)
    boss_game = SimpleNamespace(
        room_number=ROOMS_TO_BOSS + 1,
        state=GameState.HUB,
        player=high_level_player,
        camera=SimpleNamespace(reset=lambda rect: None),
        collision=SimpleNamespace(clear=lambda: None),
        room_flow=SimpleNamespace(clear_scene=lambda: None),
        enemies=[],
        projectiles=[],
        enemy_bullets=[],
        loot=SimpleNamespace(reset=lambda: None),
        events=FakeEvents(),
        prefabs=SimpleNamespace(spawn_prefab=lambda *args, **kwargs: boss_enemy),
        audio=FakeAudio(),
        effects=SimpleNamespace(ring=lambda *args, **kwargs: None),
    )
    high_level_player.cancel_tea = lambda: None
    high_level_player.move_to_room_spawn = lambda: None
    enter_boss(boss_game)
    assert_true(boss_game.state == GameState.BOSS, f"boss gate after room {ROOMS_TO_BOSS} should enter boss state")
    assert_true(len(boss_game.enemies) == 1 and boss_game.enemies[0].type == EnemyType.BOSS, "boss state should spawn one boss")
    assert_true("Boss awakened" in boss_game.message and "2/2" not in boss_game.message, "single boss flow should not label the only boss as stage 2")
    assert_true("boss_spawn" in boss_game.audio.played, "boss entry should use the boss_spawn sound key")

    from game import Game
    win_game = SimpleNamespace(
        room_number=ROOMS_TO_BOSS + 1,
        state=GameState.BOSS,
        music=FakeMusic(),
    )
    Game.complete_boss_encounter(win_game)
    assert_true(win_game.state == GameState.WIN, f"defeating the post-room-{ROOMS_TO_BOSS} boss should trigger win")
    assert_true(win_game.music.stopped == [1200], "win transition should fade out music")


def check_combat_system():
    combat = CombatSystem()
    player = FakePlayer(pygame.Rect(300, 300, 38, 38))

    enemy = FakeEnemy(pygame.Rect(100, 100, 34, 34), health=30)
    projectile = FakeProjectile(enemy.rect.copy(), damage=10)
    kills, boss_killed = combat.update(0.0, player, [projectile], [enemy], [])
    assert_true(enemy.health == 20, f"projectile hit should damage enemy, health={enemy.health}")
    assert_true(kills == 0 and not boss_killed, "non-lethal hit should not report a kill")

    primary = FakeEnemy(pygame.Rect(200, 100, 34, 34), health=100)
    splash = FakeEnemy(pygame.Rect(300, 100, 34, 34), health=100)
    outside = FakeEnemy(pygame.Rect(340, 100, 34, 34), health=100)
    boss = FakeEnemy(pygame.Rect(300, 132, 34, 34), health=100, enemy_type=EnemyType.BOSS)
    projectile = FakeProjectile(primary.rect.copy(), damage=60)
    projectile.explosive = True
    projectile.explosion_radius = 115
    projectile.explosion_splash_ratio = 0.40
    combat.update(0.0, player, [projectile], [primary, splash, outside, boss], [])
    assert_true(splash.health == 76, f"explosive splash should use projectile ratio, health={splash.health}")
    assert_true(outside.health == 100, "explosive splash should use projectile radius snapshot")
    assert_true(boss.health == 100, "explosive splash should exclude bosses")

    enemy = FakeEnemy(pygame.Rect(140, 100, 34, 34), health=10)
    projectile = FakeProjectile(enemy.rect.copy(), damage=10)
    loot = LootSystem()
    gold_before = player.gold
    xp_before = player.xp
    kills, boss_killed = combat.update(0.0, player, [projectile], [enemy], [], loot_system=loot)
    assert_true(kills == 1 and not boss_killed, "lethal non-boss hit should report one kill")
    assert_true(player.gold == gold_before and player.xp == xp_before, "loot rewards should not be added instantly")
    assert_true(len(loot.pickups) > 0, "lethal non-boss hit should spawn loot pickups")

    total_gold = sum(pickup.value for pickup in loot.pickups if pickup.pickup_type == "gold")
    total_xp = sum(pickup.value for pickup in loot.pickups if pickup.pickup_type == "xp")
    assert_true(total_gold == 8, f"gold pickup total should preserve reward, got {total_gold}")
    assert_true(total_xp == ENEMY_XP_REWARD, f"xp pickup total should preserve reward, got {total_xp}")

    for pickup in loot.pickups:
        pickup.rect.center = player.rect.center
        pickup.pos.update(player.rect.center)
        pickup.velocity.update(0, 0)
    loot.update(0.0, player)
    assert_true(player.gold == gold_before + total_gold, "gold should be added after collection")
    assert_true(player.xp == xp_before + total_xp, "xp should be added after collection")

    special_loot = LootSystem()
    original_random = random.random
    random.random = lambda: 0.0
    try:
        special_loot.spawn_special_enemy_drop((120, 120), EnemyType.CHASER)
    finally:
        random.random = original_random
    assert_true(any(p.pickup_type == "heal_potion" for p in special_loot.pickups), "enemy special drops should be able to spawn heal potions")
    potion_player = FakePlayer(pygame.Rect(120, 120, 38, 38))
    potion_player.health = 40
    potion_player.max_health = 100
    for pickup in special_loot.pickups:
        pickup.rect.center = potion_player.rect.center
        pickup.pos.update(potion_player.rect.center)
    special_loot.update(0.0, potion_player)
    assert_true(potion_player.health in (55, 65, 75), f"heal potion should restore one valid amount, got {potion_player.health}")

    time_loot = LootSystem()
    time_loot.pickups.append(Pickup(120, 120, "time_stop", 2.0))
    time_player = FakePlayer(pygame.Rect(120, 120, 38, 38))
    for pickup in time_loot.pickups:
        pickup.rect.center = time_player.rect.center
        pickup.pos.update(time_player.rect.center)
    time_loot.update(0.0, time_player)
    assert_true(time_player.enemy_time_stop_timer == 2.0, "time stop pickup should arm enemy freeze timer")

    exit_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    exit_loot = LootSystem()
    exit_loot.spawn_gold((100, 100), 23)
    exit_loot.spawn_xp((100, 100), 44)
    exit_loot.pickups.append(Pickup(100, 100, "debug", 999))
    expected_gold = sum(p.value for p in exit_loot.pickups if p.pickup_type == "gold")
    expected_xp = sum(p.value for p in exit_loot.pickups if p.pickup_type == "xp")
    fake_exit_game = SimpleNamespace(player=exit_player, loot=exit_loot, effects=None, audio=None)
    collected = collect_exit_loot(fake_exit_game)
    assert_true(collected == {"gold": expected_gold, "xp": expected_xp}, "room exit should collect remaining XP/gold totals")
    assert_true(exit_player.gold == expected_gold and exit_player.xp == expected_xp, "room exit should award remaining loot through normal collection")
    assert_true(len(exit_loot.pickups) == 1 and exit_loot.pickups[0].pickup_type == "debug", "room exit should leave invalid non-reward pickups alone")
    collect_exit_loot(fake_exit_game)
    assert_true(exit_player.gold == expected_gold and exit_player.xp == expected_xp, "room exit loot collection should not duplicate rewards")

    loot = LootSystem()
    assert_true(sum(loot._split_xp_amount(44)) == 44, "44 XP split should preserve exact value")
    assert_true(len(loot._split_xp_amount(44)) <= 4, "44 XP should respect enemy pickup cap")
    assert_true(loot._split_xp_amount(75) == [75], "75 XP should create one tier-3 crystal")
    assert_true(loot._split_xp_amount(600) == [500, 75, 25], "600 XP should split into 500 + 75 + 25")
    assert_true(loot._split_xp_amount(1200) == [500, 500, 200], "1200 XP should split into 500 + 500 + 200")
    assert_true(sum(loot._split_xp_amount(250)) == 250, "250 XP split should preserve total value")
    assert_true(len(loot._split_xp_amount(250)) <= 4, "250 XP should respect enemy pickup cap")

    tiered = loot._split_xp_pickups(75)
    assert_true(tiered == [(75, "xp_tier_3")], f"75 XP should use xp_tier_3 metadata, got {tiered}")
    tiered = loot._split_xp_pickups(600)
    assert_true(
        [tier_id for _value, tier_id in tiered] == ["xp_tier_5", "xp_tier_3", "xp_tier_2"],
        f"600 XP should use high-value tier metadata, got {tiered}",
    )

    magnet_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    pickup = Pickup(145, 300, "xp", 17)
    pickup.age = 10.0
    pickup.velocity.update(0, 900)
    for _ in range(80):
        if pickup.update(1 / 30, magnet_player, 220):
            break
        assert_true(pickup.velocity.length() <= 760.1, "magnetized pickup speed should stay capped")
    assert_true(not pickup.alive, "magnetized pickup should reach final collection and not orbit indefinitely")
    assert_true(pickup.value == 17, "magnet damping should preserve exact pickup value")

    bullet = EnemyBullet(96, 100, (1, 0), 5)
    wall = pygame.Rect(112, 92, 28, 40)
    bullet.update(0.1)
    if bullet.rect.colliderect(wall):
        bullet.kill()
    assert_true(not bullet.alive, "enemy bullets should be killed when they collide with room walls")

    contact_enemy = FakeEnemy(player.rect.copy(), health=30)
    health_before = player.health
    kills, boss_killed = combat.update(0.0, player, [], [contact_enemy], [])
    assert_true(player.health == health_before - ENEMY_DAMAGE, "contact damage should damage player")
    assert_true(combat.player_contact_timer == ENEMY_CONTACT_COOLDOWN, "contact damage should start cooldown")

    health_after_first_contact = player.health
    combat.update(0.0, player, [], [contact_enemy], [])
    assert_true(player.health == health_after_first_contact, "contact damage should respect cooldown")


def check_build_mechanics():
    combat = CombatSystem()

    ninja = FakePlayer(pygame.Rect(100, 100, 38, 38))
    ninja.dash_timer = 0.2
    ninja.skill_cooldown_timer = 5.0
    ninja.dash_cooldown_timer = 5.0
    ninja.dash_strike_damage = 12
    ninja.dash_strike_cooldown_restore = 0.5
    ninja.dash_refund_cap = 0.5
    projectiles = []
    enemy = FakeEnemy(pygame.Rect(112, 100, 34, 34), health=30)
    combat.update(0.0, ninja, projectiles, [enemy], [])
    assert_true(enemy.health == 18, "dash strike should damage a nearby enemy once")
    assert_true(ninja.skill_cooldown_timer == 4.5, "dash strike should restore bounded skill cooldown")
    combat.update(0.0, ninja, projectiles, [enemy], [])
    assert_true(enemy.health == 18, "dash strike should not repeat damage every frame on the same enemy")
    assert_true(ninja.dash_refund_this_dash <= ninja.dash_refund_cap, "dash refund should stay capped")

    engineer = FakePlayer(pygame.Rect(100, 100, 38, 38))
    engineer.engineer_helper_enabled = True
    engineer.engineer_helper_damage = 9
    engineer.engineer_helper_cooldown = 0.5
    engineer.engineer_gun_range = 500
    enemy = FakeEnemy(pygame.Rect(180, 100, 34, 34), health=30)
    projectiles = []
    combat.update(0.0, engineer, projectiles, [enemy], [])
    assert_true(enemy.health == 30, "engineer helper should not damage before visible projectile hits")
    assert_true(len(projectiles) == 1 and getattr(projectiles[0], "source", "") == "engineer_drone", "engineer helper should create a visible drone projectile")
    assert_true(engineer.engineer_helper_timer == 0.5, "engineer helper should enter cooldown")
    combat.update(0.0, engineer, projectiles, [enemy], [])
    assert_true(len(projectiles) == 1, "engineer helper should not fire while on cooldown")

    vampire = FakePlayer(pygame.Rect(100, 100, 38, 38))
    vampire.health = 50
    vampire.vampire_kill_heal = 7
    vampire.vampire_max_blood = 10
    vampire.vampire_blood_per_kill = 3
    enemy = FakeEnemy(pygame.Rect(140, 100, 34, 34), health=10)
    projectile = FakeProjectile(enemy.rect.copy(), damage=10)
    combat.update(0.0, vampire, [projectile], [enemy], [])
    assert_true(vampire.health == 60, "vampire kill heal should include bounded Blood feed bonus")
    assert_true(vampire.vampire_blood == 3, "vampire kill should add Blood once")
    combat._apply_vampire_kill_reward(vampire, enemy)
    assert_true(vampire.health == 60 and vampire.vampire_blood == 3, "vampire kill reward should not duplicate from one enemy")

    boss_feed = FakePlayer(pygame.Rect(100, 100, 38, 38))
    boss_feed.vampire_max_blood = 4
    boss_feed.vampire_blood_on_boss_hit = 2
    boss = FakeEnemy(pygame.Rect(140, 100, 34, 34), health=100, enemy_type=EnemyType.BOSS)
    boss.phase = 2
    projectile = FakeProjectile(boss.rect.copy(), damage=10)
    combat.update(0.0, boss_feed, [projectile], [boss], [])
    assert_true(boss_feed.vampire_blood == 2, "boss-compatible hit feed should add bounded Blood")
    projectile = FakeProjectile(boss.rect.copy(), damage=10)
    combat.update(0.0, boss_feed, [projectile], [boss], [])
    assert_true(boss_feed.vampire_blood == 4, "boss-compatible hit feed should cap at max Blood")

    ecosystem = FakePlayer(pygame.Rect(100, 100, 38, 38))
    for key in ("sanguine_rounds", "battle_recovery", "vital_core", "blood_bat", "blood_trail"):
        grant_perk_to_limit(ecosystem, key)
    assert_true(ecosystem.vampire_wound_max_stacks == 3, "Sanguine Rounds should enable capped Wounds")
    assert_true(ecosystem.vampire_bat_enabled, "Blood Bat should enable the single bat helper")
    assert_true(ecosystem.vampire_bat_chain_cap == 4, "Blood Bat legendary should chain up to four wounded kills")
    assert_true(ecosystem.vampire_trail_harvest_cap == 3, "Blood Trail should reach bounded legendary harvest cap")
    assert_true(ecosystem.vampire_trail_radius == 88, "Blood Trail should use movement-proximity harvest radius")
    assert_true(ecosystem.vampire_blood_moon_unlocked, "Blood Trail legendary should unlock Blood Moon")

    wounded_enemy = FakeEnemy(pygame.Rect(140, 100, 34, 34), health=40)
    projectile = FakeProjectile(wounded_enemy.rect.copy(), damage=5)
    combat.update(0.0, ecosystem, [projectile], [wounded_enemy], [])
    assert_true(getattr(wounded_enemy, "vampire_wound_stacks", 0) > 0, "projectile hits should apply Sanguine Wounds")
    ecosystem.vampire_orb_drop_chance = 1.0
    projectile = FakeProjectile(wounded_enemy.rect.copy(), damage=50)
    combat.update(0.0, ecosystem, [projectile], [wounded_enemy], [])
    assert_true(len(ecosystem.vampire_blood_orbs) == 1, "wounded deaths should spawn one capped Blood Orb")
    ecosystem.vampire_blood_orbs[0]["pos"].update(ecosystem.rect.center)
    before_blood = ecosystem.vampire_blood
    combat.update(0.1, ecosystem, [], [], [])
    assert_true(ecosystem.vampire_blood > before_blood, "Blood Orbs should collect into Blood")
    radius_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    radius_player.vampire_max_blood = 20
    radius_player.vampire_orb_attract_radius = 150
    radius_player.vampire_blood_orbs.append({"pos": pygame.Vector2(radius_player.rect.center) + pygame.Vector2(40, 0), "vel": pygame.Vector2(0, 0), "value": 1, "life": 8.0})
    combat.update(0.0, radius_player, [], [], [])
    assert_true(radius_player.vampire_blood == 1, "Blood Orb collection radius should scale from attract radius")
    radius_player.vampire_orb_attract_radius = 400
    radius_player.vampire_blood_orbs.append({"pos": pygame.Vector2(radius_player.rect.center) + pygame.Vector2(70, 0), "vel": pygame.Vector2(0, 0), "value": 1, "life": 8.0})
    combat.update(0.0, radius_player, [], [], [])
    assert_true(radius_player.vampire_blood == 1 and len(radius_player.vampire_blood_orbs) == 1, "Blood Orb collection radius should stay bounded")

    bat_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    bat_player.vampire_max_blood = 10
    bat_player.vampire_bat_enabled = True
    bat_player.vampire_bat_state = "ready"
    bat_player.vampire_bat_damage = 38
    bat_player.vampire_bat_speed = 900
    bat_player.vampire_bat_feed_value = 2
    bat_player.vampire_bat_chain_cap = 4
    bat_enemy = FakeEnemy(pygame.Rect(180, 100, 34, 34), health=20)
    bat_enemy.vampire_wound_stacks = 2
    bat_enemy.vampire_wound_timer = 5.0
    chain_enemy = FakeEnemy(pygame.Rect(255, 100, 34, 34), health=35)
    chain_enemy.vampire_wound_stacks = 3
    chain_enemy.vampire_wound_timer = 5.0
    bat_player.vampire_bat_search_timer = 0.0
    bat_player.vampire_bat_pos.update((170, 100))
    combat.update(0.05, bat_player, [], [bat_enemy, chain_enemy], [])
    assert_true(bat_player.vampire_bat_state == "diving", "Blood Bat should acquire wounded targets with minimal search delay")
    assert_true(bat_player.vampire_bat_target_id == id(chain_enemy), "Blood Bat should prefer the highest-wound target")
    bat_health_before = chain_enemy.health
    combat.update(0.20, bat_player, [], [bat_enemy, chain_enemy], [])
    assert_true(bat_player.vampire_bat_state == "feeding", "Blood Bat should pause briefly in FEEDING state")
    assert_true(chain_enemy.health < bat_health_before, "Blood Bat should apply feed damage once on entering FEEDING")
    health_after_feed = chain_enemy.health
    bat_blood_before = bat_player.vampire_blood
    combat.update(0.05, bat_player, [], [bat_enemy], [])
    assert_true(chain_enemy.health == health_after_feed, "Blood Bat FEEDING state should not repeat damage every frame")
    combat.update(0.05, bat_player, [], [bat_enemy, chain_enemy], [])
    assert_true(bat_player.vampire_bat_state == "diving", "Blood Bat should chain to the next wounded target before returning")
    assert_true(bat_player.vampire_bat_carried_blood > 0 and bat_player.vampire_blood == bat_blood_before, "Blood Bat should carry Blood without banking until return")
    bat_player.vampire_bat_chain_kills = bat_player.vampire_bat_chain_cap
    combat.update(0.30, bat_player, [], [bat_enemy], [])
    assert_true(bat_player.vampire_bat_state in ("feeding", "returning"), "Blood Bat should stop chaining at its kill cap")
    combat.update(0.10, bat_player, [], [bat_enemy], [])
    assert_true(bat_player.vampire_bat_state == "returning", "Blood Bat should return once chain cap is reached")
    bat_player.vampire_bat_pos.update(bat_player.rect.center)
    combat.update(0.1, bat_player, [], [bat_enemy], [])
    assert_true(bat_player.vampire_bat_state == "cooldown", "Blood Bat should enter cooldown after delivering Blood")
    assert_true(bat_player.vampire_blood > bat_blood_before, "Blood Bat should bank carried Blood on final return")

    trail_enemy = FakeEnemy(pygame.Rect(106, 100, 34, 34), health=70)
    trail_enemy.vampire_wound_stacks = 2
    trail_enemy.vampire_wound_timer = 5.0
    ecosystem.dash_timer = 0.0
    ecosystem.move_direction.update(1, 0)
    ecosystem.vampire_trail_hit_ids.clear()
    ecosystem.vampire_trail_harvested_this_dash = 0
    blood_before_trail = ecosystem.vampire_blood
    combat.update(0.1, ecosystem, [], [trail_enemy], [])
    assert_true(ecosystem.vampire_blood > blood_before_trail, "Blood Trail should harvest Blood while moving near wounded enemies without Dash")
    trail_blood_after = ecosystem.vampire_blood
    combat.update(0.1, ecosystem, [], [trail_enemy], [])
    assert_true(ecosystem.vampire_blood == trail_blood_after, "Blood Trail movement harvest should respect its pulse interval")
    ecosystem.vampire_feast_unlocked = True
    ecosystem.vampire_feast_threshold = 1
    ecosystem.vampire_feast_duration = 6.0
    ecosystem.vampire_blood_moon_unlocked = True
    ecosystem.add_blood(1, source="trail")
    assert_true(ecosystem.vampire_feast_timer > 0 and ecosystem.vampire_blood_moon_timer > 0, "all successful Blood gains should trigger Feast and Blood Moon when thresholds allow")
    generic_feast = FakePlayer(pygame.Rect(100, 100, 38, 38))
    generic_feast.vampire_max_blood = 5
    generic_feast.vampire_feast_unlocked = True
    generic_feast.vampire_feast_threshold = 1
    generic_feast.vampire_feast_duration = 4.0
    generic_feast.add_blood(1)
    assert_true(generic_feast.vampire_feast_timer > 0, "generic Blood gains should explicitly advance Feast")
    timer_after = generic_feast.vampire_feast_timer
    generic_feast.add_blood(0, source="feast")
    assert_true(generic_feast.vampire_feast_timer == timer_after, "zero-gain Blood events should not recursively refresh Feast")

    moon_shooter = FakePlayer(pygame.Rect(100, 100, 38, 38))
    shooter = ShootingSystem()
    normal_projectiles = []
    shooter.try_shoot(moon_shooter, normal_projectiles)
    normal_damage = normal_projectiles[0].damage
    shooter.shoot_timer = 0.0
    moon_shooter.vampire_blood_moon_timer = 3.0
    moon_projectiles = []
    shooter.try_shoot(moon_shooter, moon_projectiles)
    moon_damage = moon_projectiles[0].damage
    assert_true(moon_damage > normal_damage, "Blood Moon projectile damage bonus should apply only while active")
    shooter.shoot_timer = 0.0
    moon_shooter.vampire_blood_moon_timer = 0.0
    reset_projectiles = []
    shooter.try_shoot(moon_shooter, reset_projectiles)
    assert_true(reset_projectiles[0].damage == normal_damage, "Blood Moon projectile damage bonus should reset after expiry")

    moon_bat = FakePlayer(pygame.Rect(100, 100, 38, 38))
    moon_bat.vampire_bat_enabled = True
    moon_bat.vampire_bat_state = "ready"
    moon_bat.vampire_bat_damage = 38
    moon_bat.vampire_bat_speed = 650
    moon_bat.vampire_bat_feed_value = 2
    moon_bat.vampire_blood_moon_timer = 4.0
    moon_bat_enemy = FakeEnemy(pygame.Rect(180, 100, 34, 34), health=100)
    moon_bat_enemy.vampire_wound_stacks = 1
    moon_bat_enemy.vampire_wound_timer = 5.0
    combat.update(0.1, moon_bat, [], [moon_bat_enemy], [])
    combat.update(1.0, moon_bat, [], [moon_bat_enemy], [])
    assert_true(moon_bat_enemy.health == 53, "existing Blood Moon bat 1.25x damage bonus should remain")

    moon_trail = FakePlayer(pygame.Rect(100, 100, 38, 38))
    moon_trail.vampire_max_blood = 20
    moon_trail.vampire_trail_enabled = True
    moon_trail.vampire_trail_level = 4
    moon_trail.vampire_trail_harvest_cap = 3
    moon_trail.vampire_trail_harvest_value = 1
    moon_trail.vampire_trail_radius = 88
    moon_trail.move_direction.update(1, 0)
    moon_trail.vampire_blood_moon_timer = 4.0
    moon_trail.dash_timer = 0.0
    trail_targets = []
    for offset in (0, 4, 8, 12):
        target = FakeEnemy(pygame.Rect(104 + offset, 100, 34, 34), health=80)
        target.vampire_wound_stacks = 1
        target.vampire_wound_timer = 5.0
        trail_targets.append(target)
    combat.update(0.1, moon_trail, [], trail_targets, [])
    assert_true(moon_trail.vampire_trail_harvested_this_dash == 4, "Blood Moon trail +1 harvest cap should remain without Dash")

    hud_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    assert_true(not vampire_hud_visible(hud_player), "Vampire HUD should stay hidden when no Vampire state is relevant")
    hud_player.vampire_max_blood = 10
    hud_player.vampire_blood = 4
    hud_player.vampire_feast_unlocked = True
    hud_player.vampire_feast_progress = 3
    hud_player.vampire_feast_threshold = 6
    assert_true(vampire_hud_visible(hud_player), "Vampire HUD should appear when Vampire mechanics are relevant")
    hud_data = vampire_hud_data(hud_player)
    assert_true(hud_data["blood_text"] == "Blood 4/10" and 0 < hud_data["feast_ratio"] < 1, "Vampire HUD data should expose Blood and Feast progress")
    vrect = vampire_hud_rect()
    center_safe = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 80, 240, 160)
    assert_true(not vrect.colliderect(center_safe), "Vampire HUD should not render in center screen")
    occupied = hud_occupied_rects()
    for name, rect in occupied.items():
        assert_true(not vrect.colliderect(rect), f"Vampire HUD should not overlap existing HUD element {name}")


def grant_perk_to_limit(player, key):
    perks = PerkSystem()
    for _ in range(4):
        definition = next(perk for perk in perks._available_perks(player) if perk["key"] == key)
        option = perks._option_for_player(definition, player)
        perks.current_options = [option]
        applied = perks.apply(player, 0)
        assert_true(applied is not None, f"granting {key} should succeed")


def grant_perk_picks(player, key, count):
    perks = PerkSystem()
    for _ in range(count):
        definition = next(perk for perk in perks._available_perks(player) if perk["key"] == key)
        option = perks._option_for_player(definition, player)
        perks.current_options = [option]
        applied = perks.apply(player, 0)
        assert_true(applied is not None, f"granting {key} pick should succeed")


def check_engineer_machine_team():
    combat = CombatSystem()
    player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    for key in ("impact_drive", "kinetic_rounds", "overclock", "blade_drone", "bomber_drone"):
        grant_perk_to_limit(player, key)

    assert_true(player.engineer_helper_enabled, "Gun Drone should be active after Engineer progression")
    assert_true(player.engineer_gun_count == 2, "Legendary Gun Drone should create a second visible drone")
    assert_true(player.engineer_helper_damage == 34, "Gun Drone should reach final derived damage")
    assert_true(abs(player.engineer_helper_cooldown - 0.44) < 0.001, "Gun Drone cooldown should derive deterministically")
    assert_true(player.engineer_gun_range == 500, "Gun Drone should use small-room engagement range")
    assert_true(player.engineer_blade_count == 4, "Legendary Blade Drone should keep four blades")
    assert_true(player.engineer_blade_radius == 108, "Legendary Blade Drone should use the base overdrive-ready orbit radius")
    assert_true(player.engineer_blade_overdrive_cooldown == 5.6, "Overclock should reduce Blade Overdrive cooldown deterministically")
    assert_true(player.engineer_bomber_count == 2, "Bomber Drone pick 2+ should show two bombers")
    assert_true(player.engineer_bomber_max_runs == 2, "Legendary Bomber should allow two bounded runs")
    assert_true(player.engineer_airstrike_unlocked, "Legendary Bomber should unlock Airstrike")
    assert_true(player.engineer_airstrike_cooldown == 25.0, "Overclock should reduce Airstrike cooldown deterministically")

    projectiles = []
    enemy = FakeEnemy(pygame.Rect(220, 100, 34, 34), health=100)
    player.engineer_drone_positions = [pygame.Vector2(100, 100), pygame.Vector2(100, 140)]
    combat.update(0.0, player, projectiles, [enemy], [])
    assert_true(enemy.health == 100, "Gun Drone should not deal invisible instant damage")
    assert_true(len(projectiles) == 2 and all(projectile.source == "engineer_drone" for projectile in projectiles), "Legendary Gun Drone should create two bounded visible projectiles")

    gun_pick_1 = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(gun_pick_1, "impact_drive", 1)
    assert_true(gun_pick_1.engineer_gun_count == 1 and gun_pick_1.engineer_gun_burst_count == 1, "Gun Pick 1 should create one normal drone")
    gun_pick_2 = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(gun_pick_2, "impact_drive", 2)
    assert_true(gun_pick_2.engineer_gun_count == 1 and gun_pick_2.engineer_gun_burst_count == 2, "Gun Pick 2 should show burst rhythm")
    gun_pick_3 = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(gun_pick_3, "impact_drive", 3)
    assert_true(gun_pick_3.engineer_helper_projectile_speed > gun_pick_2.engineer_helper_projectile_speed, "Gun Pick 3 should improve projectile quality")

    blade_pick_1 = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(blade_pick_1, "blade_drone", 1)
    assert_true(blade_pick_1.engineer_blade_count == 2, "Blade Pick 1 should create two defensive blades")
    blade_pick_2 = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(blade_pick_2, "blade_drone", 2)
    assert_true(blade_pick_2.engineer_blade_count == 3, "Blade Pick 2 should create three blades")
    blade_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_to_limit(blade_player, "blade_drone")
    assert_true(blade_player.engineer_blade_count == 4, "Blade Pick 3+ should create four blades")
    angle = 0.37
    blade_player.engineer_blade_angle = angle
    positions = []
    for index in range(blade_player.engineer_blade_count):
        blade_angle = blade_player.engineer_blade_angle + (6.28318 / blade_player.engineer_blade_count) * index
        positions.append(pygame.Vector2(blade_player.rect.center) + pygame.Vector2(blade_player.engineer_blade_radius, 0).rotate_rad(blade_angle))
    assert_true(len(positions) == 4, "full Blade Drone should expose four orbit visuals/hit positions")
    assert_true(abs(positions[0].distance_to(positions[2]) - blade_player.engineer_blade_radius * 2) < 1.0, "opposite Blade Drone positions should stay paired")
    art_player = Player()
    assert_true(Player._engineer_blade_image is not None, "Blade Drone sprite should load once on Player initialization")
    assert_true(Player._engineer_blade_image.get_size() == (32, 32), "Blade Drone sprite should be scaled to 32x32")
    art_player.engineer_blade_count = 2
    art_player.engineer_blade_radius = 90
    art_player.engineer_blade_orbit_speed = 3.0
    previous_spin = art_player.engineer_blade_spin_angle
    for _ in range(8):
        Player._update_engineer_blades(art_player, 0.08)
    assert_true(art_player.engineer_blade_spin_angle != previous_spin, "Blade sprite spin should advance from dt")
    assert_true(0 < len(art_player.engineer_blade_trail) <= 5, "Blade afterimage trail should stay bounded")
    blade_player.engineer_blade_positions = [pygame.Vector2(130, 100), pygame.Vector2(70, 100)]
    enemy_a = FakeEnemy(pygame.Rect(118, 90, 34, 34), health=100)
    enemy_b = FakeEnemy(pygame.Rect(66, 90, 34, 34), health=100)
    blade_effects = EffectsSystem()
    combat.update(0.0, blade_player, [], [enemy_a, enemy_b], [], effects=blade_effects)
    assert_true(enemy_a.health == 76 and enemy_b.health == 76, "Blade Drone should hit different enemies independently")
    assert_true(len(blade_effects.sprite_effects) == 2, "Blade Drone should spawn one-shot VFX only on real damage events")
    combat.update(0.0, blade_player, [], [enemy_a, enemy_b], [])
    assert_true(enemy_a.health == 76 and enemy_b.health == 76, "Blade Drone should not damage same enemy every frame")
    assert_true(len(blade_effects.sprite_effects) == 2, "Blade cooldown-blocked contacts should not spawn extra VFX")
    blade_effects.update(0.4)
    assert_true(len(blade_effects.sprite_effects) == 0, "Blade hit VFX should clean up after its animation")
    blade_player.engineer_blade_overdrive_timer = 1.0
    blade_player.engineer_blade_hit_timers.clear()
    overdrive_enemy = FakeEnemy(pygame.Rect(118, 90, 34, 34), health=100)
    overdrive_effects = EffectsSystem()
    combat.update(0.0, blade_player, [], [overdrive_enemy], [], effects=overdrive_effects)
    assert_true(overdrive_enemy.health == 64, "Blade Overdrive should add temporary contact damage")
    assert_true(len(overdrive_effects.sprite_effects) == 1 and overdrive_effects.sprite_effects[0].image.get_size() == (56, 56), "Blade Overdrive should use the stronger impact VFX")
    blade_player.engineer_blade_overdrive_timer = 0.0
    blade_player.engineer_blade_overdrive_cooldown_timer = blade_player.engineer_blade_overdrive_cooldown
    assert_true(blade_player.engineer_blade_overdrive_cooldown_timer > 0, "Blade Overdrive should expire into cooldown")
    blade_player.engineer_blade_hit_timers[id(enemy_a)] = 0.0
    enemy_a.alive = False
    combat.update(0.1, blade_player, [], [enemy_a, enemy_b], [])
    assert_true(id(enemy_a) not in blade_player.engineer_blade_hit_timers, "Blade stale tracking should clean dead enemies")

    bomber_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_picks(bomber_player, "bomber_drone", 1)
    assert_true(bomber_player.engineer_bomber_count == 1 and bomber_player.engineer_bomber_radius == 82, "Bomber Pick 1 should create one small bomber")
    grant_perk_picks(bomber_player, "bomber_drone", 1)
    assert_true(bomber_player.engineer_bomber_count == 2, "Bomber Pick 2 should create a second bomber")
    grant_perk_picks(bomber_player, "bomber_drone", 2)
    target = FakeEnemy(pygame.Rect(190, 100, 34, 34), health=80)
    neighbors = [target, FakeEnemy(pygame.Rect(205, 105, 34, 34), health=80)]
    states = []
    for _ in range(20):
        combat.update(0.2, bomber_player, [], neighbors, [])
        states.append(bomber_player.engineer_bomber_state)
        if any(enemy.health < 80 for enemy in neighbors):
            break
    assert_true("acquire" in states or "flying" in states, "Bomber should enter acquire/flying states")
    assert_true(any(enemy.health < 80 for enemy in neighbors), "Bomber explosion should damage bounded nearby enemies")
    damaged_once = [enemy.health for enemy in neighbors]
    combat.update(0.0, bomber_player, [], neighbors, [])
    assert_true([enemy.health for enemy in neighbors] == damaged_once, "Bomber should not recurse explosions in one state")
    assert_true(bomber_player.engineer_bomber_state in ("cooldown", "respawn", "flying"), "Bomber should leave explosion into bounded downtime or second run")

    air_player = FakePlayer(pygame.Rect(100, 100, 38, 38))
    grant_perk_to_limit(air_player, "bomber_drone")
    air_targets = [
        FakeEnemy(pygame.Rect(180, 100, 34, 34), health=120),
        FakeEnemy(pygame.Rect(205, 105, 34, 34), health=120),
        FakeEnemy(pygame.Rect(235, 120, 34, 34), health=120),
    ]
    combat.update(0.0, air_player, [], air_targets, [])
    assert_true(air_player.engineer_airstrike_state == "telegraph", "Legendary Bomber should telegraph Airstrike")
    combat.update(1.0, air_player, [], air_targets, [])
    assert_true(air_player.engineer_airstrike_state == "cooldown", "Airstrike should enter cooldown after impact")
    assert_true(all(not enemy.alive for enemy in air_targets), "Airstrike should damage dense enemy area significantly")
    loot = LootSystem()
    kills, _boss = combat.update(0.0, air_player, [], air_targets, [], loot_system=loot)
    assert_true(kills == 0 and len(loot.pickups) == 0, "Airstrike should not recurse or duplicate rewards on dead targets")

    first = FakePlayer(pygame.Rect(100, 100, 38, 38))
    second = FakePlayer(pygame.Rect(100, 100, 38, 38))
    for actor in (first, second):
        for key in ("impact_drive", "kinetic_rounds", "overclock", "blade_drone", "bomber_drone"):
            grant_perk_to_limit(actor, key)
    assert_true(
        (first.engineer_helper_cooldown, first.engineer_blade_hit_cooldown, first.engineer_bomber_cooldown)
        == (second.engineer_helper_cooldown, second.engineer_blade_hit_cooldown, second.engineer_bomber_cooldown),
        "Machine values should not drift for the same perk counts",
    )
    first.engineer_blade_overdrive_timer = 1.0
    first.engineer_airstrike_state = "telegraph"
    first.reset_engineer_scene_state()
    assert_true(first.engineer_blade_overdrive_timer == 0.0 and first.engineer_airstrike_state == "ready", "scene transitions should clear transient Engineer states")


def check_enemy_feel_pass():
    player_rect = pygame.Rect(420, 100, 38, 38)
    chaser = Enemy(100, 100, enemy_type=EnemyType.CHASER, difficulty=1.0)
    chaser.update(0.1, player_rect)
    assert_true(chaser.chaser_burst_timer == 0, "chaser should not burst immediately after spawn")

    chaser.speed = 0
    chaser.chaser_burst_cooldown = 0
    for _ in range(30):
        chaser.update(0.1, player_rect)
    assert_true(chaser.chaser_burst_timer > 0 or chaser.chaser_burst_cooldown > 0, "chaser burst should trigger after sustained medium-range pursuit")
    cooldown_after_burst = chaser.chaser_burst_cooldown
    chaser.chaser_burst_timer = 0
    chaser.chase_pressure_timer = 2.0
    chaser.update(0.1, player_rect)
    assert_true(chaser.chaser_burst_cooldown <= cooldown_after_burst, "chaser burst should respect cooldown before retriggering")

    close_chaser = Enemy(100, 100, enemy_type=EnemyType.CHASER, difficulty=1.0)
    close_player = pygame.Rect(120, 100, 38, 38)
    close_chaser.chaser_burst_cooldown = 0
    close_chaser.chase_pressure_timer = 2.0
    close_chaser.update(0.1, close_player)
    assert_true(close_chaser.chaser_burst_timer == 0, "chaser should not burst when already close")

    ranged = Enemy(100, 100, enemy_type=EnemyType.RANGED, difficulty=1.0)
    ranged.windup_action = "enemy_shoot"
    assert_true(ranged.windup_telegraph_length() == RANGED_ATTACK_RANGE, "ranged telegraph should match attack range")
    rain = Enemy(100, 100, enemy_type=EnemyType.RANGED_RAIN, difficulty=1.0)
    rain.windup_action = "enemy_rain"
    assert_true(rain.windup_telegraph_length() == RANGED_ATTACK_RANGE, "rain telegraph should match attack range")
    jumper = Enemy(100, 100, enemy_type=EnemyType.JUMPER, difficulty=1.0)
    jumper.windup_action = "enemy_jump"
    assert_true(jumper.windup_telegraph_length() == JUMPER_ATTACK_RANGE, "jumper telegraph should match jump trigger range")
    heavy = Enemy(100, 100, enemy_type=EnemyType.JUMPER_HEAVY, difficulty=1.0)
    heavy.windup_action = "enemy_jump"
    assert_true(heavy.windup_telegraph_length() == JUMPER_ATTACK_RANGE + 60, "heavy jumper telegraph should match heavy jump trigger range")
    hunter = Enemy(100, 100, enemy_type=EnemyType.HUNTER, difficulty=1.0)
    hunter.windup_action = "hunter_homing"
    assert_true(hunter.windup_telegraph_length() == RANGED_ATTACK_RANGE + 170, "hunter telegraph should match homing trigger range")


def check_definition_registry():
    assert_true(definition_registry.validate() is True, "definition registry validation should pass")
    assert_true(definition_registry.require_weapon("pistol").id == "pistol", "registry should load pistol definition")
    assert_true(definition_registry.require_weapon("sword").attack_type == "melee_rect", "registry should load sword melee_rect definition")
    assert_true(definition_registry.require_room("combat").id == "combat", "registry should load combat room definition")
    assert_true("power_rounds" in definition_registry.upgrade_max_levels, "registry should expose upgrade max levels")

    try:
        definition_registry.require_weapon("__missing__")
    except KeyError as error:
        assert_true("Unknown weapon definition" in str(error), "missing weapon error should be clear")
    else:
        raise AssertionError("missing weapon definition should raise KeyError")


def check_perk_integrity():
    keys = set(definition_registry.perks)
    effect_keys = set(PERK_EFFECTS)
    assert_true(keys == effect_keys, f"perk definitions and effects should match, missing={keys ^ effect_keys}")
    player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    perks = PerkSystem()
    options = perks.roll_options(player)
    assert_true(len(options) > 0, "perk option generation should produce options")
    assert_true(all(option.get("key") in keys for option in options), "perk options should resolve to known keys")
    assert_true(all(option.get("build") for option in options), "perk options should include build identity metadata")
    engineer_option = perks._option_for_player(definition_registry.perks["impact_drive"], player)
    assert_true(_build_badge_text(engineer_option) == ("ENGINEER", False), "Engineer cards should render Engineer build identity")
    gunslinger_option = perks._option_for_player(definition_registry.perks["rapid_fire"], player)
    assert_true(_build_badge_text(gunslinger_option) == ("GUNSLINGER", False), "Gunslinger cards should render Gunslinger build identity")
    shared_option = perks._option_for_player(definition_registry.perks["glass_cannon"], player)
    assert_true(_build_badge_text(shared_option) == ("SHARED", True), "Shared/hybrid cards should render Shared plus hybrid marker")
    assert_true({"shadow_shuriken", "sanguine_rounds", "blood_bat", "blood_trail", "blade_drone", "bomber_drone"} <= keys, "new completion cards should resolve")

    player.perk_counts["scout_boots"] = 1
    unrelated = perks._option_for_player(definition_registry.perks["critical_spark"], player)
    assert_true(unrelated.get("synergy", "") == "", "synergy label should not show on unrelated off-build cards")
    related = perks._option_for_player(definition_registry.perks["overclock"], player)
    assert_true(related.get("synergy", "").startswith("NINJA "), "synergy label should be build-qualified when relevant")
    ninja_seen = False
    for _ in range(20):
        options = perks.roll_options(player)
        ninja_seen = ninja_seen or any(option.get("build") == "Ninja" for option in options)
    assert_true(ninja_seen, "emerging build affinity should keep matching build cards visible")


def check_starter_and_reroll_system():
    starter_keys = set(STARTER_BUILD_CARDS.values())
    missing_keys = starter_keys - set(definition_registry.perks)
    assert_true(not missing_keys, f"starter cards should exist, missing={missing_keys}")

    player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    perks = PerkSystem()
    starter_options = perks.roll_starter_options(player)
    assert_true(len(starter_options) == 3, "starter discovery should show exactly three cards")
    starter_builds = [option["build"] for option in starter_options]
    assert_true(len(set(starter_builds)) == 3, "starter discovery should show three different builds")
    assert_true(set(starter_builds) <= set(OFFICIAL_STARTER_BUILDS), "starter builds should be official builds only")
    assert_true(player.starter_choice_active, "starter choice should mark starter state active")
    assert_true(player.starter_missing_build in OFFICIAL_STARTER_BUILDS, "starter choice should track the hidden fourth build")
    assert_true(player.reroll_tokens == 0, "normal reroll tokens should start at zero")
    assert_true(perks.reroll_labels(player) == ["FREE STARTER REROLL"] * 3, "starter screen should show free starter reroll labels")

    old_options = [option["key"] for option in starter_options]
    old_missing = player.starter_missing_build
    old_gold = player.gold
    success, message = perks.reroll_option(player, 1)
    new_options = [option["key"] for option in perks.current_options]
    assert_true(success and old_missing in message, "starter reroll should replace one slot with hidden build")
    assert_true(new_options[0] == old_options[0] and new_options[2] == old_options[2], "starter reroll should only replace the requested slot")
    assert_true(perks.current_options[1]["build"] == old_missing, "starter reroll replacement should use the hidden fourth build")
    assert_true(player.gold == old_gold and player.reroll_tokens == 0, "starter reroll should not charge gold or token")
    assert_true(perks.reroll_labels(player) == ["NO REROLL"] * 3, "free starter reroll should be once per starter screen")

    selected = perks.apply(player, 1)
    assert_true(selected is not None, "starter selection should apply")
    assert_true(player.starter_build == old_missing, "first pick should store selected starter build")
    assert_true(not player.starter_choice_active, "selecting starter should end starter state")
    assert_true(player.perk_choices_made == 1, "selecting starter should count as first perk choice")

    ninja_player = Player()
    ninja_player.starter_choice_active = True
    ninja_perks = PerkSystem()
    ninja_definition = next(perk for perk in ninja_perks._available_perks(ninja_player) if perk["key"] == STARTER_BUILD_CARDS["Ninja"])
    ninja_perks.current_options = [ninja_perks._option_for_player(ninja_definition, ninja_player)]
    selected = ninja_perks.apply(ninja_player, 0)
    assert_true(selected is not None and ninja_player.starter_build == "Ninja", "Ninja starter should apply as a starter build")
    assert_true(ninja_player.active_weapon_key == "pistol", "Demo starters should keep the pistol until class weapons are enabled")

    affinity_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    affinity_player.starter_build = "Engineer"
    engineer_seen = False
    for _ in range(20):
        engineer_seen = engineer_seen or any(option.get("build") == "Engineer" for option in perks.roll_options(affinity_player))
    assert_true(engineer_seen, "starter build should softly bias later normal rolls")

    paid_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    paid_player.perk_counts["rapid_fire"] = 1
    perks.current_options = [
        perks._option_for_player(definition_registry.perks["rapid_fire"], paid_player),
        perks._option_for_player(definition_registry.perks["impact_drive"], paid_player),
        perks._option_for_player(definition_registry.perks["phantom_step"], paid_player),
    ]
    before_keys = [option["key"] for option in perks.current_options]
    paid_player.reroll_tokens = 1
    paid_player.gold = PERK_REROLL_GOLD_COST
    success, _message = perks.reroll_option(paid_player, 0)
    after_keys = [option["key"] for option in perks.current_options]
    assert_true(success, "normal reroll should work with a token")
    assert_true(paid_player.reroll_tokens == 0 and paid_player.gold == PERK_REROLL_GOLD_COST, "normal reroll should spend token before gold")
    assert_true(after_keys[1:] == before_keys[1:], "normal reroll should only replace one slot")
    assert_true(after_keys[0] != before_keys[0], "normal reroll should not return the same card key")
    assert_true(len(set(after_keys)) == len(after_keys), "normal reroll should avoid visible duplicate cards")

    paid_player.gold = PERK_REROLL_GOLD_COST
    before_gold_keys = [option["key"] for option in perks.current_options]
    success, _message = perks.reroll_option(paid_player, 1)
    assert_true(success, "normal reroll should work with gold when no token is available")
    assert_true(paid_player.gold == 0 and paid_player.reroll_gold_spent == PERK_REROLL_GOLD_COST, "gold reroll should spend exact named cost")
    assert_true(perks.current_options[0]["key"] == before_gold_keys[0] and perks.current_options[2]["key"] == before_gold_keys[2], "gold reroll should only replace selected slot")
    assert_true(paid_player.total_rerolls_used == 2, "normal reroll count should track successful paid rerolls")

    broke_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    perks.roll_options(broke_player)
    before = [option["key"] for option in perks.current_options]
    success, message = perks.reroll_option(broke_player, 0)
    assert_true(not success and "Need 1 token" in message, "normal reroll should block without token or gold")
    assert_true([option["key"] for option in perks.current_options] == before, "blocked reroll should not change options")


def check_tea_vendor_interaction():
    from definitions.prefab_definitions import PREFAB_DEFINITIONS
    from entities.npc import NPC

    assert_true("npc_tea_vendor" in PREFAB_DEFINITIONS, "tea vendor prefab should exist")
    assert_true("tea_drink" in SOUND_FILES and SOUND_FILES["tea_drink"] == "tea_drink.wav", "tea_drink audio key should exist")
    assert_true(0.90 <= DIALOGUE_WIDTH_RATIO <= 0.94, "dialogue box should use 90-94 percent width")
    assert_true(DIALOGUE_HEIGHT <= 100, "dialogue box should be compact")
    assert_true(DIALOGUE_BOTTOM_MARGIN >= 70, "dialogue box should avoid bottom toast/status overlap")
    vendor = NPC(0, 0, "Tea Vendor", "tea_vendor", "tea_vendor")
    assert_true(vendor.greet(FakePlayer(pygame.Rect(0, 0, 38, 38)), 1, 8) == "tea_vendor", "tea vendor should use tea dialogue")

    player = Player()
    stats_before = (
        player.max_health,
        player.health,
        player.damage_bonus,
        player.fire_rate_multiplier,
        player.active_weapon_key,
    )
    player.receive_tea()
    assert_true(player.tea_state == "holding", "tea should be held after vendor interaction")
    assert_true(player.try_weapon_attack() is None, "held tea should temporarily suppress weapon attack")

    tea_game = SimpleNamespace(player=player, audio=FakeAudio(), message="", npcs=[], dialogue=SimpleNamespace(close=lambda: None))
    handle_hub_events(tea_game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_t}))
    assert_true(tea_game.audio.played == ["tea_drink"], "tea_drink should play once when drinking starts")
    handle_hub_events(tea_game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_t}))
    assert_true(tea_game.audio.played == ["tea_drink"], "tea_drink should not spam while already drinking")
    player.cancel_tea()
    player.receive_tea()

    assert_true(player.start_drinking_tea() is True, "held tea should start drinking")
    player.update(0.2, [])
    assert_true(player.tea_state == "drinking", "tea drink animation should remain visible briefly")
    player.update(1.0, [])
    assert_true(player.tea_state is None, "tea should disappear after drinking animation")
    assert_true(player.active_weapon_key == stats_before[-1], "previous weapon should remain selected after drinking")
    stats_after = (
        player.max_health,
        player.health,
        player.damage_bonus,
        player.fire_rate_multiplier,
        player.active_weapon_key,
    )
    assert_true(stats_after == stats_before, "tea should not change gameplay stats")

    player.receive_tea()
    player.cancel_tea()
    assert_true(player.tea_state is None, "tea cancel should clear held tea safely")


def check_hub_layout_interactions():
    from game import Game

    game = Game()
    enter_hub(game)
    bounds = current_room_bounds()
    assert_true((bounds.width, bounds.height) == (HUB_ROOM_BOUNDS.width, HUB_ROOM_BOUNDS.height), "Hub should use compact bounds")
    roles = {npc.role: npc for npc in game.npcs}
    for role in ("blacksmith", "healer", "portal", "seer", "tea_vendor"):
        assert_true(role in roles, f"Hub should include {role}")
        assert_true(bounds.rect.contains(roles[role].rect), f"{role} should be inside compact Hub bounds")

    game.player.gold = 500
    gold_before = game.player.gold
    game.player.rect.center = roles["blacksmith"].rect.center
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1, "unicode": "1"}))
    assert_true(game.player.gold < gold_before, "blacksmith upgrade purchase should still work after repositioning")

    game.player.rect.center = roles["healer"].rect.center
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1, "unicode": "1"}))
    assert_true(game.dialogue.current_speaker == roles["healer"].name, "healer purchase/dialogue should still route to healer")

    game.player.rect.center = roles["seer"].rect.center
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    assert_true(game.dialogue.current_speaker == roles["seer"].name, "seer dialogue should still work after repositioning")

    game.player.rect.center = roles["tea_vendor"].rect.center
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    assert_true(game.player.tea_state == "holding", "tea vendor should still give tea after repositioning")
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_t}))
    assert_true(game.player.tea_state == "drinking", "tea should still start drinking in compact Hub")

    game.player.cancel_tea()
    game.player.rect.center = roles["portal"].rect.center
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    assert_true(getattr(game, "gatekeeper_ready", False), "first gatekeeper interaction should arm Stage start")
    handle_hub_events(game, pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    assert_true(game.stage.active and game.state == GameState.ROOM, "second gatekeeper interaction should start Stage through StageSystem")


def check_boss_small_room_adaptation():
    assert_true(BOSS_CLOSE_DASH_DISTANCE == 210, "boss close dash threshold should be retuned for small rooms")
    assert_true(BOSS_FAR_GRAVITY_DISTANCE == 720, "boss gravity threshold should be retuned for small rooms")

    boss_attacks = BossAttackSystem()
    player = FakePlayer(pygame.Rect(1300, 520, 38, 38))
    action = {
        "type": "boss_cone",
        "x": 520,
        "y": 520,
        "direction": pygame.Vector2(1, 0),
        "phase": 2,
        "difficulty": 2.0,
        "damage_multiplier": 1.0,
    }
    bullets = []
    boss_attacks.handle_action(action, [], bullets, player=player)
    assert_true(len(bullets) >= 6, "far boss action should create small-room gravity bullets")
    assert_true(any(abs(b.rect.centerx - player.rect.centerx) < 420 for b in bullets), "gravity redesign should spawn pressure around player area")

    combat = CombatSystem()
    real_player = FakePlayer(pygame.Rect(300, 300, 38, 38))
    boss = Enemy(320, 300, enemy_type=EnemyType.BOSS, difficulty=1.0)
    boss.phase = 3
    boss.encounter.phase = 3
    boss.encounter.state = 'exposed'
    boss.shield = 0
    boss.health = 1
    projectile = FakeProjectile(boss.rect.copy(), damage=9999)
    kills, boss_killed = combat.update(0.0, real_player, [projectile], [boss], [])
    assert_true(kills == 1 and boss_killed and not boss.alive, "boss should remain damageable and killable after attack retune")


def check_music_system():
    assert_true(MUSIC_TRACKS["hub"] == "hub.ogg", "hub music should use existing hub.ogg")
    assert_true(MUSIC_TRACKS["room"] == "combat.ogg", "room music should use existing combat.ogg")
    assert_true(MUSIC_TRACKS["boss"] == "boss_01.ogg", "boss music should use boss_01.ogg")

    music = MusicSystem()
    original_enabled = music.enabled
    music.enabled = False
    assert_true(music.play_music("hub") is False, "disabled music system should not play")
    assert_true(music.stop_music() is False, "disabled music system should not stop mixer music")

    music.enabled = True
    music.current_key = "hub"
    assert_true(music.play_music("hub") is True, "same music key should be treated as already playing")

    music.current_key = None
    music.music_path = ROOT / "__missing_music_dir__"
    assert_true(music.play_music("hub") is False, "missing music file should fail silently")
    music.enabled = original_enabled


def check_dev_tools_perk_tester():
    game = FakeDevGame()
    tools = DevTools(game)
    wave_designer = FakeWaveDesigner()
    asset_browser = FakeAssetBrowser()
    panel = DevPanel(
        game,
        tools,
        authoring_panel=FakeToolPanel(),
        wave_designer_panel=FakeToolPanel(),
        wave_designer=wave_designer,
        asset_browser=asset_browser,
    )

    if not DEV_TOOLS_ENABLED:
        panel.toggle()
        assert_true(not panel.active, "demo build should keep F12 dev panel closed")
        before = dict(game.player.perk_counts)
        assert_true(tools.grant_xp(500) is False, "demo build should block dev XP grants")
        assert_true(game.player.perk_counts == before, "demo build should not mutate perks through dev tools")
        return

    panel.toggle()
    assert_true(panel.active, "F12 dev panel should open")
    for category in CATEGORIES:
        panel._set_category(category)
        assert_true(panel.active_category == category, f"category should switch to {category}")

    panel.active_category = "Perks"
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (1200, 80)})
    handled = panel.handle_event(event)
    assert_true(handled, "inactive tool panel event should be consumed by dev panel")
    assert_true(panel.authoring_panel.calls == 0, "inactive Rooms panel should not consume input")

    player = game.player
    panel._set_category("Gameplay")
    gameplay_labels = [item["label"] for item in panel._layout()]
    for label in ("+5 XP", "+25 XP", "+75 XP", "+200 XP", "+500 XP"):
        assert_true(label in gameplay_labels, f"Gameplay dev tools should include {label}")

    xp_before = player.xp
    level_before = player.level
    assert_true(tools.grant_xp(500) is True, "dev XP grant should succeed when enabled")
    assert_true(player.xp > xp_before or player.level > level_before, "dev XP grant should use player XP gain path")

    assert_true(any(perk["key"] == "explosive_rounds" for perk in tools.perk_definitions()), "perk tester should discover real perk definitions")
    tools.cycle_perk_build_filter()
    assert_true(tools.perk_build_filter == "Gunslinger", "perk tester should cycle build filters")
    assert_true(all("Gunslinger" in perk.get("build_roles", [perk.get("build")]) for perk in tools.perk_definitions()), "Gunslinger filter should only show Gunslinger-compatible cards")
    tools.perk_build_filter = "All"
    tools.perk_build_filter = "Engineer"
    engineer_keys = {perk["key"] for perk in tools.perk_definitions()}
    assert_true({"impact_drive", "kinetic_rounds", "overclock", "explosive_rounds", "blade_drone", "bomber_drone"} <= engineer_keys, "Engineer filter should expose the complete machine package")
    tools.perk_build_filter = "Ninja"
    ninja_keys = {perk["key"] for perk in tools.perk_definitions()}
    assert_true({"scout_boots", "phantom_step", "overclock", "shadow_shuriken"} <= ninja_keys, "Ninja filter should expose the complete package")
    tools.perk_build_filter = "Vampire"
    vampire_keys = {perk["key"] for perk in tools.perk_definitions()}
    assert_true({"vital_core", "battle_recovery", "sanguine_rounds", "blood_bat", "blood_trail", "glass_cannon"} <= vampire_keys, "Vampire filter should expose the complete package")
    tools.perk_build_filter = "All"
    tools.select_perk_by_key("explosive_rounds")
    assert_true(tools.selected_perk_definition()["key"] == "explosive_rounds", "perk tester should select explosive_rounds")

    tools.grant_selected_perk_next_pick()
    assert_true(player.perk_counts["explosive_rounds"] == 1, "explosive pick 1 should increment count")
    assert_true(player.explosive_rounds is True, "pick 1 should unlock explosive bullets")
    assert_true(player.explosion_radius == 95, "pick 1 should keep baseline radius")
    assert_true(abs(player.explosion_splash_ratio - (1 / 3)) < 0.0001, "pick 1 should keep baseline splash")
    assert_true(abs(player.fire_rate_multiplier - 0.85) < 0.0001, "pick 1 should apply one fire-rate penalty")

    tools.grant_selected_perk_next_pick()
    assert_true(player.perk_counts["explosive_rounds"] == 2, "explosive pick 2 should increment count")
    assert_true(player.explosion_radius == 115, "pick 2 should upgrade radius")
    assert_true(abs(player.explosion_splash_ratio - (1 / 3)) < 0.0001, "pick 2 should not change splash")
    assert_true(abs(player.fire_rate_multiplier - 0.85) < 0.0001, "pick 2 should not apply another penalty")

    tools.grant_selected_perk_next_pick()
    assert_true(player.perk_counts["explosive_rounds"] == 3, "explosive pick 3 should increment count")
    assert_true(player.explosion_radius == 115, "pick 3 should keep radius")
    assert_true(abs(player.explosion_splash_ratio - 0.40) < 0.0001, "pick 3 should upgrade splash")
    assert_true(abs(player.fire_rate_multiplier - 0.85) < 0.0001, "pick 3 should not change fire rate")

    tools.grant_selected_perk_next_pick()
    assert_true(player.perk_counts["explosive_rounds"] == 4, "legendary should be fourth pick")
    assert_true(player.explosion_radius == 130, "legendary should upgrade radius")
    assert_true(abs(player.explosion_splash_ratio - 0.45) < 0.0001, "legendary should upgrade splash")
    assert_true(abs(player.fire_rate_multiplier - 1.0) < 0.0001, "legendary should restore fire-rate penalty")

    import systems.dev_tools as dev_tools_module
    original_enabled = dev_tools_module.DEV_TOOLS_ENABLED
    try:
        dev_tools_module.DEV_TOOLS_ENABLED = False
        before = dict(player.perk_counts)
        assert_true(tools.grant_selected_perk_next_pick() is None, "DEV_TOOLS_ENABLED false should prevent grants")
        assert_true(player.perk_counts == before, "disabled dev tools should not mutate perk counts")
        disabled_xp = player.xp
        disabled_level = player.level
        assert_true(tools.grant_xp(500) is False, "DEV_TOOLS_ENABLED false should block dev XP grants")
        assert_true(player.xp == disabled_xp and player.level == disabled_level, "disabled dev XP grants should not mutate XP")
    finally:
        dev_tools_module.DEV_TOOLS_ENABLED = original_enabled

    game.perks.roll_options(game.player)
    assert_true(len(game.perks.current_options) > 0, "normal perk selection should still roll options")
    tools.spawn_lab_enemy = lambda: "enemy"
    selected_before = tools.selected_enemy
    tools.cycle_selected_enemy()
    assert_true(tools.selected_enemy != selected_before, "Enemy Lab selection should still cycle")
    tools.toggle_author_mode()
    assert_true(tools.author_mode, "Author Mode should still toggle")
    runtime_info = tools.runtime_info()
    assert_true(f"Route: Room 1/{ROOMS_TO_BOSS}" in runtime_info, "DevTools Overview should show route progress")
    assert_true("Music: room" in runtime_info, "DevTools Overview should show current music key")
    panel._set_category("Waves")
    for item in panel._layout():
        if item["label"] == "Wave Designer":
            item["action"]()
            break
    assert_true(wave_designer.visible, "Wave Designer should still open")
    panel._set_category("Assets")
    for item in panel._layout():
        if item["label"] == "Asset Browser":
            item["action"]()
            break
    assert_true(asset_browser.visible, "Asset Browser should still open")


def check_dev_workspace_tools():
    import settings as settings_module
    import systems.dev_tools as dev_tools_module

    game = FakeDevGame()
    game.audio = SimpleNamespace(sounds={}, sounds_path=ROOT / "__missing_sounds__")
    game.music = SimpleNamespace(
        current_key="room",
        music_path=ROOT / "__missing_music__",
        play_music=lambda *args, **kwargs: False,
        stop_music=lambda *args, **kwargs: False,
    )
    game.horde = SimpleNamespace(last_metrics={}, enabled=False)
    game.loot = SimpleNamespace(pickups=[])
    game.effects = SimpleNamespace(sprite_effects=[])
    tools = DevTools(game)
    panel = DevPanel(game, tools, wave_designer_panel=FakeToolPanel(), wave_designer=FakeWaveDesigner(), asset_browser=FakeAssetBrowser())

    expected_tabs = {"Overview", "Gameplay", "Builds", "Tuning", "Waves", "Assets", "Audio", "Benchmark", "Logs"}
    assert_true(expected_tabs <= set(CATEGORIES), "Dev Workspace tabs should exist")
    for tab in expected_tabs:
        panel._set_category(tab)
        assert_true(panel.active_category == tab, f"Dev Workspace should switch to {tab}")

    tuning_lines = tools.workspace.tuning_lines()
    assert_true(any("Level 1 -> 2 XP" in line for line in tuning_lines), "Tuning tab should display XP values")
    assert_true(any("[RESTART REQUIRED]" in line or "[NEXT ROOM]" in line or "[LIVE]" in line for line in tuning_lines), "Tuning values should show reload safety status")
    if not DEV_TOOLS_ENABLED:
        xp_before = game.player.xp
        assert_true(tools.workspace.set_tuning_value("weapon.damage", 999) is False, "release mode should block tuning edits")
        assert_true(tools.workspace.save_snapshot() is None, "release mode should block snapshot writes")
        assert_true(tools.workspace.grant_build("Engineer", full=False) is False, "release mode should block build grants")
        assert_true(tools.grant_xp(500) is False and game.player.xp == xp_before, "release mode should block dev XP grants")
        return
    assert_true(tools.workspace.set_tuning_value("weapon.cooldown", -1) is False, "invalid negative cooldown should be rejected")
    assert_true(any("rejected" in line for line in tools.workspace.logs), "invalid tuning edit should be logged")

    snapshot = tools.workspace.save_snapshot()
    assert_true(snapshot is not None and snapshot.exists(), "snapshot save should create a JSON file")
    preview = tools.workspace.preview_snapshot(snapshot)
    assert_true(preview and "edited_values" in preview, "snapshot preview should read edited values")

    before_count = game.player.perk_counts.get("impact_drive", 0)
    assert_true(tools.workspace.grant_build("Engineer", full=False), "Build tester should grant starter Engineer through perk path")
    assert_true(game.player.perk_counts.get("impact_drive", 0) > before_count, "Build tester should mutate perk counts through PerkSystem")
    tools.workspace.clear_perk_state()
    assert_true(game.player.perk_counts == {}, "Build tester should clear perk state in dev mode")
    tools.workspace.give_level_pending_gold()
    assert_true(game.player.pending_level_ups > 0 and game.player.gold > 0, "Build tester should grant pending pick and gold")

    wave_lines = tools.workspace.wave_lines()
    assert_true(any("Room 1 Group" in line for line in wave_lines), "Wave tab should read Room 1 group data safely")
    asset_lines = tools.workspace.asset_lines()
    assert_true(any("archer/idle" in line for line in asset_lines), "Asset previewer should list Archer sliced sheets")
    audio_lines = tools.workspace.audio_lines()
    assert_true(any("MISSING" in line or "ok" in line for line in audio_lines), "Audio preview should show file availability")
    assert_true(tools.workspace.play_selected_audio() is False, "Audio preview should handle missing files safely")
    benchmark_lines = tools.workspace.benchmark_lines()
    assert_true(any("FPS:" in line for line in benchmark_lines), "Benchmark tab should show FPS")

    for index in range(100):
        tools.workspace.log(f"log {index}")
    assert_true(len(tools.workspace.logs) <= 80, "Workspace logs should be bounded")

    original_settings_enabled = settings_module.DEV_TOOLS_ENABLED
    original_dev_enabled = dev_tools_module.DEV_TOOLS_ENABLED
    try:
        settings_module.DEV_TOOLS_ENABLED = False
        dev_tools_module.DEV_TOOLS_ENABLED = False
        blocked_game = FakeDevGame()
        blocked_tools = DevTools(blocked_game)
        xp_before = blocked_game.player.xp
        assert_true(blocked_tools.workspace.set_tuning_value("weapon.damage", 999) is False, "DEV_TOOLS_ENABLED false should block tuning edits")
        assert_true(blocked_tools.workspace.save_snapshot() is None, "DEV_TOOLS_ENABLED false should block file writes")
        assert_true(blocked_tools.workspace.grant_build("Engineer", full=False) is False, "DEV_TOOLS_ENABLED false should block build grants")
        assert_true(blocked_tools.grant_xp(500) is False and blocked_game.player.xp == xp_before, "DEV_TOOLS_ENABLED false should block dev actions")
    finally:
        settings_module.DEV_TOOLS_ENABLED = original_settings_enabled
        dev_tools_module.DEV_TOOLS_ENABLED = original_dev_enabled


def check_release_dev_tools_flag():
    base_env = os.environ.copy()
    base_env.pop("BLUECUBE_DEV_TOOLS", None)
    dev_result = subprocess.check_output(
        [sys.executable, "-c", "import settings; print(int(settings.DEV_TOOLS_ENABLED))"],
        cwd=ROOT,
        env=base_env,
        text=True,
    ).strip()
    release_env = base_env.copy()
    release_env["BLUECUBE_DEV_TOOLS"] = "0"
    release_result = subprocess.check_output(
        [sys.executable, "-c", "import settings; print(int(settings.DEV_TOOLS_ENABLED))"],
        cwd=ROOT,
        env=release_env,
        text=True,
    ).strip()
    frozen_result = subprocess.check_output(
        [sys.executable, "-c", "import sys; sys.frozen=True; import settings; print(int(settings.DEV_TOOLS_ENABLED))"],
        cwd=ROOT,
        env=base_env,
        text=True,
    ).strip()
    assert_true(dev_result == "1", "normal source invocation should default DEV_TOOLS_ENABLED on")
    assert_true(release_result == "0", "release invocation should disable DEV_TOOLS_ENABLED with BLUECUBE_DEV_TOOLS=0")
    assert_true(frozen_result == "0", "packaged/frozen invocation should default DEV_TOOLS_ENABLED off")


def check_sprite_sheet_animation_loader():
    expected = {
        ("archer", "idle"): 6,
        ("archer", "run"): 4,
        ("archer", "shoot"): 8,
        ("warrior", "idle"): 8,
        ("warrior", "run"): 6,
        ("warrior", "attack1"): 4,
        ("warrior", "attack2"): 4,
        ("warrior", "guard"): 6,
    }
    report = sprite_animation_report()
    for key, expected_count in expected.items():
        character, state = key
        spec = animation_spec(character, state)
        frames = load_animation_frames(character, state)
        assert_true(spec is not None, f"{character}/{state} should have an animation spec")
        assert_true(detected_frame_count(character, state) == expected_count, f"{character}/{state} sheet should expose {expected_count} horizontal frames")
        assert_true(len(frames) == expected_count, f"{character}/{state} should load {expected_count} sliced frames")
        assert_true(frames[0].get_flags() & pygame.SRCALPHA, f"{character}/{state} frames should preserve alpha")
        assert_true(report[character][state]["loaded"] == expected_count, f"{character}/{state} report should match loaded frames")

    idle = SpriteSheetAnimation("archer", "idle")
    first_index = idle.current_frame_index()
    idle.update(1.0 / animation_spec("archer", "idle").fps)
    assert_true(idle.current_frame_index() != first_index, "looping animation should advance by dt")
    idle.update(10.0)
    assert_true(not idle.finished, "looping animation should not finish")

    shoot = SpriteSheetAnimation("archer", "shoot")
    shoot.update(10.0)
    assert_true(shoot.finished, "non-looping shoot animation should finish")
    assert_true(shoot.current_frame_index() == len(shoot.frames) - 1, "non-looping animation should hold final frame")

    normal = idle.current_frame(facing_left=False)
    flipped = idle.current_frame(facing_left=True)
    assert_true(normal is not None and flipped is not None, "facing direction should return renderable frames")
    assert_true(normal.get_size() == flipped.get_size(), "flipped frame should keep the same size")

    missing = SpriteSheetAnimation("missing_character", "idle")
    assert_true(missing.current_frame() is None, "missing animation should fall back by returning no frame")


def main():
    pygame.init()
    checks = [
        ("RoomSystem", check_room_system),
        ("SpawnSystem", check_spawn_system),
        ("WaveSystem", check_wave_system),
        ("RoomFlowSystem", check_room_flow_system),
        ("XPProgression", check_xp_progression),
        ("HordeSystem", check_horde_system),
        ("RoomXPBudget", check_room_xp_budget),
        ("StageRoute", check_stage_route_verification),
        ("CombatSystem", check_combat_system),
        ("BuildMechanics", check_build_mechanics),
        ("EngineerMachineTeam", check_engineer_machine_team),
        ("EnemyFeelPass", check_enemy_feel_pass),
        ("DefinitionRegistry", check_definition_registry),
        ("PerkIntegrity", check_perk_integrity),
        ("StarterRerollSystem", check_starter_and_reroll_system),
        ("TeaVendor", check_tea_vendor_interaction),
        ("HubLayoutInteractions", check_hub_layout_interactions),
        ("BossSmallRoomAdaptation", check_boss_small_room_adaptation),
        ("MusicSystem", check_music_system),
        ("DevToolsPerkTester", check_dev_tools_perk_tester),
        ("DevWorkspace", check_dev_workspace_tools),
        ("ReleaseDevToolsFlag", check_release_dev_tools_flag),
        ("SpriteSheetAnimation", check_sprite_sheet_animation_loader),
    ]

    for name, check in checks:
        check()
        print(f"PASS {name}")

    print("HEADLESS_CHECKS_OK")


if __name__ == "__main__":
    main()
