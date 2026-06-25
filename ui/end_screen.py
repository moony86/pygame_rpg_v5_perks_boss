import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, DARK_GRAY
from ui.common import draw_text


def draw_end_screen(surface, big_font, font, title, subtitle):
    t = pygame.time.get_ticks() / 1000.0

    surface.fill((6, 6, 14))

    # win vs lose palette
    is_win   = "BOSS" in title or "WIN" in title
    col_main = (80, 220, 120) if is_win else (220, 60, 60)
    col_dim  = (30, 90, 50)   if is_win else (80, 20, 20)

    # pulsing background glow
    glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    a    = int(30 + 15 * math.sin(t * 1.5))
    pygame.draw.ellipse(glow, (*col_dim, a),
                        (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 200, 600, 400))
    surface.blit(glow, (0, 0))

    # title
    sh = big_font.render(title, True, (0, 0, 0))
    ts = big_font.render(title, True, col_main)
    cy = SCREEN_HEIGHT // 2 - 80
    surface.blit(sh, sh.get_rect(center=(SCREEN_WIDTH // 2 + 2, cy + 2)))
    surface.blit(ts, ts.get_rect(center=(SCREEN_WIDTH // 2, cy)))

    # accent line
    line_w = int(min(500, ts.get_width() + 60))
    pygame.draw.line(surface, col_main,
                     (SCREEN_WIDTH // 2 - line_w // 2, cy + 44),
                     (SCREEN_WIDTH // 2 + line_w // 2, cy + 44), 1)

    # subtitle
    ss = font.render(subtitle, True, (180, 180, 200))
    surface.blit(ss, ss.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

    # restart prompt – blinking
    if int(t * 2) % 2 == 0:
        rs = font.render("[ Enter ]  Restart    [ Esc ]  Quit", True, (120, 200, 120))
        surface.blit(rs, rs.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))
