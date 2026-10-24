import pygame
import sys
import random
import math
from time import perf_counter
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK,
    ROOMS_TO_BOSS,
    DEBUG_ROOM_FLOW,
    ENEMY_SEPARATION_FORCE,
    ENEMY_PLAYER_PRESSURE_FORCE,
    ENEMY_RESPAWN_SAFE_RADIUS,
    BLAST_RADIUS,
    BLAST_FORCE,
    DEV_TOOLS_ENABLED,
)
from game_state import GameState
from entities.player import Player
from entities.enemy import EnemyType
from systems.camera import Camera
from systems.dialogue_system import DialogueSystem
from systems.combat_system import CombatSystem
from systems.spawn_system import SpawnSystem
from systems.upgrade_system import UpgradeSystem
from systems.perk_system import PerkSystem
from systems.room_system import RoomSystem, RoomType
from systems.effects import EffectsSystem
from systems.audio_system import AudioSystem

from ui.menu import draw_menu
from ui.front_end import layout_menu
from ui.guidance import draw_guidance
from ui.pause import draw_pause_menu
from ui.perk_screen import draw_perk_select
from ui.hud import draw_hud
from ui.shop import draw_shop_hint
from ui.end_screen import draw_end_screen
from ui.room_banner import draw_room_banner
from ui.minimap import draw_minimap
from ui.dev_panel import DevPanel
from ui.authoring_panel import AuthoringPanel
from ui.wave_designer_panel import WaveDesignerPanel
from ui.asset_browser import AssetBrowser

from systems.collision_system import CollisionSystem
from systems.world_utils import (
    nearest_npc,
    draw_world_background,
)
from systems.aim_system import update_player_aim
from systems.shooting_system import ShootingSystem
from systems.boss_attack_system import BossAttackSystem
from systems.scene_system import enter_hub
from systems.event_system import EventSystem
from systems.crosshair_system import CrosshairSystem
from systems.input_system import InputSystem
from systems.wave_system import WaveSystem
from states.combat_state import DASH_HOLD_THRESHOLD
from systems.room_layout import draw_room_obstacles
from systems.object_catalog import draw_object, definition as object_definition, reload_catalog
from systems.enemy_pool import EnemyPool
from systems.combat_action_resolver import CombatActionResolver
from systems.dev_tools import DevTools
from systems.room_authoring import RoomAuthoring
from systems.wave_designer import WaveDesigner
from systems.asset_pipeline import AssetPipeline
from systems.prefab_factory import PrefabFactory
from systems.prefab_registry import PrefabRegistry
from systems.room_loader import RoomLoader
from systems.loot_system import LootSystem
from systems.game_feel import GameFeelSystem
from systems.room_flow import RoomFlowSystem
from systems.xp_budget import award_room_completion_xp
from systems.frame_profiler import FrameProfiler
from systems.music_system import MusicSystem
from systems.room_bounds import current_room_bounds, current_room_rect
from systems.prototype_room import PrototypeCombatRoom
from systems.stage_system import StageSystem
from data.dialogues import DIALOGUES


class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("Blue Cube v0.5")
        self.window = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE
        )
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        self.viewport_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.render_scale = 1.0
        self.configure_viewport(self.window.get_size())
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Arial", 22)
        self.big_font = pygame.font.SysFont("Arial", 48)

        self.menu_title_surf = self.big_font.render("BLUE CUBE v0.5", True, (255, 255, 255))
        self.menu_hint_surf = self.font.render("Click on an option to select", True, (255, 255, 255))

        self.rect_new_run = pygame.Rect(0, 0, 200, 50)
        self.rect_new_run.center = (SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) - 10)

        self.rect_quit = pygame.Rect(0, 0, 200, 50)
        self.rect_quit.center    = (SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 55)
        layout_menu(self)

        self.text_new_run = self.font.render("New Run", True, (0, 255, 0))
        self.text_quit = self.font.render("Quit", True, (255, 0, 0))

        self.state = GameState.MENU
        self.previous_state = GameState.HUB

        self.player = Player()
        self.camera = Camera()
        self.dialogue = DialogueSystem(self.font, DIALOGUES)
        self.combat = CombatSystem()
        self.spawn = SpawnSystem()
        self.upgrades = UpgradeSystem()
        self.perks = PerkSystem()
        self.rooms = RoomSystem()
        self.effects = EffectsSystem()
        self.audio = AudioSystem()
        self.music = MusicSystem()
        self.collision = CollisionSystem()
        self.events = EventSystem()
        self.shooting = ShootingSystem()
        self.combat.projectile_pool = self.shooting.projectile_pool
        self.boss_attacks = BossAttackSystem()
        self.combat_actions = CombatActionResolver()
        self.enemy_pool = EnemyPool()
        self.prefabs = PrefabRegistry(PrefabFactory(self))
        self.crosshair = CrosshairSystem()
        self.room_authoring = RoomAuthoring(self)
        self.room_loader = RoomLoader(self, self.room_authoring)
        self.authoring_panel = AuthoringPanel(self, self.room_authoring, self.room_loader)
        self.wave_designer = WaveDesigner(self)
        self.wave_designer_panel = WaveDesignerPanel(self.wave_designer)
        self.asset_pipeline = AssetPipeline()
        self.asset_browser = AssetBrowser(self.asset_pipeline)
        self.loot = LootSystem()
        self.feel = GameFeelSystem()
        self.room_flow = RoomFlowSystem()
        self.horde = None
        self.prototype_room = PrototypeCombatRoom(self)
        self.stage = StageSystem(self)
        self.movement_pickups = []
        self.profiler = FrameProfiler(enabled=DEV_TOOLS_ENABLED)
        self.dev_tools = DevTools(self, self.room_authoring)
        self.dev_panel = DevPanel(
            self,
            self.dev_tools,
            self.authoring_panel,
            self.wave_designer_panel,
            self.wave_designer,
            self.asset_browser,
        )
        self.perk_card_rects = []
        self.perk_reroll_rects = []

        self.setup_event_listeners()


        self.npcs = []
        bounds = current_room_bounds()
        self.portal_rect = self.prefabs.spawn_prefab("portal_hub", x=bounds.centerx - 45, y=bounds.centery - 170)
        self.enemies = []
        self.projectiles = []
        self.enemy_bullets = []
        self.room_obstacles = []

        self.input = InputSystem()
        self.perk_input_lock = 0.0
        self.pause_sliders = {}

        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.room_completion_xp_awarded = set()
        self.message = ""
        self.wave_notice_text = ""
        self.wave_notice_timer = 0.0
        self._last_exit_debug = None
        self._last_draw_portal_debug = None

        self.waves = WaveSystem()
        self.room_exit_open = False
        self.room_exit_rect = self.prefabs.spawn_prefab("room_exit", x=0, y=0)
        self.room_exit_rect.center = (bounds.centerx, bounds.centery - 180)

        #self.reset_run()


    def setup_event_listeners(self):
        self.events.subscribe("player_shoot", lambda data: self.audio.play("shoot"))
        self.events.subscribe("player_dash", lambda data: self.audio.play("dash"))
        self.events.subscribe("enemy_hit", lambda data: self.audio.play("hit"))
        self.events.subscribe("enemy_killed", lambda data: self.audio.play("enemy_death"))
        self.events.subscribe("perk_available", lambda data: self.audio.play("peckcard"))
        self.events.subscribe("room_cleared", lambda data: self.audio.play("room_clear"))
        self.events.subscribe("boss_spawned", lambda data: self.audio.play("boss_spawn"))
        self.events.subscribe("boss_phase_changed", lambda data: self.audio.play("boss_phase"))
        self.events.subscribe("npc_purchase", lambda data: self.audio.play("upgrade_buy"))


        self.events.subscribe("state_hub", lambda data: self.music.play_music("hub", fade_ms=600))
        self.events.subscribe("state_room", lambda data: self.music.play_music("room", fade_ms=600))
        self.events.subscribe("state_boss", lambda data: self.music.play_music("boss", fade_ms=600))

    def configure_viewport(self, window_size):
        window_w = max(1, int(window_size[0]))
        window_h = max(1, int(window_size[1]))
        self.render_scale = min(window_w / SCREEN_WIDTH, window_h / SCREEN_HEIGHT)
        scaled_w = max(1, int(SCREEN_WIDTH * self.render_scale))
        scaled_h = max(1, int(SCREEN_HEIGHT * self.render_scale))
        self.viewport_rect = pygame.Rect(
            (window_w - scaled_w) // 2,
            (window_h - scaled_h) // 2,
            scaled_w,
            scaled_h,
        )

    def resize_window(self, size):
        width = max(480, int(size[0]))
        height = max(320, int(size[1]))
        self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.configure_viewport((width, height))

    def window_to_game_pos(self, pos):
        if self.render_scale <= 0:
            return (0, 0)

        game_x = (pos[0] - self.viewport_rect.x) / self.render_scale
        game_y = (pos[1] - self.viewport_rect.y) / self.render_scale
        game_x = max(0, min(SCREEN_WIDTH - 1, game_x))
        game_y = max(0, min(SCREEN_HEIGHT - 1, game_y))
        return (round(game_x), round(game_y))

    def game_mouse_pos(self):
        return self.window_to_game_pos(pygame.mouse.get_pos())

    def translate_event(self, event):
        if not hasattr(event, "pos"):
            return event

        data = event.__dict__.copy()
        data["window_pos"] = event.pos
        data["pos"] = self.window_to_game_pos(event.pos)
        return pygame.event.Event(event.type, data)

    def present(self):
        self.window.fill(BLACK)
        if self.viewport_rect.size == (SCREEN_WIDTH, SCREEN_HEIGHT):
            frame = self.screen
        else:
            buffer=getattr(self,'_present_buffer',None)
            if buffer is None or buffer.get_size()!=self.viewport_rect.size:
                buffer=pygame.Surface(self.viewport_rect.size).convert(self.screen)
                self._present_buffer=buffer
            frame = pygame.transform.smoothscale(self.screen, self.viewport_rect.size, buffer)
        self.window.blit(frame, self.viewport_rect)
        pygame.display.flip()

    def reset_run(self):
        self.audio.reset_context()
        reload_catalog()
        from systems.shot_presentation import prepare
        prepare()
        self.player.reset()
        self.shooting.reset()
        self.perks.current_options = []
        self.space_dash_down_time = None
        self.last_space_dash_tap_time = -999.0
        self.upgrades.reset()
        self.loot.reset()
        self.room_flow.reset_run()
        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.room_completion_xp_awarded.clear()
        self.message = ""
        self.effects.reset()
        self.feel.reset()
        self.stage.active = False
        self.stage.completed = False
        if self.horde is not None:
            self.horde.clear(self)
        self.movement_pickups.clear()
        enter_hub(self)
        # Asset preparation is loading time, not elapsed combat simulation time.
        self.clock.tick()
        self.events.emit("run_started")

    def ensure_horde(self):
        if self.horde is None:
            from systems.horde_system import HordeSystem
            self.horde = HordeSystem()
        return self.horde

    def spawn_prefab(self, prefab_id, **overrides):
        return self.prefabs.spawn_prefab(prefab_id, **overrides)

    def open_perk_select_if_needed(self):
        if self.player.pending_level_ups > 0 and self.state in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            self.previous_state = self.state
            if getattr(self.player, "perk_choices_made", 0) == 0:
                options = self.perks.roll_starter_options(self.player)
            else:
                options = self.perks.roll_options(self.player)
            if not options:
                self.player.consume_pending_level_up()
                self.message = "All perk cards are maxed."
                return
            self.state = GameState.PERK_SELECT
            self.events.emit("perk_available")
            self.perk_input_lock = 0.25

    def open_room_exit(self):
        if self.room_exit_open:
            return
        exit_center = pygame.Vector2(self.player.rect.center) + pygame.Vector2(165, 0)
        half_w = self.room_exit_rect.width // 2
        half_h = self.room_exit_rect.height // 2
        bounds = current_room_bounds()
        exit_center.x = max(bounds.left + half_w, min(bounds.right - half_w, exit_center.x))
        exit_center.y = max(bounds.top + half_h, min(bounds.bottom - half_h, exit_center.y))
        self.room_exit_rect.center = (round(exit_center.x), round(exit_center.y))
        self.room_exit_open = True
        clear_time = self.room_flow.mark_room_clear(self.rooms.room_time)
        self.events.emit("room_cleared")
        self.events.emit("room_clear_time", {"room_number": self.room_number, "room_time": clear_time})
        self.audio.play("portal_open")
        self.feel.room_clear()
        room_xp = award_room_completion_xp(self, self.room_exit_rect.center)
        self.effects.ring(self.room_exit_rect.center, radius=170, life=0.9, width=6)
        reward_text = f" +{room_xp} room XP." if room_xp else ""
        self.message = f"Room cleared in {clear_time:.1f}s.{reward_text} Exit portal opened. Press E near it."
        self.show_wave_notice("EXIT PORTAL OPEN")

        if DEBUG_ROOM_FLOW:
            snapshot = (self.room_exit_open, self.room_exit_rect, self.player.rect.center, tuple(self.camera.offset))
            if snapshot != self._last_exit_debug:
                self._last_exit_debug = snapshot
                print("[EXIT OPEN]", self.room_exit_open, self.room_exit_rect, self.player.rect.center, self.camera.offset)

    def complete_boss_encounter(self):
        if self.room_number > ROOMS_TO_BOSS:
            self.state = GameState.WIN
            self.music.stop_music(fade_ms=1200)
        else:
            self.room_number += 1
            self.message = "Boss defeated."
            enter_hub(self)

    def show_wave_notice(self, text):
        self.wave_notice_text = text
        self.wave_notice_timer = 2.0

    def draw_exit_portal(self):
        if not self.room_exit_open:
            return

        screen_center = self.camera.apply_pos(pygame.Vector2(self.room_exit_rect.center))
        cx, cy = round(screen_center.x), round(screen_center.y)
        if draw_object(self.screen, 'portal', (cx, cy), pygame.time.get_ticks()/1000):
            label = self.font.render('[E] EXIT', True, (160, 240, 230))
            self.screen.blit(label, label.get_rect(center=(cx, cy-84)))
            return
        pulse = 6 if (pygame.time.get_ticks() // 180) % 2 == 0 else 0

        pygame.draw.circle(self.screen, (80, 0, 0), (cx, cy), 96 + pulse)
        pygame.draw.circle(self.screen, (255, 70, 0), (cx, cy), 86)
        pygame.draw.circle(self.screen, (255, 165, 0), (cx, cy), 66)
        pygame.draw.circle(self.screen, (255, 235, 80), (cx, cy), 42)
        pygame.draw.circle(self.screen, (120, 0, 0), (cx, cy), 24)
        pygame.draw.circle(self.screen, (255, 245, 180), (cx, cy), 92, 5)
        pygame.draw.circle(self.screen, (255, 40, 0), (cx, cy), 55, 5)

        label = self.big_font.render("EXIT", True, (255, 80, 0))
        shadow = self.big_font.render("EXIT", True, (40, 0, 0))
        label_rect = label.get_rect(center=(cx, cy - 118))
        shadow_rect = shadow.get_rect(center=(label_rect.centerx + 2, label_rect.centery + 2))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(label, label_rect)

        if DEBUG_ROOM_FLOW:
            draw_rect = self.camera.apply_rect(self.room_exit_rect)
            snapshot = (self.room_exit_open, draw_rect)
            if snapshot != self._last_draw_portal_debug:
                self._last_draw_portal_debug = snapshot
                print("[DRAW PORTAL]", self.room_exit_open, draw_rect)

    def draw_wave_notice(self):
        if self.wave_notice_timer <= 0 or not self.wave_notice_text:
            return

        panel = pygame.Surface((500, 78), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 185))
        panel_rect = panel.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(panel, panel_rect)

        notice_font = self.big_font if self.big_font.size(self.wave_notice_text)[0] <= 470 else self.font
        text = notice_font.render(self.wave_notice_text, True, (255, 210, 60))
        text_rect = text.get_rect(center=panel_rect.center)
        self.screen.blit(text, text_rect)

    def update_movement_pickups(self, dt):
        kept = []
        for pickup in getattr(self, "movement_pickups", []):
            if not pickup.get("alive", False):
                if pickup.get('respawn_delay', 0) <= 0:
                    continue
                pickup["respawn_timer"] = max(0.0, pickup.get("respawn_timer", 0.0) - dt)
                if pickup["respawn_timer"] <= 0.0:
                    pickup["rect"] = pickup.get("spawn_rect", pickup["rect"]).copy()
                    pickup["alive"] = True
                kept.append(pickup)
                continue
            if self.player.rect.colliderect(pickup["rect"]):
                if pickup["type"] == "dash_refresh":
                    if hasattr(self.player, "refill_dash_charge"):
                        self.player.refill_dash_charge(object_definition('dash_refresh')['charges'])
                    self.player.dash_cooldown_timer = 0.0
                    self.player.ghost_timer = max(getattr(self.player, "ghost_timer", 0.0), pickup.get("duration", 1.8))
                    self.player.invulnerable_timer = max(getattr(self.player, "invulnerable_timer", 0.0), pickup.get("duration", 1.8))
                    self.effects.collect_pickup('dash_refresh',1,self.player.rect.center)
                    self.audio.play('boost_pickup')
                    self.message = "Movement charge: Dash charge restored, speed boosted, and protected briefly."
                elif pickup['type'] == 'heal_potion':
                    before_heal=self.player.health
                    self.player.heal(pickup['value'])
                    self.effects.collect_pickup('heal_potion',self.player.health-before_heal,self.player.rect.center)
                    self.audio.play('heal_pickup')
                elif pickup['type'] == 'time_stop':
                    self.player.enemy_time_stop_timer = max(self.player.enemy_time_stop_timer, pickup['value'])
                    self.effects.time_stop_trigger(self.player.rect.center, pickup['value'])
                    self.effects.collect_pickup('time_stop',pickup['value'],self.player.rect.center)
                    self.audio.play('time_stop_pickup')
                pickup["alive"] = False
                pickup["respawn_timer"] = pickup.get("respawn_delay", 12.0)
                kept.append(pickup)
                continue
            kept.append(pickup)
        self.movement_pickups = kept

    def draw_movement_pickups(self):
        for pickup in getattr(self, "movement_pickups", []):
            if not pickup.get("alive", False):
                remaining = pickup.get("respawn_timer", 0.0)
                if remaining > 3.0:
                    continue
                base_rect = self.camera.apply_rect(pickup.get("spawn_rect", pickup["rect"]))
                progress = max(0.0, min(1.0, 1.0 - remaining / 3.0))
                radius = max(5, round(20 * progress))
                alpha = round(55 + 165 * progress)
                glow = pygame.Surface((72, 72), pygame.SRCALPHA)
                pygame.draw.circle(glow, (80, 220, 255, alpha), (36, 36), radius, max(2, round(4 * progress)))
                pygame.draw.circle(glow, (230, 255, 255, max(30, alpha - 30)), (36, 36), max(3, radius // 2), 2)
                self.screen.blit(glow, (base_rect.centerx - 36, base_rect.centery - 36))
                continue
            rect = self.camera.apply_rect(pickup["rect"])
            if draw_object(self.screen, pickup['type'], rect.center, pygame.time.get_ticks()/1000):
                continue
            pulse = 1.0 + 0.16 * abs(math.sin(pygame.time.get_ticks() * 0.012))
            pygame.draw.circle(self.screen, (80, 220, 255), rect.center, round(21 * pulse), 3)
            pygame.draw.circle(self.screen, (80, 220, 255), rect.center, 18)
            pygame.draw.circle(self.screen, (230, 255, 255), rect.center, 10)
            pygame.draw.circle(self.screen, (20, 80, 120), rect.center, 20, 3)

    def draw_player_ghost_aura(self):
        if getattr(self.player, "ghost_timer", 0.0) <= 0:
            return
        center = self.camera.apply_pos(pygame.Vector2(self.player.rect.center))
        pulse = 1.0 + 0.18 * abs(math.sin(pygame.time.get_ticks() * 0.018))
        radius = round(42 * pulse)
        pygame.draw.circle(self.screen, (80, 220, 255), (round(center.x), round(center.y)), radius, 4)
        pygame.draw.circle(self.screen, (210, 255, 255), (round(center.x), round(center.y)), radius + 9, 2)

    def resolve_enemy_crowding(self):
        enemies = [
            e for e in self.enemies
            if e.alive and getattr(e, "type", None).name != "BOSS"
        ]

        if len(enemies) <= 1:
            return

        cell_size = 90
        grid = {}

        for enemy in enemies:
            cell = (
                enemy.rect.centerx // cell_size,
                enemy.rect.centery // cell_size,
            )
            grid.setdefault(cell, []).append(enemy)

        checked_pairs = set()

        for enemy in enemies:
            cx = enemy.rect.centerx // cell_size
            cy = enemy.rect.centery // cell_size

            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    neighbor_cell = (cx + ox, cy + oy)

                    for other in grid.get(neighbor_cell, []):
                        if enemy is other:
                            continue

                        pair_id = tuple(sorted((id(enemy), id(other))))
                        if pair_id in checked_pairs:
                            continue
                        checked_pairs.add(pair_id)

                        dx = other.rect.centerx - enemy.rect.centerx
                        dy = other.rect.centery - enemy.rect.centery

                        min_dist = (enemy.rect.width + other.rect.width) * 0.48
                        dist_sq = dx * dx + dy * dy

                        if dist_sq == 0:
                            dx, dy = 1, 0
                            dist_sq = 1

                        if dist_sq >= min_dist * min_dist:
                            continue

                        dist = dist_sq ** 0.5
                        nx, ny = dx / dist, dy / dist

                        overlap = (min_dist - dist) * ENEMY_SEPARATION_FORCE

                        push_x = round(nx * overlap * 0.5)
                        push_y = round(ny * overlap * 0.5)

                        if push_x == 0 and push_y == 0:
                            push_x = 1 if nx >= 0 else -1

                        enemy.rect.x -= push_x
                        enemy.rect.y -= push_y
                        other.rect.x += push_x
                        other.rect.y += push_y

        player_center = pygame.Vector2(self.player.rect.center)

        for enemy in enemies:
            to_enemy = pygame.Vector2(enemy.rect.center) - player_center
            dist = to_enemy.length()

            if 1 <= dist < 42:
                push = (
                    to_enemy.normalize()
                    * ENEMY_PLAYER_PRESSURE_FORCE
                    * (42 - dist)
                    * 0.35
                )
                enemy.rect.x += round(push.x)
                enemy.rect.y += round(push.y)

            enemy.rect.clamp_ip(current_room_rect())

    def respawn_distant_enemies(self):
        if self.state not in (GameState.ROOM, GameState.BOSS):
            return

        player_pos = pygame.Vector2(self.player.rect.center)
        screen_margin = 900
        lost_enemy_distance = 1800
        screen_rect = pygame.Rect(
            -screen_margin,
            -screen_margin,
            SCREEN_WIDTH + screen_margin * 2,
            SCREEN_HEIGHT + screen_margin * 2,
        )

        for enemy in self.enemies:
            enemy_type = getattr(enemy, "type", None)
            type_name = enemy_type.name if enemy_type is not None else ""
            if type_name == "BOSS" or getattr(enemy,'is_boss_eye',False) or not enemy.alive:
                continue

            enemy_pos = pygame.Vector2(enemy.rect.center)
            screen_pos = self.camera.apply_pos(enemy_pos)

            if screen_rect.collidepoint(round(screen_pos.x), round(screen_pos.y)):
                continue

            distance = enemy_pos.distance_to(player_pos)
            if type_name.startswith("RANGED") or type_name in ("HUNTER", "ELITE"):
                min_distance = max(lost_enemy_distance, ENEMY_RESPAWN_SAFE_RADIUS + 260)
            else:
                min_distance = lost_enemy_distance

            if distance < min_distance:
                continue

            new_x, new_y = self.spawn.get_spawn_position(self.camera, self.player.rect)
            enemy.rect.topleft = (round(new_x), round(new_y))
            enemy.last_player_center = None
            enemy.leap_timer = 0.0
            enemy.windup_timer = 0.0


    def apply_player_skill(self, skill):
        dash_variant = getattr(self.player, "dash_variant", "normal")
        radius = 82 if skill != "blast" else BLAST_RADIUS
        if skill == "dash" and dash_variant == "super":
            radius = 128
        self.effects.ring(self.player.rect.center, radius=radius, life=0.34 if dash_variant == "super" else 0.28, width=9 if dash_variant == "super" else 8 if skill == "blast" else 4)
        if skill == "dash" and dash_variant == "super":
            self.effects.super_dash_burst(self.player.rect.center)
            self.feel.shake(0.22, 7.0)
            self.audio.play("dash")
        if skill == "blast":
            center = pygame.Vector2(self.player.rect.center)
            for enemy in self.enemies:
                if not enemy.alive or getattr(enemy, "type", None) == EnemyType.BOSS:
                    continue
                offset = pygame.Vector2(enemy.rect.center) - center
                dist = offset.length()
                if 1 <= dist <= BLAST_RADIUS:
                    push = offset.normalize() * (BLAST_FORCE * (1.0 - dist / (BLAST_RADIUS * 1.25)))
                    enemy.rect.x += round(push.x)
                    enemy.rect.y += round(push.y)
                    enemy.rect.clamp_ip(current_room_rect())
            self.message = "Blast skill pushed nearby enemies."
        elif skill == "surge":
            self.message = "Surge active: damage and fire rate boosted."
        elif skill == "ghost":
            self.message = "Ghost active: fast and invulnerable."
        elif skill == "dash" and dash_variant == "super":
            self.message = "Super Dash."
        elif skill == "dash" and dash_variant == "chain":
            self.message = "Chain Dash."
        else:
            self.message = "Dash."

    def enemy_reward_values(self, enemy, reward_multiplier=None):
        from systems.combat_system import (
            ENEMY_XP_REWARD,
            ENEMY_GOLD_REWARD,
            LOOT_HIT_GOLD_REWARD,
            LOOT_HIT_XP_REWARD,
            LOOT_ESCAPE_KILL_BONUS_MULTIPLIER,
        )

        if reward_multiplier is None:
            reward_multiplier = self.rooms.reward_multiplier if self.state == GameState.ROOM else 1

        if getattr(enemy, "type", None) == EnemyType.LOOT:
            return (
                LOOT_HIT_GOLD_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER,
                LOOT_HIT_XP_REWARD * LOOT_ESCAPE_KILL_BONUS_MULTIPLIER,
            )

        gold = ENEMY_GOLD_REWARD * reward_multiplier
        xp = ENEMY_XP_REWARD * reward_multiplier
        if getattr(enemy, "type", None) == EnemyType.ELITE:
            gold *= 6
            xp *= 5
        return gold, xp

    def spawn_enemy_reward_drops(self, enemy):
        if getattr(enemy, "type", None) == EnemyType.BOSS:
            return
        gold, xp = self.enemy_reward_values(enemy)
        self.loot.spawn_enemy_rewards(enemy.rect.center, gold, xp, getattr(enemy, "type", None))

    def apply_melee_attack(self, attack):
        origin = pygame.Vector2(attack["origin"])
        direction = attack["direction"]

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)

        direction = direction.normalize()

        damage = attack["damage"]
        attack_range = attack["range"]
        arc = attack.get("arc_degrees", 0) / 2
        knockback = attack["knockback"]
        kills = 0

        if self.player:
            if attack["type"] == "melee_rect":
                self.player.trigger_sword_attack()
            else:
                self.player.trigger_knife_attack()

        for enemy in self.enemies:
            if not enemy.alive:
                continue

            if attack["type"] == "melee_rect":
                if not self._enemy_in_melee_rect(enemy, origin, direction, attack):
                    continue
            elif not self._enemy_in_melee_arc(enemy, origin, direction, attack_range, arc):
                continue

            killed = enemy.take_damage(damage)
            if self.feel:
                self.feel.normal_hit()

            enemy.rect.x += round(direction.x * knockback)
            enemy.rect.y += round(direction.y * knockback)
            enemy.rect.clamp_ip(current_room_rect())

            if self.effects:
                self.effects.damage_number(damage, enemy.rect.midtop, critical=False)
                self.effects.ring(enemy.rect.center, radius=34, life=0.16, width=2)

            if self.audio:
                self.audio.play("hit")

            if killed:
                kills += 1
                self.spawn_enemy_reward_drops(enemy)
                if getattr(enemy, "type", None) == EnemyType.ELITE:
                    self.feel.elite_kill()
                else:
                    self.feel.enemy_kill()
                owner_id = id(enemy)
                for bullet in self.enemy_bullets:
                    if getattr(bullet, "owner_id", None) == owner_id:
                        bullet.kill()
                if self.audio:
                    self.audio.play("enemy_death")

        if kills:
            self.room_kills += kills
            self.total_kills += kills

    def _enemy_in_melee_arc(self, enemy, origin, direction, attack_range, arc):
        to_enemy = pygame.Vector2(enemy.rect.center) - origin
        distance = to_enemy.length()

        if distance <= 0:
            return False

        if distance > attack_range + max(enemy.rect.width, enemy.rect.height) / 2:
            return False

        enemy_dir = to_enemy.normalize()
        angle = direction.angle_to(enemy_dir)
        return abs(angle) <= arc

    def _enemy_in_melee_rect(self, enemy, origin, direction, attack):
        to_enemy = pygame.Vector2(enemy.rect.center) - origin
        forward = to_enemy.dot(direction)
        radius = max(enemy.rect.width, enemy.rect.height) / 2
        length = attack.get("length") or attack.get("range") or 0
        width = attack.get("width") or 0

        if forward < -radius or forward > length + radius:
            return False

        side = pygame.Vector2(-direction.y, direction.x)
        lateral = abs(to_enemy.dot(side))
        return lateral <= (width / 2) + radius

    def update_treasure_room(self):
        if self.state != GameState.ROOM or self.rooms.room_type != RoomType.TREASURE:
            return
        if self.room_exit_open:
            return
        if self.rooms.room_time < 15.0:
            return
        escaped = False
        for enemy in self.enemies:
            if getattr(enemy, "type", None) == EnemyType.LOOT and enemy.alive:
                enemy.alive = False
                escaped = True
        if escaped:
            self.enemies = [enemy for enemy in self.enemies if enemy.alive]
            self.shooting.projectile_pool.reset()
            self.projectiles.clear()
            self.enemy_bullets.clear()
            self.message = "Loot Beasts escaped. Exit portal opened."
            self.open_room_exit()

    def update(self, dt):
        self.audio.update_context(self.player,self.state.name,dt)
        with self.profiler.section("game update"):
            if self.perk_input_lock > 0:
                self.perk_input_lock = max(0, self.perk_input_lock - dt)

            if self.wave_notice_timer > 0:
                self.wave_notice_timer = max(0, self.wave_notice_timer - dt)
                if self.wave_notice_timer == 0:
                    self.wave_notice_text = ""

            if self.state not in (GameState.HUB, GameState.ROOM, GameState.BOSS):
                if self.state == GameState.PERK_SELECT:
                    self.effects.update(dt)
                return

            self.room_flow.update_run_timer(dt)
            if self.state == GameState.HUB:
                for npc in self.npcs:
                    npc.update(dt)

            self.shooting.update(dt)
            self.player.handle_movement_input()
            update_player_aim(self.player, self.enemies, self.camera, self.game_mouse_pos())

            with self.profiler.section("player update"):
                # ─── [تحسين 1] جلب العقبات القريبة من اللاعب فقط بدلاً من فحص الغرفة كاملة ───
                nearby_player_colliders = self.collision.get_nearby_colliders(self.player.rect)
                self.player.update(dt, nearby_player_colliders)
                self.player.ninja_dash_solids = self.collision.get_colliders()

                if getattr(self.player, "dash_bounce_effect_pending", False):
                    self.player.dash_bounce_effect_pending = False
                    self.effects.ring(self.player.rect.center, color=(120, 235, 255), radius=58, life=0.18, width=3)
                    self.feel.shake(0.08, 2.5)

            self.player.visual_charge=0.
            if pygame.mouse.get_pressed()[0] and not (self.state == GameState.HUB and self.dialogue.active):
                attack = self.player.try_weapon_attack()

                if attack is None:
                    pass
                elif attack["type"] == "projectile":
                    did_shoot = self.shooting.try_shoot(self.player, self.projectiles)
                    if did_shoot:
                        self.events.emit("player_shoot", {"player": self.player})

                elif attack["type"] == "melee_arc":
                    self.apply_melee_attack(attack)
                elif attack["type"] == "melee_rect":
                    self.apply_melee_attack(attack)
                if self.player.active_weapon_key=='pistol' and self.player.tea_state is None and self.player.dash_timer<=0:
                    interval=self.shooting.last_fire_interval or .45
                    self.player.visual_charge=max(0.,min(1.,1-self.shooting.shoot_timer/interval))

            if self.state == GameState.ROOM:
                if self.prototype_room.active:
                    self.prototype_room.update(dt)
                else:
                    room_dt, countdown_finished = self.room_flow.advance_countdown(dt)
                    if countdown_finished:
                        self.show_wave_notice("GO")

                    if self.room_flow.room_can_advance():
                        self.rooms.update(room_dt)
                        spawned_enemies = self.waves.update(
                            room_dt,
                            lambda: self.spawn.get_spawn_position(self.camera, self.player.rect),
                            len(self.enemies),
                            self.enemy_pool.acquire,
                            living_enemies=self.enemies,
                            player_rect=self.player.rect,
                        )
                        if spawned_enemies:
                            self.enemies.extend(spawned_enemies)
                        wave_message = self.waves.consume_wave_message()
                        if wave_message:
                            self.show_wave_notice(wave_message)
                            if "cleared" in wave_message.lower():
                                self.audio.play("wave_clear")
                            else:
                                self.audio.play("wave_start")
                        self.update_treasure_room()

            self.respawn_distant_enemies()

            enemies_time_stopped = getattr(self.player, "enemy_time_stop_timer", 0.0) > 0
            with self.profiler.section("enemy update"):
                if enemies_time_stopped:
                    pass
                elif self.horde is not None and getattr(self.horde, "enabled", False):
                    self.horde.update_enemies(self, dt, self.combat_actions.handle)
                else:
                    for enemy in self.enemies:
                        previous_phase = getattr(enemy, "phase", None) if getattr(enemy, "type", None) == EnemyType.BOSS else None

                        # ─── [تحسين 2] جلب العقبات القريبة من هذا العدو بالتحديد ───
                        nearby_enemy_colliders = self.collision.get_nearby_colliders(enemy.rect)
                        action = enemy.update(dt, self.player.rect, nearby_enemy_colliders)

                        current_phase = getattr(enemy, "phase", None) if getattr(enemy, "type", None) == EnemyType.BOSS else None
                        if previous_phase is not None and current_phase is not None and current_phase != previous_phase:
                            self.events.emit("boss_phase_changed", {"enemy": enemy, "phase": current_phase})
                            self.feel.boss_phase()
                        if not action:
                            continue
                        self.combat_actions.handle(action, self)

                self.resolve_enemy_crowding()

            # ─── [تحسين 3] تحديث رصاص اللاعب وتصادمه الذكي مع أقرب جدار له ───
            for p in self.projectiles:
                p.update(dt)
                if p.alive:
                    nearby_projectile_colliders = self.collision.get_nearby_colliders(p.rect)
                    if any(p.rect.colliderect(solid) for solid in nearby_projectile_colliders):
                        p.kill()
                        self.effects.projectile_hit(p,p.pos)
                        if self.effects:
                            self.effects.ring(p.rect.center, color=(255, 230, 120), radius=18, life=0.12, width=2)

            # ─── [تحسين 4] تحديث رصاص الأعداء وتصادمه الذكي مع أقرب جدار له ───
            if not enemies_time_stopped:
                for b in self.enemy_bullets:
                    b.update(dt)
                    if b.alive:
                        nearby_bullet_colliders = self.collision.get_nearby_colliders(b.rect)
                        if any(b.rect.colliderect(solid) for solid in nearby_bullet_colliders):
                            b.kill()
                            if getattr(b,'can_damage',True):
                                self.effects.projectile_hit(b,b.pos)

            reward_multiplier = self.rooms.reward_multiplier if self.state == GameState.ROOM else 1
            spatial_grid = self.horde.rebuild_spatial_grid(self.enemies) if self.horde is not None and getattr(self.horde, "enabled", False) else None
            combat_start = perf_counter()
            kills, boss_killed = self.combat.update(
                dt,
                self.player,
                self.projectiles,
                self.enemies,
                self.enemy_bullets,
                effects=self.effects,
                audio=self.audio,
                reward_multiplier=reward_multiplier,
                enemy_factory=self.enemy_pool.acquire,
                loot_system=self.loot,
                feel=self.feel,
                spatial_grid=spatial_grid,
            )
            if self.horde is not None and getattr(self.horde, "enabled", False):
                self.horde.set_combat_ms((perf_counter() - combat_start) * 1000.0)
                self.horde.update_debug_metrics(self)

            if kills:
                self.room_kills += kills
                self.total_kills += kills

            # ─── [تحسين 5] إرجاع رصاص اللاعب الميت إلى الـ Pool بنجاح ودون إزاحة للمسافات ───
            dead_projectiles = [p for p in self.projectiles if not p.alive]
            for p in dead_projectiles:
                self.shooting.projectile_pool.release(p)
            self.projectiles = [p for p in self.projectiles if p.alive]

            self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

            dead_enemies = [e for e in self.enemies if not e.alive]
            self.enemy_pool.release_many(dead_enemies)
            self.enemies = [e for e in self.enemies if e.alive]

            with self.profiler.section("pickups update"):
                self.loot.update(dt, self.player, effects=self.effects, audio=self.audio)
                self.update_movement_pickups(dt)
            self.effects.update(dt)
            self.camera.follow(self.player.rect, self.player.velocity, dt)

            if self.player.is_dead():
                self.state = GameState.GAME_OVER
                self.music.stop_music(fade_ms=900)
                return

            if (
                self.state == GameState.ROOM
                and not self.room_exit_open
                and not self.prototype_room.active
                and self.waves.all_waves_spawned()
                and len(self.enemies) == 0
            ):
                self.open_room_exit()
                return

            if self.prototype_room.ready_to_clear():
                self.prototype_room.open_exit()
                return

            if self.state == GameState.BOSS and boss_killed:
                self.audio.play("boss_death")
                self.complete_boss_encounter()
                return

            self.open_perk_select_if_needed()

    def draw(self):
        draw_start = perf_counter()
        with self.profiler.section("draw total"):
            self.camera.render_offset = self.feel.shake_offset

            if self.state == GameState.MENU:
                draw_menu(self.screen, self)

            elif self.state == GameState.PERK_SELECT:
                self.perk_card_rects, self.perk_reroll_rects = draw_perk_select(
                    self.screen,
                    self.big_font,
                    self.font,
                    self.perks.current_options,
                    self.game_mouse_pos(),
                    self.perks.reroll_labels(self.player),
                    self.player,
                )

            elif self.state in (GameState.HUB, GameState.ROOM, GameState.BOSS):
                with self.profiler.section("world draw"):
                    draw_world_background(self.screen, self.camera, hub=self.state == GameState.HUB, room_type=self.rooms.room_type, profiler=self.profiler)

                    if getattr(self, "room_obstacles", None):
                        with self.profiler.section("props/environment draw"):
                            draw_room_obstacles(self.screen, self.camera, self.room_obstacles)
                    self.draw_movement_pickups()

                    if self.state == GameState.HUB:
                        with self.profiler.section("hub portal draw"):
                            draw_object(self.screen, 'portal', self.camera.apply_rect(self.portal_rect).center, pygame.time.get_ticks()/1000)
                        with self.profiler.section("npc draw"):
                            for npc in self.npcs:
                                npc.draw(self.screen, self.camera)

                with self.profiler.section("enemy draw"):
                    if self.state == GameState.ROOM:
                        self.prototype_room.draw_telegraphs(self.screen, self.camera, self.font)
                    for enemy in self.enemies:
                        enemy.draw(self.screen, self.camera)
                with self.profiler.section("projectile draw"):
                    for p in self.projectiles:
                        p.draw(self.screen, self.camera)
                    for b in self.enemy_bullets:
                        b.draw(self.screen, self.camera)

                with self.profiler.section("pickups draw"):
                    self.loot.draw(self.screen, self.camera)
                with self.profiler.section("player draw"):
                    if self.state in (GameState.ROOM, GameState.BOSS):
                        held = 0.0
                        if pygame.key.get_pressed()[pygame.K_SPACE]:
                            down_time = getattr(self, "space_dash_down_time", None)
                            if down_time is not None and getattr(self.player, "dash_charges", 0) >= 3:
                                held = max(0.0, pygame.time.get_ticks() / 1000.0 - down_time)
                        if held > 0:
                            self.effects.draw_dash_charge(self.screen, self.camera, self.player.rect.center, held / DASH_HOLD_THRESHOLD)
                    self.draw_player_ghost_aura()
                    self.player.draw(self.screen, self.camera)
                with self.profiler.section("effects draw"):
                    self.effects.draw(self.screen, self.camera, self.font)
                if self.state == GameState.ROOM:
                    with self.profiler.section("portal draw"):
                        self.prototype_room.draw_stage_doors(self.screen, self.camera, self.font)
                        self.draw_exit_portal()

                with self.profiler.section("ui draw"):
                    trial_boss=next((enemy for enemy in self.enemies if enemy.alive and getattr(enemy,'encounter',None)),None)
                    if trial_boss is not None:
                        from systems.boss_encounter import draw_hud as draw_trial_hud
                        draw_trial_hud(self.screen,self.font,trial_boss)
                    room_target = self.rooms.target_kills
                    objective_label = "Kills"
                    stage_boss = bool(getattr(getattr(self.stage, "current_room", None), "boss", False))
                    boss = next((enemy for enemy in self.enemies if enemy.type == EnemyType.BOSS and enemy.alive), None)
                    if boss is not None and (self.state == GameState.BOSS or stage_boss):
                        room_target = boss.max_health
                        shown_kills = boss.health
                        objective_label = "Boss HP"
                    elif self.rooms.room_type == RoomType.SURVIVAL:
                        room_target = self.rooms.target_kills
                        shown_kills = self.room_kills
                        objective_label = "Horde"
                    elif self.rooms.room_type == RoomType.TREASURE:
                        room_target = 1
                        shown_kills = 1
                        objective_label = "Reward"
                    else:
                        shown_kills = self.room_kills

                    stage = getattr(self, "stage", None)
                    room_total = len(stage.rooms) if stage else ROOMS_TO_BOSS
                    hud_room_number = self.room_number
                    if getattr(stage, "active", False) and stage.current_room:
                        hud_room_number = stage.current_room.index
                    elif self.state == GameState.HUB and stage:
                        hud_room_number = 0 if not getattr(stage, "completed", False) else room_total
                    draw_hud(
                        self.screen,
                        self.font,
                        self.player,
                        min(hud_room_number, room_total),
                        shown_kills,
                        room_target,
                        len(self.enemies),
                        "BOSS" if stage_boss else self.state.name,
                        self.rooms.display_name() if self.state == GameState.ROOM else "",
                        self.rooms.room_time,
                        objective_label,
                        self.room_flow.run_time,
                        room_total,
                    )
                    if self.state == GameState.ROOM and self.wave_notice_timer <= 0:
                        draw_room_banner(self.screen, self.big_font, self.font, self.rooms)
                    draw_minimap(self.screen, self.player, self.enemies, getattr(self, "room_obstacles", []), stage=stage)

                    if self.state == GameState.HUB:
                        from ui.hub import draw as draw_hub
                        draw_hub(self.screen, self)

                    if self.message and pygame.key.get_pressed()[pygame.K_TAB]:
                        txt = self.font.render(self.message, True, BLACK)
                        self.screen.blit(txt, (22, SCREEN_HEIGHT - 34))

                    draw_guidance(self.screen, self)
                    self.dialogue.draw(self.screen)
                    if self.state == GameState.ROOM:
                        self.draw_wave_notice()
                        self.draw_room_countdown()

                with self.profiler.section("devtools draw"):
                    self.dev_panel.draw(self.screen)

            elif self.state == GameState.PAUSED:
                draw_world_background(
                    self.screen,
                    self.camera,
                    hub=self.previous_state == GameState.HUB,
                    room_type=self.rooms.room_type,
                )
                self.player.draw(self.screen, self.camera)
                self.pause_sliders = draw_pause_menu(self.screen, self.big_font, self.font)
                self.dev_panel.draw(self.screen)

            elif self.state == GameState.GAME_OVER:
                draw_end_screen(self.screen, self.big_font, self.font, "GAME OVER", f"Rooms reached: {self.room_number} | Total kills: {self.total_kills}")

            elif self.state == GameState.WIN:
                draw_end_screen(self.screen, self.big_font, self.font, "BOSS DEFEATED", f"Level {self.player.level} | Gold {self.player.gold} | Kills {self.total_kills}")

            if self.state != GameState.MENU:
                self.crosshair.draw(self.screen, self.game_mouse_pos())
            if self.state == GameState.MENU:
                self.dev_panel.draw(self.screen)
        with self.profiler.section("present"):
            self.present()
        if self.horde is not None and getattr(self.horde, "enabled", False):
            self.horde.set_draw_ms((perf_counter() - draw_start) * 1000.0)
        self.camera.render_offset.update(0, 0)

    def draw_room_countdown(self):
        label = self.room_flow.countdown_label()
        if not label:
            return
        text = self.big_font.render(label, True, (255, 235, 120))
        shadow = self.big_font.render(label, True, (20, 20, 30))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(shadow, (rect.x + 3, rect.y + 3))
        self.screen.blit(text, rect)

    def run_frame(self, dt):
        """One shared frame for desktop and the private browser test harness."""
        self.profiler.begin_frame()
        pygame.mouse.set_visible(self.state == GameState.MENU)
        with self.profiler.section("input/events"):
            self.input.handle_events(self)
        with self.profiler.section("feel/audio triggers"):
            self.feel.update(dt)
        gameplay_dt = dt * self.dev_tools.time_scale
        if not self.dev_tools.author_mode and not self.feel.gameplay_paused():
            self.update(gameplay_dt)
        if DEV_TOOLS_ENABLED:
            with self.profiler.section("wave designer update"):
                self.wave_designer.update()
            with self.profiler.section("devtools update"):
                self.dev_tools.update(gameplay_dt)
        self.draw()
        self.profiler.end_frame(
            state=self.state.name,
            enemies=len(self.enemies),
            projectiles=len(self.projectiles) + len(self.enemy_bullets),
            pickups=len(getattr(self.loot, "pickups", [])),
            effects=sum(len(getattr(self.effects,key,[])) for key in
                        ('floating_texts','rings','slashes','sprite_effects','shot_effects','collection_effects')),
        )

    def run(self):
        while True:
            self.run_frame(self.clock.tick(FPS) / 1000.0)

    def quit(self):
        pygame.quit()
        sys.exit()
