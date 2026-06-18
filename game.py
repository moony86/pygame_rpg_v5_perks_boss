import pygame
import sys
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FPS, BLACK,
    ROOMS_TO_BOSS,
    ENEMY_BULLET_DAMAGE,
)
from game_state import GameState
from entities.player import Player
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
from systems.ui import (
    draw_hud,
    draw_menu,
    draw_end_screen,
    draw_shop_hint,
    draw_perk_select,
    draw_room_banner,
)
from systems.collision_system import CollisionSystem
from systems.world_utils import (
    rotate_vector,
    nearest_npc,
    draw_world_background,
)
from systems.aim_system import update_player_aim
from systems.shooting_system import ShootingSystem
from systems.boss_attack_system import BossAttackSystem
from systems.scene_system import enter_hub, enter_room, enter_boss
from data.dialogues import DIALOGUES


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
        self.collision = CollisionSystem()

        self.npcs = []
        self.portal_rect = pygame.Rect(MAP_SIZE // 2 - 45, MAP_SIZE // 2 - 170, 90, 55)
        self.enemies = []
        self.projectiles = []
        self.enemy_bullets = []

        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.shooting = ShootingSystem()
        self.message = ""

        self.reset_run()

        self.boss_attacks = BossAttackSystem()


    def reset_run(self):
        self.player.reset()
        self.room_number = 1
        self.room_kills = 0
        self.total_kills = 0
        self.message = ""
        self.effects.reset()
        enter_hub(self)

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
                                    enter_boss(self)
                                else:
                                    enter_room(self)
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


    def update(self, dt):
        if self.state not in (GameState.HUB, GameState.ROOM, GameState.BOSS):
            if self.state == GameState.PERK_SELECT:
                self.effects.update(dt)
            return

        self.shooting.update(dt)
        self.player.handle_movement_input()
        update_player_aim(self.player, self.enemies, self.camera)

        self.player.update(dt, self.collision.get_colliders())

        if pygame.mouse.get_pressed()[0]:
            self.shooting.try_shoot(self.player, self.projectiles, self.audio)

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
                self.boss_attacks.handle_action(
                        action,
                        self.enemies,
                        self.enemy_bullets,
                        self.effects,
                        self.audio,
                    )

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
            enter_hub(self)
            return

        if self.state == GameState.BOSS and boss_killed:
            self.state = GameState.WIN
            return

        self.open_perk_select_if_needed()

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
            if self.state == GameState.ROOM:
                draw_room_banner(self.screen, self.big_font, self.font, self.rooms)

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

