"""Desktop front end: one hero scene, primary run action, settings and controls."""
import math
from functools import lru_cache
import pygame
from config import CONFIG
from systems.environment_art import floor_image
from systems.object_catalog import sprite, revision

INK = (10, 18, 29)
TEXT = (225, 239, 245)
MUTED = (157, 184, 198)
ACCENT = (83, 225, 248)
ACTIONS = ('start', 'settings', 'controls', 'quit')
LABELS = ('START RUN', 'Settings', 'How to play', 'Quit')
OPTIONS = ('master_volume','music_volume','sfx_volume','screen_shake','aim_assist','reduced_flashes')
OPTION_LABELS = ('Master volume','Music','Sound effects','Screen shake','Aim assist','Reduced clock flashes')


def layout_menu(game):
    game.menu_buttons = {key:pygame.Rect(180,530+i*78,430 if i==0 else 360,64)
                         for i,key in enumerate(ACTIONS)}
    game.rect_new_run = game.menu_buttons['start']
    game.rect_quit = game.menu_buttons['quit']
    game.menu_back = pygame.Rect(180,850,360,60)
    game.menu_option_rects = {key:pygame.Rect(230,400+i*64,550,42) for i,key in enumerate(OPTIONS)}
    game.menu_page = 'main'
    game.menu_focus = 0
    game.menu_status = ''


@lru_cache(maxsize=1)
def fonts():
    return {size:pygame.font.SysFont('Arial',size,bold=size in (86,34)) for size in (22,26,34,86)}


def text(surface, label, pos, size=26, color=TEXT):
    surface.blit(fonts()[size].render(label,True,color),pos)


@lru_cache(maxsize=2)
def backdrop(size, visual_revision):
    result = pygame.Surface(size)
    floor = floor_image(size)
    if floor is not None:
        result.blit(floor,(0,0))
    else:
        result.fill(INK)
    shade = pygame.Surface(size,pygame.SRCALPHA)
    w,h = size
    for x in range(0,w,8):
        alpha=round(240-160*min(1.,x/(w*.72)))
        pygame.draw.rect(shade,(6,13,23,alpha),(x,0,8,h))
    for y in range(h-240,h,8):
        pygame.draw.rect(shade,(6,13,23,round(120+100*(y-h+240)/240)),(0,y,w,8))
    result.blit(shade,(0,0))
    return result


def draw_button(surface, rect, label, active=False, primary=False):
    if primary:
        pygame.draw.rect(surface, (39, 157, 180) if active else (22, 111, 133),rect,border_radius=8)
        pygame.draw.rect(surface,ACCENT,rect,2,border_radius=8)
    elif active:
        pygame.draw.rect(surface,(20,47,61),rect,border_radius=8)
    if active:
        pygame.draw.rect(surface,ACCENT,(rect.x-15,rect.y+15,4,rect.h-30),border_radius=2)
    text(surface,label,(rect.x+24,rect.y+15),26,TEXT if primary or active else MUTED)


def draw_scene(surface, time):
    # Existing authored assets, not debug geometry or external placeholder art.
    portal = sprite('portal',size=(280,350))
    hero = sprite('hero',size=(154,154))
    if portal:
        surface.blit(portal,portal.get_rect(center=(1390,480+round(4*math.sin(time)))))
    if hero:
        surface.blit(hero,hero.get_rect(center=(1310,690+round(3*math.sin(time*2)))))
    gun = sprite('pistol',size=(94,70))
    if gun:
        surface.blit(gun,gun.get_rect(center=(1225,710)))


def draw_settings(surface,game):
    text(surface,'SETTINGS',(180,255),34)
    text(surface,'Applied immediately. Saved on this computer.',(180,315),22,MUTED)
    for index,key in enumerate(OPTIONS):
        rect = game.menu_option_rects[key]
        active = game.menu_focus==index or rect.collidepoint(game.game_mouse_pos())
        if active:
            pygame.draw.rect(surface,(15,39,53),rect.inflate(24,12),border_radius=8)
        text(surface,OPTION_LABELS[index],(rect.x,rect.y+5),26)
        if key.endswith('_volume'):
            track = pygame.Rect(rect.x+280,rect.y+18,200,6)
            pygame.draw.rect(surface,(40,67,80),track,border_radius=3)
            value = CONFIG[key]
            pygame.draw.rect(surface,ACCENT,(track.x,track.y,round(track.w*value),track.h),border_radius=3)
            pygame.draw.circle(surface,TEXT,(track.x+round(track.w*value),track.centery),7)
            text(surface,f'{round(value*100)}%',(rect.right-54,rect.y+4),22,MUTED)
        else:
            text(surface,'ON' if CONFIG[key] else 'OFF',(rect.right-65,rect.y+5),26,
                 ACCENT if CONFIG[key] else MUTED)
    text(surface,game.menu_status or 'Up / Down: select   Left / Right: adjust',(180,805),22,MUTED)
    draw_button(surface,game.menu_back,'Back  [Esc]',True)


def draw_controls(surface,game):
    text(surface,'ONE RUN. BUILD YOUR EDGE.',(180,255),34)
    for row,label in enumerate((
        'Enter the portal in the hub to begin.',
        'Clear enemies. Choose upgrades. Find the boss.',
        'Defeat the boss to complete the stage.',
        'Stage clear: keep gold, reset the build, return to hub.',
        'W A S D     Move',
        'Mouse         Aim + hold left click to fire',
        'Space           Press, then release to dash',
        'E                   Use a nearby labelled portal / NPC',
        'Tab               Hold for build stats and the map',
        'Esc               Pause / audio settings',
    )):
        text(surface,label,(180,345+row*44),26,MUTED if row<3 else TEXT)
    draw_button(surface,game.menu_back,'Back  [Esc]',True)


def draw_menu(surface,game):
    if not hasattr(game,'menu_buttons'):
        layout_menu(game)
    surface.blit(backdrop(surface.get_size(),revision()),(0,0))
    draw_scene(surface,pygame.time.get_ticks()/1000.)
    text(surface,'BLUE CUBE',(180,130),86)
    if game.menu_page=='main':
        text(surface,'FAST RUNS  /  EVOLVING BUILDS',(185,232),22,ACCENT)
    if game.menu_page=='settings':
        draw_settings(surface,game)
    elif game.menu_page=='controls':
        draw_controls(surface,game)
    else:
        text(surface,'Fight. Adapt. Reach the boss.',(185,340),34)
        text(surface,'A fast action roguelite. One pistol. Your build.',(185,395),26,MUTED)
        mouse = game.game_mouse_pos()
        for index,(key,label) in enumerate(zip(ACTIONS,LABELS)):
            rect=game.menu_buttons[key]
            draw_button(surface,rect,label,game.menu_focus==index or rect.collidepoint(mouse),index==0)
        text(surface,'WASD move    Mouse fire    Release Space to dash',(185,905),22,MUTED)
    text(surface,'DEVELOPMENT DEMO',(1400,990),22,MUTED)
    # Native pointer is hidden by Game; menu must still show an actual pointer.
    x,y=game.game_mouse_pos()
    pygame.draw.polygon(surface,TEXT,[(x,y),(x+5,y+20),(x+10,y+13),(x+18,y+12)])
