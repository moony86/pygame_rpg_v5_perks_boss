import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, DARK_GRAY, RED, GREEN, YELLOW, GOLD, CYAN, ROOMS_TO_BOSS
from systems.upgrade_system import UPGRADES


def draw_text(surface, font, text, x, y, color=WHITE, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)


def draw_bar(surface, x, y, w, h, ratio, fg, bg=(70, 70, 70)):
    ratio = max(0, min(1, ratio))
    pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=4)
    pygame.draw.rect(surface, fg, (x, y, int(w * ratio), h), border_radius=4)
    pygame.draw.rect(surface, BLACK, (x, y, w, h), 2, border_radius=4)


def draw_hud(surface, font, player, room_number, room_kills, room_target, enemies_count, state_name, room_name, room_timer):
    padding = 14
    draw_text(surface, font, f"HP {player.health}/{player.max_health}", padding, 10, BLACK)
    draw_bar(surface, padding, 38, 220, 18, player.health / player.max_health, RED)

    draw_text(surface, font, f"LVL {player.level}", padding, 64, BLACK)
    draw_bar(surface, padding + 70, 68, 150, 14, player.xp / player.xp_to_next, YELLOW)

    draw_text(surface, font, f"Gold: {player.gold}", padding, 90, BLACK)
    draw_text(surface, font, f"Weapon: DMG+{player.damage_bonus} Shots {player.projectile_count} Pierce {player.pierce}", padding, 116, BLACK)
    draw_text(surface, font, f"Crit {int(player.crit_chance*100)}% | FR x{player.fire_rate_multiplier:.2f}", padding, 142, BLACK)

    dash_ratio = 1 if player.dash_cooldown_timer <= 0 else 1 - player.dash_cooldown_timer / 4.5
    draw_text(surface, font, "Q Dash", padding, 168, BLACK)
    draw_bar(surface, padding + 80, 172, 140, 12, dash_ratio, CYAN)

    draw_text(surface, font, f"State: {state_name}", SCREEN_WIDTH - 240, 10, BLACK)
    draw_text(surface, font, f"Room: {room_number}/{ROOMS_TO_BOSS} {room_name}", SCREEN_WIDTH - 240, 36, BLACK)
    draw_text(surface, font, f"Kills: {room_kills}/{room_target}", SCREEN_WIDTH - 240, 62, BLACK)
    draw_text(surface, font, f"Timer: {int(room_timer)}s", SCREEN_WIDTH - 240, 88, BLACK)
    draw_text(surface, font, f"Enemies: {enemies_count}", SCREEN_WIDTH - 240, 114, BLACK)
    draw_text(surface, font, "Aim: MANUAL + ASSIST", SCREEN_WIDTH - 240, 140, BLACK)


def draw_shop_hint(surface, font, npc_role):
    options = UPGRADES.get(npc_role, [])
    if not options:
        return
    x, y = 58, 365
    pygame.draw.rect(surface, (0, 0, 0), (45, 350, 470, 95), border_radius=8)
    pygame.draw.rect(surface, WHITE, (45, 350, 470, 95), 2, border_radius=8)
    for i, (name, cost, key) in enumerate(options, start=1):
        draw_text(surface, font, f"{i}) {name} - {cost} gold", x, y + (i - 1) * 27, WHITE)


def draw_perk_select(surface, big_font, font, options):
    surface.fill(DARK_GRAY)
    draw_text(surface, big_font, "LEVEL UP", SCREEN_WIDTH // 2, 88, GOLD, center=True)
    draw_text(surface, font, "Choose one perk", SCREEN_WIDTH // 2, 135, WHITE, center=True)

    card_w, card_h = 250, 260
    gap = 35
    start_x = SCREEN_WIDTH // 2 - (card_w * 3 + gap * 2) // 2

    for i, perk in enumerate(options):
        x = start_x + i * (card_w + gap)
        y = 210
        rect = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(surface, (32, 32, 32), rect, border_radius=12)
        pygame.draw.rect(surface, GOLD, rect, 3, border_radius=12)

        draw_text(surface, font, f"{i+1}", x + card_w // 2, y + 35, GOLD, center=True)
        draw_text(surface, font, perk["name"], x + card_w // 2, y + 95, WHITE, center=True)
        draw_text(surface, font, perk["desc"], x + card_w // 2, y + 155, WHITE, center=True)
        draw_text(surface, font, f"Press {i+1}", x + card_w // 2, y + 220, GREEN, center=True)


def draw_menu(surface, big_font, font):
    surface.fill(DARK_GRAY)
    draw_text(surface, big_font, "BLUE CUBE v5", SCREEN_WIDTH // 2, 105, WHITE, center=True)
    draw_text(surface, font, "Perk Cards + Room Types + Special Ability + Boss Rework", SCREEN_WIDTH // 2, 172, WHITE, center=True)
    draw_text(surface, font, "Manual aim only. Aim Assist stays. Auto Aim removed.", SCREEN_WIDTH // 2, 215, WHITE, center=True)
    draw_text(surface, font, "Q Dash | Hold Left Click Shoot | 1/2/3 choose upgrades", SCREEN_WIDTH // 2, 255, WHITE, center=True)
    draw_text(surface, font, "Press Enter to Start", SCREEN_WIDTH // 2, 355, GREEN, center=True)


def draw_end_screen(surface, big_font, font, title, subtitle):
    surface.fill(DARK_GRAY)
    draw_text(surface, big_font, title, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70, WHITE, center=True)
    draw_text(surface, font, subtitle, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, WHITE, center=True)
    draw_text(surface, font, "Press Enter to Restart | Esc to Quit", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, GREEN, center=True)


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
