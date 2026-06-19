from settings import (
    SCREEN_WIDTH,
    BLACK,
    RED,
    YELLOW,
    CYAN,
    ROOMS_TO_BOSS,
)
from ui.common import draw_text, draw_bar

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

