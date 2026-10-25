"""Cosmetic class identity only. No targeting, movement or damage rules."""
import math
import pygame
from systems.object_catalog import sprite, definition
from systems.shot_presentation import transformed, faded, draw_trail

BUILDS = {'Ninja': 'ninja', 'Engineer': 'engineer', 'Vampire': 'vampire',
          'Gunslinger': 'gunslinger'}


def identity(player):
    return BUILDS.get(getattr(player, 'starter_build', ''), '')


def draw_held(surface, player, pose):
    kind = identity(player)
    if not kind:
        return False
    if kind in ('gunslinger', 'engineer'):
        from systems.pistol_presentation import render_pistol
        render_pistol(surface, sprite('weapon_' + kind), pose, 0)
        draw_launch(surface, kind, pose, player.gun_shoot_timer)
        return True
    key = 'weapon_' + kind
    config = definition(key)
    angle = -pose.angle
    if kind == 'ninja':
        angle += player.anim_time * 120
    elif kind == 'engineer':
        angle += 18 * max(0, player.gun_shoot_timer / .12)
    art = transformed(key, (config['width'], config['height']), angle)
    if art is not None:
        center = pose.muzzle.copy()
        if kind == 'vampire':
            center.y += math.sin(player.anim_time * 5) * 2
        surface.blit(art, art.get_rect(center=center))
    draw_launch(surface, kind, pose, player.gun_shoot_timer)
    return True


def draw_launch(surface, kind, pose, timer):
    if timer <= .035:
        return
    key = 'launch_' + kind
    config = definition(key)
    alpha = min(240, round(timer/.12*220/16)*16)
    image = faded(key, (config['width'], config['height']), -pose.angle, alpha)
    if image is not None:
        surface.blit(image, image.get_rect(center=pose.muzzle + pose.direction * 10))


def draw_projectile(surface, camera, shot):
    kind = getattr(shot, 'class_visual', '')
    if not kind and getattr(shot, 'source', '') == 'ninja_shuriken':
        kind = 'ninja'
    if kind not in BUILDS.values():
        return False
    key = 'shot_' + kind
    config = definition(key)
    angle = -shot.direction.as_polar()[1]
    if kind in ('ninja', 'engineer'):
        angle += shot.anim_time * (900 if kind == 'ninja' else 540)
    if shot.explosive:
        draw_trail(surface, camera, shot)
    trail_key = 'trail_' + kind
    trail = definition(trail_key)
    for point, age in getattr(shot, 'visual_trail', ())[-3:]:
        alpha = round(105 * max(0., 1-age/.12) / 16) * 16
        echo = faded(trail_key, (trail['width'], trail['height']),
                     -shot.direction.as_polar()[1], alpha)
        if echo is not None:
            surface.blit(echo, echo.get_rect(center=camera.apply_pos(point)))
    art = transformed(key, (config['width'], config['height']), angle)
    if art is not None:
        surface.blit(art, art.get_rect(center=camera.apply_pos(shot.pos)))
    return art is not None


def draw_hit(surface, camera, effect):
    kind = effect.class_visual
    if kind not in BUILDS.values():
        return False
    progress = 1 - max(0., effect.life / effect.max_life)
    key = 'impact_' + kind
    config = definition(key)
    size = (round(config['width']*(.75+.35*progress)), round(config['height']*(.75+.35*progress)))
    alpha = round(230*(1-progress)/16)*16
    image = faded(key, size, -effect.direction.as_polar()[1], alpha)
    if image is not None:
        surface.blit(image, image.get_rect(center=camera.apply_pos(effect.pos)))
    target = effect.target() if effect.target else None
    if target is not None and getattr(target, 'alive', False):
        key = 'target_' + kind
        config = definition(key)
        image = faded(key, (config['width'], config['height']), 0, round(alpha*.65/16)*16)
        if image is not None:
            surface.blit(image, image.get_rect(center=camera.apply_pos(pygame.Vector2(target.rect.center))))
    return True
