"""Pure remaining-actor poses; no combat geometry or gameplay mutation."""
import math
import pygame
REMAINING=frozenset(('CHASER_FAST','CHASER_TANK','HUNTER','ELITE','BOSS','LOOT'))

def enemy_pose(e,image):
    name=e.type.name
    phase=e.visual_stride
    sx,sy,angle=1.,1.,0.
    offset=pygame.Vector2()
    state='move' if e.visual_moving else 'idle'
    if name in ('CHASER_FAST','CHASER_TANK','HUNTER','LOOT'):
        speed=1.5 if name in ('CHASER_FAST','HUNTER') else .65 if name=='CHASER_TANK' else 1.
        wave=math.sin(phase*speed)
        sx,sy=1+.03*wave,1-.03*wave
        angle=3*wave
        offset.y=-2*abs(wave)
    else:
        offset.y=-2-2*math.sin(e._anim*(2+getattr(e,'phase',1)*.3))
        sy=1+.012*math.sin(e._anim*3)
    if e.windup_timer>0:
        state='prepare'
        progress=max(0.,min(1.,1-e.windup_timer/max(.001,e.visual_windup_total)))
        sx*=1-.10*progress
        sy*=1+.09*progress
        if e.windup_direction.length_squared():
            offset-=e.windup_direction.normalize()*4*progress
    elif e.leap_timer>0:
        state='lunge'
        sx,sy=1.1,.92
        angle=-7 if e.leap_velocity.x<0 else 7
    elif e.visual_release_timer>0:
        state='release'
        amount=e.visual_release_timer/.24
        sx*=1+.09*amount
        sy*=1-.07*amount
    if e.hit_flash>0:
        state='hit'
        sx*=.94
        angle+=4*math.sin(e._anim*40)
    art=pygame.transform.scale(image,(max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art,angle),offset,state

def hero_pose(p,image):
    sx,sy,angle=1.,1.,0.
    if p.dash_timer>0:
        sx,sy=1.08,.92
    elif getattr(p,'visual_hurt_timer',0)>0:
        sx,sy=.94,1.05
    elif getattr(p,'move_direction',pygame.Vector2()).length_squared()>0:
        wave=math.sin(p.anim_time*14)
        sx,sy=1+.022*wave,1-.022*wave
        angle=1.5*wave
    else:
        sy=1+.008*math.sin(p.anim_time*3)
    art=pygame.transform.scale(image,(max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art,angle)
