import pygame
from systems.shooting_system import crit_stats
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, RED, YELLOW, CYAN, ROOMS_TO_BOSS, DASH_COOLDOWN, PLAYER_SKILL_COOLDOWN
from ui.common import fitted_text


def _txt(surface, font, text, x, y, color, shadow=True, max_width=None):
    if shadow:
        s = fitted_text(font, text, (0, 0, 0), max_width) if max_width else font.render(text, True, (0, 0, 0))
        surface.blit(s, (x + 1, y + 1))
    r = fitted_text(font, text, color, max_width) if max_width else font.render(text, True, color)
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


def _segmented_dash_bar(surface, x, y, w, h, player):
    max_charges = max(1, int(getattr(player, "max_dash_charges", 1)))
    charges = max(0.0, min(float(max_charges), float(getattr(player, "dash_charges", max_charges))))
    refill = max(0.0, float(getattr(player, "dash_charge_refill_timer", 0.0)))
    refill_total = 1.35
    gap = 4
    seg_w = max(1, (w - gap * (max_charges - 1)) // max_charges)
    for index in range(max_charges):
        sx = x + index * (seg_w + gap)
        ratio = max(0.0, min(1.0, charges - index))
        if ratio <= 0.0 and index <= int(charges) and charges < max_charges:
            ratio = 1.0 - min(1.0, refill / refill_total)
        col = CYAN if ratio >= 1.0 else (45, 125, 165)
        _bar(surface, sx, y, seg_w, h, ratio, col)


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
    return pygame.Rect(12, 208, 242, 98)


def hud_occupied_rects(font=None):
    details = pygame.key.get_pressed()[pygame.K_TAB]
    left = pygame.Rect(12, 12, 360 if details else 290, 188 if details else 140)
    right = pygame.Rect(SCREEN_WIDTH - 300, 12, 288, 148 if details else 104)
    minimap = pygame.Rect(SCREEN_WIDTH - 150 - 14, 14 + 280, 150, 150) if details else pygame.Rect(0,0,0,0)
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
    if not pygame.key.get_pressed()[pygame.K_TAB]:
        _draw_compact_hud(surface, font, player, room_number, room_kills,
                          room_target, state_name, run_timer, room_total)
        return
    pad = 12

    lx, ly = pad, pad
    details = pygame.key.get_pressed()[pygame.K_TAB]
    lw, lh = (360, 188) if details else (242, 144)
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
    if details:
        _txt(surface, font, f"DMG +{player.damage_bonus}  Shots {player.projectile_count}  Pierce {player.pierce}", lx + 10, ly + 100, stat_col, max_width=lw - 20)
    _, crit_multiplier = crit_stats(player)
    if details:
        _txt(surface, font, f"Crit {int(player.crit_chance * 100)}% x{crit_multiplier:.2f}  FR x{player.fire_rate_multiplier:.2f}", lx + 10, ly + 122, stat_col, max_width=lw - 20)

    skill = getattr(player, "active_skill", "dash")
    if skill == "dash" and getattr(player, "max_dash_charges", 1) > 1:
        dash_col = CYAN if getattr(player, "dash_charges", 0) > 0 else (45, 125, 165)
        _txt(surface, font, "Space: Ninja Dash", lx + 10, ly + lh - 38, dash_col)
        _segmented_dash_bar(surface, lx + 10, ly + lh - 11, lw - 20, 6, player)
    else:
        remaining = getattr(player, "skill_cooldown_timer", 0.0)
        total = PLAYER_SKILL_COOLDOWN * getattr(player, "skill_cooldown_multiplier", 1.0)
        if skill == "dash":
            remaining = max(remaining, player.dash_cooldown_timer)
            total = max(total, DASH_COOLDOWN)
        dash_ratio = max(0.0, min(1.0, 1 - remaining / max(0.01, total)))
        dash_col = CYAN if dash_ratio >= 1.0 else (45, 125, 165)
        _txt(surface, font, f"Space: {skill.title()}", lx + 10, ly + lh - 38, dash_col, max_width=lw - 20)
        _bar(surface, lx + 10, ly + lh - 11, lw - 20, 6, dash_ratio, dash_col)

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

    if state_name == "HUB":
        _txt(surface, font, "Stage 1", rx + 12, ry + 42, (220, 225, 230))
        _txt(surface, font, f"Rooms {max(0, min(room_number, room_total))}/{room_total}", rx + 12, ry + 64, (185, 190, 230))
    else:
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


def _draw_compact_hud(surface, font, player, room_number, kills, target, state, run_time, total):
    """Gameplay first; expanded statistics and route remain available on Tab."""
    ink, muted, danger, accent, gold = (235,240,248), (160,180,200), (240,70,90), (65,220,245), (245,202,80)
    x, y, width = 22, 20, 270
    from ui.cube_health import draw as draw_cube_health
    from systems.object_catalog import sprite
    draw_cube_health(surface,player,x,y)
    crystal=sprite('visual_xp_tier_1',size=(22,26))
    coin=sprite('visual_gold',size=(24,24),frame=int(player.anim_time*10))
    if crystal is not None:
        surface.blit(crystal,(x,y+45))
    if coin is not None:
        surface.blit(coin,(x+153,y+46))
    _txt(surface, font, str(player.level), x+31, y+48, ink)
    _txt(surface, font, str(player.gold), x+185, y+48, gold)
    _bar(surface, x, y+76, width, 4, player.xp/max(1,player.xp_to_next), (150,125,245))
    skill = getattr(player,'active_skill','dash')
    dash_icon=sprite('dash_refresh',size=(25,28))
    if dash_icon is not None:
        surface.blit(dash_icon,(x,y+91))
    _txt(surface, font, '[Space] '+('Parry / Dash' if getattr(player,'ninja_dash_charges_enabled',False) else skill.title()), x+33, y+91, accent)
    if skill=='dash' and getattr(player,'max_dash_charges',1)>1:
        _segmented_dash_bar(surface,x,y+120,width,5,player)
    else:
        remaining = getattr(player,'skill_cooldown_timer',0.)
        duration = PLAYER_SKILL_COOLDOWN*getattr(player,'skill_cooldown_multiplier',1.)
        if skill=='dash':
            remaining=max(remaining,player.dash_cooldown_timer)
            duration=max(duration,DASH_COOLDOWN)
        _bar(surface,x,y+120,width,5,1-remaining/max(.01,duration),accent)
    # Reserve enough space for the labels; never draw bars through their text.
    if vampire_hud_visible(player):
        data=vampire_hud_data(player)
        _txt(surface,font,data['blood_text'],x,y+144,(245,110,140))
        _bar(surface,x,y+172,width,5,data['blood_ratio'],danger)
        if getattr(player,'vampire_feast_unlocked',False):
            _txt(surface,font,data['feast_text'],x,y+186,muted)
            _bar(surface,x,y+214,width,5,data['feast_ratio'],(195,85,145))
    text = 'HUB' if state=='HUB' else f'Room {room_number}/{total}  -  WARDEN' if state=='BOSS' else f'Room {room_number}/{total}  -  Kills {kills}/{target}'
    right=SCREEN_WIDTH-22-font.size(text)[0]
    _txt(surface,font,text,right,20,ink)
    clock=_format_time(run_time)
    _txt(surface,font,clock,SCREEN_WIDTH-22-font.size(clock)[0],50,muted)
    _txt(surface,font,'[Tab] Stats / map',SCREEN_WIDTH-220,82,muted)
    # The temporal overlay owns the stopwatch countdown; do not duplicate it here.
