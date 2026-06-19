import pygame

from settings import SCREEN_WIDTH, WHITE
from ui.common import draw_text


def draw_room_banner(surface, big_font, font, room_system):
    if room_system.banner_timer <= 0:
        return

    info = room_system.info()
    title = info["title"]
    message = info["message"]
    color = info["color"]

    overlay = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 185))

    draw_text(surface, big_font, title, SCREEN_WIDTH // 2, 220, color, center=True)
    draw_text(surface, font, message, SCREEN_WIDTH // 2, 270, WHITE, center=True)
