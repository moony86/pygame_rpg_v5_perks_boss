import pygame

from game_state import GameState
from systems.scene_system import enter_hub


def collect_exit_loot(game):
    if hasattr(game, "loot"):
        return game.loot.collect_remaining(game.player, effects=getattr(game, "effects", None), audio=getattr(game, "audio", None))
    return {"gold": 0, "xp": 0}


def handle_combat_events(game, event):
    if game.state not in (GameState.ROOM, GameState.BOSS):
        return

    if event.key == pygame.K_SPACE:
        skill = game.player.try_active_skill()
        if skill:
            game.events.emit("player_dash")
            game.apply_player_skill(skill)
    elif event.key == pygame.K_e:
        if game.state == GameState.ROOM and getattr(getattr(game, "stage", None), "active", False):
            collect_exit_loot(game)
            if game.stage.try_use_door(game.player.rect):
                return
            if game.room_exit_open and game.player.rect.colliderect(game.room_exit_rect):
                game.stage.try_complete_or_use_center_exit()
                return
        if game.state == GameState.ROOM and game.room_exit_open:
            if game.player.rect.colliderect(game.room_exit_rect):
                collect_exit_loot(game)
                if getattr(getattr(game, "stage", None), "active", False):
                    game.stage.advance_after_exit()
                elif getattr(getattr(game, "prototype_room", None), "active", False):
                    game.prototype_room.exit_to_hub()
                else:
                    game.room_number += 1
                    enter_hub(game)
