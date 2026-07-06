import pygame

from settings import DEV_TOOLS_ENABLED


PADDING = 12


class WaveDesignerPanel:
    def __init__(self, wave_designer):
        self.wave_designer = wave_designer
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        self.rect = pygame.Rect(1120, 610, 760, 430)
        self.export_rect = pygame.Rect(self.rect.x + PADDING, self.rect.bottom - 40, 180, 26)

    def handle_event(self, event):
        if not DEV_TOOLS_ENABLED or not self.wave_designer.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.export_rect.collidepoint(event.pos):
                self.wave_designer.export()
                return True
            return self.rect.collidepoint(event.pos)
        return self.rect.collidepoint(getattr(event, "pos", (-1, -1)))

    def draw(self, surface):
        if not DEV_TOOLS_ENABLED or not self.wave_designer.visible:
            return

        data = self.wave_designer.snapshot()
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill((8, 11, 18, 230))
        surface.blit(panel, self.rect.topleft)
        pygame.draw.rect(surface, (120, 200, 255), self.rect, 2, border_radius=8)

        self._text(surface, "WAVE DESIGNER", self.rect.x + PADDING, self.rect.y + 10, (190, 230, 255), self.font)
        self._text(surface, "Read-only inspection | JSON report export only", self.rect.x + PADDING, self.rect.y + 34, (150, 170, 190), self.small_font)

        y = self.rect.y + 62
        for line in self.wave_designer.lines()[:14]:
            self._text(surface, line, self.rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 18

        self._draw_timeline(surface, data["timeline"])
        self._draw_composition(surface, data["enemy_composition"])
        self._draw_queue(surface, data["remaining_spawn_queue"])
        self._draw_history(surface, data["spawn_history"])
        self._button(surface, self.export_rect, "Export Wave Report")
        self._text(surface, self.wave_designer.message, self.export_rect.right + 16, self.export_rect.y + 5, (120, 245, 180), self.small_font)

    def _draw_timeline(self, surface, timeline):
        x = self.rect.x + 310
        y = self.rect.y + 68
        self._text(surface, "Timeline", x, y - 22, (255, 235, 120), self.small_font)
        width = 410
        if not timeline:
            return
        step_w = max(28, width // len(timeline))
        for index, item in enumerate(timeline):
            box = pygame.Rect(x + index * step_w, y, step_w - 4, 24)
            color = (70, 160, 230)
            if item["type"] == "break":
                color = (120, 120, 150)
            elif item["type"] == "complete":
                color = (120, 210, 140)
            pygame.draw.rect(surface, color, box, border_radius=4)
            label = "S" if item["type"] == "spawn" else ("B" if item["type"] == "break" else "C")
            self._text(surface, label, box.x + 8, box.y + 5, (10, 15, 20), self.small_font)

    def _draw_composition(self, surface, rows):
        x = self.rect.x + 310
        y = self.rect.y + 124
        self._text(surface, "Enemy Composition", x, y - 22, (255, 235, 120), self.small_font)
        self._text(surface, "type                 count  rem  cost", x, y, (150, 170, 190), self.small_font)
        y += 18
        for row in rows[:8]:
            text = f"{row['enemy_type'][:20]:20} {row['current_count']:>5} {row['remaining_count']:>4} {str(row['threat_cost']):>5}"
            self._text(surface, text, x, y, (230, 235, 245), self.small_font)
            y += 18

    def _draw_queue(self, surface, queue):
        x = self.rect.x + 310
        y = self.rect.y + 304
        self._text(surface, "Remaining Spawn Queue", x, y - 22, (255, 235, 120), self.small_font)
        text = ", ".join(queue[:10]) if queue else "-"
        if len(queue) > 10:
            text += f" ... +{len(queue) - 10}"
        self._text(surface, text[:72], x, y, (230, 235, 245), self.small_font)

    def _draw_history(self, surface, history):
        x = self.rect.x + PADDING
        y = self.rect.y + 322
        self._text(surface, "Spawn History", x, y - 22, (255, 235, 120), self.small_font)
        for item in history[-4:]:
            text = f"wave={item['wave_index']} {item['enemy_type']} source={item['source']}"
            self._text(surface, text[:40], x, y, (230, 235, 245), self.small_font)
            y += 18

    def _button(self, surface, rect, label):
        pygame.draw.rect(surface, (30, 45, 64), rect, border_radius=5)
        pygame.draw.rect(surface, (72, 130, 170), rect, 1, border_radius=5)
        text = self.small_font.render(label, True, (230, 240, 250))
        surface.blit(text, text.get_rect(center=rect.center))

    def _text(self, surface, text, x, y, color, font):
        surface.blit(font.render(str(text), True, color), (x, y))
