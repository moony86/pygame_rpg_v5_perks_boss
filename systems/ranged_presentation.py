"""Ranged caster presentation driven by real attack events, never by a fake loop."""
import math
import pygame

RANGED_NAMES = frozenset(('RANGED','RANGED_THREE','RANGED_FIVE','RANGED_RAIN'))
RELEASE_SECONDS = .12
RECOVERY_SECONDS = .18


def is_ranged(enemy):
    return enemy.type.name in RANGED_NAMES


def pose(enemy, image):
    direction=enemy.windup_direction
    aim=direction.normalize() if direction.length_squared() else pygame.Vector2(-1 if getattr(enemy,'facing_left',False) else 1,0)
    release=getattr(enemy,'ranged_release_timer',0.)
    charge=enemy.windup_timer>0 and enemy.windup_action in ('enemy_shoot','enemy_rain')
    sx,sy,angle=1.,1.,0.
    offset=pygame.Vector2(0,-1-abs(math.sin(enemy._anim*4))*2)
    progress=0.
    if enemy.hit_flash>0:
        state='hit'
        sx,sy=.9,1.1
        offset-=aim*3
    elif charge:
        state='prepare'
        progress=max(0.,min(1.,1-enemy.windup_timer/max(.001,enemy.ranged_windup_total)))
        sx,sy=1-.09*progress,1+.10*progress
        offset-=aim*(2+3*progress)
    elif release>RECOVERY_SECONDS:
        state='release'
        strength=(release-RECOVERY_SECONDS)/RELEASE_SECONDS
        sx,sy=1+.12*strength,1-.08*strength
        offset-=aim*5*strength
    elif release>0:
        state='recover'
        sx,sy=1+.025*release/RECOVERY_SECONDS,1-.025*release/RECOVERY_SECONDS
    else:
        state='move'
        angle=2*math.sin(enemy._anim*5)
    art=pygame.transform.scale(image,(max(1,round(image.get_width()*sx)),max(1,round(image.get_height()*sy))))
    return pygame.transform.rotate(art,angle),offset,state,progress,aim


def draw_cast(surface, center, aim, state, progress):
    """Local charge/release cue; existing trajectory telegraphs remain authoritative."""
    if state not in ('prepare','release'):
        return
    from systems.shot_presentation import draw_charge
    draw_charge(surface,pygame.Vector2(center)+aim*23,aim,
                max(.15,progress) if state=='prepare' else 1.,'magic',release=state=='release')
    point=pygame.Vector2(center)+aim*23
    point=(round(point.x),round(point.y))
    radius=round(3+4*progress) if state=='prepare' else 9
    pygame.draw.circle(surface,(38,18,60),point,radius+3)
    pygame.draw.circle(surface,(195,120,255),point,radius,2)
    pygame.draw.circle(surface,(245,220,255),point,2)


def draw_telegraph(surface, start, direction, length, remaining, total, time,
                   palette=((185,110,250),(225,180,255))):
    """Broken arcane path: fixed aim, travelling runes and a charging seal.

    Bounded alpha layer keeps this inexpensive and avoids a screen-spanning solid line.
    No randomness, input, collision, or gameplay state is changed here.
    """
    if remaining<=0 or direction.length_squared()==0:
        return
    aim=direction.normalize()
    side=pygame.Vector2(-aim.y,aim.x)
    start=pygame.Vector2(start)
    end=start+aim*length
    bounds=pygame.Rect(min(start.x,end.x)-42,min(start.y,end.y)-42,
                       abs(end.x-start.x)+84,abs(end.y-start.y)+84).clip(surface.get_rect())
    if not bounds.width or not bounds.height:
        return
    layer=pygame.Surface(bounds.size,pygame.SRCALPHA)
    origin=start-pygame.Vector2(bounds.topleft)
    progress=max(0.,min(1.,1-remaining/max(.001,total)))
    alpha=round(95+130*progress)
    def point(v):
        return round(v.x),round(v.y)
    # A short rotating pair of arcs frames the casting point, not the whole body.
    seal=origin+aim*25
    radius=10+round(4*progress)
    box=pygame.Rect(0,0,radius*2,radius*2)
    box.center=point(seal)
    angle=time*3
    for turn in (0,math.pi):
        pygame.draw.arc(layer,(*palette[0],alpha),box,angle+turn,angle+turn+2.0,2)
    # Pale centers remain readable on the dungeon; violet glows stay subtle.
    shift=(time*45)%34
    for index in range(max(0,int((length-48)/34))):
        distance=48+index*34+shift
        if distance>length:
            break
        pos=origin+aim*distance
        fade=(1-distance/max(1,length))*.7+.3
        a=round(alpha*fade)
        if index%3==0:
            tip=pos+aim*4
            pygame.draw.lines(layer,(*palette[0],max(10,a//3)),False,
                [point(pos-aim*3+side*5),point(tip),point(pos-aim*3-side*5)],5)
            pygame.draw.lines(layer,(*palette[1],a),False,
                [point(pos-aim*3+side*4),point(tip),point(pos-aim*3-side*4)],2)
        else:
            pygame.draw.circle(layer,(*palette[0],a),point(pos),2)
    surface.blit(layer,bounds.topleft)
