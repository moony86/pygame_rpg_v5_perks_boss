import pygame
from settings import GREEN, GOLD, CYAN


class NPC:
    def __init__(self, x, y, name, role, dialogue_id):
        self.rect = pygame.Rect(x, y, 46, 46)
        self.name = name
        self.role = role
        self.dialogue_id = dialogue_id
        self.alive = True

    def draw(self, surface, camera):
        rect = camera.apply_rect(self.rect)
        if self.role == "blacksmith":
            color = GOLD
        elif self.role == "healer":
            color = GREEN
        else:
            color = CYAN
        pygame.draw.rect(surface, color, rect, border_radius=8)
