import pygame


class CrosshairSystem:
    def __init__(self):
        self.radius = 8

    def draw(self, surface, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        x, y = mouse_pos

        # outline
        pygame.draw.circle(
            surface,
            (0, 0, 0),
            (x, y),
            self.radius + 1,
            2,
        )

        # main ring
        pygame.draw.circle(
            surface,
            (80, 220, 255),
            (x, y),
            self.radius,
            2,
        )

        # center dot
        pygame.draw.circle(
            surface,
            (255, 255, 255),
            (x, y),
            2,
        )