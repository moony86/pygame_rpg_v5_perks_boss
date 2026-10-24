"""Visual-only jumper poses and actual-ground landing cue; no extra area damage."""
import math
import pygame
from systems.object_catalog import sprite


def is_jumper(enemy):
    return enemy.type.name in ('JUMPER','JUMPER_FAST','JUMPER_HEAVY')


def pose(enemy, image):
    sx,sy,angle,lift=1.,1.,0.,0.
    if enemy.leap_timer>0:
        state='air'
        progress=max(0.,min(1.,1-enemy.leap_timer/max(.001,enemy.jumper_flight_total)))
        lift=-12*math.sin(math.pi*progress)
        sx,sy= .92,1.08
        angle=(9 if enemy.leap_velocity.x>=0 else -9)*math.sin(math.pi*progress)
    elif enemy.windup_timer>0 and enemy.windup_action=='enemy_jump':
        state='prepare'
        progress=1-enemy.windup_timer/max(.001,enemy.jumper_windup_total)
        sx,sy=1+.18*progress,1-.2*progress
        lift=4*progress
    elif enemy.jumper_landing_timer>0:
        state='land'
        amount=enemy.jumper_landing_timer/.22
        sx,sy=1+.18*amount,1-.18*amount
        lift=3*amount
    else:
        state='move'
        sx,sy=1+.025*math.sin(enemy._anim*12),1-.025*math.sin(enemy._anim*12)
    if enemy.hit_flash>0:
        sx*=.94
    art=pygame.transform.scale(image,(max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art,angle),(0,round(lift)),state


def draw_ground(surface,center,enemy):
    # The cue follows the real ground position, never promises an unreachable target.
    if enemy.leap_timer<=0 and enemy.jumper_landing_timer<=0:
        return
    landing=enemy.jumper_landing_timer>0
    progress=1-enemy.jumper_landing_timer/.22 if landing else 0
    width=round(30+36*progress) if landing else 28
    height=max(8,round(width*.42))
    ring=sprite('fx_ring',size=(width,width))
    if ring is not None:
        ring=pygame.transform.scale(ring,(width,height)).copy()
        ring.set_alpha(round(180*(1-progress)) if landing else 100)
        surface.blit(ring,ring.get_rect(center=(round(center[0]),round(center[1]+14))))
