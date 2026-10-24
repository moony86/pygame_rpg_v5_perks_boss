from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import pygame

import settings
from systems.definition_registry import definition_registry
from systems.audio_system import SOUND_FILES
from systems.music_system import MUSIC_TRACKS
from systems.perk_system import OFFICIAL_STARTER_BUILDS, STARTER_BUILD_CARDS
from systems.sprite_animation import sprite_animation_report


MAX_WORKSPACE_LOGS = 80
SNAPSHOT_DIR = Path("dev_snapshots")


@dataclass
class TuningValue:
    key: str
    label: str
    module_name: str
    attr: str
    status: str
    minimum: float | None = None
    maximum: float | None = None
    step: float = 1.0


class DevWorkspace:
    def __init__(self, game, tools):
        self.game = game
        self.tools = tools
        self.logs = []
        self.last_snapshot_path = None
        self.selected_tuning_index = 0
        self.selected_audio_index = 0
        self.last_audio_preview = 0.0
        self.benchmark_sample = {}
        self.tuning_values = self._build_tuning_values()
        self.default_values = {value.key: self._read_value(value) for value in self.tuning_values}

    def dev_enabled(self):
        return bool(settings.DEV_TOOLS_ENABLED)

    def log(self, message):
        stamp = time.strftime("%H:%M:%S")
        self.logs.append(f"{stamp} {message}")
        if len(self.logs) > MAX_WORKSPACE_LOGS:
            self.logs = self.logs[-MAX_WORKSPACE_LOGS:]
        self.tools.message = message
        return message

    def _require_dev(self, action):
        if self.dev_enabled():
            return True
        self.log(f"blocked: {action} requires DEV_TOOLS_ENABLED")
        return False

    def _build_tuning_values(self):
        return [
            TuningValue("xp.level_1_to_2", "Level 1 -> 2 XP", "systems.xp_progression", "EARLY_XP_BASE", "RESTART REQUIRED", 1, 100000, 25),
            TuningValue("xp.early_increment", "Early XP Increment", "systems.xp_progression", "EARLY_XP_STEP", "RESTART REQUIRED", 0, 10000, 5),
            TuningValue("xp.late_multiplier", "Late XP Multiplier", "systems.xp_progression", "LATE_XP_MULTIPLIER", "RESTART REQUIRED", 0.1, 10, 0.1),
            TuningValue("weapon.damage", "Base Bullet Damage", "settings", "PROJECTILE_DAMAGE", "RESTART REQUIRED", 1, 999, 1),
            TuningValue("weapon.speed", "Bullet Speed", "settings", "PROJECTILE_SPEED", "RESTART REQUIRED", 50, 4000, 25),
            TuningValue("weapon.cooldown", "Fire Cooldown", "settings", "SHOOT_COOLDOWN", "RESTART REQUIRED", 0.05, 5, 0.025),
            TuningValue("enemy.chaser_hp", "Chaser HP", "settings", "ENEMY_HEALTH", "RESTART REQUIRED", 1, 9999, 5),
            TuningValue("enemy.chaser_speed", "Chaser Speed", "settings", "ENEMY_SPEED", "RESTART REQUIRED", 1, 2000, 5),
            TuningValue("enemy.contact_damage", "Contact Damage", "settings", "ENEMY_DAMAGE", "RESTART REQUIRED", 0, 500, 1),
            TuningValue("enemy.ranged_speed", "Ranged Speed Base", "settings", "ENEMY_SPEED", "RESTART REQUIRED", 1, 2000, 5),
            TuningValue("enemy.jumper_speed", "Jumper Speed Base", "settings", "ENEMY_SPEED", "RESTART REQUIRED", 1, 2000, 5),
            TuningValue("difficulty.build_power_room1", "Build Power Room 1", "systems.wave_system", "DEFAULT_BUILD_POWER_INFLUENCE", "NEXT ROOM", 0, 10, 0.05),
            TuningValue("difficulty.hp_exponent", "Enemy HP Difficulty Exponent", "entities.enemy", "Enemy.health_scale", "RESTART REQUIRED", None, None, 0.05),
            TuningValue("difficulty.damage_multiplier", "Enemy Damage Multiplier Formula", "entities.enemy", "Enemy.damage_multiplier", "RESTART REQUIRED", None, None, 0.05),
            TuningValue("difficulty.speed_multiplier", "Enemy Speed Multiplier Formula", "entities.enemy", "Enemy.speed_scale", "RESTART REQUIRED", None, None, 0.05),
            TuningValue("room1.hard_cap", "Room 1 Hard Cap", "systems.wave_system", "ROOM_1_GROUP_HARD_CAP", "NEXT ROOM", 1, 500, 1),
            TuningValue("room1.expected_min", "Room 1 Expected Clear Min", "systems.wave_system", "ROOM_1_EXPECTED_CLEAR_MIN", "NEXT ROOM", 0.1, 120, 0.5),
            TuningValue("room1.expected_max", "Room 1 Expected Clear Max", "systems.wave_system", "ROOM_1_EXPECTED_CLEAR_MAX", "NEXT ROOM", 0.1, 180, 0.5),
            TuningValue("room1.burst_size", "Room 1 Burst Size", "systems.wave_system", "ROOM_1_GROUP_SATURATION_CAP", "NEXT ROOM", 1, 200, 1),
            TuningValue("horde.real_cap", "Horde Real Enemy Cap", "systems.horde_system", "HORDE_REAL_CAP", "RESTART REQUIRED", 1, 2000, 10),
            TuningValue("horde.lod0", "Horde LOD0 Distance", "systems.horde_system", "LOD0_DISTANCE", "RESTART REQUIRED", 1, 5000, 25),
            TuningValue("horde.lod1", "Horde LOD1 Distance", "systems.horde_system", "LOD1_DISTANCE", "RESTART REQUIRED", 1, 8000, 25),
            TuningValue("horde.lod1_interval", "Horde LOD1 Interval", "systems.horde_system", "LOD1_INTERVAL", "RESTART REQUIRED", 1, 60, 1),
            TuningValue("horde.lod2_interval", "Horde LOD2 Interval", "systems.horde_system", "LOD2_INTERVAL", "RESTART REQUIRED", 1, 120, 1),
            TuningValue("horde.grid_size", "Horde Spatial Grid Size", "systems.horde_system", "HORDE_GRID_CELL_SIZE", "RESTART REQUIRED", 16, 512, 8),
            TuningValue("loot.magnet_radius", "Loot Magnet Radius", "systems.loot_system", "DEFAULT_MAGNET_RADIUS", "RESTART REQUIRED", 0, 1000, 10),
            TuningValue("loot.max_magnet_speed", "Loot Max Magnet Speed", "entities.pickup", "PICKUP_MAX_MAGNET_SPEED", "LIVE", 0, 4000, 25),
            TuningValue("loot.direct_homing_timeout", "Loot Direct Homing Timeout", "entities.pickup", "PICKUP_MAGNET_DELAY", "LIVE", 0, 5, 0.05),
        ]

    def _module(self, name):
        return __import__(name, fromlist=["*"])

    def _read_value(self, value):
        try:
            if "." in value.attr:
                return "formula"
            return getattr(self._module(value.module_name), value.attr)
        except Exception:
            return None

    def tuning_lines(self, limit=18):
        lines = ["Tuning Values  [LIVE / NEXT ROOM / RESTART REQUIRED]"]
        for index, value in enumerate(self.tuning_values[:limit]):
            current = self._read_value(value)
            marker = ">" if index == self.selected_tuning_index else " "
            lines.append(f"{marker} {value.label}: {current} [{value.status}]")
        return lines

    def selected_tuning(self):
        if not self.tuning_values:
            return None
        self.selected_tuning_index %= len(self.tuning_values)
        return self.tuning_values[self.selected_tuning_index]

    def select_next_tuning(self):
        self.selected_tuning_index = (self.selected_tuning_index + 1) % len(self.tuning_values)
        value = self.selected_tuning()
        self.log(f"selected tuning {value.key}")
        return value

    def select_previous_tuning(self):
        self.selected_tuning_index = (self.selected_tuning_index - 1) % len(self.tuning_values)
        value = self.selected_tuning()
        self.log(f"selected tuning {value.key}")
        return value

    def edit_selected_tuning(self, direction, large=False):
        if not self._require_dev("edit tuning"):
            return False
        value = self.selected_tuning()
        current = self._read_value(value)
        if not isinstance(current, (int, float)):
            self.log(f"edit rejected: {value.key} is preview-only")
            return False
        step = value.step * (10 if large else 1)
        return self.set_tuning_value(value.key, current + direction * step)

    def reset_selected_tuning(self):
        value = self.selected_tuning()
        return self.set_tuning_value(value.key, self.default_values.get(value.key))

    def set_tuning_value(self, key, new_value):
        if not self._require_dev("set tuning"):
            return False
        value = next((item for item in self.tuning_values if item.key == key), None)
        if value is None:
            self.log(f"edit rejected: unknown tuning {key}")
            return False
        if not isinstance(new_value, (int, float)):
            self.log(f"edit rejected: {key} needs a number")
            return False
        if value.minimum is not None and new_value < value.minimum:
            self.log(f"edit rejected: {key} below minimum {value.minimum}")
            return False
        if value.maximum is not None and new_value > value.maximum:
            self.log(f"edit rejected: {key} above maximum {value.maximum}")
            return False
        if "." in value.attr:
            self.log(f"edit rejected: {key} is formula/documentation only")
            return False
        module = self._module(value.module_name)
        old_value = getattr(module, value.attr)
        if isinstance(old_value, int) and not isinstance(old_value, bool):
            new_value = int(round(new_value))
        setattr(module, value.attr, new_value)
        self.log(f"tuning {key}: {old_value} -> {new_value} [{value.status}]")
        return True

    def reload_tuning(self):
        self.log("tuning reload requested; code constants marked restart/next-room are not hot-reloaded")
        return False

    def snapshot_data(self):
        player = self.game.player
        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "current_room": getattr(self.game, "room_number", None),
            "state": getattr(getattr(self.game, "state", None), "name", "-"),
            "player_level": getattr(player, "level", None),
            "active_build": self.strongest_build(),
            "dev_enabled": self.dev_enabled(),
            "edited_values": {value.key: self._read_value(value) for value in self.tuning_values},
        }

    def save_snapshot(self):
        if not self._require_dev("save snapshot"):
            return None
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        path = SNAPSHOT_DIR / f"tuning_{time.strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(self.snapshot_data(), indent=2), encoding="utf-8")
        self.last_snapshot_path = str(path)
        self.log(f"snapshot saved: {path}")
        return path

    def preview_snapshot(self, path=None):
        path = Path(path or self.last_snapshot_path or "")
        if not path.exists():
            self.log("snapshot preview failed: no snapshot path")
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        self.log(f"snapshot preview loaded: {path} restart required for unsafe values")
        return data

    def strongest_build(self):
        counts = {build: 0 for build in OFFICIAL_STARTER_BUILDS}
        for key, count in self.game.player.perk_counts.items():
            perk = definition_registry.perks.get(key)
            build = (perk or {}).get("build")
            if build in counts:
                counts[build] += count
        return max(counts, key=counts.get) if any(counts.values()) else "-"

    def build_lines(self):
        p = self.game.player
        perks = ", ".join(f"{k}:{v}" for k, v in sorted(p.perk_counts.items()) if v) or "-"
        return [
            f"Strongest build: {self.strongest_build()}",
            f"Owned cards: {perks}",
            f"Engineer: gun={p.engineer_gun_count} blade={p.engineer_blade_count} bomber={p.engineer_bomber_count} airstrike={p.engineer_airstrike_unlocked}",
            f"Vampire: blood={p.vampire_blood}/{p.vampire_blood_max} feast={p.vampire_feast_timer:.1f} moon={p.vampire_blood_moon_timer:.1f} bat={p.vampire_bat_state}",
            f"Ninja: dash={p.dash_cooldown_timer:.1f} momentum={p.ninja_momentum:.1f}/{p.ninja_momentum_max:.1f} refund={p.dash_refund_this_dash:.1f}/{p.dash_refund_cap:.1f}",
            f"Gunslinger: projectiles={p.projectile_count} fire_rate={p.fire_rate_multiplier:.2f} crit={p.crit_chance:.2f} pierce={p.pierce}",
            f"Pending picks={p.pending_level_ups} gold={p.gold} rerolls={getattr(p, 'reroll_tokens', 0)}",
        ]

    def grant_build(self, build, full=True):
        if not self._require_dev("grant build"):
            return False
        keys = [definition["key"] for definition in self.tools.perk_definitions() if definition.get("build") == build]
        if not keys and build in STARTER_BUILD_CARDS:
            keys = [STARTER_BUILD_CARDS[build]]
        applied = 0
        for key in keys:
            target = 4 if full else 1
            self.tools.select_perk_by_key(key)
            while self.game.player.perk_counts.get(key, 0) < target:
                if self.tools.grant_selected_perk_next_pick() is None:
                    break
                applied += 1
        self.log(f"build grant {build} {'full' if full else 'starter'} applied={applied}")
        return applied > 0

    def clear_perk_state(self):
        if not self._require_dev("clear perk state"):
            return False
        player = self.game.player
        if not callable(getattr(player, "reset", None)):
            self.log("build reset unavailable: player has no reset method")
            return False
        center = player.rect.center
        progress = {key: getattr(player, key) for key in
                    ("gold", "level", "xp", "xp_to_next", "pending_level_ups", "reroll_tokens")}
        player.reset()
        for key, value in progress.items():
            setattr(player, key, value)
        player.rect.center = center
        if hasattr(self.game, "upgrades"):
            self.game.upgrades.reset()
        if hasattr(self.game, "shooting"):
            self.game.shooting.reset()
        for projectile in self.game.projectiles:
            if hasattr(projectile, "kill"):
                projectile.kill()
        self.game.projectiles.clear()
        self.game.perks.current_options = []
        if getattr(self.game.state, "name", "") == "PERK_SELECT":
            self.game.state = self.game.previous_state
        self.log("reset build and shop effects; level, XP and gold preserved")
        return True

    def give_level_pending_gold(self):
        if not self._require_dev("give level/gold"):
            return False
        self.game.player.pending_level_ups += 1
        self.game.player.add_gold(250)
        self.log("added pending pick and 250 gold")
        return True

    def wave_lines(self):
        info = self.tools._wave_info()
        return [
            f"Room 1 Group: {info['group_number']}/{info['group_total']} {info['group_id']} {info['group_name']}",
            f"State: {info['group_state']} elapsed={info['group_elapsed']} expected={info['expected_clear_time']} max={info['max_time']}",
            f"Spawned/living: {info['group_spawned']} / {info['group_living']} threshold={info['release_reason']}",
            f"Hard cap={info['hard_cap']} saturation={info['saturation_cap']} pressure={info['nearby_pressure']}",
            f"Wave mode={info['mode']} index={info['index']}/{info['total']} left={info['left']}",
            "Actions are dev-only: restart room1, spawn group, skip group, pause/resume, clear enemies, export snapshot",
        ]

    def restart_room_one(self):
        if not self._require_dev("restart room 1"):
            return False
        self.game.room_number = 1
        from systems.scene_system import enter_room
        enter_room(self.game)
        self.log("restarted room 1")
        return True

    def spawn_selected_group_now(self):
        if not self._require_dev("spawn selected group"):
            return False
        waves = self.game.waves
        wave = waves.waves[waves.current_wave_index] if waves.waves else None
        group = wave.get("groups", [None])[0] if wave else None
        if not group:
            self.log("no group to spawn")
            return False
        count = 0
        for enemy_type in group.get("enemies", [])[: group.get("burst", 3)]:
            enemy = self.game.enemy_pool.acquire(self.game.player.rect.centerx + 120, self.game.player.rect.centery, enemy_type, 1.0)
            self.game.enemies.append(enemy)
            count += 1
        self.log(f"spawned selected group burst count={count}")
        return True

    def skip_group(self):
        if not self._require_dev("skip group"):
            return False
        waves = self.game.waves
        waves.current_group_state = "skipped"
        waves.next_group_release_reason = "dev skip"
        self.log("skipped current group")
        return True

    def toggle_wave_pause(self):
        if not self._require_dev("pause waves"):
            return False
        self.game.waves.wave_state = "paused" if self.game.waves.wave_state != "paused" else "spawning"
        self.log(f"wave spawning {self.game.waves.wave_state}")
        return True

    def clear_enemies(self):
        if not self._require_dev("clear enemies"):
            return False
        count = len(self.game.enemies)
        self.game.enemy_pool.release_many(self.game.enemies)
        self.game.enemies.clear()
        self.log(f"cleared enemies count={count}")
        return True

    def export_room1_group_snapshot(self):
        if not self._require_dev("export room1 group"):
            return None
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        path = SNAPSHOT_DIR / f"room1_groups_{time.strftime('%Y%m%d_%H%M%S')}.json"
        data = {"timestamp": time.time(), "wave": self.tools._wave_info()}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.last_snapshot_path = str(path)
        self.log(f"room1 group snapshot saved: {path}")
        return path

    def asset_lines(self):
        report = sprite_animation_report()
        lines = ["Asset definitions / sliced animation preview"]
        for character, states in report.items():
            for state, data in states.items():
                lines.append(f"{character}/{state}: {data['loaded']}/{data['expected']} frames {data['fps']}fps loop={data['loop']} {data['path']}")
        lines.extend([
            "Other preview targets: engineer blade, blade hit VFX, pickups, projectiles are listed in Asset Browser.",
            "Controls in Asset Browser: Up/Down select, / search, R reload, F filter.",
        ])
        return lines

    def audio_keys(self):
        sfx = [(key, SOUND_FILES[key], "sfx") for key in sorted(SOUND_FILES)]
        music = [(key, MUSIC_TRACKS[key], "music") for key in sorted(MUSIC_TRACKS)]
        return sfx + music

    def audio_lines(self):
        keys = self.audio_keys()
        lines = ["Audio Preview"]
        for index, (key, filename, kind) in enumerate(keys[:18]):
            marker = ">" if index == self.selected_audio_index else " "
            root = self.game.audio.sounds_path if kind == "sfx" else self.game.music.music_path
            exists = (root / filename).exists()
            lines.append(f"{marker} {kind} {key}: {filename} {'ok' if exists else 'MISSING'}")
        return lines

    def select_next_audio(self):
        self.selected_audio_index = (self.selected_audio_index + 1) % len(self.audio_keys())
        key = self.audio_keys()[self.selected_audio_index][0]
        self.log(f"selected audio {key}")

    def play_selected_audio(self):
        if not self._require_dev("audio preview"):
            return False
        now = time.time()
        if now - self.last_audio_preview < 0.25:
            return False
        self.last_audio_preview = now
        key, filename, kind = self.audio_keys()[self.selected_audio_index]
        if kind == "sfx":
            sound = self.game.audio.sounds.get(key)
            if sound is None:
                self.log(f"missing sound preview: {key} {filename}")
                return False
            sound.play()
        else:
            ok = self.game.music.play_music(key, fade_ms=0)
            if not ok:
                self.log(f"missing music preview: {key} {filename}")
                return False
        self.log(f"played {kind}: {key}")
        return True

    def stop_audio(self):
        if not self._require_dev("stop audio"):
            return False
        self.game.music.stop_music(fade_ms=0)
        self.log("audio stopped")
        return True

    def benchmark_lines(self):
        horde = getattr(self.game, "horde", None)
        metrics = getattr(horde, "last_metrics", {})
        return [
            f"FPS: {self.game.clock.get_fps():.1f}",
            f"Enemy ms: {metrics.get('enemy_update_ms', 0.0):.2f}",
            f"Draw ms: {metrics.get('draw_ms', 0.0):.2f}",
            f"Combat ms: {metrics.get('combat_collision_ms', 0.0):.2f}",
            f"Projectile checks: {metrics.get('projectile_checks', 0)}",
            f"Real/Virtual: {metrics.get('real', 0)} / {metrics.get('virtual', 0)}",
            f"LOD: {metrics.get('lod0', 0)} / {metrics.get('lod1', 0)} / {metrics.get('lod2', 0)}",
            f"Pickups/effects: {len(getattr(self.game.loot, 'pickups', []))} / {len(getattr(self.game.effects, 'sprite_effects', []))}",
        ]

    def spawn_benchmark_horde(self, count):
        return self.tools.spawn_horde_test(count)

    def run_short_benchmark_sample(self):
        if not self._require_dev("benchmark sample"):
            return False
        self.benchmark_sample = {
            "fps": self.game.clock.get_fps(),
            "horde": getattr(getattr(self.game, "horde", None), "last_metrics", {}).copy(),
            "enemies": len(self.game.enemies),
            "time": time.time(),
        }
        self.log("captured short benchmark sample")
        return True
