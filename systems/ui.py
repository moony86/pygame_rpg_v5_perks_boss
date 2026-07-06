"""Legacy UI helper module.

Active UI modules import shared helpers from ui.common. This module is retained
temporarily as a removal candidate and should not receive new UI code.
"""

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, DARK_GRAY, RED, GREEN, YELLOW, GOLD, CYAN, ROOMS_TO_BOSS
from systems.upgrade_system import UPGRADES
from config import CONFIG


def draw_text(surface, font, text, x, y, color=WHITE, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)


def draw_bar(surface, x, y, w, h, ratio, fg, bg=(70, 70, 70)):
    ratio = max(0, min(1, ratio))
    pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=4)
    pygame.draw.rect(surface, fg, (x, y, int(w * ratio), h), border_radius=4)
    pygame.draw.rect(surface, BLACK, (x, y, w, h), 2, border_radius=4)

