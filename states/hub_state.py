import pygame

from settings import ROOMS_TO_BOSS
from systems.world_utils import nearest_npc
from systems.scene_system import enter_room, enter_boss

def handle_hub_events (game, event):
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
