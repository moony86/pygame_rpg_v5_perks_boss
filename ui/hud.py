import pygame
from systems.shooting_system import crit_stats
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, RED, YELLOW, CYAN, ROOMS_TO_BOSS


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


def _format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def vampire_hud_visible(player):
    return (
        getattr(player, "vampire_max_blood", 0) > 0
        or getattr(player, "vampire_blood", 0) > 0
        or getattr(player, "vampire_feast_unlocked", False)
        or getattr(player, "vampire_blood_moon_unlocked", False)
    )


def vampire_hud_rect():
    return pygame.Rect(12, 196, 242, 98)


def hud_occupied_rects(font=None):
    left = pygame.Rect(12, 12, 242, 172)
    right = pygame.Rect(SCREEN_WIDTH - 246 - 12, 12, 246, 148)
    minimap = pygame.Rect(SCREEN_WIDTH - 150 - 14, 14 + 280, 150, 150)
    wave_notice = pygame.Rect(0, 0, 500, 78)
    wave_notice.center = (SCREEN_WIDTH // 2, 210)
    message = pygame.Rect(22, SCREEN_HEIGHT - 38, SCREEN_WIDTH - 44, 26)
    timer_width = font.size("Run 00:00   Room 00:00")[0] if font else 190
    timer = pygame.Rect(SCREEN_WIDTH // 2 - timer_width // 2, 12, timer_width, 22)
    return {
        "left_stats": left,
        "right_room": right,
        "minimap": minimap,
        "wave_notice": wave_notice,
        "bottom_message": message,
        "top_timer": timer,
    }


def vampire_hud_data(player):
    max_blood = max(0, getattr(player, "vampire_max_blood", 0))
    blood = max(0, getattr(player, "vampire_blood", 0))
    threshold = max(1, getattr(player, "vampire_feast_threshold", 1))
    progress = max(0, getattr(player, "vampire_feast_progress", 0))
    moon_cd = max(0.0, getattr(player, "vampire_blood_moon_cooldown_timer", 0.0))
    moon_cd_max = max(0.01, getattr(player, "vampire_blood_moon_cooldown", 20.0))
    return {
        "blood_text": f"Blood {blood}/{max_blood}",
        "blood_ratio": blood / max(1, max_blood),
        "feast_text": f"Feast {progress}/{threshold}",
        "feast_ratio": progress / threshold,
        "feast_timer": max(0.0, getattr(player, "vampire_feast_timer", 0.0)),
        "moon_timer": max(0.0, getattr(player, "vampire_blood_moon_timer", 0.0)),
        "moon_cooldown": moon_cd,
        "moon_cooldown_ratio": 1.0 - min(1.0, moon_cd / moon_cd_max),
    }


def _draw_vampire_hud(surface, font, player):
    if not vampire_hud_visible(player):
        return None
    rect = vampire_hud_rect()
    data = vampire_hud_data(player)
    _panel(surface, rect.x, rect.y, rect.w, rect.h, alpha=215)
    _txt(surface, font, data["blood_text"], rect.x + 10, rect.y + 8, (245, 85, 110))
    _bar(surface, rect.x + 94, rect.y + 15, rect.w - 106, 8, data["blood_ratio"], (220, 35, 75), bg_col=(42, 14, 24))

    _txt(surface, font, data["feast_text"], rect.x + 10, rect.y + 34, (240, 150, 165))
    _bar(surface, rect.x + 94, rect.y + 41, rect.w - 106, 8, data["feast_ratio"], (210, 55, 95), bg_col=(42, 14, 24))

    if data["moon_timer"] > 0:
        state = f"Blood Moon {data['moon_timer']:.1f}s"
        color = (255, 75, 110)
        ratio = min(1.0, data["moon_timer"] / max(0.01, getattr(player, "vampire_blood_moon_duration", 9.0)))
    elif data["feast_timer"] > 0:
        state = f"Feast {data['feast_timer']:.1f}s"
        color = (245, 105, 135)
        ratio = min(1.0, data["feast_timer"] / max(0.01, getattr(player, "vampire_feast_duration", 6.0)))
    elif getattr(player, "vampire_blood_moon_unlocked", False):
        state = "Moon ready" if data["moon_cooldown"] <= 0 else f"Moon CD {data['moon_cooldown']:.1f}s"
        color = (185, 135, 165)
        ratio = data["moon_cooldown_ratio"]
    else:
        state = "Feast charging"
        color = (160, 130, 150)
        ratio = 0.0
    _txt(surface, font, state, rect.x + 10, rect.y + 62, color)
    _bar(surface, rect.x + 10, rect.y + 84, rect.w - 20, 6, ratio, color, bg_col=(42, 14, 24))
    return rect


def draw_hud(surface, font, player, room_number, room_kills, room_target,
             enemies_count, state_name, room_name, room_timer, objective_label="Kills", run_timer=0.0,
             room_total=ROOMS_TO_BOSS):
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
    _txt(surface, font, "Space Dash", lx + 10, ly + 145, dash_col)
    _bar(surface, lx + 118, ly + 151, lw - 130, 8, dash_ratio, dash_col)

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

    _txt(surface, font, f"Room {room_number}/{room_total}", rx + 12, ry + 42, (220, 225, 230))
    if room_name:
        _txt(surface, font, room_name, rx + 12, ry + 64, (185, 190, 230))

    objective_ratio = min(1.0, room_kills / max(1, room_target))
    _txt(surface, font, f"{objective_label} {room_kills}/{room_target}", rx + 12, ry + 88, (225, 225, 230))
    _bar(surface, rx + 12, ry + 112, rw - 24, 8, objective_ratio, (205, 70, 75))

    _txt(surface, font, f"Enemies {enemies_count}   Time {int(room_timer)}s", rx + 12, ry + 126, (155, 165, 185))

    timer_text = f"Run {_format_time(run_timer)}   Room {_format_time(room_timer)}"
    tx = SCREEN_WIDTH // 2 - font.size(timer_text)[0] // 2
    _txt(surface, font, timer_text, tx, 12, (220, 235, 245))
    _draw_vampire_hud(surface, font, player)
