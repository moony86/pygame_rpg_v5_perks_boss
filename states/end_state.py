import pygame

from game_state import GameState


def handle_end_screen_events(game, event):
    if game.state not in (GameState.GAME_OVER, GameState.WIN):
        return

    if event.key == pygame.K_RETURN:
        game.reset_run()
        game.state = GameState.HUB
