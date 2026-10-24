import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

DIALOGUE_WIDTH_RATIO = 0.92
DIALOGUE_HEIGHT = 92
DIALOGUE_BOTTOM_MARGIN = 82


class DialogueSystem:
    def __init__(self, font, dialogues):
        self.font = font
        self.dialogues = dialogues
        self.active = False
        self.current_speaker = ""
        self.current_text = ""
        self._cached_key = None
        self._cached_surfaces = []

    def show(self, speaker, text):
        self.active = True
        self.current_speaker = speaker
        self.current_text = text
        self._cached_key = None

    def toggle_npc(self, npc):
        if self.active and self.current_speaker == npc.name:
            self.close()
            return
        self.show(npc.name, self.dialogues.get(npc.dialogue_id, "..."))

    def close(self):
        self.active = False
        self.current_speaker = ""
        self.current_text = ""
        self._cached_key = None
        self._cached_surfaces = []

    def draw(self, surface):
        if not self.active:
            return

        width = int(SCREEN_WIDTH * DIALOGUE_WIDTH_RATIO)
        box_rect = pygame.Rect(
            (SCREEN_WIDTH - width) // 2,
            SCREEN_HEIGHT - DIALOGUE_BOTTOM_MARGIN - DIALOGUE_HEIGHT,
            width,
            DIALOGUE_HEIGHT,
        )
        pygame.draw.rect(surface, (11,20,30), box_rect, border_radius=10)
        pygame.draw.line(surface, (81,177,197), box_rect.topleft, box_rect.topright, 2)

        full_text = f"{self.current_speaker}: {self.current_text}"
        self._draw_wrapped_text(surface, full_text, box_rect.x + 18, box_rect.y + 16, box_rect.width - 36)

    def _draw_wrapped_text(self, surface, text, x, y, max_width):
        cache_key = (text, max_width)
        if self._cached_key != cache_key:
            self._cached_key = cache_key
            self._cached_surfaces = [
                self.font.render(line, True, WHITE)
                for line in self._wrap_lines(text, max_width)
            ]
        line_height = self.font.get_linesize()
        for rendered in self._cached_surfaces:
            surface.blit(rendered, (x, y))
            y += line_height

    def _wrap_lines(self, text, max_width):
        words = text.split(" ")
        line = ""
        lines = []

        for word in words:
            test_line = line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word + " "

        if line:
            lines.append(line)
        return lines
