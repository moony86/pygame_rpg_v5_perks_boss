import pygame

from game_state import GameState
from systems.scene_system import enter_hub


DASH_DOUBLE_TAP_WINDOW = 0.24
DASH_HOLD_THRESHOLD = 0.32


def collect_exit_loot(game):
    if hasattr(game, "loot"):
        return game.loot.collect_remaining(game.player, effects=getattr(game, "effects", None), audio=getattr(game, "audio", None))
    return {"gold": 0, "xp": 0}


def handle_combat_events(game, event):
    if game.state not in (GameState.ROOM, GameState.BOSS):
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
        game.space_dash_down_time = pygame.time.get_ticks() / 1000.0
        return

    if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
        now = pygame.time.get_ticks() / 1000.0
        down_time = getattr(game, "space_dash_down_time", None)
        if down_time is None:
            return
        game.space_dash_down_time = None
        held = max(0.0, now - down_time)
        last_tap = getattr(game, "last_space_dash_tap_time", -999.0)
        variant = "super" if held >= DASH_HOLD_THRESHOLD else "chain" if now - last_tap <= DASH_DOUBLE_TAP_WINDOW else "normal"

        skill = game.player.try_active_skill(variant=variant)
        if not skill and variant == "super":
            variant = "normal"
            skill = game.player.try_active_skill(variant=variant)
        if skill:
            game.last_space_dash_tap_time = now
            game.events.emit("player_dash", {"variant": getattr(game.player, "dash_variant", variant)})
            game.apply_player_skill(skill)
        return

    if event.type != pygame.KEYDOWN:
        return

    if event.key == pygame.K_e:
        if game.state == GameState.ROOM and getattr(getattr(game, "stage", None), "active", False):
            node = game.stage.current_node
            if node is None or not node.cleared:
                return
            on_door = any(game.player.rect.colliderect(rect) for _, _, rect in game.stage.open_doors())
            on_exit = game.room_exit_open and game.player.rect.colliderect(game.room_exit_rect)
            if not (on_door or on_exit):
                return
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
