import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_GRAY, WHITE, GOLD, GREEN

from ui.common import draw_text


# perk rarity color palette
PERK_COLORS = [
    (80,  160, 255),   # blue  – card 0
    (180, 80,  255),   # purple – card 1
    (255, 160, 40),    # gold   – card 2
]


def draw_perk_select(surface, big_font, font, options, mouse_pos=None):
    t = pygame.time.get_ticks() / 1000.0

    # dark vignette bg
    surface.fill((6, 6, 14))

    # animated radial glow behind cards
    for i, col in enumerate([(20, 50, 120), (60, 20, 100), (80, 60, 10)]):
        glow = pygame.Surface((400, 300), pygame.SRCALPHA)
        a    = int(35 + 15 * math.sin(t * 1.2 + i))
        pygame.draw.ellipse(glow, (*col, a), (0, 0, 400, 300))
        gx = SCREEN_WIDTH // 4 * (i + 1) - 200
        surface.blit(glow, (gx, SCREEN_HEIGHT // 2 - 150))

    # header
    lv_surf  = big_font.render("LEVEL UP", True, GOLD)
    lv_sh    = big_font.render("LEVEL UP", True, (80, 60, 0))
    surface.blit(lv_sh, lv_sh.get_rect(center=(SCREEN_WIDTH // 2 + 2, 90)))
    surface.blit(lv_surf, lv_surf.get_rect(center=(SCREEN_WIDTH // 2, 88)))

    sub = font.render("Choose one perk", True, (160, 160, 180))
    surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 136)))

    # thin gold accent line
    pygame.draw.line(surface, (100, 80, 20),
                     (SCREEN_WIDTH // 2 - 200, 152),
                     (SCREEN_WIDTH // 2 + 200, 152), 1)

    card_rects = []
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    card_w, card_h = 248, 268
    gap     = 30
    start_x = SCREEN_WIDTH // 2 - (card_w * 3 + gap * 2) // 2

    for i, perk in enumerate(options):
        col      = PERK_COLORS[i % len(PERK_COLORS)]
        x        = start_x + i * (card_w + gap)
        y        = 178
        rect     = pygame.Rect(x, y, card_w, card_h)
        card_rects.append(rect)

        hovered  = rect.collidepoint(mouse_pos)
        bob      = int(math.sin(t * 2.0 + i * 1.2) * 4) if hovered else 0
        draw_y   = y - bob

        # card shadow
        sh_surf = pygame.Surface((card_w + 12, card_h + 12), pygame.SRCALPHA)
        sh_a    = 100 if hovered else 60
        pygame.draw.rect(sh_surf, (0, 0, 0, sh_a),
                         (0, 0, card_w + 12, card_h + 12), border_radius=14)
        surface.blit(sh_surf, (x - 6, draw_y + 6))

        # card body
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        bg_a      = 230 if hovered else 200
        pygame.draw.rect(card_surf, (14, 16, 28, bg_a),
                         (0, 0, card_w, card_h), border_radius=12)

        # top colour band
        band_h = 6
        pygame.draw.rect(card_surf, col,
                         (0, 0, card_w, band_h), border_radius=12)
        pygame.draw.rect(card_surf, (0, 0, 0), (0, band_h, card_w, 1))

        # border
        brd_w = 3 if hovered else 1
        brd_a = 220 if hovered else 120
        pygame.draw.rect(card_surf, (*col, brd_a),
                         (0, 0, card_w, card_h), brd_w, border_radius=12)

        surface.blit(card_surf, (x, draw_y))

        # icon placeholder – geometric shape per card
        icon_cx = x + card_w // 2
        icon_cy = draw_y + 70
        icon_r  = 28
        # pulsing ring
        pulse_r = icon_r + int(4 * math.sin(t * 3 + i))
        pygame.draw.circle(surface, (*col, 60), (icon_cx, icon_cy), pulse_r, 2)

        if i == 0:
            # diamond
            pts = [(icon_cx, icon_cy - icon_r),
                   (icon_cx + icon_r, icon_cy),
                   (icon_cx, icon_cy + icon_r),
                   (icon_cx - icon_r, icon_cy)]
            pygame.draw.polygon(surface, col, pts)
            pygame.draw.polygon(surface, (200, 200, 255), pts, 2)
        elif i == 1:
            # hexagon
            pts = [(icon_cx + int(icon_r * math.cos(math.pi / 3 * k - math.pi / 6)),
                    icon_cy + int(icon_r * math.sin(math.pi / 3 * k - math.pi / 6)))
                   for k in range(6)]
            pygame.draw.polygon(surface, col, pts)
            pygame.draw.polygon(surface, (220, 180, 255), pts, 2)
        else:
            # star
            pts = []
            for k in range(5):
                outer_a = math.pi / 2 + 2 * math.pi / 5 * k
                inner_a = outer_a + math.pi / 5
                pts.append((icon_cx + int(icon_r * math.cos(outer_a)),
                             icon_cy - int(icon_r * math.sin(outer_a))))
                pts.append((icon_cx + int((icon_r * 0.45) * math.cos(inner_a)),
                             icon_cy - int((icon_r * 0.45) * math.sin(inner_a))))
            pygame.draw.polygon(surface, col, pts)
            pygame.draw.polygon(surface, (255, 220, 100), pts, 2)

        # perk name
        name_surf = font.render(perk["name"], True, WHITE)
        surface.blit(name_surf,
                     name_surf.get_rect(center=(x + card_w // 2, draw_y + 128)))

        # perk description – wrap if long
        desc = perk["desc"]
        words      = desc.split()
        lines      = []
        cur        = ""
        max_w      = card_w - 24
        for word in words:
            test = (cur + " " + word).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)

        desc_col = (160, 170, 200)
        for li, line in enumerate(lines[:3]):
            ls = font.render(line, True, desc_col)
            surface.blit(ls,
                         ls.get_rect(center=(x + card_w // 2, draw_y + 160 + li * 22)))

        limit_text = f"{perk.get('taken', 0)}/{perk.get('limit', 3)} taken"
        limit_surf = font.render(limit_text, True, (190, 190, 210))
        surface.blit(limit_surf, limit_surf.get_rect(center=(x + card_w // 2, draw_y + card_h - 44)))

        # bottom hint
        hint_col  = col if hovered else (80, 80, 80)
        hint_text = "▶  Click to choose" if hovered else "hover to preview"
        hs        = font.render(hint_text, True, hint_col)
        surface.blit(hs, hs.get_rect(center=(x + card_w // 2, draw_y + card_h - 18)))

    return card_rects
