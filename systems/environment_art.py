"""Image-backed environment renderer shared with the desktop level editor."""
import pygame
from systems.asset_loader import load_image

_tiles = None
_floor_cache = {}
_cover_cache = {}


def tiles():
    global _tiles
    if _tiles is None:
        atlas = load_image("environment/cube_dungeon_atlas_v1.png")
        if atlas is None:
            return None
        w, h = atlas.get_width() // 2, atlas.get_height() // 2
        _tiles = [atlas.subsurface((x * w, y * h, w, h)).copy()
                  for y in range(2) for x in range(2)]
    return _tiles


def cover_image(size):
    size = (max(16, int(size[0])), max(16, int(size[1])))
    if size in _cover_cache:
        return _cover_cache[size]
    art = tiles()
    if not art:
        return None
    source = pygame.transform.scale(art[1], (160, 160))
    # Nine-slice keeps the bevel sharp instead of repeating tiny box sprites.
    result = pygame.Surface(size, pygame.SRCALPHA)
    corner = min(22, size[0] // 3, size[1] // 3)
    src = (0, 22, 138, 160)
    xs, ys = (0, corner, size[0] - corner, size[0]), (0, corner, size[1] - corner, size[1])
    for row in range(3):
        for col in range(3):
            patch = source.subsurface((src[col], src[row], src[col+1]-src[col], src[row+1]-src[row]))
            result.blit(pygame.transform.scale(patch, (xs[col+1]-xs[col], ys[row+1]-ys[row])), (xs[col], ys[row]))
    if len(_cover_cache) > 256:
        _cover_cache.clear()
    _cover_cache[size] = result
    return result


def floor_image(size):
    size = tuple(size)
    if size in _floor_cache:
        return _floor_cache[size]
    art = tiles()
    if not art:
        return None
    tile = pygame.transform.scale(art[0], (320, 320))
    tile.fill((150, 158, 172), special_flags=pygame.BLEND_RGB_MULT)
    floor = pygame.Surface(size)
    for y in range(0, size[1], 320):
        for x in range(0, size[0], 320):
            floor.blit(tile, (x, y))
    # The wall is art, not a high-contrast red/yellow debug border.
    strip = art[2].subsurface((0, int(art[2].get_height()*.24), art[2].get_width(), int(art[2].get_height()*.56)))
    horizontal = pygame.transform.scale(strip, (192, 36))
    vertical = pygame.transform.rotate(horizontal, 90)
    for x in range(0, size[0], 192):
        floor.blit(horizontal, (x, 0))
        floor.blit(horizontal, (x, size[1]-36))
    for y in range(0, size[1], 192):
        floor.blit(vertical, (0, y))
        floor.blit(vertical, (size[0]-36, y))
    if len(_floor_cache) > 4:
        _floor_cache.clear()
    _floor_cache[size] = floor
    return floor


def draw_environment(surface, camera, bounds):
    floor = floor_image((bounds.width, bounds.height))
    if floor is None:
        return False
    surface.blit(floor, camera.apply_rect(bounds).topleft)
    return True


def draw_cover(surface, screen_rect):
    art = cover_image(screen_rect.size)
    if art is None:
        return False
    shadow = pygame.Surface((screen_rect.width+12, screen_rect.height+16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=8)
    surface.blit(shadow, (screen_rect.x-3, screen_rect.y+7))
    surface.blit(art, screen_rect)
    return True
