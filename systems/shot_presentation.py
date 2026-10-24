"""Data-backed shot VFX. No damage, collision, status effects or gameplay RNG."""
import math
import weakref
from collections import OrderedDict
import pygame
from systems.object_catalog import sprite, definition, revision

_poses=OrderedDict()
_pose_bytes=0
MAX_POSE_BYTES=16*1024*1024
_faded=OrderedDict()
_faded_bytes=0
MAX_POSES=2048
MAX_FADED=8192
MAX_FADED_BYTES=32*1024*1024
_prepared_revision=-1
_ribbons=OrderedDict()
_ribbon_bytes=0
MAX_RIBBONS=1024
MAX_RIBBON_BYTES=24*1024*1024

def clear_caches():
    global _faded_bytes,_prepared_revision,_ribbon_bytes,_pose_bytes
    _poses.clear()
    _faded.clear()
    _faded_bytes=0
    _prepared_revision=-1
    _ribbons.clear()
    _ribbon_bytes=0
    _pose_bytes=0

def style(shot):
    explicit=getattr(shot,'visual_style',None)
    if explicit in ('metal','magic','fire'):
        return explicit
    if getattr(shot,'explosive',False):
        return 'fire'
    if getattr(shot,'source','player') in ('engineer_drone','ninja_shuriken') or hasattr(shot,'owner_id'):
        return 'magic'
    return 'metal'

def visible(surface,camera,shot):
    # Leave enough margin for the complete .12s history and the largest sprite.
    # Rendering only: offscreen shots keep updating and colliding normally.
    margin=max(160,getattr(shot,'speed',0)*.18+96)
    x=shot.pos.x-camera.offset.x+camera.render_offset.x
    y=shot.pos.y-camera.offset.y+camera.render_offset.y
    return -margin<=x<=surface.get_width()+margin and -margin<=y<=surface.get_height()+margin

def record_trail(shot,dt):
    history=getattr(shot,'visual_trail',[])
    history=[(point,age+dt) for point,age in history if age+dt<.12]
    if shot.pos.distance_squared_to(shot.previous_pos)>0:
        history.append((shot.previous_pos.copy(),0.))
    shot.visual_trail=history[-8:]

def transformed(key,size,angle=0):
    global _pose_bytes
    angle=round(angle/5)*5
    cache=(key,tuple(size),angle,revision())
    if cache in _poses:
        _poses.move_to_end(cache)
        return _poses[cache]
    image=sprite(key,size=size)
    if image is None:
        return None
    image=pygame.transform.rotate(image,angle)
    _poses[cache]=image
    _pose_bytes+=image.get_pitch()*image.get_height()
    while len(_poses)>MAX_POSES or _pose_bytes>MAX_POSE_BYTES:
        _,old=_poses.popitem(last=False)
        _pose_bytes-=old.get_pitch()*old.get_height()
    return image

def faded(key,size,angle,alpha):
    angle=round(angle/5)*5
    cache=(key,tuple(size),angle,alpha,revision())
    image=_faded.get(cache)
    if image is not None:
        _faded.move_to_end(cache)
        return image
    source=transformed(key,size,angle)
    if source is None:
        return None
    image=source.copy()
    image.set_alpha(alpha)
    return _remember_fade(cache,image)

def _remember_fade(cache,image):
    global _faded_bytes
    _faded[cache]=image
    _faded_bytes+=image.get_pitch()*image.get_height()
    while len(_faded)>MAX_FADED or _faded_bytes>MAX_FADED_BYTES:
        _,old=_faded.popitem(last=False)
        _faded_bytes-=old.get_pitch()*old.get_height()
    return image

def target_overlay(key,frame,size,alpha):
    cache=('target',key,frame,tuple(size),alpha,revision())
    image=_faded.get(cache)
    if image is not None:
        _faded.move_to_end(cache)
        return image
    source=sprite(key,frame=frame)
    if source is None:
        return None
    image=pygame.transform.scale(source,size) if source.get_size()!=size else source.copy()
    image.set_alpha(alpha)
    return _remember_fade(cache,image)

def ribbon(shot):
    """Bake the same eight pieces once into a shared, head-relative image.

    Keep actual curved history. Only sub-pixel translation is snapped to the pixel
    grid (at most one pixel relative to drawing each piece separately).
    """
    global _ribbon_bytes
    history=getattr(shot,'visual_trail',[])
    if not history:
        return None
    kind=style(shot)
    key='fx_trail_hostile' if hasattr(shot,'owner_id') else 'fx_trail_'+kind
    config=definition(key)
    opacity=config['opacity']
    shape=tuple((round((point.x-shot.pos.x)*1024),round((point.y-shot.pos.y)*1024),
                 round(155*max(0.,1-age/.12)*opacity/255)) for point,age in history)
    cache=(key,shape,revision())
    cached=_ribbons.get(cache)
    if cached is not None:
        _ribbons.move_to_end(cache)
        return cached
    scale=config['width']/(48 if kind=='metal' else 56)
    height=config['height']
    commands=[]
    bounds=None
    for i,(x,y,alpha) in enumerate(shape):
        start=pygame.Vector2(x/1024,y/1024)
        end=pygame.Vector2(shape[i+1][0]/1024,shape[i+1][1]/1024) if i+1<len(shape) else pygame.Vector2()
        delta=end-start
        length=delta.length()
        if length<1:
            continue
        width=max(4,min(96,round((length+4)*scale/4)*4))
        image=faded(key,(width,height),-delta.as_polar()[1],alpha)
        if image is not None:
            rect=image.get_rect(center=(start+end)*.5)
            commands.append((image,rect))
            bounds=rect.copy() if bounds is None else bounds.union(rect)
    if not commands:
        return None
    layer=pygame.Surface(bounds.size,pygame.SRCALPHA)
    layer.blits([(image,rect.move(-bounds.x,-bounds.y)) for image,rect in commands],doreturn=False)
    result=(layer,bounds.topleft)
    _ribbons[cache]=result
    _ribbon_bytes+=layer.get_pitch()*layer.get_height()
    while len(_ribbons)>MAX_RIBBONS or _ribbon_bytes>MAX_RIBBON_BYTES:
        _,(old,_)=_ribbons.popitem(last=False)
        _ribbon_bytes-=old.get_pitch()*old.get_height()
    return result

def draw_trail(surface,camera,shot):
    prepared=ribbon(shot)
    if prepared is not None:
        image,offset=prepared
        pos=camera.apply_pos(shot.pos)
        surface.blit(image,(round(pos.x)+offset[0],round(pos.y)+offset[1]))

def draw_charge(surface,center,aim,progress,kind='magic',release=False):
    if progress<=0:
        return
    key='fx_charge_'+kind
    size=round((10 if kind=='metal' else 15)+(8 if release else 5)*progress)
    config=definition(key)
    dimensions=(max(1,round(size*config['width']/24)),max(1,round(size*config['height']/24)))
    image=faded(key,dimensions,-aim.as_polar()[1],round((130+100*progress)*config['opacity']/255))
    if image is not None:
        surface.blit(image,image.get_rect(center=(round(center[0]),round(center[1]))))

def prepare():
    """Run before entering the run; preload sources and common reusable poses."""
    global _prepared_revision
    current=revision()
    if _prepared_revision==current:
        return
    from types import SimpleNamespace
    from settings import ENEMY_BULLET_SPEED
    from systems.object_catalog import catalog
    for key in catalog()['objects']:
        if key.startswith(('bullet_','fx_','enemy_','companion_','visual_')) or key in ('hero','pistol','sword','portal','heal_potion','dash_refresh','time_stop'):
            sprite(key)
    from systems.environment_art import floor_image
    from settings import SCREEN_WIDTH,SCREEN_HEIGHT
    floor_image((SCREEN_WIDTH,SCREEN_HEIGHT))
    scratch=pygame.Surface((128,128),pygame.SRCALPHA)
    speed=definition('pistol')['projectile_speed']
    for kind in ('metal','magic','fire','hostile'):
        for angle in range(0,360,5):
            direction=pygame.Vector2(1,0).rotate(angle)
            for dt in (1/60,1/30):
                count=min(8,math.ceil(.12/dt))
                velocity=direction*(ENEMY_BULLET_SPEED if kind=='hostile' else speed)
                shot=SimpleNamespace(pos=pygame.Vector2(),direction=direction,
                    visual_style='magic' if kind=='hostile' else kind,
                    visual_trail=[(-velocity*((count-i)*dt),(count-i-1)*dt) for i in range(count)])
                if kind=='hostile': shot.owner_id=0
                ribbon(shot)
            if kind!='hostile':
                for amount in (.25,.5,.75,1.):
                    draw_charge(scratch,(64,64),direction,amount,kind)
    _prepared_revision=current

class ShotHit:
    def __init__(self,shot,pos,target=None,shield=False):
        self.kind='magic' if shield else style(shot)
        suffix='hostile' if hasattr(shot,'owner_id') and not shield else self.kind
        self.key='fx_sparks_'+suffix
        self.hit_key='fx_hit_'+suffix
        self.pos=pygame.Vector2(pos)
        self.direction=pygame.Vector2(getattr(shot,'direction',(1,0)))
        self.fragment_vectors=tuple(self.direction.rotate(i*137.5)*(18+6*i) for i in range(5))
        self.target=weakref.ref(target) if target is not None and not shield else None
        self.life=definition(self.hit_key)['life']
        self.max_life=self.life
        self.alive=True

    def update(self,dt):
        self.life-=dt
        self.alive=self.life>0

    def draw(self,surface,camera):
        progress=1-max(0.,self.life/self.max_life)
        config=definition(self.key)
        size=(max(1,round(config['width']*.75)),max(1,round(config['height']*.75)))
        alpha=round(230*(1-progress)*config['opacity']/255)
        # Deterministic flying fragments: never consume random values used by combat.
        for i,velocity in enumerate(self.fragment_vectors):
            angle=i*137.5
            pos=self.pos+velocity*progress
            image=faded(self.key,size,angle+progress*90,alpha)
            if image is not None:
                surface.blit(image,image.get_rect(center=camera.apply_pos(pos)))
        target=self.target() if self.target else None
        if target is not None and getattr(target,'alive',True) and getattr(target,'health',1)>0:
            key=self.hit_key
            config=definition(key)
            elapsed=self.max_life-self.life
            size=(config['width'],config['height'])
            if self.kind=='fire':
                size=(max(1,round(size[0]*(1+.05*math.sin(elapsed*45)))),
                      max(1,round(size[1]*(1+.08*math.sin(elapsed*30)))))
            frame=int(elapsed*config['fps'])%config['frames']
            image=target_overlay(key,frame,size,round(150*(1-progress)*config['opacity']/255))
            if image is not None:
                pos=camera.apply_pos(pygame.Vector2(target.rect.center))
                surface.blit(image,image.get_rect(center=pos))
