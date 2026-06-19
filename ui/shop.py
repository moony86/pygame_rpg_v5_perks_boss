import pygame

from settings import WHITE
from systems.upgrade_system import UPGRADES
from ui.common import draw_text


def draw_shop_hint(surface, font, npc_role):
    options = UPGRADES.get(npc_role, [])

    if not options:
        return

    x, y = 58, 365

    pygame.draw.rect(surface, (0, 0, 0), (45, 350, 470, 95), border_radius=8)
    pygame.draw.rect(surface, WHITE, (45, 350, 470, 95), 2, border_radius=8)

    for i, (name, cost, key) in enumerate(options, start=1):
        draw_text(surface, font, f"{i}) {name} - {cost} gold", x, y + (i - 1) * 27, WHITE)
