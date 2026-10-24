import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_GRAY, WHITE, GOLD, GREEN
from systems.asset_loader import load_image
from systems.object_catalog import sprite as visual_sprite, definition as visual_definition

from ui.common import draw_text, wrap_text, fitted_text


# perk rarity color palette
PERK_COLORS = [
    (80,  160, 255),   # blue  – card 0
    (180, 80,  255),   # purple – card 1
    (255, 160, 40),    # gold   – card 2
]


BUILD_COLORS = {
    "GUNSLINGER": (90, 170, 255),
    "ENGINEER": (90, 220, 210),
    "NINJA": (190, 120, 255),
    "VAMPIRE": (240, 70, 105),
    "SHARED": (225, 190, 85),
}


# Space is reserved independently for art, complete descriptions and synergy.
CARD_ART_SIZE = 96
_card_art_cache = {}


def get_card_art(key):
    style = visual_definition('card_style')
    config = visual_definition('card_'+key)
    size = tuple(min(128,round(config[field]*style['art_size']/96)) for field in ('width','height'))
    art = visual_sprite('card_'+key,size,frame=int(pygame.time.get_ticks()/1000*config['fps']))
    if art is not None:
        return art
    if key not in _card_art_cache:
        _card_art_cache[key] = load_image(f"cards/{key}.png", (CARD_ART_SIZE, CARD_ART_SIZE))
    return _card_art_cache[key]


def _build_badge_text(perk):
    label = perk.get("build_label") or perk.get("build", "Shared/Utility")
    label = "SHARED" if label == "Shared/Utility" else str(label).upper()
    hybrids = [str(build).upper() for build in perk.get("hybrid_builds", [])]
    return label, bool(hybrids)


def draw_perk_select(surface, big_font, font, options, mouse_pos=None, reroll_labels=None, player=None):
    t = pygame.time.get_ticks() / 1000.0
    style = visual_definition('card_style')
    palette = {key.upper():tuple(pygame.Color(style[key]))[:3] for key in ('gunslinger','engineer','ninja','vampire','shared')}

    # dark vignette bg
    surface.fill((6, 6, 14))

    # header
    lv_surf  = big_font.render("LEVEL UP", True, GOLD)
    lv_sh    = big_font.render("LEVEL UP", True, (80, 60, 0))
    surface.blit(lv_sh, lv_sh.get_rect(center=(SCREEN_WIDTH // 2 + 2, 90)))
    surface.blit(lv_surf, lv_surf.get_rect(center=(SCREEN_WIDTH // 2, 88)))

    sub = font.render("Choose one upgrade for this run  |  Click or press 1 / 2 / 3", True, (190, 195, 215))
    surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 136)))
    if player is not None:
        if getattr(player, "starter_choice_active", False):
            status_text = "First upgrade: choose a playstyle. All builds use the Pistol in this demo."
        else:
            status_text = f"Rerolls: {getattr(player, 'reroll_tokens', 0)} token(s) | Gold reroll {getattr(player, 'gold', 0)}g"
        status = font.render(status_text, True, (130, 145, 175))
        surface.blit(status, status.get_rect(center=(SCREEN_WIDTH // 2, 160)))

    # thin gold accent line
    pygame.draw.line(surface, (100, 80, 20),
                     (SCREEN_WIDTH // 2 - 200, 174),
                     (SCREEN_WIDTH // 2 + 200, 174), 1)

    card_rects = []
    reroll_rects = []
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    card_w = style['width']
    max_lines = max((len(wrap_text(font, perk["desc"], card_w - 88)) for perk in options), default=1)
    card_h = max(style['height'], style['desc_y'] + max_lines * style['line_height'] + 130)
    gap     = 30
    start_x = SCREEN_WIDTH // 2 - (card_w * 3 + gap * 2) // 2

    for i, perk in enumerate(options):
        build_label, hybrid = _build_badge_text(perk)
        col      = palette.get(build_label, (190, 190, 210))
        x        = start_x + i * (card_w + gap)
        y        = 190
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
        pygame.draw.rect(card_surf, pygame.Color(style['body']),
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
        frame = visual_sprite('card_style',(card_w,card_h))
        if frame is not None:
            if perk.get('legendary',False):
                frame = pygame.transform.grayscale(frame)
                frame.fill(pygame.Color(style['legendary']),special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(frame,(x,draw_y))
            pygame.draw.rect(surface,pygame.Color(style['body']),
                (x+40,draw_y+40,card_w-80,card_h-80),border_radius=8)

        build_label, hybrid = _build_badge_text(perk)
        badge_col = palette.get(build_label, (190, 190, 210))
        badge_text = build_label + (" +HYBRID" if hybrid else "")
        badge = fitted_text(font, badge_text, (8, 10, 18), card_w - 128)
        badge_rect = pygame.Rect(x + 44, draw_y + 46, min(card_w-112,max(86, badge.get_width() + 16)), 24)
        pygame.draw.rect(surface, badge_col, badge_rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), badge_rect, 1, border_radius=5)
        surface.blit(badge, badge.get_rect(center=badge_rect.center))

        # Card art replaces the geometric placeholder when an asset exists.
        # Keep the original placeholder as a safe fallback for missing cards.
        icon_cx = x + card_w // 2
        icon_cy = draw_y + style['art_y']
        icon_r  = 28
        card_art = get_card_art(perk["key"])
        if card_art is not None:
            art_rect = card_art.get_rect(center=(icon_cx, icon_cy))
            surface.blit(card_art, art_rect)
        else:
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
        name_surf = fitted_text(font, perk["name"], pygame.Color(style['text']), card_w - 88)
        surface.blit(name_surf,
                     name_surf.get_rect(center=(x + card_w // 2, draw_y + style['title_y'])))

        # perk description – wrap if long
        desc = perk["desc"]
        desc_col = pygame.Color(style['description'])
        lines = wrap_text(font, desc, card_w - 88)
        for li, line in enumerate(lines):
            ls = font.render(line, True, desc_col)
            surface.blit(ls,
                         ls.get_rect(center=(x + card_w // 2, draw_y + style['desc_y'] + li * style['line_height'])))

        synergy = perk.get("synergy", "")
        limit_y = draw_y + card_h - 44
        if synergy:
            badge = fitted_text(font, synergy, (255, 220, 90), card_w - 88)
            badge_rect = badge.get_rect(center=(x + card_w // 2, draw_y + card_h - 90))
            badge_bg = pygame.Surface((badge_rect.width + 14, badge_rect.height + 6), pygame.SRCALPHA)
            badge_bg.fill((70, 55, 10, 210))
            badge_bg_rect = badge_bg.get_rect(center=badge_rect.center)
            surface.blit(badge_bg, badge_bg_rect)
            surface.blit(badge, badge_rect)
            limit_y = draw_y + card_h - 64

        limit_y = draw_y + card_h - 64
        limit_text = f"{perk.get('taken', 0)}/{perk.get('limit', 3)} taken"
        limit_surf = font.render(limit_text, True, (190, 190, 210))
        surface.blit(limit_surf, limit_surf.get_rect(center=(x + card_w // 2, limit_y)))

        # bottom hint
        hint_col  = col if hovered else (170, 185, 205)
        key_label = font.render(str(i+1),True,hint_col)
        surface.blit(key_label,key_label.get_rect(center=(x+card_w-52,draw_y+58)))

        label = (reroll_labels or ["NO REROLL"] * len(options))[i]
        button_w, button_h = 190, 28
        button_rect = pygame.Rect(x + (card_w - button_w) // 2, y + card_h + 12, button_w, button_h)
        reroll_rects.append(button_rect)
        enabled = label != "NO REROLL"
        button_hovered = button_rect.collidepoint(mouse_pos)
        button_bg = (45, 52, 78) if enabled else (28, 30, 42)
        if enabled and button_hovered:
            button_bg = (70, 84, 126)
        button_border = col if enabled else (80, 80, 90)
        pygame.draw.rect(surface, button_bg, button_rect, border_radius=6)
        pygame.draw.rect(surface, button_border, button_rect, 1, border_radius=6)
        label_col = (235, 240, 255) if enabled else (105, 108, 122)
        label_surf = font.render(label, True, label_col)
        surface.blit(label_surf, label_surf.get_rect(center=button_rect.center))

    return card_rects, reroll_rects
