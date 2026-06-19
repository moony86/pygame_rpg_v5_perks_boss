from game_state import GameState
import pygame


def handle_menu_events(game, event):
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_pos = event.pos

        if game.rect_new_run.collidepoint(mouse_pos):
            game.reset_run()
            game.state = GameState.HUB

        elif game.rect_quit.collidepoint(mouse_pos):
            game.quit()
