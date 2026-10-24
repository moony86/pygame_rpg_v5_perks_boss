"""Short, mergeable collection feedback using the existing editable asset library."""
import pygame
from systems.object_catalog import sprite,definition

KINDS=('gold','xp','heal_potion','dash_refresh','time_stop','blood')

def draw_magnet_trail(surface,camera,pickup):
    from systems.shot_presentation import transformed
    delta=pickup.pos-pickup.previous_pos
    length=delta.length()
    if length<2:
        return
    key='fx_trail_metal' if pickup.pickup_type=='gold' else 'fx_trail_magic'
    width=max(4,min(28,round(length)))
    image=transformed(key,(width,4),-delta.as_polar()[1])
    if image is not None:
        image=image.copy()
        image.set_alpha(round(100*definition(key)['opacity']/255))
        surface.blit(image,image.get_rect(center=camera.apply_pos((pickup.pos+pickup.previous_pos)*.5)))

class CollectPulse:
    def __init__(self,kind,value,pos):
        self.kind=kind
        self.key='fx_collect_'+kind
        self.value=value
        self.pos=pygame.Vector2(pos)
        self.age=0.
        self.max_life=definition(self.key)['life']
        self.alive=True

    def merge(self,value,pos):
        self.value+=value
        self.pos.update(pos)

    def update(self,dt):
        self.age+=dt
        self.alive=self.age<self.max_life

    def label(self):
        if self.kind=='gold': return f'+{self.value:g} G'
        if self.kind=='xp': return f'+{self.value:g} XP'
        if self.kind=='heal_potion': return f'+{self.value:g} HP' if self.value>0 else 'HP FULL'
        if self.kind=='blood': return f'+{self.value:g} BLOOD'
        return 'DASH READY' if self.kind=='dash_refresh' else 'TIME STOP'

    def draw(self,surface,camera,font,row=0):
        config=definition(self.key)
        progress=min(1.,self.age/max(.001,self.max_life))
        alpha=round(255*min(1.,(1-progress)*2.5)*config['opacity']/255)
        center=camera.apply_pos(self.pos)
        # Use only occupied rows: a lone special pickup stays close to the hero.
        y=center.y-42-row*25-progress*18
        text=font.render(self.label(),True,pygame.Color(config['tint']))
        text.set_alpha(alpha)
        rect=text.get_rect(midbottom=(round(center.x),round(y)))
        backdrop=pygame.Surface((rect.width+10,rect.height+4),pygame.SRCALPHA)
        backdrop.fill((5,10,18,round(alpha*.7)))
        surface.blit(backdrop,(rect.x-5,rect.y-2))
        surface.blit(text,rect)
        icon=sprite(self.key,frame=int(self.age*config['fps']))
        if icon is not None:
            icon=icon.copy()
            icon.set_alpha(alpha)
            surface.blit(icon,icon.get_rect(midright=(rect.left-8,rect.centery)))
        # A low ground pulse, not a full-screen flash or a new gameplay radius.
        size=round(26+progress*30)
        ring=sprite('fx_ring',size=(size,size))
        if ring is not None:
            ring=pygame.transform.scale(ring,(size,max(1,size//3))).copy()
            ring.fill((*pygame.Color(config['tint'])[:3],255),special_flags=pygame.BLEND_RGBA_MULT)
            ring.set_alpha(round(100*(1-progress)*config['opacity']/255))
            surface.blit(ring,ring.get_rect(center=(round(center.x),round(center.y+18))))
