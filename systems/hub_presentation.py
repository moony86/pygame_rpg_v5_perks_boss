"""Asset-backed sanctuary; all art paths and actor display sizes are data-backed."""
from functools import lru_cache
import json
import math
import pygame
from systems.asset_loader import ASSET_ROOT, load_image

HUB = json.loads((ASSET_ROOT / 'data/hub.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=12)
def art(role):
    config = HUB['npcs'][role]
    source = load_image(config['art']) if config['art'] else None
    if source is None:
        return None
    bounds = source.get_bounding_rect(min_alpha=16)
    if not bounds.width or not bounds.height:
        return None
    return pygame.transform.scale(source.subsurface(bounds), config['size'])


@lru_cache(maxsize=2)
def background(size):
    return load_image(HUB['background'], size)


def draw_background(surface, camera, rect):
    image = background(rect.size)
    if image is None:
        return False
    surface.blit(image, camera.apply_rect(rect))
    return True


def draw_npc(surface, camera, npc):
    if npc.role not in HUB['npcs']:
        return False
    # The gate is already represented by the real portal asset, not a second NPC.
    if npc.role == 'portal':
        return True
    image = art(npc.role)
    if image is None:
        return False
    pos = camera.apply_rect(npc.rect).midbottom
    bob = round(math.sin(npc._anim * 2) * 2)
    shadow = pygame.Rect(0, 0, 70, 16)
    shadow.center = pos
    pygame.draw.ellipse(surface, (10, 16, 22), shadow)
    surface.blit(image, image.get_rect(midbottom=(pos[0], pos[1] + bob)))
    return True
