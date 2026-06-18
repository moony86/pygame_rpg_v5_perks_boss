import math
import random
import pygame
import sys

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FPS,
    GRAY, WHITE, LIGHT_GRAY, BLACK,
    INTERACTION_DISTANCE, PROJECTILE_DAMAGE, PROJECTILE_SPEED, SHOOT_COOLDOWN,
    AIM_ASSIST_RADIUS, AIM_ASSIST_STRENGTH, AIM_ASSIST_RANGE,
    ROOMS_TO_BOSS,
    ENEMY_BULLET_DAMAGE, BOSS_DAMAGE
)
from game_state import GameState
from entities.player import Player
from entities.npc import NPC
from entities.projectile import Projectile
from entities.enemy_bullet import EnemyBullet
from entities.enemy import Enemy, EnemyType
from systems.camera import Camera
from systems.dialogue_system import DialogueSystem
from systems.combat_system import CombatSystem
from systems.spawn_system import SpawnSystem
from systems.upgrade_system import UpgradeSystem
from systems.perk_system import PerkSystem
from systems.room_system import RoomSystem, RoomType
from systems.effects import EffectsSystem
from systems.audio_system import AudioSystem
from systems.ui import draw_hud, draw_menu, draw_end_screen, draw_shop_hint, draw_perk_select
from data.dialogues import DIALOGUES


def rotate_vector(vec, degrees):
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    return pygame.Vector2(vec.x * cos_a - vec.y * sin_a, vec.x * sin_a + vec.y * cos_a)


def distance_between(rect_a, rect_b):
    ax, ay = rect_a.center
    bx, by = rect_b.center
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def nearest_npc(player, npcs):
    best = None
    best_d = INTERACTION_DISTANCE
    for npc in npcs:
        d = distance_between(player.rect, npc.rect)
        if d < best_d:
            best = npc
            best_d = d
    return best


def nearest_enemy(player, enemies, max_range):
    best = None
    best_d = max_range
    for enemy in enemies:
        if not enemy.alive:
            continue
        d = distance_between(player.rect, enemy.rect)
        if d < best_d:
            best = enemy
            best_d = d
    return best


def draw_world_background(screen, camera, hub=False, room_type=None):
    screen.fill(GRAY)
    world_rect = pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE)

    if hub:
        bg = (245, 239, 220)
    elif room_type == RoomType.CURSE:
        bg = (235, 218, 235)
    elif room_type == RoomType.TREASURE:
        bg = (248, 239, 200)
    elif room_type == RoomType.ELITE:
        bg = (235, 230, 245)
    else:
        bg = WHITE

    pygame.draw.rect(screen, bg, camera.apply_rect(world_rect))

    grid_size = 120
    for x in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(screen, LIGHT_GRAY, camera.apply_pos(pygame.Vector2(x, 0)), camera.apply_pos(pygame.Vector2(x, MAP_SIZE)), 1)
    for y in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(screen, LIGHT_GRAY, camera.apply_pos(pygame.Vector2(0, y)), camera.apply_pos(pygame.Vector2(MAP_SIZE, y)), 1)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Blue Cube v5")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Arial", 22)
        self.big_font = pygame.font.SysFont("Arial", 48)

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

        self.npcs = []
        self.portal_rect = pygame.Rect(MAP_SIZE // 2 - 45, MAP_SIZE // 2 - 170, 90, 55)
        self.enemies = []
        self.projectiles = []
        self.enemy_bullets = []

        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.shoot_timer = 0.0
        self.message = ""

        self.reset_run()

    def reset_run(self):
        self.player.reset()
        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.message = ""
        self.effects.reset()
        self.enter_hub()

    def enter_hub(self):
        self.state = GameState.HUB
        self.player.move_to_hub_spawn()
        self.player.heal(self.player.regen_on_room_clear)
        self.camera.reset(self.player.rect)
        self.dialogue.close()
        self.combat.reset()
        self.enemies.clear()
        self.projectiles.clear()
        self.enemy_bullets.clear()

        self.npcs = [
            NPC(MAP_SIZE // 2 - 150, MAP_SIZE // 2, "Blacksmith", "blacksmith", "blacksmith_intro"),
            NPC(MAP_SIZE // 2 + 150, MAP_SIZE // 2, "Healer", "healer", "healer_intro"),
            NPC(MAP_SIZE // 2, MAP_SIZE // 2 - 120, "Gatekeeper", "portal", "portal_intro"),
        ]

    def enter_room(self):
        self.state = GameState.ROOM
        self.player.move_to_room_spawn()
        self.camera.reset(self.player.rect)
        self.dialogue.close()
        self.enemies.clear()
        self.projectiles.clear()
        self.enemy_bullets.clear()
        self.room_kills = 0

        room_type = self.rooms.choose_next_room(self.room_number)
        self.spawn.reset(self.room_number, room_type)

        if room_type == RoomType.TREASURE:
            reward = 25 + self.room_number * 8
            self.player.add_gold(reward)
            self.message = f"Treasure room: +{reward} gold. Return to hub."
            self.audio.play("room")
            self.effects.ring(self.player.rect.center, radius=120, life=0.7)
            self.room_number += 1
            self.enter_hub()
            return

        self.message = f"{self.rooms.display_name()} Room started."
        if room_type == RoomType.CURSE:
            self.message += " Rewards x2."
        self.audio.play("room")

    def enter_boss(self):
        self.state = GameState.BOSS
        self.player.move_to_room_spawn()
        self.camera.reset(self.player.rect)
        self.enemies.clear()
        self.projectiles.clear()
        self.enemy_bullets.clear()
        boss = Enemy(MAP_SIZE // 2, MAP_SIZE // 2 - 360, EnemyType.BOSS, difficulty=1.0)
        self.enemies.append(boss)
        self.message = "Boss awakened. Phase attacks have warnings."
        self.audio.play("boss")
        self.effects.ring(boss.rect.center, radius=180, life=1.0, width=5)

    def open_perk_select_if_needed(self):
        if self.player.pending_level_ups > 0 and self.state in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            self.previous_state = self.state
            self.state = GameState.PERK_SELECT
            self.perks.roll_options()
            self.audio.play("level")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()

                if self.state == GameState.MENU:
                    if event.key == pygame.K_RETURN:
                        self.reset_run()
                        self.state = GameState.HUB

                elif self.state in (GameState.GAME_OVER, GameState.WIN):
                    if event.key == pygame.K_RETURN:
                        self.reset_run()
                        self.state = GameState.HUB

                elif self.state == GameState.PERK_SELECT:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        index = int(event.unicode) - 1
                        perk = self.perks.apply(self.player, index)
                        if perk:
                            self.player.consume_pending_level_up()
                            self.message = f"Perk: {perk['name']}"
                            self.audio.play("select")
                            self.effects.ring(self.player.rect.center, radius=130, life=0.55)
                        self.state = self.previous_state
                        self.open_perk_select_if_needed()

                elif self.state == GameState.HUB:
                    if event.key == pygame.K_e:
                        npc = nearest_npc(self.player, self.npcs)
                        if npc:
                            if npc.role == "portal":
                                if self.room_number > ROOMS_TO_BOSS:
                                    self.enter_boss()
                                else:
                                    self.enter_room()
                            else:
                                self.dialogue.toggle_npc(npc)
                        else:
                            self.dialogue.close()

                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        npc = nearest_npc(self.player, self.npcs)
                        if npc and npc.role in ("blacksmith", "healer"):
                            index = int(event.unicode) - 1
                            self.message = self.upgrades.buy(self.player, npc.role, index)
                            self.dialogue.show(npc.name, self.message)
                            self.audio.play("select")

                elif self.state in (GameState.ROOM, GameState.BOSS):
                    if event.key == pygame.K_q:
                        if self.player.try_dash():
                            self.audio.play("dash")
                            self.effects.ring(self.player.rect.center, radius=70, life=0.22)

    def update_aim(self):
        target = nearest_enemy(self.player, self.enemies, AIM_ASSIST_RANGE)
        mouse_world = self.camera.screen_to_world(pygame.mouse.get_pos())
        aim_target = mouse_world

        if target:
            target_pos = pygame.Vector2(target.rect.center)
            if target_pos.distance_to(mouse_world) <= AIM_ASSIST_RADIUS:
                aim_target = mouse_world.lerp(target_pos, AIM_ASSIST_STRENGTH)

        self.player.update_aim(aim_target)

    def try_shoot(self):
        if self.shoot_timer > 0:
            return
        if self.state not in (GameState.ROOM, GameState.BOSS):
            return

        base_damage = PROJECTILE_DAMAGE + self.player.damage_bonus
        speed = PROJECTILE_SPEED + self.player.projectile_speed_bonus
        count = self.player.projectile_count

        if count <= 1:
            angles = [0]
        else:
            total = self.player.spread_degrees
            start = -total / 2
            step = total / max(1, count - 1)
            angles = [start + i * step for i in range(count)]

        for angle in angles:
            direction = rotate_vector(self.player.aim_direction, angle)
            critical = random.random() < self.player.crit_chance
            damage = int(base_damage * (self.player.crit_multiplier if critical else 1))
            self.projectiles.append(
                Projectile(
                    self.player.rect.centerx,
                    self.player.rect.centery,
                    direction,
                    damage,
                    speed=speed,
                    pierce=self.player.pierce,
                    critical=critical,
                )
            )

        self.audio.play("shoot")
        self.shoot_timer = max(0.055, SHOOT_COOLDOWN / self.player.fire_rate_multiplier)

    def update(self, dt):
        if self.state not in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            if self.state == GameState.PERK_SELECT:
                self.effects.update(dt)
            return

        self.shoot_timer = max(0, self.shoot_timer - dt)
        self.player.handle_movement_input()
        self.update_aim()
        self.player.update(dt)

        if pygame.mouse.get_pressed()[0]:
            self.try_shoot()

        if self.state == GameState.ROOM:
            self.rooms.update(dt)
            enemy = self.spawn.update(dt, self.camera)
            if enemy:
                self.enemies.append(enemy)

        for enemy in self.enemies:
            action = enemy.update(dt, self.player.rect)
            if not action:
                continue
            if action["type"] == "enemy_shoot":
                self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], action["direction"], ENEMY_BULLET_DAMAGE))
            elif action["type"] == "elite_burst":
                for angle in [-18, 0, 18]:
                    self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(action["direction"], angle), ENEMY_BULLET_DAMAGE + 2))
            elif action["type"] in ("boss_cone", "boss_ring", "boss_summon_leap"):
                self.spawn_boss_pattern(action)

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

        if self.state == GameState.ROOM and self.rooms.is_clear(self.room_kills):
            self.audio.play("room")
            self.effects.ring(self.player.rect.center, radius=140, life=0.75, width=5)
            self.room_number += 1
            self.message = "Room cleared. Return to the hub and upgrade."
            self.enter_hub()
            return

        if self.state == GameState.BOSS and boss_killed:
            self.state = GameState.WIN
            return

        self.open_perk_select_if_needed()

    def spawn_boss_pattern(self, action):
        base = action["direction"]
        phase = action.get("phase", 1)

        if action["type"] == "boss_cone":
            angles = [-24, -12, 0, 12, 24] if phase == 1 else [-36, -24, -12, 0, 12, 24, 36]
            for angle in angles:
                self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(base, angle), 14 if phase == 1 else BOSS_DAMAGE))

        elif action["type"] == "boss_ring":
            step = 30 if phase == 1 else 20
            for angle in range(0, 360, step):
                self.enemy_bullets.append(EnemyBullet(action["x"], action["y"], rotate_vector(pygame.Vector2(1, 0), angle), 12 if phase == 1 else 16, speed=240 if phase == 1 else 290))
            self.audio.play("boss")
            self.effects.ring((action["x"], action["y"]), radius=160, life=0.45, width=5)

        elif action["type"] == "boss_summon_leap":
            boss_pos = pygame.Vector2(action["x"], action["y"])
            for angle in [-90, 0, 90]:
                pos = boss_pos + rotate_vector(base, angle) * 120
                self.enemies.append(Enemy(pos.x, pos.y, EnemyType.CHASER, difficulty=1.8 if phase == 1 else 2.2))
            # boss leap itself
            for enemy in self.enemies:
                if enemy.type == EnemyType.BOSS:
                    enemy.leap_timer = 0.34
                    enemy.leap_velocity = base * (680 if phase == 1 else 820)
                    break
            self.effects.ring(boss_pos, radius=120, life=0.35, width=4)

    def draw(self):
        if self.state == GameState.MENU:
            draw_menu(self.screen, self.big_font, self.font)

        elif self.state == GameState.PERK_SELECT:
            draw_perk_select(self.screen, self.big_font, self.font, self.perks.current_options)

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

            room_target = self.rooms.target_kills
            if self.rooms.room_type == RoomType.SURVIVAL:
                room_target = int(self.rooms.survival_time)
                shown_kills = int(self.rooms.room_time)
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
            )

            npc = nearest_npc(self.player, self.npcs) if self.state == GameState.HUB else None
            if npc and npc.role in ("blacksmith", "healer"):
                draw_shop_hint(self.screen, self.font, npc.role)

            if self.message:
                txt = self.font.render(self.message, True, BLACK)
                self.screen.blit(txt, (22, SCREEN_HEIGHT - 34))

            self.dialogue.draw(self.screen)

        elif self.state == GameState.GAME_OVER:
            draw_end_screen(self.screen, self.big_font, self.font, "GAME OVER", f"Rooms reached: {self.room_number} | Total kills: {self.total_kills}")

        elif self.state == GameState.WIN:
            draw_end_screen(self.screen, self.big_font, self.font, "BOSS DEFEATED", f"Level {self.player.level} | Gold {self.player.gold} | Kills {self.total_kills}")

        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def quit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
