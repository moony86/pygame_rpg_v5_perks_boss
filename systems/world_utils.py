import math
import pygame

from settings import MAP_SIZE, INTERACTION_DISTANCE, AIM_ASSIST_RANGE
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
    screen.fill((8, 9, 14))
    world_rect = pygame.Rect(0, 0, MAP_SIZE, MAP_SIZE)

    if hub:
        bg = (28, 34, 34)
        grid_col = (48, 58, 58)
    elif room_type == RoomType.CURSE:
        bg = (33, 22, 42)
        grid_col = (58, 42, 70)
    elif room_type == RoomType.TREASURE:
        bg = (42, 34, 20)
        grid_col = (70, 58, 34)
    elif room_type == RoomType.ELITE:
        bg = (30, 28, 46)
        grid_col = (55, 50, 78)
    elif room_type == RoomType.SURVIVAL:
        bg = (35, 31, 24)
        grid_col = (62, 54, 40)
    else:
        bg = (24, 27, 36)
        grid_col = (45, 50, 64)

    pygame.draw.rect(screen, bg, camera.apply_rect(world_rect))

    grid_size = 120
    for x in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(
            screen,
            grid_col,
            camera.apply_pos(pygame.Vector2(x, 0)),
            camera.apply_pos(pygame.Vector2(x, MAP_SIZE)),
            1,
        )
    for y in range(0, MAP_SIZE + 1, grid_size):
        pygame.draw.line(
            screen,
            grid_col,
            camera.apply_pos(pygame.Vector2(0, y)),
            camera.apply_pos(pygame.Vector2(MAP_SIZE, y)),
            1,
        )
    edge_warning_rects = [
        pygame.Rect(0, 0, MAP_SIZE, 76),
        pygame.Rect(0, MAP_SIZE - 76, MAP_SIZE, 76),
        pygame.Rect(0, 0, 76, MAP_SIZE),
        pygame.Rect(MAP_SIZE - 76, 0, 76, MAP_SIZE),
    ]
    for edge_rect in edge_warning_rects:
        pygame.draw.rect(screen, (70, 18, 16), camera.apply_rect(edge_rect))

    border_rect = camera.apply_rect(world_rect)
    pygame.draw.rect(screen, (255, 54, 38), border_rect, 12)
    pygame.draw.rect(screen, (255, 210, 48), border_rect.inflate(-28, -28), 4)