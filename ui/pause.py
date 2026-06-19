import pygame

from config import CONFIG
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from ui.common import draw_text


def draw_slider(surface, font, label, x, y, width, value):
    value = max(0.0, min(1.0, value))

    label_text = f"{label}: {int(value * 100)}%"
    draw_text(surface, font, label_text, x, y - 32, WHITE)

    track_rect = pygame.Rect(x, y, width, 8)
    fill_rect = pygame.Rect(x, y, int(width * value), 8)

    pygame.draw.rect(surface, (80, 80, 80), track_rect, border_radius=4)
    pygame.draw.rect(surface, (255, 220, 0), fill_rect, border_radius=4)

    knob_x = x + int(width * value)
    knob_rect = pygame.Rect(knob_x - 8, y - 8, 16, 24)

    pygame.draw.rect(surface, (0, 0, 0), knob_rect.inflate(4, 4), border_radius=8)
    pygame.draw.rect(surface, (255, 255, 255), knob_rect, border_radius=8)

    return track_rect


def draw_pause_menu(surface, big_font, font):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

    draw_text(surface, big_font, "PAUSED", SCREEN_WIDTH // 2, 130, WHITE, center=True)
    draw_text(surface, font, "ESC - Resume", SCREEN_WIDTH // 2, 210, WHITE, center=True)
    draw_text(surface, font, "Q - Quit Game", SCREEN_WIDTH // 2, 245, WHITE, center=True)

    sliders = {}

    sliders["music"] = draw_slider(
        surface,
        font,
        "Music",
        SCREEN_WIDTH // 2 - 180,
        330,
        360,
        CONFIG["music_volume"],
    )

    sliders["sfx"] = draw_slider(
        surface,
        font,
        "SFX",
        SCREEN_WIDTH // 2 - 180,
        400,
        360,
        CONFIG["sfx_volume"],
    )

    return sliders
