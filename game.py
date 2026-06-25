import pygame
import sys
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FPS, BLACK,
    ROOMS_TO_BOSS,
    ENEMY_BULLET_DAMAGE,
    DEBUG_ROOM_FLOW,
    ENEMY_SEPARATION_FORCE,
    ENEMY_PLAYER_PRESSURE_FORCE,
)
from game_state import GameState
from entities.player import Player
from entities.enemy import EnemyType
from entities.enemy_bullet import EnemyBullet
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
from ui.pause import draw_pause_menu
from ui.perk_screen import draw_perk_select
from ui.hud import draw_hud
from ui.shop import draw_shop_hint
from ui.end_screen import draw_end_screen
from ui.room_banner import draw_room_banner

from systems.collision_system import CollisionSystem
from systems.world_utils import (
    rotate_vector,
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
from data.dialogues import DIALOGUES


class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("Blue Cube v5")
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

        self.menu_title_surf = self.big_font.render("BLUE CUBE v5", True, (255, 255, 255))
        self.menu_hint_surf = self.font.render("Click on an option to select", True, (255, 255, 255))

        self.rect_new_run = pygame.Rect(0, 0, 200, 50)
        self.rect_new_run.center = (SCREEN_WIDTH // 2, 350)

        self.rect_quit = pygame.Rect(0, 0, 200, 50)
        self.rect_quit.center = (SCREEN_WIDTH // 2, 430)

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
        self.collision = CollisionSystem()
        self.events = EventSystem()
        self.shooting = ShootingSystem()
        self.boss_attacks = BossAttackSystem()
        self.crosshair = CrosshairSystem()
        self.perk_card_rects = []

        self.setup_event_listeners()
        

        self.npcs = []
        self.portal_rect = pygame.Rect(MAP_SIZE // 2 - 45, MAP_SIZE // 2 - 170, 90, 55)
        self.enemies = []
        self.projectiles = []
        self.enemy_bullets = []

        self.input = InputSystem()
        self.perk_input_lock = 0.0
        self.pause_sliders = {}

        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.message = ""
        self.wave_notice_text = ""
        self.wave_notice_timer = 0.0
        self._last_exit_debug = None
        self._last_draw_portal_debug = None

        self.waves = WaveSystem()
        self.room_exit_open = False
        self.room_exit_rect = pygame.Rect(0, 0, 170, 170)
        self.room_exit_rect.center = (MAP_SIZE // 2, MAP_SIZE // 2 - 180)

        #self.reset_run()
        

    def setup_event_listeners(self):
        self.events.subscribe("player_shoot", lambda data: self.audio.play("shoot"))
        self.events.subscribe("player_dash", lambda data: self.audio.play("dash"))
        self.events.subscribe("enemy_hit", lambda data: self.audio.play("hit"))
        self.events.subscribe("enemy_killed", lambda data: self.audio.play("enemy_death"))
        self.events.subscribe("perk_available",lambda data: self.audio.play("level_up"))
        self.events.subscribe("room_cleared", lambda data: self.audio.play("room_clear"))
        self.events.subscribe("boss_spawned", lambda data: self.audio.play("boss_spawn"))
        self.events.subscribe("boss_phase_changed", lambda data: self.audio.play("boss_phase"))
        self.events.subscribe("npc_purchase", lambda data: self.audio.play("menu_select"))


        self.events.subscribe("state_hub", lambda data: self.audio.play_music("hub.ogg"))
        self.events.subscribe("state_room", lambda data: self.audio.play_music("combat.ogg"))
        self.events.subscribe("state_boss", lambda data: self.audio.play_music("boss.ogg"))

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
            frame = pygame.transform.smoothscale(self.screen, self.viewport_rect.size)
        self.window.blit(frame, self.viewport_rect)
        pygame.display.flip()

    def reset_run(self):
        self.player.reset()
        self.upgrades.reset()
        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.message = ""
        self.effects.reset()
        enter_hub(self)
        self.events.emit("run_started")

    def open_perk_select_if_needed(self):
        if self.player.pending_level_ups > 0 and self.state in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            self.previous_state = self.state
            options = self.perks.roll_options(self.player)
            if not options:
                self.player.consume_pending_level_up()
                self.message = "All perk cards are maxed."
                return
            self.state = GameState.PERK_SELECT
            self.events.emit("perk_available")
            self.perk_input_lock = 0.25

    def open_room_exit(self):
        exit_center = pygame.Vector2(self.player.rect.center) + pygame.Vector2(165, 0)
        half_w = self.room_exit_rect.width // 2
        half_h = self.room_exit_rect.height // 2
        exit_center.x = max(half_w, min(MAP_SIZE - half_w, exit_center.x))
        exit_center.y = max(half_h, min(MAP_SIZE - half_h, exit_center.y))
        self.room_exit_rect.center = (round(exit_center.x), round(exit_center.y))
        self.room_exit_open = True
        self.events.emit("room_cleared")
        self.effects.ring(self.room_exit_rect.center, radius=170, life=0.9, width=6)
        self.message = "Room cleared. Exit portal opened. Press E near it."
        self.show_wave_notice("EXIT PORTAL OPEN")

        if DEBUG_ROOM_FLOW:
            snapshot = (self.room_exit_open, self.room_exit_rect, self.player.rect.center, tuple(self.camera.offset))
            if snapshot != self._last_exit_debug:
                self._last_exit_debug = snapshot
                print("[EXIT OPEN]", self.room_exit_open, self.room_exit_rect, self.player.rect.center, self.camera.offset)

    def show_wave_notice(self, text):
        self.wave_notice_text = text
        self.wave_notice_timer = 2.0

    def draw_exit_portal(self):
        if not self.room_exit_open:
            return

        screen_center = self.camera.apply_pos(pygame.Vector2(self.room_exit_rect.center))
        cx, cy = round(screen_center.x), round(screen_center.y)
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
    
            enemy.rect.clamp_ip(pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE))

    def respawn_distant_enemies(self):
        if self.state not in (GameState.ROOM, GameState.BOSS):
            return

        player_pos = pygame.Vector2(self.player.rect.center)
        screen_margin = 560
        screen_rect = pygame.Rect(
            -screen_margin,
            -screen_margin,
            SCREEN_WIDTH + screen_margin * 2,
            SCREEN_HEIGHT + screen_margin * 2,
        )

        for enemy in self.enemies:
            enemy_type = getattr(enemy, "type", None)
            type_name = enemy_type.name if enemy_type is not None else ""
            if type_name == "BOSS" or not enemy.alive:
                continue

            enemy_pos = pygame.Vector2(enemy.rect.center)
            screen_pos = self.camera.apply_pos(enemy_pos)
            if screen_rect.collidepoint(round(screen_pos.x), round(screen_pos.y)):
                continue

            distance = enemy_pos.distance_to(player_pos)
            if type_name in ("RANGED", "HUNTER", "ELITE"):
                min_distance = 1280
                spawn_radius = random.randint(620, 820)
            else:
                min_distance = 920
                spawn_radius = random.randint(420, 640)

            if distance < min_distance:
                continue

            velocity = pygame.Vector2(self.player.velocity)
            if velocity.length_squared() > 0 and random.random() < 0.62:
                base_angle = velocity.as_polar()[1] + random.uniform(-75, 75)
            else:
                base_angle = random.uniform(0, 360)

            offset = pygame.Vector2(spawn_radius, 0).rotate(base_angle)
            new_pos = player_pos + offset
            half_w = enemy.rect.width // 2
            half_h = enemy.rect.height // 2
            new_pos.x = max(half_w, min(MAP_SIZE - half_w, new_pos.x))
            new_pos.y = max(half_h, min(MAP_SIZE - half_h, new_pos.y))
            enemy.rect.center = (round(new_pos.x), round(new_pos.y))
            enemy.last_player_center = None
            enemy.leap_timer = 0.0
            enemy.windup_timer = 0.0


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
            self.projectiles.clear()
            self.enemy_bullets.clear()
            self.message = "Loot Beasts escaped. Exit portal opened."
            self.open_room_exit()

    def update(self, dt):
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

        self.shooting.update(dt)
        self.player.handle_movement_input()
        update_player_aim(self.player, self.enemies, self.camera, self.game_mouse_pos())

        self.player.update(dt, self.collision.get_colliders())

        if pygame.mouse.get_pressed()[0]:
            did_shoot = self.shooting.try_shoot(self.player, self.projectiles, self.audio)
            if did_shoot:
                self.events.emit("player_shoot", {
                    "player": self.player
                })

        if self.state == GameState.ROOM:
            self.rooms.update(dt)
            spawned_enemies = self.waves.update(
                dt,
                lambda: self.spawn.get_spawn_position(self.camera),
                len(self.enemies),
            )
            if spawned_enemies:
                self.enemies.extend(spawned_enemies)
            wave_message = self.waves.consume_wave_message()
            if wave_message:
                self.show_wave_notice(wave_message)
            self.update_treasure_room()

        self.respawn_distant_enemies()

        for enemy in self.enemies:
            action = enemy.update(dt, self.player.rect)
            if not action:
                continue
            if action["type"] == "enemy_shoot":
                base_damage = int(ENEMY_BULLET_DAMAGE * action.get("damage_multiplier", 1.0))
                speed = 410 + int(action.get("difficulty", 1.0) * 12)
                for angle, damage_scale in [(-28, 0.65), (-14, 0.85), (0, 1.0), (14, 0.85), (28, 0.65)]:
                    damage = max(1, int(base_damage * damage_scale))
                    self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=speed, owner_id=action.get("owner_id")))
            elif action["type"] == "elite_burst":
                difficulty = action.get("difficulty", 1.0)
                base_damage = int((ENEMY_BULLET_DAMAGE + 2) * action.get("damage_multiplier", 1.0))
                fan_speed = 470 + int(difficulty * 16)
                ring_speed = 330 + int(difficulty * 10)
                for angle, damage_scale in [(-34, 0.75), (-18, 0.9), (0, 1.0), (18, 0.9), (34, 0.75)]:
                    damage = max(1, int(base_damage * damage_scale))
                    self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=fan_speed, owner_id=action.get("owner_id")))
                for angle in range(0, 360, 60):
                    damage = max(1, int(base_damage * 0.55))
                    self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), damage, speed=ring_speed, owner_id=action.get("owner_id")))
            elif action["type"] == "hunter_homing":
                damage = int((ENEMY_BULLET_DAMAGE + 1) * action.get("damage_multiplier", 1.0))
                speed = 330 + int(action.get("difficulty", 1.0) * 12)
                self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], action["direction"], damage, speed=speed, homing_target=self.player, turn_rate=1.55, owner_id=action.get("owner_id")))
            elif action["type"] in ("boss_cone", "boss_ring", "boss_summon_leap"):
                self.boss_attacks.handle_action(
                        action,
                        self.enemies,
                        self.enemy_bullets,
                        self.effects,
                        self.audio,
                        player=self.player
                    )

        self.resolve_enemy_crowding()

        for p in self.projectiles:
            p.update(dt)
        for b in self.enemy_bullets:
            b.update(dt)

        reward_multiplier = self.rooms.reward_multiplier if self.state == GameState.ROOM else 1
        kills, boss_killed = self.combat.update(
            dt,
            self.player,
            self.projectiles,
            self.enemies,
            self.enemy_bullets,
            effects=self.effects,
            audio=self.audio,
            reward_multiplier=reward_multiplier,
        )

        if kills:
            self.room_kills += kills
            self.total_kills += kills

        self.projectiles = [p for p in self.projectiles if p.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        self.effects.update(dt)
        self.camera.follow(self.player.rect, self.player.velocity, dt)

        if self.player.is_dead():
            self.state = GameState.GAME_OVER
            return

        if (
            self.state == GameState.ROOM
            and not self.room_exit_open
            and self.waves.all_waves_spawned()
            and len(self.enemies) == 0
        ):
            self.open_room_exit()
            return

        if self.state == GameState.BOSS and boss_killed:
            if self.room_number > ROOMS_TO_BOSS:
                self.state = GameState.WIN
            else:
                self.room_number += 1
                self.message = "Boss defeated. Stage 2 opened."
                enter_hub(self)
            return

        self.open_perk_select_if_needed()

    def draw(self):

        if self.state == GameState.MENU:
            draw_menu(self.screen, self)

        elif self.state == GameState.PERK_SELECT:
            self.perk_card_rects = draw_perk_select(
                self.screen,
                self.big_font,
                self.font,
                self.perks.current_options,
                self.game_mouse_pos(),
            )

        elif self.state in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            draw_world_background(self.screen, self.camera, hub=self.state == GameState.HUB, room_type=self.rooms.room_type)

            if self.state == GameState.HUB:
                pygame.draw.rect(self.screen, (60, 60, 60), self.camera.apply_rect(self.portal_rect), border_radius=10)
                for npc in self.npcs:
                    npc.draw(self.screen, self.camera)

            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
            for p in self.projectiles:
                p.draw(self.screen, self.camera)
            for b in self.enemy_bullets:
                b.draw(self.screen, self.camera)

            self.player.draw(self.screen, self.camera)
            self.effects.draw(self.screen, self.camera, self.font)
            if self.state == GameState.ROOM:
                self.draw_exit_portal()

            room_target = self.rooms.target_kills
            objective_label = "Kills"
            if self.state == GameState.BOSS and self.enemies:
                boss = self.enemies[0]
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

            draw_hud(
                self.screen,
                self.font,
                self.player,
                min(self.room_number, ROOMS_TO_BOSS),
                shown_kills,
                room_target,
                len(self.enemies),
                self.state.name,
                self.rooms.display_name() if self.state == GameState.ROOM else "",
                self.rooms.room_time,
                objective_label,
            )
            if self.state == GameState.ROOM:
                draw_room_banner(self.screen, self.big_font, self.font, self.rooms)

            npc = nearest_npc(self.player, self.npcs) if self.state == GameState.HUB else None
            if npc:
                pos = self.camera.apply_pos(pygame.Vector2(npc.rect.centerx, npc.rect.top - 26))
                hint = "Press E to enter dungeon" if npc.role == "portal" else "Press E to talk"
                hint_surf = self.font.render(hint, True, (255, 235, 120))
                hint_bg = pygame.Surface((hint_surf.get_width() + 18, hint_surf.get_height() + 10), pygame.SRCALPHA)
                hint_bg.fill((0, 0, 0, 175))
                hint_rect = hint_bg.get_rect(center=(round(pos.x), round(pos.y)))
                self.screen.blit(hint_bg, hint_rect)
                self.screen.blit(hint_surf, hint_surf.get_rect(center=hint_rect.center))
            if npc and npc.role in ("blacksmith", "healer"):
                draw_shop_hint(self.screen, self.font, npc.role, self.upgrades, player_gold=self.player.gold)

            if self.message:
                txt = self.font.render(self.message, True, BLACK)
                self.screen.blit(txt, (22, SCREEN_HEIGHT - 34))

            self.dialogue.draw(self.screen)
            if self.state == GameState.ROOM:
                self.draw_wave_notice()
        
        elif self.state == GameState.PAUSED:
            draw_world_background(
                self.screen,
                self.camera,
                hub=self.previous_state == GameState.HUB,
                room_type=self.rooms.room_type,
            )
            self.player.draw(self.screen, self.camera)
            self.pause_sliders = draw_pause_menu(self.screen, self.big_font, self.font)

        elif self.state == GameState.GAME_OVER:
            draw_end_screen(self.screen, self.big_font, self.font, "GAME OVER", f"Rooms reached: {self.room_number} | Total kills: {self.total_kills}")

        elif self.state == GameState.WIN:
            draw_end_screen(self.screen, self.big_font, self.font, "BOSS DEFEATED", f"Level {self.player.level} | Gold {self.player.gold} | Kills {self.total_kills}")

        if self.state != GameState.MENU:
            self.crosshair.draw(self.screen, self.game_mouse_pos())
        self.present()

    def run(self):
        while True:
            pygame.mouse.set_visible(self.state == GameState.MENU)
            dt = self.clock.tick(FPS) / 1000.0
            self.input.handle_events(self)
            self.update(dt)
            self.draw()

    def quit(self):
        pygame.quit()
        sys.exit()

