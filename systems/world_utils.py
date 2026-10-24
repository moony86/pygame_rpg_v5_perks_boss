import math
from contextlib import nullcontext
import pygame

from settings import INTERACTION_DISTANCE, AIM_ASSIST_RANGE, SCREEN_WIDTH, SCREEN_HEIGHT
from systems.room_system import RoomType
from systems.room_bounds import current_room_bounds
from systems.environment_art import draw_environment


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
        if not enemy.alive or (getattr(enemy,'encounter',None) and enemy.encounter.airborne):
            continue
        d = distance_between(player.rect, enemy.rect)
        if d < best_d:
            best = enemy
            best_d = d
    return best


def draw_world_background(screen, camera, hub=False, room_type=None, profiler=None):
    section = profiler.section if profiler is not None else lambda _name: nullcontext()
    with section("background fill"):
        screen.fill((8, 9, 14))
    bounds = current_room_bounds()
    world_rect = bounds.rect
    if not hub and draw_environment(screen, camera, world_rect):
        return

    if hub:
        bg = (24, 36, 34)
        grid_col = (48, 68, 64)
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

    with section("floor draw"):
        pygame.draw.rect(screen, bg, camera.apply_rect(world_rect))

    grid_size = 120
    visible = pygame.Rect(
        int(camera.offset.x),
        int(camera.offset.y),
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
    ).clip(world_rect)
    start_x = max(bounds.left, (visible.left // grid_size) * grid_size)
    end_x = min(bounds.right, ((visible.right + grid_size - 1) // grid_size) * grid_size)
    start_y = max(bounds.top, (visible.top // grid_size) * grid_size)
    end_y = min(bounds.bottom, ((visible.bottom + grid_size - 1) // grid_size) * grid_size)

    with section("world grid draw"):
        for x in range(start_x, end_x + 1, grid_size):
            pygame.draw.line(
                screen,
                grid_col,
                camera.apply_pos(pygame.Vector2(x, visible.top)),
                camera.apply_pos(pygame.Vector2(x, visible.bottom)),
                1,
            )
        for y in range(start_y, end_y + 1, grid_size):
            pygame.draw.line(
                screen,
                grid_col,
                camera.apply_pos(pygame.Vector2(visible.left, y)),
                camera.apply_pos(pygame.Vector2(visible.right, y)),
                1,
            )
    if hub:
        with section("hub safe-zone draw"):
            center = camera.apply_pos(pygame.Vector2(bounds.center))
            cx, cy = round(center.x), round(center.y)
            pygame.draw.circle(screen, (55, 92, 80), (cx, cy), 310, 3)
            pygame.draw.circle(screen, (76, 122, 105), (cx, cy), 150, 2)
            for angle in range(0, 360, 45):
                spoke = pygame.Vector2(260, 0).rotate(angle)
                end = pygame.Vector2(cx, cy) + spoke
                pygame.draw.line(screen, (45, 76, 68), (cx, cy), (round(end.x), round(end.y)), 1)
    draw_edge_warning = bounds.width > SCREEN_WIDTH or bounds.height > SCREEN_HEIGHT
    edge_warning_rects = [
        pygame.Rect(bounds.left, bounds.top, bounds.width, 76),
        pygame.Rect(bounds.left, bounds.bottom - 76, bounds.width, 76),
        pygame.Rect(bounds.left, bounds.top, 76, bounds.height),
        pygame.Rect(bounds.right - 76, bounds.top, 76, bounds.height),
    ] if draw_edge_warning else []
    with section("world edge draw"):
        for edge_rect in edge_warning_rects:
            if edge_rect.colliderect(visible):
                pygame.draw.rect(screen, (70, 18, 16), camera.apply_rect(edge_rect))

        border_rect = camera.apply_rect(world_rect)
        border_outer = (58, 108, 94) if hub else (255, 54, 38)
        border_inner = (105, 178, 150) if hub else (255, 210, 48)
        pygame.draw.rect(screen, border_outer, border_rect, 12)
        pygame.draw.rect(screen, border_inner, border_rect.inflate(-28, -28), 4)
