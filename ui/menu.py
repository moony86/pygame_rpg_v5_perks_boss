import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


def draw_menu(surface, game):
    t = pygame.time.get_ticks() / 1000.0

    # ── background – animated dark grid ──────────────────────────────────
    surface.fill((8, 8, 18))

    # subtle moving grid
    grid_col = (20, 24, 40)
    offset   = int(t * 18) % 40
    for gx in range(-40, SCREEN_WIDTH + 40, 40):
        pygame.draw.line(surface, grid_col, (gx + offset, 0), (gx + offset, SCREEN_HEIGHT), 1)
    for gy in range(-40, SCREEN_HEIGHT + 40, 40):
        pygame.draw.line(surface, grid_col, (0, gy + offset), (SCREEN_WIDTH, gy + offset), 1)

    # corner glow blobs (simulated with alpha rects)
    for bx, by, col in [
        (0,           0,            (0, 40, 100)),
        (SCREEN_WIDTH, SCREEN_HEIGHT, (60, 0, 80)),
    ]:
        blob = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.circle(blob, (*col, 60), (150, 150), 150)
        surface.blit(blob, (bx - 150, by - 150))

    # ── title ────────────────────────────────────────────────────────────
    cy_title = SCREEN_HEIGHT // 2 - 130

    # glow behind title
    glow_surf = pygame.Surface((500, 80), pygame.SRCALPHA)
    glow_a    = int(40 + 20 * math.sin(t * 1.5))
    pygame.draw.rect(glow_surf, (60, 120, 255, glow_a), (0, 0, 500, 80), border_radius=12)
    surface.blit(glow_surf, (SCREEN_WIDTH // 2 - 250, cy_title - 10))

    # title text with manual shadow
    title_str = "BLUE CUBE  v5"
    shadow    = game.big_font.render(title_str, True, (0, 0, 0))
    title_s   = game.big_font.render(title_str, True, (100, 180, 255))
    surface.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, cy_title + 2)))
    surface.blit(title_s, title_s.get_rect(center=(SCREEN_WIDTH // 2, cy_title)))

    # subtitle
    sub = game.font.render("geometric roguelite  |  WASD + Mouse", True, (100, 120, 160))
    surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, cy_title + 52)))

    # thin accent line
    line_y = cy_title + 72
    pygame.draw.line(surface, (40, 80, 160),
                     (SCREEN_WIDTH // 2 - 180, line_y),
                     (SCREEN_WIDTH // 2 + 180, line_y), 1)

    # ── buttons ──────────────────────────────────────────────────────────
    mouse   = game.game_mouse_pos()
    hover_n = game.rect_new_run.collidepoint(mouse)
    hover_q = game.rect_quit.collidepoint(mouse)

    def draw_btn(rect, label, col_border, hovered):
        bg_a   = 200 if hovered else 140
        bg     = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        bg.fill((16, 20, 40, bg_a))
        if hovered:
            pygame.draw.rect(bg, (*col_border, 80), (0, 0, rect.w, rect.h), border_radius=8)
        pygame.draw.rect(bg, col_border, (0, 0, rect.w, rect.h), 2, border_radius=8)
        surface.blit(bg, rect.topleft)

        scale = 1.06 if hovered else 1.0
        txt   = game.font.render(label, True,
                                  (255, 255, 255) if hovered else (200, 200, 200))
        if scale != 1.0:
            txt = pygame.transform.scale(txt,
                                         (int(txt.get_width() * scale),
                                          int(txt.get_height() * scale)))
        surface.blit(txt, txt.get_rect(center=rect.center))

        # hover arrow indicator
        if hovered:
            ax = rect.left - 18
            ay = rect.centery
            pts = [(ax, ay - 6), (ax + 10, ay), (ax, ay + 6)]
            pygame.draw.polygon(surface, col_border, pts)

    draw_btn(game.rect_new_run, "New Run",  (60, 200, 100), hover_n)
    draw_btn(game.rect_quit,    "Quit",     (200, 60,  60), hover_q)

    # ── hint ─────────────────────────────────────────────────────────────
    hint = game.font.render("click to select", True, (60, 70, 100))
    surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 185)))
