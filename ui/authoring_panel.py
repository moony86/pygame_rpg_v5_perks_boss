import pygame

from settings import DEV_TOOLS_ENABLED, MAP_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH


PADDING = 12
BUTTON_H = 26
HANDLE_SIZE = 10


class AuthoringPanel:
    def __init__(self, game, authoring, room_loader=None):
        self.game = game
        self.authoring = authoring
        self.room_loader = room_loader
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        self.rect = pygame.Rect(1120, 70, 360, 520)
        self.drag_mode = None
        self.grab_offset = pygame.Vector2(0, 0)

    def handle_event(self, event):
        if not DEV_TOOLS_ENABLED or not self.authoring.active:
            return False

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self._handle_click(event.pos)
            return self._handle_world_mouse_down(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_mode:
                self.drag_mode = None
                return True
            return False

        if event.type == pygame.MOUSEMOTION and self.drag_mode:
            world_pos = self.game.camera.screen_to_world(event.pos)
            if self.drag_mode == "move":
                self.authoring.drag_selected_to(world_pos, self.grab_offset)
            elif self.drag_mode == "resize":
                self.authoring.resize_selected_to(world_pos)
            return True

        return self.rect.collidepoint(getattr(event, "pos", (-1, -1)))

    def _handle_key(self, event):
        step = self.authoring.grid_size if self.authoring.snap_enabled else 8
        if event.key == pygame.K_DELETE:
            self.authoring.delete_selected()
        elif event.key == pygame.K_d and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.authoring.duplicate_selected()
        elif event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.authoring.export()
        elif event.key == pygame.K_g:
            self.authoring.toggle_grid()
        elif event.key == pygame.K_s:
            self.authoring.toggle_snap()
        elif event.key == pygame.K_TAB:
            self.authoring.cycle_grid_size()
        elif event.key == pygame.K_LEFT:
            self.authoring.move_selected(-step, 0)
        elif event.key == pygame.K_RIGHT:
            self.authoring.move_selected(step, 0)
        elif event.key == pygame.K_UP:
            self.authoring.move_selected(0, -step)
        elif event.key == pygame.K_DOWN:
            self.authoring.move_selected(0, step)
        elif event.key == pygame.K_EQUALS:
            self.authoring.resize_selected(step, step)
        elif event.key == pygame.K_MINUS:
            self.authoring.resize_selected(-step, -step)
        else:
            return False
        return True

    def _handle_click(self, pos):
        for item in self._layout():
            if item["rect"].collidepoint(pos):
                item["action"]()
                return True
        return True

    def _handle_world_mouse_down(self, pos):
        selected = self.authoring.selected()
        if selected is not None and self._resize_handle(selected).collidepoint(pos):
            self.drag_mode = "resize"
            return True

        if self.authoring.select_at_screen_pos(pos):
            selected = self.authoring.selected()
            if selected is not None:
                world_pos = self.game.camera.screen_to_world(pos)
                self.grab_offset = pygame.Vector2(world_pos.x - selected.rect.x, world_pos.y - selected.rect.y)
                self.drag_mode = "move"
            return True
        return False

    def draw(self, surface):
        if not DEV_TOOLS_ENABLED or not self.authoring.active:
            return
        if not self.authoring.context_matches_current_scene():
            self.authoring.message = "authoring context hidden: scene changed"
            return
        self._draw_grid(surface)
        self._draw_gizmos(surface)
        self._draw_panel(surface)

    def _layout(self):
        x = self.rect.x + PADDING
        y = self.rect.y + 178
        w = self.rect.w - PADDING * 2
        items = []

        def row(buttons):
            nonlocal y
            bw = (w - 8 * (len(buttons) - 1)) // len(buttons)
            bx = x
            for label, action in buttons:
                items.append({"label": label, "action": action, "rect": pygame.Rect(bx, y, bw, BUTTON_H)})
                bx += bw + 8
            y += BUTTON_H + 8

        row([
            ("Obstacle", lambda: self.authoring.create("Obstacle")),
            ("Portal", lambda: self.authoring.create("Portal")),
        ])
        row([
            ("NPC", lambda: self.authoring.create("NPC")),
            ("Spawn Zone", lambda: self.authoring.create("Spawn Zone")),
        ])
        row([
            ("Room Exit", lambda: self.authoring.create("Room Exit")),
            ("Duplicate", self.authoring.duplicate_selected),
        ])
        row([
            ("Delete", self.authoring.delete_selected),
            ("Export", self.authoring.export),
        ])
        if self.room_loader is not None:
            row([
                ("Preview JSON", self.room_loader.preview_current_room),
                ("Apply Preview", self.room_loader.apply_to_current_room),
            ])
        row([
            ("Grid", self.authoring.toggle_grid),
            ("Snap", self.authoring.toggle_snap),
            ("Size", self.authoring.cycle_grid_size),
        ])
        return items

    def _draw_panel(self, surface):
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill((8, 11, 18, 226))
        surface.blit(panel, self.rect.topleft)
        pygame.draw.rect(surface, (110, 190, 250), self.rect, 2, border_radius=8)

        self._draw_text(surface, "ROOM AUTHORING v1", self.rect.x + PADDING, self.rect.y + 12, (190, 230, 255), self.font)
        self._draw_text(surface, "Draft only | no auto-load | export room_layout.json", self.rect.x + PADDING, self.rect.y + 38, (150, 170, 190), self.small_font)

        state_lines = [
            f"Objects: {len(self.authoring.objects)}",
            f"Grid: {'on' if self.authoring.grid_visible else 'off'} size={self.authoring.grid_size}",
            f"Snap: {'on' if self.authoring.snap_enabled else 'off'}",
            "Keys: Del delete | Ctrl+D duplicate | Ctrl+E export",
            "Move: drag/arrows | Resize: handle or +/-",
        ]
        y = self.rect.y + 66
        for line in state_lines:
            self._draw_text(surface, line, self.rect.x + PADDING, y, (225, 232, 240), self.small_font)
            y += 18

        for item in self._layout():
            self._draw_button(surface, item)

        y = self.rect.y + 366
        self._draw_text(surface, "Selection", self.rect.x + PADDING, y, (255, 235, 120), self.small_font)
        y += 22
        for line in self.authoring.selected_lines()[:5]:
            self._draw_text(surface, line, self.rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 18

        if self.room_loader is not None:
            y += 4
            self._draw_text(surface, "Loader", self.rect.x + PADDING, y, (255, 235, 120), self.small_font)
            y += 18
            for line in self.room_loader.report_lines()[:4]:
                self._draw_text(surface, line[:46], self.rect.x + PADDING, y, (230, 235, 245), self.small_font)
                y += 16

        self._draw_text(surface, self.authoring.message, self.rect.x + PADDING, self.rect.bottom - 28, (120, 245, 180), self.small_font)

    def _draw_gizmos(self, surface):
        for obj in self.authoring.objects:
            sr = self.game.camera.apply_rect(obj.rect)
            selected = obj.id == self.authoring.selected_id
            color = self._object_color(obj.type)
            width = 3 if selected else 1
            pygame.draw.rect(surface, color, sr, width, border_radius=3)
            center = sr.center
            pygame.draw.line(surface, color, (center[0] - 6, center[1]), (center[0] + 6, center[1]), 1)
            pygame.draw.line(surface, color, (center[0], center[1] - 6), (center[0], center[1] + 6), 1)
            label = f"{obj.id} {obj.rect.x},{obj.rect.y} {obj.rect.w}x{obj.rect.h}"
            self._draw_text(surface, label, sr.x, sr.y - 18, color, self.small_font)
            if selected:
                handle = self._resize_handle(obj)
                pygame.draw.rect(surface, (255, 255, 120), handle)

    def _draw_grid(self, surface):
        if not self.authoring.grid_visible:
            return
        grid = self.authoring.grid_size
        offset_x = int(self.game.camera.offset.x)
        offset_y = int(self.game.camera.offset.y)
        start_x = -(offset_x % grid)
        start_y = -(offset_y % grid)
        color = (45, 55, 70)
        for x in range(start_x, SCREEN_WIDTH, grid):
            pygame.draw.line(surface, color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(start_y, SCREEN_HEIGHT, grid):
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y), 1)

    def _resize_handle(self, obj):
        sr = self.game.camera.apply_rect(obj.rect)
        return pygame.Rect(sr.right - HANDLE_SIZE, sr.bottom - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)

    def _object_color(self, object_type):
        return {
            "Obstacle": (80, 255, 120),
            "Portal": (180, 120, 255),
            "NPC": (80, 220, 255),
            "Spawn Zone": (255, 210, 80),
            "Room Exit": (255, 140, 60),
        }.get(object_type, (240, 240, 240))

    def _draw_text(self, surface, text, x, y, color, font):
        surface.blit(font.render(str(text), True, color), (x, y))

    def _draw_button(self, surface, item):
        pygame.draw.rect(surface, (30, 45, 64), item["rect"], border_radius=5)
        pygame.draw.rect(surface, (72, 130, 170), item["rect"], 1, border_radius=5)
        text = self.small_font.render(item["label"], True, (230, 240, 250))
        surface.blit(text, text.get_rect(center=item["rect"].center))
