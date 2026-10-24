import pygame

from game_state import GameState
from settings import (
    DEV_TOOLS_ENABLED,
    ENEMY_RESPAWN_SAFE_RADIUS,
    ENEMY_HEALTH,
    ENEMY_SPAWN_SAFE_RADIUS,
    PROJECTILE_DAMAGE,
    ROOMS_TO_BOSS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from entities.enemy import EnemyType
from systems.definition_registry import definition_registry
from systems.scene_system import enter_boss, enter_hub, enter_room
from systems.xp_budget import room_completion_xp
from systems.room_bounds import current_room_bounds
from systems.dev_workspace import DevWorkspace


MAX_EVENT_LOG = 100
DEV_PERK_ORDER = [
    "rapid_fire",
    "power_rounds",
    "hollow_point",
    "glass_cannon",
    "split_shot",
    "needle_rounds",
    "kinetic_rounds",
    "critical_spark",
    "overclock",
    "explosive_rounds",
    "impact_drive",
    "blade_drone",
    "bomber_drone",
    "vital_core",
    "battle_recovery",
    "sanguine_rounds",
    "blood_bat",
    "blood_trail",
    "scout_boots",
    "phantom_step",
    "shadow_shuriken",
]
DEV_PERK_GROUPS = ["All", "Gunslinger", "Ninja", "Engineer", "Vampire", "Shared/Utility"]


class DevTools:
    def __init__(self, game, authoring=None):
        self.game = game
        self.authoring = authoring
        self.show_hitboxes = False
        self.show_spawn_debug = False
        self.show_camera_debug = False
        self.show_collision_debug = False
        self.show_wave_debug = False
        self.god_mode = False
        self.slow_motion = False
        self.selected_enemy = EnemyType.CHASER
        self.last_spawn_position = None
        self.selected_object = None
        self.selected_kind = None
        self.search_query = ""
        self.search_results = []
        self.event_log = []
        self.log_paused = False
        self.log_auto_scroll = True
        self.author_mode = False
        self._focus_target = None
        self.selected_perk_index = 0
        self.perk_search_query = ""
        self.perk_build_filter = "All"
        self.message = "Dev tools ready"
        self.workspace = DevWorkspace(game, self)
        if DEV_TOOLS_ENABLED:
            self.game.events.subscribe("*", self.record_event)

    @property
    def time_scale(self):
        if not DEV_TOOLS_ENABLED:
            return 1.0
        return 0.25 if self.slow_motion else 1.0

    def runtime_info(self):
        game = self.game
        player = game.player
        room_type = getattr(game.rooms, "room_type", None)
        wave_info = self._wave_info()
        last_spawn = self._format_point(self.last_spawn_position)
        route_progress = self._route_progress()
        music = getattr(game, "music", None)
        music_key = getattr(music, "current_key", None) or "-"
        return [
            f"FPS: {game.clock.get_fps():.1f}",
            f"State: {game.state.name}",
            f"Room: {game.room_number}",
            f"Room type: {room_type.name if room_type else '-'}",
            f"Route: {route_progress}",
            f"Room XP: {room_completion_xp(game.room_number)}",
            f"Player: {player.rect.centerx}, {player.rect.centery}",
            f"Level: {player.level}",
            f"XP: {player.xp} / {player.xp_to_next}",
            f"Pending perks: {player.pending_level_ups}",
            f"Music: {music_key}",
            f"Camera: {int(game.camera.offset.x)}, {int(game.camera.offset.y)}",
            f"Enemies: {len(game.enemies)}",
            f"Projectiles: {len(game.projectiles)}",
            f"Bullets: {len(game.enemy_bullets)}",
            *self._horde_lines(),
            f"Weapon: {player.active_weapon.name}",
            f"Exit open: {game.room_exit_open}",
            f"Wave: {wave_info['state']} mode={wave_info['mode']}",
            f"Wave index: {wave_info['index']} / {wave_info['total']}",
            f"Wave left: {wave_info['left']} active_limit: {wave_info['active_limit']}",
            f"Group: {wave_info['group_number']} / {wave_info['group_total']} {wave_info['group_id']} {wave_info['group_name']} state={wave_info['group_state']}",
            f"Group elapsed/expected/max: {wave_info['group_elapsed']}s / {wave_info['expected_clear_time']}s / {wave_info['max_time']}s",
            f"Group spawned/living: {wave_info['group_spawned']} / {wave_info['group_living']}",
            f"Next group release: {wave_info['release_reason']}",
            f"Pressure debug: nearby={wave_info['nearby_pressure']} soft_cap={wave_info['saturation_cap']} hard={wave_info['hard_cap']} blocked={wave_info['blocked_reason']}",
            f"Ownership: old_queue={wave_info['old_spawn_queue_length']} legacy_clear={wave_info['legacy_clearing_gate']}",
            f"Room 1 STK est: {wave_info['stk_estimate']}",
            f"Build power influence: {wave_info['build_power_influence']}",
            f"All waves spawned: {wave_info['all_spawned']}",
            f"Spawn radius: {ENEMY_SPAWN_SAFE_RADIUS} last: {last_spawn}",
            f"Author mode: {'on' if self.author_mode else 'off'}",
            f"Selected enemy: {self.selected_enemy.name}",
        ]

    def _route_progress(self):
        state_name = getattr(getattr(self.game, "state", None), "name", "")
        if state_name == "BOSS" or self.game.room_number > ROOMS_TO_BOSS:
            return "Boss"
        room_number = max(1, min(self.game.room_number, ROOMS_TO_BOSS))
        return f"Room {room_number}/{ROOMS_TO_BOSS}"

    def _wave_info(self):
        waves = getattr(self.game, "waves", None)
        if waves is None:
            return {
                "state": "-",
                "index": "-",
                "total": "-",
                "left": "-",
                "active_limit": "-",
                "all_spawned": "-",
                "timer": "-",
                "label": "-",
                "mode": "-",
                "group_id": "-",
                "group_name": "-",
                "group_number": "-",
                "group_total": "-",
                "group_state": "-",
                "group_elapsed": "-",
                "group_spawned": "-",
                "group_living": "-",
                "expected_clear_time": "-",
                "max_time": "-",
                "release_reason": "-",
                "nearby_pressure": "-",
                "saturation_cap": "-",
                "hard_cap": "-",
                "blocked_reason": "-",
                "old_spawn_queue_length": "-",
                "legacy_clearing_gate": "-",
                "stk_estimate": "-",
                "build_power_influence": "-",
            }

        wave = None
        wave_list = getattr(waves, "waves", [])
        index = getattr(waves, "current_wave_index", 0)
        if 0 <= index < len(wave_list):
            wave = wave_list[index]

        active_limit = "-"
        if wave is not None and hasattr(waves, "_current_active_limit"):
            active_limit = waves._current_active_limit(wave)
            if active_limit is None:
                active_limit = "-"

        all_spawned = waves.all_waves_spawned() if hasattr(waves, "all_waves_spawned") else "-"
        current_wave = waves.current_wave_number() if hasattr(waves, "current_wave_number") else "-"
        return {
            "state": getattr(waves, "wave_state", "-"),
            "index": current_wave,
            "total": len(wave_list),
            "left": getattr(waves, "enemies_left_to_spawn", "-"),
            "active_limit": active_limit,
            "all_spawned": all_spawned,
            "timer": getattr(waves, "wave_timer", "-"),
            "label": wave.get("label", "-") if wave is not None else "-",
            "mode": getattr(waves, "wave_mode", "-"),
            "group_id": getattr(waves, "current_group_id", "-"),
            "group_name": getattr(waves, "current_group_name", "-"),
            "group_number": getattr(waves, "current_group_number", "-"),
            "group_total": getattr(waves, "current_group_total", "-"),
            "group_state": getattr(waves, "current_group_state", "-"),
            "group_elapsed": f"{getattr(waves, 'current_group_elapsed', 0.0):.1f}",
            "group_spawned": getattr(waves, "current_group_spawned", "-"),
            "group_living": getattr(waves, "current_group_living", "-"),
            "expected_clear_time": self._format_float(getattr(waves, "current_group_expected_clear_time", "-")),
            "max_time": self._format_float(getattr(waves, "current_group_max_time", "-")),
            "release_reason": getattr(waves, "next_group_release_reason", "-"),
            "nearby_pressure": getattr(waves, "nearby_pressure_count", "-"),
            "saturation_cap": getattr(waves, "current_group_saturation_cap", "-"),
            "hard_cap": getattr(waves, "current_group_hard_cap", "-"),
            "blocked_reason": getattr(waves, "release_blocked_reason", "-"),
            "old_spawn_queue_length": getattr(waves, "old_spawn_queue_length", "-"),
            "legacy_clearing_gate": getattr(waves, "legacy_clearing_gate_active", "-"),
            "stk_estimate": self._room_one_stk_estimate(wave),
            "build_power_influence": f"{getattr(waves, 'build_power_influence', 1.0):.2f}",
        }

    def _format_float(self, value):
        if isinstance(value, (int, float)):
            return f"{value:.1f}"
        return value

    def _room_one_stk_estimate(self, wave):
        if not wave or wave.get("enemy_difficulty_override") is None:
            return "-"
        difficulty = max(1.0, wave.get("enemy_difficulty_override", 1.0))
        base_hp = int(ENEMY_HEALTH * (difficulty ** 1.45))
        chaser_stk = (base_hp + PROJECTILE_DAMAGE - 1) // PROJECTILE_DAMAGE
        ranged_hp = int(base_hp * 0.76)
        ranged_stk = (ranged_hp + PROJECTILE_DAMAGE - 1) // PROJECTILE_DAMAGE
        return f"Chaser {chaser_stk}, Ranged {ranged_stk}"

    def _format_point(self, point):
        if point is None:
            return "-"
        return f"{int(point[0])}, {int(point[1])}"

    def update(self, dt):
        if not DEV_TOOLS_ENABLED:
            return
        if self.author_mode:
            self._update_author_camera(dt)
        if self._focus_target is None:
            return
        rect = self._object_rect(self.selected_object)
        if rect is None:
            self._focus_target = None
            return
        target = pygame.Vector2(rect.centerx - SCREEN_WIDTH / 2, rect.centery - SCREEN_HEIGHT / 2)
        bounds = current_room_bounds()
        target.x = max(bounds.left, min(target.x, bounds.right - SCREEN_WIDTH))
        target.y = max(bounds.top, min(target.y, bounds.bottom - SCREEN_HEIGHT))
        factor = min(1.0, 7.5 * dt)
        self.game.camera.offset += (target - self.game.camera.offset) * factor
        self._focus_target = target
        if self.game.camera.offset.distance_to(target) < 2:
            self.game.camera.offset.update(target)
            self._focus_target = None

    def _update_author_camera(self, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        speed = 1450 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 720
        self.game.camera.offset += direction * speed * dt
        bounds = current_room_bounds()
        self.game.camera.offset.x = max(bounds.left, min(self.game.camera.offset.x, bounds.right - SCREEN_WIDTH))
        self.game.camera.offset.y = max(bounds.top, min(self.game.camera.offset.y, bounds.bottom - SCREEN_HEIGHT))

    def toggle_author_mode(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.author_mode = not self.author_mode
        if self.author_mode and self.authoring is not None:
            self.authoring.active = True
            if not self.authoring.objects:
                self.authoring.refresh_from_runtime()
        self.message = f"author mode {'on' if self.author_mode else 'off'}"
        self.add_event(f"Author Mode: {'on' if self.author_mode else 'off'}")

    def clear_scene_transition_state(self):
        if self.authoring is not None:
            self.authoring.clear_authoring_context()
        room_loader = getattr(self.game, "room_loader", None)
        if room_loader is not None:
            room_loader.clear_preview_state()
        self.selected_object = None
        self.selected_kind = None
        self.search_query = ""
        self.search_results = []
        self._focus_target = None
        self.message = "dev scene context cleared"

    def record_event(self, event_name, data=None):
        if not DEV_TOOLS_ENABLED or self.log_paused:
            return
        label = self._event_label(event_name, data or {})
        self.event_log.append(label)
        if len(self.event_log) > MAX_EVENT_LOG:
            self.event_log = self.event_log[-MAX_EVENT_LOG:]

    def add_event(self, label):
        self.record_event("dev", {"label": label})

    def perk_definitions(self):
        perks = []
        for key in DEV_PERK_ORDER:
            definition = definition_registry.perks.get(key)
            if definition is not None:
                perks.append(definition)
        ordered = {definition["key"] for definition in perks}
        for key, definition in definition_registry.perks.items():
            if key not in ordered:
                perks.append(definition)
        query = self.perk_search_query.strip().lower()
        if self.perk_build_filter != "All":
            perks = [
                definition for definition in perks
                if self.perk_build_filter in definition.get("build_roles", [definition.get("build", "Shared/Utility")])
            ]
        if query:
            perks = [
                definition for definition in perks
                if query in definition.get("key", "").lower()
                or query in definition.get("name", "").lower()
                or query in " ".join(definition.get("tags", [])).lower()
            ]
        if perks:
            self.selected_perk_index %= len(perks)
        else:
            self.selected_perk_index = 0
        return perks

    def selected_perk_definition(self):
        perks = self.perk_definitions()
        if not perks:
            return None
        return perks[self.selected_perk_index]

    def set_perk_search(self, query):
        self.perk_search_query = query
        self.selected_perk_index = 0
        self.message = f"perk search: {query or '-'}"

    def cycle_perk_build_filter(self):
        index = DEV_PERK_GROUPS.index(self.perk_build_filter) if self.perk_build_filter in DEV_PERK_GROUPS else 0
        self.perk_build_filter = DEV_PERK_GROUPS[(index + 1) % len(DEV_PERK_GROUPS)]
        self.selected_perk_index = 0
        self.message = f"perk build filter: {self.perk_build_filter}"
        return self.perk_build_filter

    def select_next_perk(self):
        perks = self.perk_definitions()
        if not perks:
            self.message = "no perks found"
            return None
        self.selected_perk_index = (self.selected_perk_index + 1) % len(perks)
        definition = self.selected_perk_definition()
        self.message = f"selected perk {definition.get('key')}"
        return definition

    def select_previous_perk(self):
        perks = self.perk_definitions()
        if not perks:
            self.message = "no perks found"
            return None
        self.selected_perk_index = (self.selected_perk_index - 1) % len(perks)
        definition = self.selected_perk_definition()
        self.message = f"selected perk {definition.get('key')}"
        return definition

    def select_perk_by_key(self, key):
        self.perk_search_query = ""
        perks = self.perk_definitions()
        for index, definition in enumerate(perks):
            if definition.get("key") == key:
                self.selected_perk_index = index
                self.message = f"selected perk {key}"
                return definition
        self.message = f"missing perk {key}"
        return None

    def selected_perk_lines(self):
        definition = self.selected_perk_definition()
        if definition is None:
            return ["No perks discovered"]
        player = self.game.player
        wounded = sum(1 for enemy in getattr(self.game, "enemies", []) if getattr(enemy, "vampire_wound_stacks", 0) > 0)
        key = definition["key"]
        count = player.perk_counts.get(key, 0)
        limit = getattr(__import__("settings"), "PERK_PICK_LIMIT", 4)
        if count >= limit:
            next_pick = "Status: Maxed"
        elif count >= 3:
            next_pick = "Next Pick: Legendary"
        else:
            next_pick = f"Next Pick: Pick {count + 1}" + (" / Unlock" if count == 0 else "")
        return [
            f"{definition.get('name', key)}",
            f"key: {key}",
            f"desc: {definition.get('desc', '-')}",
            f"legendary: {definition.get('legendary_desc', '-')}",
            f"tags: {', '.join(definition.get('tags', [])) or '-'}",
            f"Build: {definition.get('build', 'Shared/Utility')}",
            f"Current Count: {count}/{limit}",
            next_pick,
            f"Starter: active={'yes' if getattr(player, 'starter_choice_active', False) else 'no'} selected={getattr(player, 'starter_build', '') or '-'} free_used={'yes' if getattr(player, 'starter_free_reroll_used', False) else 'no'} missing={getattr(player, 'starter_missing_build', '') or '-'}",
            f"Rerolls: tokens={getattr(player, 'reroll_tokens', 0)} earned={getattr(player, 'reroll_tokens_earned', 0)} gold_spent={getattr(player, 'reroll_gold_spent', 0)} total={getattr(player, 'total_rerolls_used', 0)}",
            f"Gun: count={getattr(player, 'engineer_gun_count', 0)} cd={getattr(player, 'engineer_helper_cooldown', 0):.2f}/{getattr(player, 'engineer_helper_timer', 0):.2f} burst={getattr(player, 'engineer_gun_burst_count', 1)} speed={getattr(player, 'engineer_helper_projectile_speed', 0)} target={getattr(player, 'engineer_drone_target_id', None) or '-'}",
            f"Blade: count={getattr(player, 'engineer_blade_count', 0)} radius={getattr(player, 'engineer_blade_radius', 0)} speed={getattr(player, 'engineer_blade_orbit_speed', 0):.2f} overdrive={getattr(player, 'engineer_blade_overdrive_timer', 0):.2f}/{getattr(player, 'engineer_blade_overdrive_cooldown_timer', 0):.2f}",
            f"Bomber: count={getattr(player, 'engineer_bomber_count', 0)} state={getattr(player, 'engineer_bomber_state', '-')} timer={getattr(player, 'engineer_bomber_timer', 0):.2f} radius={getattr(player, 'engineer_bomber_radius', 0)} target={getattr(player, 'engineer_bomber_target_id', None) or '-'}",
            f"Airstrike: state={getattr(player, 'engineer_airstrike_state', '-')} cd={getattr(player, 'engineer_airstrike_cooldown_timer', 0):.1f}/{getattr(player, 'engineer_airstrike_cooldown', 0):.1f} radius={getattr(player, 'engineer_airstrike_radius', 0)}",
            f"Overclock: level={getattr(player, 'engineer_overclock_level', 0)} gun_cd={getattr(player, 'engineer_helper_cooldown', 0):.2f} blade_od_cd={getattr(player, 'engineer_blade_overdrive_cooldown', 0):.2f} bomber_cd={getattr(player, 'engineer_bomber_cooldown', 0):.2f}",
            f"Ninja Momentum: {getattr(player, 'ninja_momentum', 0):.2f}/{getattr(player, 'ninja_momentum_max', 0):.2f} refund={getattr(player, 'dash_refund_this_dash', 0):.2f}/{getattr(player, 'dash_refund_cap', 0):.2f}",
            f"Blood: {getattr(player, 'vampire_blood', 0)}/{getattr(player, 'vampire_max_blood', 0)} feast={getattr(player, 'vampire_feast_timer', 0):.1f}s moon={getattr(player, 'vampire_blood_moon_timer', 0):.1f}s",
            f"Wounds/Orbs: wounded={wounded} stacks={getattr(player, 'vampire_wound_max_stacks', 0)} orbs={len(getattr(player, 'vampire_blood_orbs', []))}/{getattr(player, 'vampire_orb_cap', 0)} attract={player.vampire_orb_attraction_radius() if hasattr(player, 'vampire_orb_attraction_radius') else getattr(player, 'vampire_orb_attract_radius', 0)}",
            f"Blood Bat: state={getattr(player, 'vampire_bat_state', '-')} carried={getattr(player, 'vampire_bat_carried_blood', 0)} cd={getattr(player, 'vampire_bat_timer', 0):.2f} target={getattr(player, 'vampire_bat_target_id', None) or '-'}",
            f"Blood Trail: cap={getattr(player, 'vampire_trail_harvest_cap', 0)} dash_hits={getattr(player, 'vampire_trail_harvested_this_dash', 0)} moon_unlocked={'yes' if getattr(player, 'vampire_blood_moon_unlocked', False) else 'no'}",
        ]

    def grant_selected_perk_next_pick(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return None
        definition = self.selected_perk_definition()
        if definition is None:
            self.message = "no selected perk"
            return None
        perk_system = getattr(self.game, "perks", None)
        if perk_system is None:
            self.message = "perk system unavailable"
            return None
        key = definition["key"]
        count = self.game.player.perk_counts.get(key, 0)
        limit = getattr(__import__("settings"), "PERK_PICK_LIMIT", 4)
        if count >= limit:
            self.message = f"{key} maxed"
            return None
        perk = dict(definition)
        try:
            apply_effect, legendary_effect = perk_system.PERK_EFFECTS[key]  # type: ignore[attr-defined]
        except AttributeError:
            from systems.perk_system import PERK_EFFECTS
            apply_effect, legendary_effect = PERK_EFFECTS[key]
        perk["apply"] = apply_effect
        perk["legendary_apply"] = legendary_effect
        if hasattr(perk_system, "_option_for_player"):
            option = perk_system._option_for_player(perk, self.game.player)
        else:
            option = dict(perk)
            option["taken"] = count
            option["limit"] = limit
            option["legendary"] = count >= 3
            if option["legendary"]:
                option["name"] = "Legendary " + perk["name"]
                option["desc"] = perk.get("legendary_desc", perk["desc"])
        previous_options = list(getattr(perk_system, "current_options", []))
        perk_system.current_options = [option]
        applied = perk_system.apply(self.game.player, 0)
        if applied is None:
            perk_system.current_options = previous_options
            self.message = f"failed to grant {key}"
            return None
        self.message = f"granted {applied['name']} {self.game.player.perk_counts.get(key, 0)}/{limit}"
        self.add_event(f"Perk Test Grant: {key} count={self.game.player.perk_counts.get(key, 0)}")
        return applied

    def _event_label(self, event_name, data):
        labels = {
            "player_shoot": "Player Shoot",
            "player_dash": "Player Dash",
            "enemy_hit": "Enemy Hit",
            "enemy_killed": "Enemy Death",
            "perk_available": "Perk Available",
            "room_cleared": "Portal Opened",
            "boss_spawned": "Boss Spawned",
            "boss_phase_changed": "Boss Phase Changed",
            "npc_purchase": "Upgrade Purchased",
            "state_hub": "Room Entered: Hub",
            "state_room": "Room Entered: Room",
            "state_boss": "Room Entered: Boss",
            "run_started": "Run Started",
            "menu_select": "Menu Select",
        }
        if event_name == "dev":
            return data.get("label", "Dev Event")
        return labels.get(event_name, event_name.replace("_", " ").title())

    def clear_log(self):
        self.event_log.clear()
        self.message = "event log cleared"

    def toggle_log_pause(self):
        self.log_paused = not self.log_paused
        self.message = f"log pause {'on' if self.log_paused else 'off'}"

    def toggle_log_auto_scroll(self):
        self.log_auto_scroll = not self.log_auto_scroll
        self.message = f"log auto scroll {'on' if self.log_auto_scroll else 'off'}"

    def select_at_screen_pos(self, screen_pos):
        if not DEV_TOOLS_ENABLED:
            return False
        world_pos = self.game.camera.screen_to_world(screen_pos)
        for kind, obj in self._selection_candidates():
            rect = self._object_rect(obj)
            if rect is not None and rect.collidepoint(round(world_pos.x), round(world_pos.y)):
                self.select_object(kind, obj)
                return True
        self.selected_kind = None
        self.selected_object = None
        self.message = "selection cleared"
        return True

    def select_object(self, kind, obj):
        self.selected_kind = kind
        self.selected_object = obj
        self.message = f"selected {kind}"
        self.add_event(f"Inspector Selected: {kind}")

    def focus_selected(self):
        if self.selected_object is None:
            self.message = "no selection to focus"
            return
        self._focus_target = pygame.Vector2(0, 0)
        self.message = f"focusing {self.selected_kind}"

    def search(self, query):
        self.search_query = query.strip()
        lowered = self.search_query.lower()
        results = []
        if not lowered:
            self.search_results = []
            return []

        for kind, obj in self._selection_candidates(include_projectiles=False):
            label = self._object_label(kind, obj)
            if lowered in kind.lower() or lowered in label.lower():
                results.append((kind, obj, label))
        self.search_results = results[:12]
        return self.search_results

    def select_search_result(self, index=0):
        if 0 <= index < len(self.search_results):
            kind, obj, _label = self.search_results[index]
            self.select_object(kind, obj)
            return True
        return False

    def _selection_candidates(self, include_projectiles=True):
        candidates = [("Player", self.game.player)]
        candidates.extend(("Enemy", enemy) for enemy in self.game.enemies)
        candidates.extend(("NPC", npc) for npc in getattr(self.game, "npcs", []))
        if self.game.state == GameState.HUB:
            candidates.append(("Portal", {"rect": self.game.portal_rect, "type": "hub_portal"}))
        if include_projectiles:
            candidates.extend(("Projectile", projectile) for projectile in self.game.projectiles)
            candidates.extend(("Projectile", bullet) for bullet in self.game.enemy_bullets)
        candidates.extend(("Obstacle", {"rect": rect, "index": index}) for index, rect in enumerate(getattr(self.game, "room_obstacles", [])))
        candidates.append(("Room Exit", {"rect": self.game.room_exit_rect}))
        return candidates

    def _object_rect(self, obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get("rect")
        return getattr(obj, "rect", None)

    def _object_label(self, kind, obj):
        if kind == "Enemy":
            enemy_type = getattr(getattr(obj, "type", None), "name", "ENEMY")
            return f"{enemy_type} #{id(obj)}"
        if kind == "NPC":
            return f"{getattr(obj, 'role', 'npc')} #{id(obj)}"
        if kind == "Portal":
            return "Hub Portal"
        if kind == "Room Exit":
            return "Room Exit"
        if kind == "Obstacle":
            return f"Obstacle {obj.get('index', '-')}"
        return f"{kind} #{id(obj)}"

    def inspector_lines(self):
        obj = self.selected_object
        kind = self.selected_kind
        if obj is None:
            return ["No selection", "Shift+Left Click to inspect", "Press / to search"]
        if kind == "Player":
            return self._inspect_player(obj)
        if kind == "Enemy":
            return self._inspect_enemy(obj)
        if kind == "Projectile":
            return self._inspect_projectile(obj)
        if kind == "Portal":
            return self._inspect_portal(obj)
        if kind == "Room Exit":
            return self._inspect_room_exit(obj)
        if kind == "NPC":
            return self._inspect_npc(obj)
        if kind == "Obstacle":
            return self._inspect_obstacle(obj)
        return [f"Type: {kind}", f"ID: {id(obj)}"]

    def _inspect_player(self, player):
        perks = ", ".join(f"{key}:{value}" for key, value in getattr(player, "perk_counts", {}).items() if value) or "-"
        return [
            f"PLAYER #{id(player)}",
            f"World Position: {player.rect.centerx}, {player.rect.centery}",
            f"Velocity: {int(player.velocity.x)}, {int(player.velocity.y)}",
            f"HP / Max HP: {player.health} / {player.max_health}",
            f"Gold: {player.gold}",
            f"XP: {player.xp} / {player.xp_to_next}",
            f"Level: {player.level}",
            f"Current Weapon: {player.active_weapon.name}",
            f"Current Perks: {perks}",
            f"Movement Speed: {getattr(player, 'speed', '-')}",
            f"Damage Bonus: {getattr(player, 'damage_bonus', '-')}",
            f"Fire Rate: {getattr(player, 'fire_rate_multiplier', '-')}",
            f"Projectile Count: {len(self.game.projectiles)}",
            f"Current State: {self.game.state.name}",
        ]

    def _inspect_enemy(self, enemy):
        enemy_type = getattr(enemy, "type", None)
        definition = definition_registry.enemies.get(enemy_type)
        distance = int(pygame.Vector2(enemy.rect.center).distance_to(self.game.player.rect.center))
        cooldowns = [
            f"attack={getattr(enemy, 'attack_timer', '-')}",
            f"windup={getattr(enemy, 'windup_timer', '-')}",
            f"leap={getattr(enemy, 'leap_timer', '-')}",
        ]
        velocity = getattr(enemy, "leap_velocity", pygame.Vector2(0, 0))
        return [
            f"ENEMY #{id(enemy)}",
            f"Definition ID: {definition.id if definition else '-'}",
            f"Enemy Type: {enemy_type.name if enemy_type else '-'}",
            f"Category: {definition.category if definition else '-'}",
            f"Behavior Type: {definition.behavior_type if definition else '-'}",
            f"Current AI State: {getattr(enemy, 'windup_action', None) or getattr(enemy, 'state', '-')}",
            f"HP / Max HP: {enemy.health} / {enemy.max_health}",
            f"Difficulty Multiplier: {getattr(enemy, 'difficulty', '-')}",
            f"Threat Cost: {definition.threat_cost if definition else '-'}",
            "Target: Player",
            f"Distance To Player: {distance}",
            "Current Cooldowns: " + ", ".join(cooldowns),
            f"Windup Status: {getattr(enemy, 'windup_action', None)} {getattr(enemy, 'windup_timer', 0):.2f}",
            f"Alive: {getattr(enemy, 'alive', '-')}",
            f"World Position: {enemy.rect.centerx}, {enemy.rect.centery}",
            f"Velocity: {int(velocity.x)}, {int(velocity.y)}",
        ]

    def _inspect_projectile(self, projectile):
        direction = getattr(projectile, "direction", pygame.Vector2(0, 0))
        remaining = getattr(projectile, "remaining_distance", "-")
        if remaining == "-" and hasattr(projectile, "remaining_life"):
            remaining = int(projectile.remaining_life * getattr(projectile, "speed", 0))
        return [
            f"PROJECTILE #{id(projectile)}",
            f"Owner: {getattr(projectile, 'owner_id', 'player')}",
            f"Damage: {getattr(projectile, 'damage', '-')}",
            f"Speed: {getattr(projectile, 'speed', '-')}",
            f"Lifetime: {getattr(projectile, 'remaining_life', '-')}",
            f"Direction: {direction.x:.2f}, {direction.y:.2f}",
            f"Remaining Distance: {remaining}",
        ]

    def _inspect_portal(self, portal):
        return [
            "PORTAL",
            f"Portal Type: {portal.get('type', 'hub_portal')}",
            "Locked / Open: open",
            "Target Scene: room",
            f"Activation State: {self.game.state == GameState.HUB}",
        ]

    def _inspect_room_exit(self, room_exit):
        rect = room_exit.get("rect", self.game.room_exit_rect)
        return [
            "ROOM EXIT",
            f"Opened: {self.game.room_exit_open}",
            "Activation Condition: room_exit_open and player interaction",
            f"Current Position: {rect.centerx}, {rect.centery}",
        ]

    def _inspect_npc(self, npc):
        return [
            f"NPC #{id(npc)}",
            f"Role: {getattr(npc, 'role', '-')}",
            f"Definition: {getattr(npc, 'dialogue_id', '-')}",
            f"Interaction State: visits={getattr(npc, 'visit_count', '-')}",
        ]

    def _inspect_obstacle(self, obstacle):
        rect = obstacle.get("rect")
        return [
            f"OBSTACLE {obstacle.get('index', '-')}",
            f"Rect: {rect.x}, {rect.y}, {rect.w}, {rect.h}",
        ]

    def toggle_hitboxes(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.show_hitboxes = not self.show_hitboxes
        self.message = f"hitboxes {'on' if self.show_hitboxes else 'off'}"

    def toggle_spawn_debug(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.show_spawn_debug = not self.show_spawn_debug
        self.message = f"spawn debug {'on' if self.show_spawn_debug else 'off'}"

    def toggle_camera_debug(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.show_camera_debug = not self.show_camera_debug
        self.message = f"camera debug {'on' if self.show_camera_debug else 'off'}"

    def toggle_collision_debug(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.show_collision_debug = not self.show_collision_debug
        self.message = f"collision debug {'on' if self.show_collision_debug else 'off'}"

    def toggle_wave_debug(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.show_wave_debug = not self.show_wave_debug
        self.message = f"wave debug {'on' if self.show_wave_debug else 'off'}"

    def toggle_god_mode(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.god_mode = not self.god_mode
        self.game.player.dev_god_mode = self.god_mode
        self.message = f"god mode {'on' if self.god_mode else 'off'}"

    def toggle_slow_motion(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.slow_motion = not self.slow_motion
        self.message = f"slow motion {'on' if self.slow_motion else 'off'}"

    def spawn_horde_test(self, count):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        horde = self.game.ensure_horde() if hasattr(self.game, "ensure_horde") else getattr(self.game, "horde", None)
        if horde is None:
            self.message = "horde system unavailable"
            return False
        horde.spawn_test(self.game, count, EnemyType.CHASER)
        self.message = f"horde test spawned {count}"
        self.add_event(f"Horde Test: spawn {count}")
        return True

    def clear_horde_test(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        horde = getattr(self.game, "horde", None)
        if horde is None:
            self.message = "horde system unavailable"
            return False
        horde.clear(self.game)
        self.message = "horde test cleared"
        self.add_event("Horde Test: clear")
        return True

    def _horde_lines(self):
        horde = getattr(self.game, "horde", None)
        if horde is None:
            return ["Horde: unavailable"]
        metrics = getattr(horde, "last_metrics", {})
        return [
            f"Horde: {'on' if getattr(horde, 'enabled', False) else 'off'} real={metrics.get('real', 0)} virtual={metrics.get('virtual', 0)} cap={getattr(horde, 'real_cap', 0)}",
            f"Horde LOD: L0={metrics.get('lod0', 0)} L1={metrics.get('lod1', 0)} L2={metrics.get('lod2', 0)} checks={metrics.get('projectile_checks', 0)}",
            f"Horde ms: enemy={metrics.get('enemy_update_ms', 0.0):.2f} combat={metrics.get('combat_collision_ms', 0.0):.2f} draw={metrics.get('draw_ms', 0.0):.2f}",
        ]

    def cycle_selected_enemy(self):
        choices = [
            EnemyType.CHASER,
            EnemyType.CHASER_FAST,
            EnemyType.CHASER_TANK,
            EnemyType.RANGED,
            EnemyType.RANGED_THREE,
            EnemyType.RANGED_FIVE,
            EnemyType.RANGED_RAIN,
            EnemyType.JUMPER,
            EnemyType.JUMPER_FAST,
            EnemyType.JUMPER_HEAVY,
            EnemyType.HUNTER,
            EnemyType.BRUTE,
            EnemyType.ELITE,
        ]
        index = choices.index(self.selected_enemy) if self.selected_enemy in choices else 0
        self.selected_enemy = choices[(index + 1) % len(choices)]
        self.message = f"selected {self.selected_enemy.name}"

    def cycle_selected_enemy_reverse(self):
        choices = self._enemy_lab_choices()
        index = choices.index(self.selected_enemy) if self.selected_enemy in choices else 0
        self.selected_enemy = choices[(index - 1) % len(choices)]
        self.message = f"selected {self.selected_enemy.name}"

    def _enemy_lab_choices(self):
        return [
            enemy_type
            for enemy_type in definition_registry.enemies
            if enemy_type not in (EnemyType.BOSS, EnemyType.LOOT)
        ]

    def spawn_selected_enemy(self):
        return self.spawn_lab_enemy()

    def spawn_lab_enemy(self):
        self.clear_lab_enemies()
        center = self.game.camera.offset + pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        bounds = current_room_bounds()
        x = max(bounds.left, min(bounds.right - 80, round(center.x)))
        y = max(bounds.top, min(bounds.bottom - 80, round(center.y)))
        self.last_spawn_position = (x, y)
        enemy = self.game.enemy_pool.acquire(x, y, self.selected_enemy, 1.0)
        enemy.dev_lab_enemy = True
        self.game.enemies.append(enemy)
        self.select_object("Enemy", enemy)
        self.message = f"lab spawned {self.selected_enemy.name}"
        self.add_event(f"Enemy Lab Spawn: {self.selected_enemy.name}")
        return enemy

    def clear_lab_enemies(self):
        removed = 0
        for enemy in self.game.enemies:
            if getattr(enemy, "dev_lab_enemy", False):
                enemy.alive = False
                removed += 1
        dead_lab = [enemy for enemy in self.game.enemies if getattr(enemy, "dev_lab_enemy", False)]
        if dead_lab:
            self.game.enemy_pool.release_many(dead_lab)
            self.game.enemies = [enemy for enemy in self.game.enemies if not getattr(enemy, "dev_lab_enemy", False)]
        if removed:
            self.message = f"cleared {removed} lab enemies"
            self.add_event(f"Enemy Lab Clear: {removed}")
        return removed

    def select_nearest_enemy(self):
        living = [enemy for enemy in self.game.enemies if getattr(enemy, "alive", True)]
        if not living:
            self.message = "no enemies to select"
            return None
        player_center = pygame.Vector2(self.game.player.rect.center)
        enemy = min(living, key=lambda item: pygame.Vector2(item.rect.center).distance_squared_to(player_center))
        self.select_object("Enemy", enemy)
        return enemy

    def focus_selected_enemy(self):
        if self.selected_kind != "Enemy":
            self.select_nearest_enemy()
        self.focus_selected()

    def enemy_lab_lines(self):
        definition = definition_registry.enemies.get(self.selected_enemy)
        lines = [
            "Enemy Lab",
            f"Selected: {self.selected_enemy.name}",
        ]
        if definition is not None:
            lines.extend([
                f"id: {definition.id}",
                f"display: {definition.display_name}",
                f"category: {definition.category}",
                f"behavior: {definition.behavior_type}",
                f"draw: {definition.draw_profile}",
                f"threat: {definition.threat_cost}",
            ])
        selected = self.selected_object if self.selected_kind == "Enemy" else None
        if selected is not None:
            distance = int(pygame.Vector2(selected.rect.center).distance_to(self.game.player.rect.center))
            lines.extend([
                f"runtime hp: {selected.health}/{selected.max_health}",
                f"speed: {getattr(selected, 'speed', '-')}",
                f"difficulty: {getattr(selected, 'difficulty', '-')}",
                f"ai/windup: {getattr(selected, 'windup_action', None)}",
                f"distance: {distance}",
                f"lab: {getattr(selected, 'dev_lab_enemy', False)}",
            ])
        return lines

    def kill_normal_enemies(self):
        killed = 0
        for enemy in self.game.enemies:
            if getattr(enemy, "type", None) != EnemyType.BOSS:
                enemy.alive = False
                killed += 1
        self.message = f"killed {killed} non-boss enemies"
        self.add_event(f"Enemy Death: {killed} non-boss enemies")

    def open_room_exit(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        if self.game.state != GameState.ROOM:
            self.message = "exit opens only in rooms"
            return False
        if not self.game.room_exit_open:
            self.game.open_room_exit()
        self.message = "room exit opened"
        self.add_event("Portal Opened: room exit")
        return True

    def give_gold(self, amount=250):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.player.add_gold(amount)
        self.message = f"added {amount} gold"
        self.add_event(f"Gold Added: {amount}")
        return True

    def force_level_up(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.player.add_xp(self.game.player.xp_to_next)
        self.message = "forced level up"
        self.add_event("Player XP Added: force level up")
        return True

    def grant_xp(self, amount):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.player.add_xp(amount)
        self.message = f"added {amount} XP"
        self.add_event(f"Player XP Added: {amount}")
        return True

    def heal_player(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.player.heal(9999)
        self.message = "healed player"
        self.add_event("Player Healed")
        return True

    def teleport_player_to_center(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.player.rect.center = current_room_bounds().center
        self.game.camera.reset(self.game.player.rect)
        self.message = "teleported player to center"
        self.add_event("Player Teleported: center")
        return True

    def enter_hub(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        enter_hub(self.game)
        self.message = "entered hub"
        self.add_event("Room Entered: Hub")
        return True

    def enter_normal_room(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        enter_room(self.game)
        self.message = "entered legacy 10-room route"
        self.add_event("Legacy Route Entered: 10-room reference")
        return True

    def enter_prototype_room(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        self.game.prototype_room.enter()
        self.message = "entered prototype small room"
        self.add_event("Room Entered: Prototype Small Room")
        return True

    def enter_boss_room(self):
        if not DEV_TOOLS_ENABLED:
            self.message = "dev tools disabled"
            return False
        enter_boss(self.game)
        self.message = "entered boss room"
        self.add_event("Room Entered: Boss")
        return True

    def draw_debug(self, surface):
        if not DEV_TOOLS_ENABLED:
            return

        game = self.game
        font = pygame.font.SysFont("Consolas", 16)
        if self.show_hitboxes:
            pygame.draw.rect(surface, (80, 220, 255), game.camera.apply_rect(game.player.rect), 2)
            self._draw_label(surface, font, game.player.rect.midtop, "player", (80, 220, 255))
            for enemy in game.enemies:
                color = (255, 80, 80) if getattr(enemy, "type", None) != EnemyType.BOSS else (255, 180, 60)
                pygame.draw.rect(surface, color, game.camera.apply_rect(enemy.rect), 2)
                self._draw_enemy_label(surface, font, enemy, color)

        if self.show_collision_debug:
            pygame.draw.rect(surface, (80, 220, 255), game.camera.apply_rect(game.player.rect), 1)
            for rect in game.collision.get_colliders():
                pygame.draw.rect(surface, (80, 255, 120), game.camera.apply_rect(rect), 2)
            for rect in getattr(game, "room_obstacles", []):
                pygame.draw.rect(surface, (80, 255, 120), game.camera.apply_rect(rect), 2)
            for enemy in game.enemies:
                pygame.draw.rect(surface, (255, 120, 120), game.camera.apply_rect(enemy.rect), 1)
            self._draw_portals_and_exits(surface)

        if self.show_spawn_debug:
            center = game.camera.apply_pos(pygame.Vector2(game.player.rect.center))
            pygame.draw.circle(surface, (80, 180, 255), (round(center.x), round(center.y)), ENEMY_SPAWN_SAFE_RADIUS, 2)
            pygame.draw.circle(surface, (120, 120, 255), (round(center.x), round(center.y)), ENEMY_RESPAWN_SAFE_RADIUS, 1)
            self._draw_label(surface, font, game.player.rect.midbottom, f"spawn safe={ENEMY_SPAWN_SAFE_RADIUS}", (80, 180, 255))
            if self.last_spawn_position is not None:
                spawn_pos = game.camera.apply_pos(pygame.Vector2(self.last_spawn_position))
                pygame.draw.circle(surface, (255, 210, 80), (round(spawn_pos.x), round(spawn_pos.y)), 10, 2)
                self._draw_screen_label(surface, font, (spawn_pos.x + 12, spawn_pos.y - 10), "last spawn", (255, 210, 80))

        if self.show_camera_debug:
            world_view = pygame.Rect(int(game.camera.offset.x), int(game.camera.offset.y), SCREEN_WIDTH, SCREEN_HEIGHT)
            pygame.draw.rect(surface, (255, 255, 80), game.camera.apply_rect(world_view), 2)
            player_screen = game.camera.apply_pos(pygame.Vector2(game.player.rect.center))
            lines = [
                f"camera offset: {int(game.camera.offset.x)}, {int(game.camera.offset.y)}",
                f"world viewport: {world_view.x},{world_view.y} {world_view.w}x{world_view.h}",
                f"player screen: {int(player_screen.x)}, {int(player_screen.y)}",
            ]
            self._draw_overlay_lines(surface, font, lines, 22, SCREEN_HEIGHT - 116, (255, 255, 120))

        if self.show_wave_debug:
            info = self._wave_info()
            lines = [
                f"wave state: {info['state']} label: {info['label']}",
                f"wave index: {info['index']} / {info['total']} left: {info['left']}",
                f"active limit: {info['active_limit']} all spawned: {info['all_spawned']}",
                f"wave timer: {info['timer']:.2f}" if isinstance(info["timer"], (int, float)) else f"wave timer: {info['timer']}",
                f"remaining enemies: {len(game.enemies)}",
            ]
            self._draw_overlay_lines(surface, font, lines, SCREEN_WIDTH - 430, 92, (255, 255, 120))

        self.draw_selection_highlight(surface)

    def draw_selection_highlight(self, surface):
        rect = self._object_rect(self.selected_object)
        if rect is None:
            return
        screen_rect = self.game.camera.apply_rect(rect).inflate(12, 12)
        pygame.draw.rect(surface, (255, 245, 90), screen_rect, 3, border_radius=4)
        pygame.draw.rect(surface, (40, 30, 0), screen_rect.inflate(8, 8), 1, border_radius=6)

    def _draw_portals_and_exits(self, surface):
        game = self.game
        if getattr(game, "room_exit_open", False):
            pygame.draw.rect(surface, (255, 170, 40), game.camera.apply_rect(game.room_exit_rect), 2)

        if game.state == GameState.HUB:
            pygame.draw.rect(surface, (180, 120, 255), game.camera.apply_rect(game.portal_rect), 2)

    def _draw_enemy_label(self, surface, font, enemy, color):
        enemy_type = getattr(getattr(enemy, "type", None), "name", "ENEMY")
        hp = getattr(enemy, "health", getattr(enemy, "hp", "-"))
        max_hp = getattr(enemy, "max_health", getattr(enemy, "max_hp", "-"))
        distance = int(pygame.Vector2(enemy.rect.center).distance_to(self.game.player.rect.center))
        parts = [enemy_type, f"HP {hp}/{max_hp}", f"d={distance}"]
        ai_state = getattr(enemy, "state", None)
        if ai_state is not None:
            parts.append(str(ai_state))
        action = getattr(enemy, "windup_action", None) or getattr(enemy, "current_action", None)
        if action is not None:
            parts.append(f"action={action}")
        self._draw_label(surface, font, enemy.rect.midtop, " | ".join(parts), color)

    def _draw_label(self, surface, font, world_pos, text, color):
        screen_pos = self.game.camera.apply_pos(pygame.Vector2(world_pos))
        self._draw_screen_label(surface, font, (screen_pos.x, screen_pos.y - 18), text, color)

    def _draw_screen_label(self, surface, font, pos, text, color):
        label = font.render(str(text), True, color)
        surface.blit(label, (int(pos[0]), int(pos[1])))

    def _draw_overlay_lines(self, surface, font, lines, x, y, color):
        for line in lines:
            self._draw_screen_label(surface, font, (x, y), line, color)
            y += 18
