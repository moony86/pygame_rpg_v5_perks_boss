import pygame

from game_state import GameState


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
