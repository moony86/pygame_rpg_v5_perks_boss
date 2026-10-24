"""Ten proportional health cells, including partial cells and unlit empty slots."""
import pygame
from systems.object_catalog import sprite


def cell_fractions(health,maximum):
    units=max(0.,min(10.,health/max(1,maximum)*10))
    return tuple(max(0.,min(1.,units-index)) for index in range(10))


def draw(surface,player,x,y):
    full=sprite('hud_health_cell')
    empty=sprite('hud_health_empty')
    if full is None or empty is None:
        return
    old_clip=surface.get_clip()
    for index,fraction in enumerate(cell_fractions(player.health,player.max_health)):
        rect=full.get_rect(topleft=(x+index*27,y))
        surface.blit(empty,rect)
        if fraction>0:
            fill=rect.copy()
            fill.height=round(rect.height*fraction)
            fill.bottom=rect.bottom
            surface.set_clip(old_clip.clip(fill))
            surface.blit(full,rect)
            surface.set_clip(old_clip)
    if getattr(player,'visual_hurt_timer',0)>0:
        pygame.draw.line(surface,(255,115,125),(x,y+33),(x+267,y+33),2)
