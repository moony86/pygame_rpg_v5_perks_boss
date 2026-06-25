import pygame
from config import CONFIG
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from ui.common import draw_text


def _slider(surface, font, label, x, y, w, value):
    value = max(0.0, min(1.0, value))

    # label + percentage
    lbl = font.render(f"{label}  {int(value * 100)}%", True, (200, 200, 220))
    surface.blit(lbl, (x, y - 26))

    # track
    track = pygame.Rect(x, y, w, 6)
    pygame.draw.rect(surface, (30, 30, 50), track, border_radius=3)

    # fill
    fill_w = int(w * value)
    if fill_w > 0:
        pygame.draw.rect(surface, (80, 160, 255),
                         pygame.Rect(x, y, fill_w, 6), border_radius=3)

    # knob
    kx = x + fill_w
    pygame.draw.circle(surface, (30, 30, 50), (kx, y + 3), 10)
    pygame.draw.circle(surface, (180, 220, 255), (kx, y + 3), 8)
    pygame.draw.circle(surface, (80, 160, 255),  (kx, y + 3), 4)

    return track


def draw_pause_menu(surface, big_font, font):
    # dark overlay
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 10, 185))
    surface.blit(ov, (0, 0))

    # card panel
    pw, ph = 400, 380
    px = SCREEN_WIDTH  // 2 - pw // 2
    py = SCREEN_HEIGHT // 2 - ph // 2 - 20
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((12, 14, 28, 220))
    pygame.draw.rect(panel, (50, 80, 130, 160), (0, 0, pw, ph), 1, border_radius=12)
    surface.blit(panel, (px, py))

    # top accent strip
    pygame.draw.rect(surface, (60, 100, 200),
                     pygame.Rect(px, py, pw, 4), border_radius=12)

    # title
    t_surf = big_font.render("PAUSED", True, (200, 220, 255))
    surface.blit(t_surf, t_surf.get_rect(center=(SCREEN_WIDTH // 2, py + 36)))

    # divider
    pygame.draw.line(surface, (40, 60, 100),
                     (px + 20, py + 64), (px + pw - 20, py + 64), 1)

    # key hints
    for i, (key, action) in enumerate([("ESC", "Resume"), ("Enter", "Return to Menu")]):
        k_surf = font.render(key,    True, (100, 160, 255))
        a_surf = font.render(action, True, (160, 160, 180))
        row_y  = py + 82 + i * 26
        surface.blit(k_surf, (px + 30,  row_y))
        surface.blit(a_surf, (px + 120, row_y))

    # divider 2
    pygame.draw.line(surface, (40, 60, 100),
                     (px + 20, py + 148), (px + pw - 20, py + 148), 1)

    # sliders
    sliders = {}
    sx = px + 30
    sw = pw - 60

    sliders["master"] = _slider(surface, font, "Master",
                                 sx, py + 184, sw, CONFIG["master_volume"])
    sliders["music"] = _slider(surface, font, "Music",
                                sx, py + 250, sw, CONFIG["music_volume"])
    sliders["sfx"]   = _slider(surface, font, "SFX",
                                sx, py + 316, sw, CONFIG["sfx_volume"])

    return sliders
