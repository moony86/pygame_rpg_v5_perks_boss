import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui.common import fitted_text


def draw_guidance(surface, game):
    state = game.state.name
    if state == "HUB":
        if game.dialogue.active:
            return  # One dialogue/interaction prompt at a time.
        text = "SANCTUARY  /  North: challenge gate  /  Approach a keeper and press E"
        for npc in game.npcs:
            if npc.role == "portal":
                pos = game.camera.apply_pos(pygame.Vector2(npc.rect.centerx, npc.rect.top - 58))
                label = game.font.render("START CHALLENGE", True, (255, 225, 110))
                rect = label.get_rect(center=(round(pos.x), round(pos.y)))
                pygame.draw.rect(surface, (8, 12, 22), rect.inflate(18, 10), border_radius=5)
                surface.blit(label, rect)
    elif state in ("ROOM", "BOSS"):
        node = getattr(game.stage, "current_node", None)
        if node and node.cleared:
            text = "Room clear - choose a door and press E"
        elif game.room_flow.run_time < 8:
            text = "WASD move  |  Mouse fire  |  Release Space: skill  |  Hold Tab: stats & map"
        else:
            return
    else:
        return
    rendered = fitted_text(game.font, text, (240, 230, 180), SCREEN_WIDTH - 100)
    rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 74))
    pygame.draw.rect(surface, (8, 12, 22), rect.inflate(24, 14), border_radius=6)
    surface.blit(rendered, rect)
