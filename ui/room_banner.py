import pygame
import math
from settings import SCREEN_WIDTH, WHITE
from ui.common import draw_text


def draw_room_banner(surface, big_font, font, room_system):
    if room_system.banner_timer <= 0:
        return

    info    = room_system.info()
    title   = info["title"]
    message = info["message"]
    color   = info["color"]

    t    = pygame.time.get_ticks() / 1000.0
    fade = min(1.0, room_system.banner_timer / 0.4)  # fade out in last 0.4s

    banner_h = 110
    banner_y = 180

    # semi-transparent panel
    ov = pygame.Surface((SCREEN_WIDTH, banner_h), pygame.SRCALPHA)
    a  = int(165 * fade)
    ov.fill((5, 5, 15, a))
    surface.blit(ov, (0, banner_y))

    # left + right accent bars
    bar_col = (*color, int(200 * fade))
    bar_surf = pygame.Surface((6, banner_h), pygame.SRCALPHA)
    bar_surf.fill(bar_col)
    surface.blit(bar_surf, (0, banner_y))
    surface.blit(bar_surf, (SCREEN_WIDTH - 6, banner_y))

    # top + bottom thin lines
    line_col = (*color, int(120 * fade))
    line_s = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
    line_s.fill(line_col)
    surface.blit(line_s, (0, banner_y))
    surface.blit(line_s, (0, banner_y + banner_h - 1))

    # title with fade alpha
    alpha = int(255 * fade)
    title_s = big_font.render(title, True, color)
    title_s.set_alpha(alpha)
    surface.blit(title_s, title_s.get_rect(center=(SCREEN_WIDTH // 2, banner_y + 38)))

    msg_s = font.render(message, True, (200, 200, 210))
    msg_s.set_alpha(alpha)
    surface.blit(msg_s, msg_s.get_rect(center=(SCREEN_WIDTH // 2, banner_y + 78)))
