"""Visual-only crystal locomotion. Never changes enemy collision or AI timing."""
import math
import pygame


def pose(enemy, image):
    from entities.enemy import CHASER_BURST_THRESHOLD
    phase = enemy._anim * 13
    pressure = min(1, max(0, enemy.chase_pressure_timer / CHASER_BURST_THRESHOLD))
    burst = enemy.chaser_burst_timer > 0
    hit = enemy.hit_flash > 0
    state = 'hit' if hit else 'burst' if burst else 'prepare' if pressure > .55 else 'move'
    sx, sy, angle, lift = 1., 1., 0., 0.
    if state == 'move':
        sx, sy = 1+.035*math.sin(phase), 1-.035*math.sin(phase)
        angle, lift = 3*math.sin(phase*.5), -2*abs(math.sin(phase*.5))
    elif state == 'prepare':
        sx, sy = 1+.14*pressure, 1-.14*pressure
        angle = 2*math.sin(phase*2)
    elif state == 'burst':
        sx, sy, angle = 1.16, .86, -10 if getattr(enemy,'facing_left',False) else 10
    else:
        sx, sy = .88, 1.1
        angle = 7*math.sin(phase*3)
    art = pygame.transform.scale(image, (max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art, angle), (0, round(lift)), state
