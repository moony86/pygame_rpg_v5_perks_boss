"""Legacy NPC copy.

Active runtime code imports entities.npc. Keep this file as a temporary
reference only until the legacy folder is removed after validation.
"""

import pygame
import math
from settings import GREEN, GOLD, CYAN, MAP_SIZE


class NPC:
    def __init__(self, x, y, name, role, dialogue_id):
        self.rect        = pygame.Rect(x, y, 46, 46)
        self.name        = name
        self.role        = role
        self.dialogue_id = dialogue_id
        self.alive       = True
        self._anim       = 0.0

        # ── memory ──────────────────────────────────────────────────────
        # visit_count persists across HUB entries within one run.
        # scene_system increments it each time enter_hub() is called.
        self.visit_count = 0

    def greet(self, player, room_number, rooms_to_boss, room_type_name=""):
        """
        Return the dialogue_id that best fits the current situation.
        Called by scene_system (or input_system) when the player presses E.
        Falls back to the default intro if nothing specific matches.
        """
        v = self.visit_count

        if self.role == "blacksmith":
            if v == 0:
                return "blacksmith_intro"
            if player.health < player.max_health * 0.35:
                return "blacksmith_lowhp"
            if player.gold >= 120:
                return "blacksmith_rich"
            if player.gold < 30:
                return "blacksmith_broke"
            if v >= 5:
                return "blacksmith_veteran"
            return "blacksmith_return"

        if self.role == "healer":
            if v == 0:
                return "healer_intro"
            if player.health >= player.max_health:
                return "healer_fullhp"
            if player.health < player.max_health * 0.25:
                return "healer_critical"
            if v >= 5:
                return "healer_veteran"
            return "healer_return"

        if self.role == "portal":
            if v == 0:
                return "portal_intro"
            if room_number >= rooms_to_boss - 1:
                return "portal_boss_near"
            if v >= 5:
                return "portal_veteran"
            return "portal_return"

        if self.role == "seer":
            if v == 0:
                return "seer_intro"
            if v >= 6:
                return "seer_veteran"
            if room_number >= rooms_to_boss - 1:
                return "seer_boss_near"
            # hint based on upcoming room type
            hints = {
                "SURVIVAL":  "seer_survival",
                "TREASURE":  "seer_treasure",
                "CURSE":     "seer_curse",
                "ELITE":     "seer_elite_warning",
            }
            for key, dialogue in hints.items():
                if key in room_type_name.upper():
                    return dialogue
            return "seer_normal"

        return self.dialogue_id

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
        elif self.role == "seer":
            self._draw_seer(surface, sr, cx, cy, x, y, w, h)
        else:
            self._draw_generic(surface, sr, cx, cy, x, y, w, h)

    # ── blacksmith (gold, blocky, anvil silhouette) ──────────────────────
    def _draw_blacksmith(self, surface, sr, cx, cy, x, y, w, h):
        pygame.draw.rect(surface, (140, 90, 10), sr, border_radius=5)
        apron = pygame.Rect(x + 6, y + h // 3, w - 12, h * 2 // 3)
        pygame.draw.rect(surface, (80, 50, 10), apron, border_radius=3)
        helmet = pygame.Rect(x + 4, y - 8, w - 8, 12)
        pygame.draw.rect(surface, (160, 110, 20), helmet, border_radius=3)
        pygame.draw.rect(surface, (200, 150, 40), helmet, 1, border_radius=3)
        pygame.draw.rect(surface, (40, 20, 0),
                         pygame.Rect(x + 8, y + 6, w - 16, 7), border_radius=2)
        pygame.draw.rect(surface, (255, 180, 40),
                         pygame.Rect(x + 8, y + 8, w - 16, 2), border_radius=1)
        bob   = int(math.sin(self._anim * 3) * 3)
        h_arm = pygame.Rect(x + w - 4, y + 10 + bob, 12, 5)
        pygame.draw.rect(surface, (100, 70, 10), h_arm, border_radius=2)
        pygame.draw.rect(surface, (180, 130, 30),
                         pygame.Rect(x + w + 4, y + 4 + bob, 10, 14), border_radius=3)
        pygame.draw.rect(surface, (220, 170, 50),
                         pygame.Rect(cx - 4, cy + 4, 8, 6), border_radius=1)

    # ── healer (green, robed, cross symbol) ─────────────────────────────
    def _draw_healer(self, surface, sr, cx, cy, x, y, w, h):
        pygame.draw.rect(surface, (30, 120, 60), sr, border_radius=8)
        hood_pts = [(x + 2, y + 8), (cx, y - 10), (x + w - 2, y + 8)]
        pygame.draw.polygon(surface, (20, 90, 45), hood_pts)
        pulse = int(2 * math.sin(self._anim * 2))
        cross_col = (80, 255, 140)
        pygame.draw.rect(surface, cross_col,
                         pygame.Rect(cx - 2, cy - 8 - pulse, 4, 16 + pulse * 2), border_radius=1)
        pygame.draw.rect(surface, cross_col,
                         pygame.Rect(cx - 7, cy - 2, 14, 4), border_radius=1)
        eye_y = y + h // 3
        pygame.draw.circle(surface, (150, 255, 180), (cx - 6, eye_y), 3)
        pygame.draw.circle(surface, (150, 255, 180), (cx + 6, eye_y), 3)
        t = self._anim
        for i in range(2):
            angle = t * 1.8 + i * math.pi
            sx = cx + int(math.cos(angle) * 18)
            sy = cy + int(math.sin(angle) * 14) - 6
            pygame.draw.circle(surface, (180, 255, 200), (sx, sy), 2)

    # ── seer (new — dark robes, floating eye, slow orbit particles) ──────
    def _draw_seer(self, surface, sr, cx, cy, x, y, w, h):
        # dark robe body
        pygame.draw.rect(surface, (35, 20, 65), sr, border_radius=10)

        # robe hem — slightly lighter at bottom
        hem = pygame.Rect(x + 2, y + h * 2 // 3, w - 4, h // 3)
        pygame.draw.rect(surface, (50, 30, 90), hem, border_radius=6)

        # tall pointed hood
        hood_pts = [
            (x,         y + 10),
            (cx,        y - 22),
            (x + w,     y + 10),
        ]
        pygame.draw.polygon(surface, (25, 12, 50), hood_pts)
        # hood outline
        pygame.draw.polygon(surface, (90, 60, 140), hood_pts, 1)

        # glowing eye on chest — slow pulse
        pulse = 0.5 + 0.5 * math.sin(self._anim * 1.4)
        eye_r = int(5 + 2 * pulse)
        eye_col = (
            int(120 + 80 * pulse),
            int(40  + 20 * pulse),
            int(200 + 55 * pulse),
        )
        pygame.draw.circle(surface, (10, 0, 20), (cx, cy - 2), eye_r + 3)  # dark surround
        pygame.draw.circle(surface, eye_col,     (cx, cy - 2), eye_r)
        pygame.draw.circle(surface, (230, 200, 255), (cx, cy - 2), max(1, eye_r - 3))  # inner glint

        # three slow-orbiting rune dots
        for i in range(3):
            angle = self._anim * 0.9 + i * (2 * math.pi / 3)
            rx = cx + int(math.cos(angle) * 20)
            ry = cy + int(math.sin(angle) * 16)
            rune_col = (
                int(100 + 80 * math.sin(self._anim + i)),
                20,
                int(180 + 75 * math.cos(self._anim * 0.7 + i)),
            )
            pygame.draw.circle(surface, rune_col, (rx, ry), 3)

        # visit_count indicator — small stars above head (1 per visit, max 5)
        stars = min(self.visit_count, 5)
        for s in range(stars):
            sx = x + 4 + s * 8
            sy = y - 10
            pygame.draw.circle(surface, (200, 180, 255), (sx, sy), 2)

    # ── generic NPC (teal, simple merchant) ─────────────────────────────
    def _draw_generic(self, surface, sr, cx, cy, x, y, w, h):
        pygame.draw.rect(surface, (20, 140, 160), sr, border_radius=6)
        brim = pygame.Rect(x - 2, y + 2, w + 4, 6)
        pygame.draw.rect(surface, (10, 100, 120), brim, border_radius=2)
        top = pygame.Rect(x + 6, y - 10, w - 12, 12)
        pygame.draw.rect(surface, (10, 100, 120), top, border_radius=3)
        eye_y = y + h // 3
        pygame.draw.circle(surface, (200, 240, 255), (cx - 5, eye_y), 3)
        pygame.draw.circle(surface, (200, 240, 255), (cx + 5, eye_y), 3)
        bag = pygame.Rect(x - 8, cy, 10, 12)
        pygame.draw.ellipse(surface, (180, 150, 20), bag)
        pygame.draw.circle(surface, (220, 190, 40), (bag.centerx, bag.top + 3), 3)
