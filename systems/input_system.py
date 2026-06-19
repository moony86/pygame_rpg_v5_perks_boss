import pygame

from config import CONFIG
from game_state import GameState
from settings import ROOMS_TO_BOSS

from systems.world_utils import nearest_npc
from systems.scene_system import enter_hub, enter_room, enter_boss


class InputSystem:
    def handle_events(self, game):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.quit()

            if game.state == GameState.PERK_SELECT:
                self.handle_perk_select_events(game, event)
                continue
            
            if game.state == GameState.PAUSED:
                self.handle_pause_mouse(game, event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.handle_escape_key(game)
                    else:
                        self.handle_pause_events(game, event)
                continue
            

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.handle_escape_key(game)
                continue

            if game.state == GameState.MENU:
                self.handle_menu_events(game, event)

            elif game.state in (GameState.GAME_OVER, GameState.WIN):
                self.handle_end_screen_events(game, event)

            elif game.state == GameState.HUB:
                self.handle_hub_events(game, event)

            elif game.state in (GameState.ROOM, GameState.BOSS):
                self.handle_combat_events(game, event)

    def handle_escape_key(self, game):
        if game.state in (GameState.ROOM, GameState.BOSS, GameState.HUB):
            game.previous_state = game.state
            game.state = GameState.PAUSED
        elif game.state == GameState.PAUSED:
            game.state = game.previous_state
        else:
            game.quit()

    def handle_menu_events(self, game, event):
        if event.key == pygame.K_RETURN:
            game.reset_run()
            game.state = GameState.HUB

    def handle_pause_events(self, game, event):
        if event.key == pygame.K_q:
            game.quit()

    def handle_end_screen_events(self, game, event):
        if event.key == pygame.K_RETURN:
            game.reset_run()
            game.state = GameState.HUB

    def handle_perk_select_events(self, game, event):
        if game.perk_input_lock > 0:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.choose_perk_by_mouse(game, event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                index = int(event.unicode) - 1
                self.choose_perk(game, index)

    def choose_perk_by_mouse(self, game, mouse_pos):
        for index, rect in enumerate(game.perk_card_rects):
            if rect.collidepoint(mouse_pos):
                self.choose_perk(game, index)
                break

    def choose_perk(self, game, index):
        perk = game.perks.apply(game.player, index)

        if not perk:
            return

        game.player.consume_pending_level_up()
        game.message = f"Perk: {perk['name']}"
        game.events.emit("menu_select")

        game.player.invulnerable_timer = max(
            game.player.invulnerable_timer,
            0.5,
        )

        game.effects.ring(
            game.player.rect.center,
            radius=130,
            life=0.55,
        )

        game.state = game.previous_state
        game.open_perk_select_if_needed()

    def handle_hub_events(self, game, event):
        if event.key == pygame.K_e:
            npc = nearest_npc(game.player, game.npcs)

            if npc:
                if npc.role == "portal":
                    if game.room_number > ROOMS_TO_BOSS:
                        enter_boss(game)
                    else:
                        enter_room(game)
                else:
                    game.dialogue.toggle_npc(npc)
            else:
                game.dialogue.close()

        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            npc = nearest_npc(game.player, game.npcs)

            if npc and npc.role in ("blacksmith", "healer"):
                index = int(event.unicode) - 1
                game.message = game.upgrades.buy(game.player, npc.role, index)
                game.dialogue.show(npc.name, game.message)
                game.events.emit("npc_purchase")

    def handle_combat_events(self, game, event):
        if event.key == pygame.K_q:
            if game.player.try_dash():
                game.events.emit("player_dash")
                game.effects.ring(
                    game.player.rect.center,
                    radius=70,
                    life=0.22,
                )

    def handle_pause_mouse(self, game, event):
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            return

        if event.type == pygame.MOUSEMOTION and not event.buttons[0]:
            return

        mouse_pos = event.pos

        for slider_name, rect in game.pause_sliders.items():
            if rect.collidepoint(mouse_pos):
                value = (mouse_pos[0] - rect.x) / rect.width
                value = max(0.0, min(1.0, value))

                if slider_name == "music":
                    CONFIG["music_volume"] = value
                elif slider_name == "sfx":
                    CONFIG["sfx_volume"] = value

                game.audio.apply_volumes()