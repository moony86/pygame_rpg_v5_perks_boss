import pygame

from config import CONFIG
from game_state import GameState
from settings import ROOMS_TO_BOSS

from systems.world_utils import nearest_npc
from systems.scene_system import enter_hub, enter_room, enter_boss

from states.menu_state import handle_menu_events
from states.pause_state import handle_pause_state
from states.perk_state import handle_perk_select_events
from states.hub_state import handle_hub_events
from states.combat_state import handle_combat_events
from states.end_state import handle_end_screen_events
from states.common_state import handle_escape_key


class InputSystem:
    def handle_events(self, game):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.quit()

            if event.type == pygame.VIDEORESIZE:
                game.resize_window(event.size)
                continue

            event = game.translate_event(event)

            if game.state == GameState.PERK_SELECT:
                handle_perk_select_events(game, event)
                continue
            
            if game.state == GameState.PAUSED:
                handle_pause_state(game, event, handle_escape_key)
                continue
            

            if game.state == GameState.MENU:
                handle_menu_events(game, event)
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                handle_escape_key(game)
                continue

            elif game.state in (GameState.GAME_OVER, GameState.WIN):
                handle_end_screen_events(game, event)

            elif game.state == GameState.HUB:
                handle_hub_events(game, event)

            elif game.state in (GameState.ROOM, GameState.BOSS):
                handle_combat_events(game, event)
