import pygame

from settings import (
    AIM_ASSIST_RADIUS,
    AIM_ASSIST_STRENGTH,
    AIM_ASSIST_RANGE,
)


def nearest_enemy(player, enemies, max_range=AIM_ASSIST_RANGE):
    best = None
    best_d = max_range

    for enemy in enemies:
        if not enemy.alive:
            continue

        d = player.rect.centerx - enemy.rect.centerx
        e = player.rect.centery - enemy.rect.centery
        distance = (d * d + e * e) ** 0.5

        if distance < best_d:
            best = enemy
            best_d = distance

    return best


def update_player_aim(player, enemies, camera, mouse_pos=None):
    target = nearest_enemy(player, enemies, AIM_ASSIST_RANGE)
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()
    mouse_world = camera.screen_to_world(mouse_pos)
    aim_target = mouse_world

    if target:
        target_pos = pygame.Vector2(target.rect.center)
        if target_pos.distance_to(mouse_world) <= AIM_ASSIST_RADIUS:
            aim_target = mouse_world.lerp(target_pos, AIM_ASSIST_STRENGTH)

    player.update_aim(aim_target)
