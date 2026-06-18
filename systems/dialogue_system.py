import pygame
from settings import SCREEN_WIDTH, WHITE, BLACK


class DialogueSystem:
    def __init__(self, font, dialogues):
        self.font = font
        self.dialogues = dialogues
        self.active = False
        self.current_speaker = ""
        self.current_text = ""

    def show(self, speaker, text):
        self.active = True
        self.current_speaker = speaker
        self.current_text = text

    def toggle_npc(self, npc):
        if self.active and self.current_speaker == npc.name:
            self.close()
            return
        self.show(npc.name, self.dialogues.get(npc.dialogue_id, "..."))

    def close(self):
        self.active = False
        self.current_speaker = ""
        self.current_text = ""

    def draw(self, surface):
        if not self.active:
            return

        box_rect = pygame.Rect(50, 455, SCREEN_WIDTH - 100, 145)
        pygame.draw.rect(surface, BLACK, box_rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, box_rect, 2, border_radius=8)

        full_text = f"{self.current_speaker}: {self.current_text}"
        self._draw_wrapped_text(surface, full_text, box_rect.x + 18, box_rect.y + 16, box_rect.width - 36)

    def _draw_wrapped_text(self, surface, text, x, y, max_width):
        words = text.split(" ")
        line = ""
        line_height = self.font.get_linesize()

        for word in words:
            test_line = line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                line = test_line
            else:
                surface.blit(self.font.render(line, True, WHITE), (x, y))
                y += line_height
                line = word + " "

        if line:
            surface.blit(self.font.render(line, True, WHITE), (x, y))
