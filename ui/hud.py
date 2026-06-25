import pygame
from systems.shooting_system import crit_stats
from settings import SCREEN_WIDTH, BLACK, RED, YELLOW, CYAN, ROOMS_TO_BOSS


def _txt(surface, font, text, x, y, color, shadow=True):
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        surface.blit(s, (x + 1, y + 1))
    r = font.render(text, True, color)
    surface.blit(r, (x, y))


def _panel(surface, x, y, w, h, alpha=210):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((10, 12, 24, alpha))
    pygame.draw.rect(s, (75, 105, 155, 160), (0, 0, w, h), 1, border_radius=6)
    pygame.draw.rect(s, (80, 170, 255, 120), (0, 0, w, 3), border_radius=6)
    surface.blit(s, (x, y))


def _bar(surface, x, y, w, h, ratio, fill_col, bg_col=(28, 30, 42)):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, bg_col, (x, y, w, h), border_radius=h)
    fill_w = int(w * ratio)
    if fill_w > 0:
        pygame.draw.rect(surface, fill_col, (x, y, fill_w, h), border_radius=h)
    pygame.draw.rect(surface, (90, 115, 165), (x, y, w, h), 1, border_radius=h)


def draw_hud(surface, font, player, room_number, room_kills, room_target,
             enemies_count, state_name, room_name, room_timer, objective_label="Kills"):
    pad = 12

    lx, ly = pad, pad
    lw, lh = 242, 172
    _panel(surface, lx, ly, lw, lh)

    hp_ratio = player.health / max(1, player.max_health)
    hp_col = (225, 55, 65) if hp_ratio > 0.3 else (255, 95, 95)
    _txt(surface, font, f"HP {player.health}/{player.max_health}", lx + 10, ly + 8, (235, 110, 115))
    _bar(surface, lx + 10, ly + 32, lw - 20, 10, hp_ratio, hp_col)

    xp_ratio = player.xp / max(1, player.xp_to_next)
    _txt(surface, font, f"LVL {player.level}", lx + 10, ly + 51, (235, 220, 80))
    _bar(surface, lx + 86, ly + 56, lw - 98, 8, xp_ratio, (220, 215, 55))

    _txt(surface, font, f"Gold {player.gold}", lx + 10, ly + 74, (235, 185, 55))
    stat_col = (175, 215, 245)
    _txt(surface, font, f"DMG +{player.damage_bonus}  Shots {player.projectile_count}  Pierce {player.pierce}", lx + 10, ly + 100, stat_col)
    _, crit_multiplier = crit_stats(player)
    _txt(surface, font, f"Crit {int(player.crit_chance * 100)}% x{crit_multiplier:.2f}  FR x{player.fire_rate_multiplier:.2f}", lx + 10, ly + 122, stat_col)

    dash_ratio = 1.0 if player.dash_cooldown_timer <= 0 else 1 - player.dash_cooldown_timer / 4.5
    dash_col = CYAN if dash_ratio >= 1.0 else (45, 125, 165)
    _txt(surface, font, "Q Dash", lx + 10, ly + 145, dash_col)
    _bar(surface, lx + 82, ly + 151, lw - 94, 8, dash_ratio, dash_col)

    rw, rh = 246, 148
    rx = SCREEN_WIDTH - rw - pad
    ry = pad
    _panel(surface, rx, ry, rw, rh)

    room_col = {
        "ROOM": (100, 180, 255),
        "BOSS": (255, 125, 45),
        "HUB": (90, 225, 135),
    }.get(state_name, (215, 220, 230))

    title = state_name
    _txt(surface, font, title, rx + rw // 2 - font.size(title)[0] // 2, ry + 8, room_col)
    pygame.draw.line(surface, room_col, (rx + 12, ry + 32), (rx + rw - 12, ry + 32), 1)

    _txt(surface, font, f"Room {room_number}/{ROOMS_TO_BOSS}", rx + 12, ry + 42, (220, 225, 230))
    if room_name:
        _txt(surface, font, room_name, rx + 12, ry + 64, (185, 190, 230))

    objective_ratio = min(1.0, room_kills / max(1, room_target))
    _txt(surface, font, f"{objective_label} {room_kills}/{room_target}", rx + 12, ry + 88, (225, 225, 230))
    _bar(surface, rx + 12, ry + 112, rw - 24, 8, objective_ratio, (205, 70, 75))

    _txt(surface, font, f"Enemies {enemies_count}   Time {int(room_timer)}s", rx + 12, ry + 126, (155, 165, 185))