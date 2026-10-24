import random
import pygame

from systems.room_system import RoomType
from systems.asset_loader import load_image
from systems.room_bounds import current_room_bounds
from systems.environment_art import draw_cover
from systems.environment_art import draw_cover


_BLOCK_TILE = None
_BOX_TILE = None


def generate_room_obstacles(room_number, room_type):
    if room_type in (RoomType.TREASURE,):
        return []

    rng = random.Random(room_number * 1009 + getattr(room_type, "value", 0) * 97)
    bounds = current_room_bounds()
    center_clear = pygame.Rect(bounds.centerx - 260, bounds.centery - 220, 520, 440)
    exit_clear = pygame.Rect(bounds.centerx - 260, bounds.centery - 350, 520, 240)
    obstacles = []
    count = 3 + min(4, room_number // 2)

    for _ in range(count * 4):
        if len(obstacles) >= count:
            break
        w = rng.choice((120, 150, 190, 230))
        h = rng.choice((70, 90, 120, 150))
        x = rng.randint(bounds.left + 260, bounds.right - 260 - w)
        y = rng.randint(bounds.top + 260, bounds.bottom - 260 - h)
        rect = pygame.Rect(x, y, w, h)
        if rect.colliderect(center_clear) or rect.colliderect(exit_clear):
            continue
        if any(rect.inflate(90, 90).colliderect(other) for other in obstacles):
            continue
        obstacles.append(rect)

    return obstacles


def draw_room_obstacles(surface, camera, obstacles):
    global _BLOCK_TILE, _BOX_TILE
    if _BLOCK_TILE is None:
        _BLOCK_TILE = load_image("block.png")
    if _BOX_TILE is None:
        _BOX_TILE = load_image("box.png")

    for rect in obstacles:
        sr = camera.apply_rect(rect)
        if draw_cover(surface, sr):
            continue
        if draw_cover(surface, sr):
            continue
        tile = _BOX_TILE if rect.width >= rect.height else _BLOCK_TILE
        if tile is None:
            pygame.draw.rect(surface, (38, 43, 54), sr, border_radius=5)
            pygame.draw.rect(surface, (92, 105, 125), sr, 2, border_radius=5)
            pygame.draw.line(surface, (26, 29, 38), sr.topleft, sr.bottomright, 1)
            continue

        _draw_tiled_obstacle(surface, sr, tile)


def _draw_tiled_obstacle(surface, screen_rect, tile):
    clip = surface.get_clip()
    surface.set_clip(screen_rect)
    for y in range(screen_rect.top, screen_rect.bottom, tile.get_height()):
        for x in range(screen_rect.left, screen_rect.right, tile.get_width()):
            surface.blit(tile, (x, y))
    surface.set_clip(clip)
    pygame.draw.rect(surface, (24, 28, 36), screen_rect, 2, border_radius=4)
