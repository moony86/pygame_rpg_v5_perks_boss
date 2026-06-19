import pygame

from config import CONFIG
from game_state import GameState

def handle_pause_events(game, event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            game.quit()


def handle_pause_mouse(game, event):
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


def handle_pause_state(game, event, handle_escape_key):
    handle_pause_mouse(game, event)

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            handle_escape_key(game)
        else:
            handle_pause_events(game, event)
