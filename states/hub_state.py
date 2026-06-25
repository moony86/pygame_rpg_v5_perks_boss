import pygame

from settings import ROOMS_TO_BOSS

FIRST_BOSS_GATE_ROOM = 6


def should_enter_boss(room_number):
    return room_number in (FIRST_BOSS_GATE_ROOM, ROOMS_TO_BOSS + 1)
from systems.world_utils import nearest_npc
from systems.scene_system import enter_room, enter_boss

def handle_hub_events (game, event):
    if event.key == pygame.K_e:
        npc = nearest_npc(game.player, game.npcs)

        if npc:
            if npc.role == "portal":
                if not getattr(game, "gatekeeper_ready", False):
                    game.gatekeeper_ready = True
                    game.dialogue.show("Gatekeeper", "Hero, the dungeon is awake. Press E again when you are ready to enter.")
                    game.message = "Press E again to start the dungeon."
                    return
                game.dialogue.show("Gatekeeper", "Then go. Survive the room and return stronger.")
                game.gatekeeper_ready = False
                if should_enter_boss(game.room_number):
                    enter_boss(game)
                else:
                    enter_room(game)
            else:
                game.gatekeeper_ready = False
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
