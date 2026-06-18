import math
import pygame

from settings import (
    MAP_SIZE,
    GRAY,
    WHITE,
    LIGHT_GRAY,
    INTERACTION_DISTANCE,
    AIM_ASSIST_RANGE,
)

from systems.room_system import RoomType


def rotate_vector(vec, degrees):
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    return pygame.Vector2(
        vec.x * cos_a - vec.y * sin_a,
        vec.x * sin_a + vec.y * cos_a,
    )


def distance_between(rect_a, rect_b):
    ax, ay = rect_a.center
    bx, by = rect_b.center
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def nearest_npc(player, npcs):
    best = None
    best_d = INTERACTION_DISTANCE

    for npc in npcs:
        d = distance_between(player.rect, npc.rect)
        if d < best_d:
            best = npc
            best_d = d

    return best


def nearest_enemy(player, enemies, max_range=AIM_ASSIST_RANGE):
    best = None
    best_d = max_range

    for enemy in enemies:
        if not enemy.alive:
            continue

        d = distance_between(player.rect, enemy.rect)
        if d < best_d:
            best = enemy
            best_d = d

    return best


def draw_world_background(screen, camera, hub=False, room_type=None):
    screen.fill(GRAY)

    world_rect = pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE)

    if hub:
        bg = (245, 239, 220)
    elif room_type == RoomType.CURSE:
        bg = (235, 218, 235)
    elif room_type == RoomType.TREASURE:
        bg = (248, 239, 200)
    elif room_type == RoomType.ELITE:
        bg = (235, 230, 245)
    else:
        bg = WHITE

    pygame.draw.rect(screen, bg, camera.apply_rect(world_rect))

    grid_size = 120

    for x in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(
            screen,
            LIGHT_GRAY,
            camera.apply_pos(pygame.Vector2(x, 0)),
            camera.apply_pos(pygame.Vector2(x, MAP_SIZE)),
            1,
        )

    for y in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(
            screen,
            LIGHT_GRAY,
            camera.apply_pos(pygame.Vector2(0, y)),
            camera.apply_pos(pygame.Vector2(MAP_SIZE, y)),
            1,
        )
