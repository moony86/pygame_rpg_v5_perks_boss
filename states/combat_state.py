import pygame

from game_state import GameState
from systems.scene_system import enter_hub


def handle_combat_events(game, event):
    if game.state not in (GameState.ROOM, GameState.BOSS):
        return

    if event.key == pygame.K_q:
        if game.player.try_dash():
            game.events.emit("player_dash")
            game.effects.ring(
                game.player.rect.center,
                radius=70,
                life=0.22,
            )
    elif event.key == pygame.K_e:
        if game.state == GameState.ROOM and game.room_exit_open:
            if game.player.rect.colliderect(game.room_exit_rect):
                game.room_number += 1
                enter_hub(game)
