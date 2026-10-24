"""Pixel-art pistol geometry shared by rendering and projectile origins.

Coordinates describe the existing 64px gun.png displayed at 32px. They do not
change the artwork, aim direction, damage, spread, or fire cadence.
"""
from dataclasses import dataclass
import pygame
from systems.object_catalog import definition

PISTOL_SIZE = (32, 32)
PISTOL_GRIP = (9, 18)
PISTOL_MUZZLE = (30, 12)
PISTOL_HOLD_REACH = 18
PISTOL_HAND_SIDE = 10
PISTOL_RECOIL_PIXELS = 3.0
PISTOL_SHOT_SECONDS = 0.12
PISTOL_FLASH_SECONDS = 0.035


@dataclass
class PistolPose:
    grip: pygame.Vector2
    center: pygame.Vector2
    muzzle: pygame.Vector2
    direction: pygame.Vector2
    angle: float
    flip_vertical: bool


def pistol_pose(player_center, aim, shot_timer=0.0):
    direction = pygame.Vector2(aim)
    if direction.length_squared() == 0:
        direction.update(1, 0)
    direction = direction.normalize()
    angle = direction.as_polar()[1]
    flip = direction.x < 0
    side = pygame.Vector2(-direction.y, direction.x)
    phase = max(0.0, min(1.0, shot_timer / PISTOL_SHOT_SECONDS))
    recoil = PISTOL_RECOIL_PIXELS * phase * phase
    grip = (pygame.Vector2(player_center) + direction * (PISTOL_HOLD_REACH - recoil)
            + side * PISTOL_HAND_SIDE * (-1 if flip else 1))
    config = definition('pistol')
    size = pygame.Vector2(config['width'], config['height'])
    image_center = size / 2
    scale = pygame.Vector2(size.x / 32, size.y / 32)

    def transform(local):
        offset = pygame.Vector2(local[0]*scale.x, local[1]*scale.y) - image_center
        if flip:
            offset.y = -offset.y
        return offset.rotate(angle)

    center = grip - transform(PISTOL_GRIP)
    return PistolPose(grip, center, center + transform(PISTOL_MUZZLE), direction, angle, flip)


def render_pistol(surface, image, pose, shot_timer=0.0):
    if image is not None:
        if pose.flip_vertical:
            image = pygame.transform.flip(image, False, True)
        # rotate, not rotozoom: nearest-neighbour rotation preserves pixels.
        rotated = pygame.transform.rotate(image, -pose.angle)
        surface.blit(rotated, rotated.get_rect(center=(round(pose.center.x), round(pose.center.y))))
    else:
        start = pose.grip
        pygame.draw.line(surface, (190, 195, 210), start, pose.muzzle, 4)

    elapsed = PISTOL_SHOT_SECONDS - shot_timer
    if shot_timer <= 0 or elapsed >= PISTOL_FLASH_SECONDS:
        return
    # Small pixel-shaped flash, anchored to the very same muzzle as bullets.
    forward = pose.direction
    side = pygame.Vector2(-forward.y, forward.x)
    size = 8 if elapsed < PISTOL_FLASH_SECONDS / 2 else 5
    muzzle = pose.muzzle
    points = [muzzle, muzzle + forward * 3 + side * 3,
              muzzle + forward * size, muzzle + forward * 3 - side * 3]
    pygame.draw.polygon(surface, (255, 190, 65), [(round(v.x), round(v.y)) for v in points])
    core = muzzle + forward * 2
    pygame.draw.rect(surface, (255, 250, 205), (round(core.x) - 1, round(core.y) - 1, 3, 3))
