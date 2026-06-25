import pygame
import math
from settings import GREEN, GOLD, CYAN


class NPC:
    def __init__(self, x, y, name, role, dialogue_id):
        self.rect        = pygame.Rect(x, y, 46, 46)
        self.name        = name
        self.role        = role
        self.dialogue_id = dialogue_id
        self.alive       = True
        self._anim       = 0.0

    def update(self, dt):
        self._anim += dt

    def draw(self, surface, camera):
        self._anim += 0.016   # fallback tick if update() not called

        sr  = camera.apply_rect(self.rect)
        cx, cy = sr.centerx, sr.centery
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        if self.role == "blacksmith":
            self._draw_blacksmith(surface, sr, cx, cy, x, y, w, h)
        elif self.role == "healer":
            self._draw_healer(surface, sr, cx, cy, x, y, w, h)
        else:
            self._draw_generic(surface, sr, cx, cy, x, y, w, h)

    # ---- blacksmith (gold, blocky, anvil silhouette) ------------------
    def _draw_blacksmith(self, surface, sr, cx, cy, x, y, w, h):
        # body – stocky dark gold
        pygame.draw.rect(surface, (140, 90, 10), sr, border_radius=5)

        # apron
        apron = pygame.Rect(x + 6, y + h // 3, w - 12, h * 2 // 3)
        pygame.draw.rect(surface, (80, 50, 10), apron, border_radius=3)

        # helmet top
        helmet = pygame.Rect(x + 4, y - 8, w - 8, 12)
        pygame.draw.rect(surface, (160, 110, 20), helmet, border_radius=3)
        pygame.draw.rect(surface, (200, 150, 40), helmet, 1, border_radius=3)

        # visor slit
        pygame.draw.rect(surface, (40, 20, 0),
                         pygame.Rect(x + 8, y + 6, w - 16, 7), border_radius=2)
        pygame.draw.rect(surface, (255, 180, 40),
                         pygame.Rect(x + 8, y + 8, w - 16, 2), border_radius=1)

        # hammer arm (animated bob)
        bob   = int(math.sin(self._anim * 3) * 3)
        h_arm = pygame.Rect(x + w - 4, y + 10 + bob, 12, 5)
        pygame.draw.rect(surface, (100, 70, 10), h_arm, border_radius=2)
        pygame.draw.rect(surface, (180, 130, 30),
                         pygame.Rect(x + w + 4, y + 4 + bob, 10, 14), border_radius=3)

        # belt buckle
        pygame.draw.rect(surface, (220, 170, 50),
                         pygame.Rect(cx - 4, cy + 4, 8, 6), border_radius=1)

    # ---- healer (green, robed, cross symbol) --------------------------
    def _draw_healer(self, surface, sr, cx, cy, x, y, w, h):
        # robe
        pygame.draw.rect(surface, (30, 120, 60), sr, border_radius=8)

        # hood
        hood_pts = [(x + 2, y + 8), (cx, y - 10), (x + w - 2, y + 8)]
        pygame.draw.polygon(surface, (20, 90, 45), hood_pts)

        # glowing cross on chest
        pulse = int(2 * math.sin(self._anim * 2))
        cross_col = (80, 255, 140)
        bar_v = pygame.Rect(cx - 2, cy - 8 - pulse, 4, 16 + pulse * 2)
        bar_h = pygame.Rect(cx - 7, cy - 2,         14, 4)
        pygame.draw.rect(surface, cross_col, bar_v, border_radius=1)
        pygame.draw.rect(surface, cross_col, bar_h, border_radius=1)

        # gentle eyes
        eye_y = y + h // 3
        pygame.draw.circle(surface, (150, 255, 180), (cx - 6, eye_y), 3)
        pygame.draw.circle(surface, (150, 255, 180), (cx + 6, eye_y), 3)

        # floating sparkle
        t = self._anim
        for i in range(2):
            angle = t * 1.8 + i * math.pi
            sx = cx + int(math.cos(angle) * 18)
            sy = cy + int(math.sin(angle) * 14) - 6
            pygame.draw.circle(surface, (180, 255, 200), (sx, sy), 2)

    # ---- generic NPC (teal, simple merchant) --------------------------
    def _draw_generic(self, surface, sr, cx, cy, x, y, w, h):
        # body
        pygame.draw.rect(surface, (20, 140, 160), sr, border_radius=6)

        # hat
        brim = pygame.Rect(x - 2, y + 2, w + 4, 6)
        pygame.draw.rect(surface, (10, 100, 120), brim, border_radius=2)
        top = pygame.Rect(x + 6, y - 10, w - 12, 12)
        pygame.draw.rect(surface, (10, 100, 120), top, border_radius=3)

        # face
        eye_y = y + h // 3
        pygame.draw.circle(surface, (200, 240, 255), (cx - 5, eye_y), 3)
        pygame.draw.circle(surface, (200, 240, 255), (cx + 5, eye_y), 3)

        # coin bag
        bag = pygame.Rect(x - 8, cy, 10, 12)
        pygame.draw.ellipse(surface, (180, 150, 20), bag)
        pygame.draw.circle(surface, (220, 190, 40), (bag.centerx, bag.top + 3), 3)
