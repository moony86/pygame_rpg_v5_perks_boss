import pygame

from definitions.sprite_asset_definitions import SPRITE_ANIMATION_DEFINITIONS
from settings import DEV_TOOLS_ENABLED
from systems.sprite_animation import SpriteSheetAnimation, animation_spec


PADDING = 12


class AssetBrowser:
    def __init__(self, asset_pipeline):
        self.pipeline = asset_pipeline
        self.visible = False
        self.search_active = False
        self.search_text = ""
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        self.rect = pygame.Rect(1120, 70, 760, 520)
        self.preview_rect = pygame.Rect(self.rect.x + 430, self.rect.y + 76, 300, 220)
        self.animation_preview = None
        self.animation_preview_key = None
        self.animation_preview_tick = pygame.time.get_ticks()

    def toggle(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.visible = not self.visible
        if self.visible:
            self.pipeline.scan()

    def handle_event(self, event):
        if not DEV_TOOLS_ENABLED or not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self._handle_click(event.pos)
            return False
        return self.rect.collidepoint(getattr(event, "pos", (-1, -1)))

    def draw(self, surface):
        if not DEV_TOOLS_ENABLED or not self.visible:
            return
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill((8, 11, 18, 232))
        surface.blit(panel, self.rect.topleft)
        pygame.draw.rect(surface, (120, 200, 255), self.rect, 2, border_radius=8)
        self._text(surface, "ASSET BROWSER", self.rect.x + PADDING, self.rect.y + 10, (190, 230, 255), self.font)
        self._text(surface, "Developer-only | scan/validate/report | no file moves", self.rect.x + PADDING, self.rect.y + 34, (150, 170, 190), self.small_font)

        self._draw_asset_list(surface)
        self._draw_preview(surface)
        self._draw_details(surface)
        self._draw_validation(surface)
        self._draw_buttons(surface)

    def _handle_key(self, event):
        if self.search_active:
            if event.key == pygame.K_ESCAPE:
                self.search_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
                self.pipeline.set_search(self.search_text)
            elif event.key == pygame.K_RETURN:
                self.search_active = False
            elif getattr(event, "unicode", "") and event.unicode.isprintable():
                self.search_text += event.unicode
                self.pipeline.set_search(self.search_text)
            return True

        if event.key == pygame.K_UP:
            self.pipeline.select_previous()
        elif event.key == pygame.K_DOWN:
            self.pipeline.select_next()
        elif event.key == pygame.K_SLASH:
            self.search_active = True
        elif event.key == pygame.K_f:
            self.pipeline.cycle_filter()
        elif event.key == pygame.K_r:
            self.pipeline.reload_selected_asset()
        elif event.key == pygame.K_F5:
            self.pipeline.reload_all_assets()
        else:
            return False
        return True

    def _handle_click(self, pos):
        for item in self._buttons():
            if item["rect"].collidepoint(pos):
                item["action"]()
                return True

        list_rect = pygame.Rect(self.rect.x + PADDING, self.rect.y + 76, 390, 230)
        if list_rect.collidepoint(pos):
            row = (pos[1] - list_rect.y) // 20
            assets = self.pipeline.filtered_assets()
            if 0 <= row < len(assets):
                self.pipeline.selected_index = row
            return True
        return True

    def _draw_asset_list(self, surface):
        x = self.rect.x + PADDING
        y = self.rect.y + 76
        self._text(surface, f"Assets filter={self.pipeline.filter_type} search='{self.pipeline.search_text}'", x, y - 22, (255, 235, 120), self.small_font)
        assets = self.pipeline.filtered_assets()
        for index, asset in enumerate(assets[:11]):
            color = (255, 235, 120) if index == self.pipeline.selected_index else (230, 235, 245)
            label = f"{asset['asset_type'][:5]:5} {asset['path'][:44]}"
            self._text(surface, label, x, y + index * 20, color, self.small_font)

    def _draw_preview(self, surface):
        pygame.draw.rect(surface, (20, 28, 40), self.preview_rect, border_radius=6)
        pygame.draw.rect(surface, (72, 130, 170), self.preview_rect, 1, border_radius=6)
        asset = self.pipeline.selected_asset()
        if asset is None:
            return
        if asset["asset_type"] != "image" or asset.get("broken"):
            self._text(surface, "No texture preview", self.preview_rect.x + 72, self.preview_rect.centery - 8, (150, 170, 190), self.small_font)
            return
        if self._draw_animation_preview(surface, asset):
            return
        try:
            image = pygame.image.load(asset["absolute_path"])
        except (pygame.error, OSError):
            self._text(surface, "Preview failed", self.preview_rect.x + 86, self.preview_rect.centery - 8, (255, 120, 120), self.small_font)
            return
        scale = min(self.preview_rect.w / image.get_width(), self.preview_rect.h / image.get_height(), 1.0)
        size = (max(1, int(image.get_width() * scale)), max(1, int(image.get_height() * scale)))
        image = pygame.transform.smoothscale(image, size)
        surface.blit(image, image.get_rect(center=self.preview_rect.center))

    def _draw_animation_preview(self, surface, asset):
        preview_key = self._animation_preview_key(asset["path"])
        if preview_key is None:
            return False

        character, state = preview_key
        if self.animation_preview_key != preview_key:
            self.animation_preview = SpriteSheetAnimation(character, state, scale=0.62)
            self.animation_preview_key = preview_key
            self.animation_preview_tick = pygame.time.get_ticks()

        now = pygame.time.get_ticks()
        dt = max(0.0, min(0.08, (now - self.animation_preview_tick) / 1000.0))
        self.animation_preview_tick = now
        self.animation_preview.update(dt)

        feet = (self.preview_rect.centerx, self.preview_rect.bottom - 18)
        if not self.animation_preview.draw(surface, feet):
            return False

        spec = animation_spec(character, state)
        frames = self.animation_preview.frames
        self._text(
            surface,
            f"{character}/{state} frames={len(frames)} fps={spec.fps:g} loop={spec.loop}",
            self.preview_rect.x + 12,
            self.preview_rect.y + 10,
            (190, 230, 255),
            self.small_font,
        )
        self._text(
            surface,
            "sliced preview",
            self.preview_rect.x + 12,
            self.preview_rect.y + 28,
            (120, 245, 180),
            self.small_font,
        )
        return True

    def _animation_preview_key(self, path):
        for character, character_def in SPRITE_ANIMATION_DEFINITIONS.items():
            for state, state_def in character_def.get("states", {}).items():
                if "alias" in state_def:
                    continue
                if state_def.get("path") == path:
                    return character, state
        return None

    def _draw_details(self, surface):
        asset = self.pipeline.selected_asset()
        x = self.rect.x + 430
        y = self.rect.y + 320
        self._text(surface, "Details", x, y - 22, (255, 235, 120), self.small_font)
        if asset is None:
            return
        resolution = asset["resolution"] or "-"
        last_loaded = f"{asset['last_loaded']:.0f}" if asset["last_loaded"] else "-"
        lines = [
            f"path: {asset['path']}",
            f"type: {asset['asset_type']} res: {resolution}",
            f"memory: {asset['memory_bytes']} bytes",
            f"load count: {asset['load_count']} last: {last_loaded}",
            f"refs: {len(asset['references'])} broken: {asset['broken']}",
            "deps: " + (", ".join(asset["references"][:2]) if asset["references"] else "-"),
        ]
        for line in lines:
            self._text(surface, line[:48], x, y, (230, 235, 245), self.small_font)
            y += 18

    def _draw_validation(self, surface):
        validation = self.pipeline.validation
        x = self.rect.x + PADDING
        y = self.rect.y + 326
        self._text(surface, "Validation", x, y - 22, (255, 235, 120), self.small_font)
        lines = [
            f"missing: {len(validation['missing_assets'])}",
            f"duplicates: {len(validation['duplicate_assets'])}",
            f"unused: {len(validation['unused_assets'])}",
            f"broken: {len(validation['broken_references'])}",
        ]
        for line in lines:
            self._text(surface, line, x, y, (230, 235, 245), self.small_font)
            y += 18
        first_missing = validation["missing_assets"][:2]
        for item in first_missing:
            self._text(surface, f"missing {item}"[:52], x, y, (255, 135, 120), self.small_font)
            y += 18

    def _draw_buttons(self, surface):
        for item in self._buttons():
            self._button(surface, item["rect"], item["label"])
        self._text(surface, self.pipeline.message, self.rect.x + PADDING, self.rect.bottom - 24, (120, 245, 180), self.small_font)

    def _buttons(self):
        x = self.rect.x + PADDING
        y = self.rect.bottom - 74
        w = 118
        gap = 8
        labels = [
            ("Scan", self.pipeline.scan),
            ("Reload", self.pipeline.reload_selected_asset),
            ("Reload All", self.pipeline.reload_all_assets),
            ("Copy Path", self.pipeline.copy_asset_path),
            ("Open Folder", self.pipeline.open_folder),
            ("Report", self.pipeline.export_report),
        ]
        return [
            {"label": label, "action": action, "rect": pygame.Rect(x + (w + gap) * index, y, w, 26)}
            for index, (label, action) in enumerate(labels)
        ]

    def _button(self, surface, rect, label):
        pygame.draw.rect(surface, (30, 45, 64), rect, border_radius=5)
        pygame.draw.rect(surface, (72, 130, 170), rect, 1, border_radius=5)
        text = self.small_font.render(label, True, (230, 240, 250))
        surface.blit(text, text.get_rect(center=rect.center))

    def _text(self, surface, text, x, y, color, font):
        surface.blit(font.render(str(text), True, color), (x, y))
