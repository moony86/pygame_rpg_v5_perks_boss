"""Heavy gait and charge poses, driven only by existing movement/attack events."""
import math
import pygame
from systems.object_catalog import sprite


def pose(enemy,image):
    sx,sy,angle=1.,1.,0.
    offset=pygame.Vector2()
    aim=enemy.windup_direction
    aim=aim.normalize() if aim.length_squared() else pygame.Vector2(1,0)
    if enemy.leap_timer>0:
        state='charge'
        sx,sy=1.1,.92
        angle=-8 if aim.x<0 else 8
        offset.y=2
    elif enemy.windup_timer>0 and enemy.windup_action=='brute_charge':
        state='prepare'
        progress=max(0.,min(1.,1-enemy.windup_timer/max(.001,enemy.brute_windup_total)))
        sx,sy=1+.10*progress,1-.14*progress
        offset=-aim*5*progress
        offset.y+=4*progress
    elif enemy.brute_stop_timer>0:
        state='stop'
        amount=enemy.brute_stop_timer/.26
        sx,sy=1+.14*amount,1-.12*amount
        offset.y=3*amount
    elif enemy.brute_moving:
        state='move'
        phase=enemy.brute_stride
        angle=2.5*math.sin(phase)
        offset.y=2*abs(math.sin(phase))
    else:
        state='idle'
        sy=1+.012*math.sin(enemy._anim*3)
    if enemy.hit_flash>0:
        sx*=.96
        offset-=aim*2
    art=pygame.transform.scale(image,(max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art,angle),offset,state


def draw_ground(surface,center,enemy):
    if enemy.brute_stop_timer<=0:
        return
    progress=1-enemy.brute_stop_timer/.26
    width=round(40+44*progress)
    ring=sprite('fx_ring',size=(width,width))
    if ring is not None:
        ring=pygame.transform.scale(ring,(width,max(1,round(width*.4)))).copy()
        ring.set_alpha(round(180*(1-progress)))
        surface.blit(ring,ring.get_rect(center=(round(center[0]),round(center[1]+18))))
