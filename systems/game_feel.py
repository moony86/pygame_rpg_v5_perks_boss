import math
import random

import pygame
from config import CONFIG


class GameFeelSystem:
    HIT_STOP_NORMAL = 0.025
    HIT_STOP_KILL = 0.045
    HIT_STOP_ELITE_KILL = 0.060
    HIT_STOP_BOSS_PHASE = 0.070

    def __init__(self):
        self.hit_stop_timer = 0.0
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.shake_offset = pygame.Vector2(0, 0)

    def reset(self):
        self.hit_stop_timer = 0.0
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.shake_offset.update(0, 0)

    def update(self, dt):
        if self.hit_stop_timer > 0:
            self.hit_stop_timer = max(0.0, self.hit_stop_timer - dt)

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            progress = self.shake_timer / max(0.001, self.shake_duration)
            strength = self.shake_strength * progress * progress
            angle = random.uniform(0.0, math.tau)
            self.shake_offset.update(math.cos(angle) * strength, math.sin(angle) * strength)
        else:
            self.shake_offset.update(0, 0)

    def gameplay_paused(self):
        return self.hit_stop_timer > 0

    def normal_hit(self):
        self.hit_stop(self.HIT_STOP_NORMAL)

    def enemy_kill(self):
        self.hit_stop(self.HIT_STOP_KILL)
        self.shake(0.12, 3.0)

    def elite_kill(self):
        self.hit_stop(self.HIT_STOP_ELITE_KILL)
        self.shake(0.16, 5.0)

    def boss_phase(self):
        self.hit_stop(self.HIT_STOP_BOSS_PHASE)
        self.shake(0.22, 7.0)

    def room_clear(self):
        self.shake(0.25, 6.0)

    def player_hit(self):
        self.shake(0.10, 2.0)

    def hit_stop(self, duration):
        self.hit_stop_timer = max(self.hit_stop_timer, duration)

    def shake(self, duration, strength):
        if not CONFIG.get("screen_shake", True):
            self.shake_timer = 0.0
            self.shake_offset.update(0, 0)
            return
        remaining_strength = self.shake_strength * (self.shake_timer / max(0.001, self.shake_duration)) if self.shake_timer > 0 else 0.0
        if strength >= remaining_strength:
            self.shake_duration = max(0.001, duration)
            self.shake_timer = max(self.shake_timer, duration)
            self.shake_strength = strength
