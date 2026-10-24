import pygame

from settings import ROOMS_TO_BOSS

def should_enter_boss(room_number):
    return room_number == ROOMS_TO_BOSS + 1
from systems.world_utils import nearest_npc

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
                if hasattr(game, "stage"):
                    game.stage.start_stage()
                else:
                    game.message = "Stage system unavailable."
            elif npc.role == "tea_vendor":
                game.gatekeeper_ready = False
                game.player.receive_tea()
                game.dialogue.show(npc.name, "Best tea in the world.")
                game.message = "Tea acquired. Press T to drink."
            else:
                game.gatekeeper_ready = False
                game.dialogue.toggle_npc(npc)
        else:
            game.dialogue.close()

    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
        npc = nearest_npc(game.player, game.npcs)

        if npc and npc.role in ("blacksmith", "healer"):
            from ui.hub import buy
            buy(game, npc, event.key - pygame.K_1)

    elif event.key == pygame.K_t:
        if getattr(game.player, "tea_state", None) == "holding":
            if game.player.start_drinking_tea():
                if hasattr(game, "audio"):
                    game.audio.play("tea_drink")
                game.message = "You drink the tea."
