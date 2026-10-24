"""Bounded forward-only finisher targeting; shared by desktop and private QA."""
import pygame
from systems.object_catalog import definition

CHAIN_RANGE = 280
CHAIN_LANE_HALF_WIDTH = 72
CHAIN_MAX_HOPS = 4
CHAIN_SPEED_MULTIPLIER = 1.12


def next_chain_target(player, enemies, solids):
    if player.ninja_chain_hops >= definition('sword')['chain_hops']:
        return None
    origin = pygame.Vector2(player.rect.center)
    heading = player.ninja_chain_heading
    candidates = []
    for enemy in enemies:
        if not enemy.alive or id(enemy) in player.dash_strike_hit_ids:
            continue
        if getattr(getattr(enemy, "type", None), "name", "") == "BOSS":
            continue
        delta = pygame.Vector2(enemy.rect.center) - origin
        distance = delta.length()
        if not 12 < distance <= definition('sword')['chain_range'] or delta.dot(heading) <= 0:
            continue
        # Stay inside the ORIGINAL dash lane, not a gradually turning homing arc.
        lane = pygame.Vector2(enemy.rect.center) - player.ninja_chain_origin
        if abs(lane.cross(heading)) > CHAIN_LANE_HALF_WIDTH:
            continue
        if delta.normalize().dot(heading) < 0.80:
            continue
        # Expand walls by the player's body: a clear centre ray alone is unsafe.
        if any(solid.inflate(player.rect.width + 2, player.rect.height + 2)
               .clipline(origin, enemy.rect.center) for solid in solids):
            continue
        candidates.append((distance, enemy))
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


def draw_dash_sword(surface, center, direction, timer, image):
    """Use the existing sword sprite, without equipping another weapon."""
    direction = pygame.Vector2(direction)
    if not direction.length_squared():
        return
    direction = direction.normalize()
    swing = (1 - min(1, timer / 0.24)) * 95 - 45
    blade = direction.rotate(swing)
    grip = pygame.Vector2(center) + direction * 14
    tip = grip + blade * 48
    side = pygame.Vector2(-blade.y, blade.x)
    # A short, local violet slash reads well without whole-screen flashing.
    pygame.draw.line(surface, (116, 66, 170), grip + side * 7, tip + side * 7, 6)
    if image is not None:
        rotated = pygame.transform.rotate(image, -pygame.Vector2(1, 0).angle_to(blade))
        surface.blit(rotated, rotated.get_rect(center=grip + blade * 22))
    else:
        pygame.draw.line(surface, (218, 195, 255), grip, tip, 5)
    pygame.draw.line(surface, (249, 243, 255), grip + blade * 15, tip, 2)
