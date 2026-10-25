"""Cached temporal tint, clock sigil and countdown; never changes freeze duration."""
from functools import lru_cache
import pygame
from config import CONFIG
from systems.object_catalog import sprite


@lru_cache(maxsize=2)
def layers(size):
    w, h = size
    frost = pygame.Surface(size, pygame.SRCALPHA)
    frost.fill((18, 95, 145, 86))
    # Strong at the edges, readable at the center. Built once per viewport size.
    for inset in range(0, 140, 7):
        pygame.draw.rect(frost, (18, 95, 145, round(130-44*inset/140)),
                         (inset, inset, w-2*inset, h-2*inset), 7)
    for side in (0, w):
        for y in range(100, h, 150):
            sign = 1 if side == 0 else -1
            pygame.draw.lines(frost, (155, 240, 255, 105), False,
                              [(side,y),(side+sign*42,y+18),(side+sign*24,y+43)], 2)
    pulse = pygame.Surface(size)
    pulse.fill((125, 225, 255))
    return frost, pulse


@lru_cache(maxsize=1)
def fonts():
    return pygame.font.SysFont('Arial', 25, bold=True), pygame.font.SysFont('Arial', 20)


def draw(surface, remaining, duration, release):
    if remaining <= 0 and release <= 0:
        return
    frost, pulse = layers(surface.get_size())
    w, h = surface.get_size()
    reduced = CONFIG.get('reduced_flashes', False)
    if remaining > 0:
        elapsed = max(0., duration - remaining)
        frost.set_alpha(160 if reduced else 255)
        surface.blit(frost, (0, 0))
        if not reduced and elapsed < .24:
            pulse.set_alpha(round(95 * (1-elapsed/.24)))
            surface.blit(pulse, (0, 0))
        # A clock face, not an obscuring full-screen white flash/strobe.
        center = (w//2, h//2)
        if not reduced and elapsed < .45:
            radius = 110 + round(elapsed*120)
            from systems.sigil_presentation import draw as draw_sigil
            draw_sigil(surface, 'fx_time_sigil', center, radius * 2,
                       210 * (1 - elapsed / .45))
        title, _ = fonts()
        label = title.render(f'TIME STOP  {remaining:.1f}s', True, (215, 250, 255))
        rect = pygame.Rect(w//2+120, 28, 296, 70)
        pygame.draw.rect(surface, (9, 28, 43), rect, border_radius=10)
        icon = sprite('time_stop', size=(34, 40))
        if icon:
            surface.blit(icon, icon.get_rect(center=(rect.left+30,rect.centery-3)))
        surface.blit(label, (rect.left+56, rect.top+10))
        ratio = min(1., remaining/max(.01,duration))
        pygame.draw.rect(surface, (30, 70, 88), (rect.left+16,rect.bottom-12,264,4))
        pygame.draw.rect(surface, (110, 235, 255), (rect.left+16,rect.bottom-12,round(264*ratio),4))
    elif release > 0 and not reduced:
        pulse.set_alpha(round(48 * release/.18))
        surface.blit(pulse, (0, 0))
