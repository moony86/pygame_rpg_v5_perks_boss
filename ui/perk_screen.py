import pygame

from settings import (
    SCREEN_WIDTH,
    DARK_GRAY,
    WHITE,
    GOLD,
    GREEN,
)

from ui.common import draw_text


def draw_perk_select(surface, big_font, font, options):
    surface.fill(DARK_GRAY)

    draw_text(surface, big_font, "LEVEL UP", SCREEN_WIDTH // 2, 88, GOLD, center=True)
    draw_text(surface, font, "Choose one perk", SCREEN_WIDTH // 2, 135, WHITE, center=True)

    card_rects = []
    mouse_pos = pygame.mouse.get_pos()

    card_w, card_h = 250, 260
    gap = 35
    start_x = SCREEN_WIDTH // 2 - (card_w * 3 + gap * 2) // 2

    for i, perk in enumerate(options):
        x = start_x + i * (card_w + gap)
        y = 210

        rect = pygame.Rect(x, y, card_w, card_h)
        card_rects.append(rect)

        hovered = rect.collidepoint(mouse_pos)
        scale = 1.05 if hovered else 1.0

        draw_w = int(card_w * scale)
        draw_h = int(card_h * scale)

        draw_x = x + (card_w - draw_w) // 2
        draw_y = y + (card_h - draw_h) // 2

        draw_rect = pygame.Rect(draw_x, draw_y, draw_w, draw_h)

        bg_color = (50, 50, 50) if hovered else (32, 32, 32)
        border_color = WHITE if hovered else GOLD
        border_width = 5 if hovered else 3

        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=12)
        pygame.draw.rect(surface, border_color, draw_rect, border_width, border_radius=12)

        draw_text(surface, font, perk["name"], x + card_w // 2, y + 75, WHITE, center=True)
        draw_text(surface, font, perk["desc"], x + card_w // 2, y + 145, WHITE, center=True)

        hint = "Click to choose" if hovered else "Hover"
        draw_text(surface, font, hint, x + card_w // 2, y + 220, GREEN, center=True)

    return card_rects
