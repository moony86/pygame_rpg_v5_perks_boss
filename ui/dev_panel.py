import pygame

from settings import DEV_TOOLS_ENABLED


PANEL_W = 520
PANEL_H = 760
PADDING = 14
ROW_H = 18
CATEGORIES = ["Overview", "Gameplay", "Builds", "Tuning", "Waves", "Assets", "Audio", "Benchmark", "Logs"]


class DevPanel:
    def __init__(
        self,
        game,
        dev_tools,
        authoring_panel=None,
        wave_designer_panel=None,
        wave_designer=None,
        asset_browser=None,
    ):
        self.game = game
        self.tools = dev_tools
        self.authoring_panel = authoring_panel
        self.wave_designer_panel = wave_designer_panel
        self.wave_designer = wave_designer
        self.asset_browser = asset_browser
        self.active = False
        self.active_category = "Overview"
        self.search_active = False
        self.perk_search_active = False
        self.search_text = ""
        self.perk_search_text = ""
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        self.rect = pygame.Rect(26, 70, PANEL_W, PANEL_H)
        self.inspector_rect = pygame.Rect(570, 70, 520, 420)
        self.log_rect = pygame.Rect(570, 510, 520, 360)

    def toggle(self):
        if not DEV_TOOLS_ENABLED:
            return
        self.active = not self.active

    def handle_event(self, event):
        if not DEV_TOOLS_ENABLED:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
            self.toggle()
            return True

        if not self.active:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.tools.toggle_author_mode()
            return True

        if self.active_category == "Rooms" and self.authoring_panel and self.authoring_panel.handle_event(event):
            return True
        if self.active_category == "Waves" and self.wave_designer_panel and self.wave_designer_panel.handle_event(event):
            return True
        if self.active_category == "Assets" and self.asset_browser and self.asset_browser.handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT and not self.rect.collidepoint(event.pos):
                return self.tools.select_at_screen_pos(event.pos)
            return self._handle_click(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            return self.tools.select_at_screen_pos(event.pos)

        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            return self.rect.collidepoint(getattr(event, "pos", (-1, -1)))

        return True

    def _handle_key(self, event):
        key = event.key
        if self.search_active:
            return self._handle_search_key(event)
        if self.perk_search_active:
            return self._handle_perk_search_key(event)

        if key == pygame.K_ESCAPE:
            self.active = False
        elif pygame.K_1 <= key <= pygame.K_9:
            self._set_category(CATEGORIES[key - pygame.K_1])
        elif key == pygame.K_F4:
            self.tools.open_room_exit()
        elif key == pygame.K_F6:
            self.tools.toggle_god_mode()
        elif key == pygame.K_F7:
            self.tools.toggle_hitboxes()
        elif key == pygame.K_F8:
            self.tools.cycle_selected_enemy()
        elif key == pygame.K_F9:
            self.tools.toggle_slow_motion()
        elif key == pygame.K_F11:
            self.tools.toggle_author_mode()
        elif key == pygame.K_f:
            self.tools.focus_selected()
        elif key == pygame.K_SLASH:
            if self.active_category == "Builds":
                self.perk_search_active = True
                self.perk_search_text = ""
                self.tools.set_perk_search("")
            else:
                self.search_active = True
                self.search_text = ""
                self.tools.search("")
        elif self.active_category == "Builds" and key in (pygame.K_LEFT, pygame.K_a):
            self.tools.select_previous_perk()
        elif self.active_category == "Builds" and key in (pygame.K_RIGHT, pygame.K_d):
            self.tools.select_next_perk()
        elif self.active_category == "Builds" and key == pygame.K_TAB:
            self.tools.cycle_perk_build_filter()
        elif self.active_category == "Builds" and key in (pygame.K_RETURN, pygame.K_g):
            self.tools.grant_selected_perk_next_pick()
        elif self.active_category == "Tuning" and key in (pygame.K_UP, pygame.K_w):
            self.tools.workspace.select_previous_tuning()
        elif self.active_category == "Tuning" and key in (pygame.K_DOWN, pygame.K_s):
            self.tools.workspace.select_next_tuning()
        elif self.active_category == "Tuning" and key in (pygame.K_LEFT, pygame.K_a):
            self.tools.workspace.edit_selected_tuning(-1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
        elif self.active_category == "Tuning" and key in (pygame.K_RIGHT, pygame.K_d):
            self.tools.workspace.edit_selected_tuning(1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
        elif self.active_category == "Tuning" and key == pygame.K_BACKSPACE:
            self.tools.workspace.reset_selected_tuning()
        elif self.active_category == "Audio" and key in (pygame.K_UP, pygame.K_DOWN):
            self.tools.workspace.select_next_audio()
        elif self.active_category == "Audio" and key in (pygame.K_RETURN, pygame.K_SPACE):
            self.tools.workspace.play_selected_audio()
        else:
            return True
        return True

    def _handle_search_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.search_active = False
        elif event.key == pygame.K_RETURN:
            self.tools.select_search_result(0)
            self.search_active = False
        elif event.key == pygame.K_BACKSPACE:
            self.search_text = self.search_text[:-1]
            self.tools.search(self.search_text)
        elif getattr(event, "unicode", "") and event.unicode.isprintable():
            self.search_text += event.unicode
            self.tools.search(self.search_text)
        return True

    def _handle_perk_search_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.perk_search_active = False
        elif event.key == pygame.K_RETURN:
            self.perk_search_active = False
        elif event.key == pygame.K_BACKSPACE:
            self.perk_search_text = self.perk_search_text[:-1]
            self.tools.set_perk_search(self.perk_search_text)
        elif getattr(event, "unicode", "") and event.unicode.isprintable():
            self.perk_search_text += event.unicode
            self.tools.set_perk_search(self.perk_search_text)
        return True

    def _set_category(self, category):
        if category not in CATEGORIES:
            return
        self.active_category = category
        if category != "Builds":
            self.perk_search_active = False
        self.tools.message = f"dev category: {category}"

    def _handle_click(self, pos):
        if not self.rect.collidepoint(pos):
            return True
        for item in self._category_layout():
            if item["rect"].collidepoint(pos):
                self._set_category(item["label"])
                return True
        for item in self._layout():
            if item["rect"].collidepoint(pos):
                item["action"]()
                return True
        return True

    def _layout(self):
        x = self.rect.x + PADDING
        y = self.rect.y + 435
        w = self.rect.w - PADDING * 2
        items = []

        def buttons(row):
            nonlocal y
            button_w = (w - 8 * (len(row) - 1)) // len(row)
            bx = x
            for label, action in row:
                items.append({
                    "label": label,
                    "action": action,
                    "rect": pygame.Rect(bx, y, button_w, 28),
                })
                bx += button_w + 8
            y += 32

        if self.active_category == "Overview":
            buttons([
                ("Clear Log", self.tools.clear_log),
                ("Pause Log", self.tools.toggle_log_pause),
                ("Auto Scroll", self.tools.toggle_log_auto_scroll),
            ])
        elif self.active_category == "Gameplay":
            buttons([
                ("Hitboxes F7", self.tools.toggle_hitboxes),
                ("Spawn Debug", self.tools.toggle_spawn_debug),
                ("Camera", self.tools.toggle_camera_debug),
            ])
            buttons([
                ("Collision", self.tools.toggle_collision_debug),
                ("Wave", self.tools.toggle_wave_debug),
                ("God F6", self.tools.toggle_god_mode),
            ])
            buttons([
                ("Slow F9", self.tools.toggle_slow_motion),
                ("Open Exit F4", self.tools.open_room_exit),
                ("Heal", self.tools.heal_player),
            ])
            buttons([
                ("Horde 100", lambda: self.tools.spawn_horde_test(100)),
                ("Horde 200", lambda: self.tools.spawn_horde_test(200)),
                ("Horde 300", lambda: self.tools.spawn_horde_test(300)),
            ])
            buttons([
                ("Horde 500", lambda: self.tools.spawn_horde_test(500)),
                ("Clear Horde", self.tools.clear_horde_test),
                ("-", lambda: None),
            ])
            buttons([
                ("Gold", self.tools.give_gold),
                ("Level Up", self.tools.force_level_up),
                ("Center", self.tools.teleport_player_to_center),
            ])
            buttons([
                ("+5 XP", lambda: self.tools.grant_xp(5)),
                ("+25 XP", lambda: self.tools.grant_xp(25)),
                ("+75 XP", lambda: self.tools.grant_xp(75)),
            ])
            buttons([
                ("+200 XP", lambda: self.tools.grant_xp(200)),
                ("+500 XP", lambda: self.tools.grant_xp(500)),
            ])
            buttons([
                ("Hub", self.tools.enter_hub),
                ("Legacy 10R", self.tools.enter_normal_room),
                ("Boss", self.tools.enter_boss_room),
            ])
            buttons([
                ("Proto Room", self.tools.enter_prototype_room),
                ("-", lambda: None),
                ("-", lambda: None),
            ])
        elif self.active_category == "Builds":
            buttons([
                ("Prev Perk", self.tools.select_previous_perk),
                ("Next Perk", self.tools.select_next_perk),
            ])
            buttons([
                ("Build Filter", self.tools.cycle_perk_build_filter),
            ])
            buttons([
                ("Grant Next Natural Pick", self.tools.grant_selected_perk_next_pick),
            ])
            buttons([
                ("Full Engineer", lambda: self.tools.workspace.grant_build("Engineer", full=True)),
                ("Full Vampire", lambda: self.tools.workspace.grant_build("Vampire", full=True)),
            ])
            buttons([
                ("Full Ninja", lambda: self.tools.workspace.grant_build("Ninja", full=True)),
                ("Full Gunslinger", lambda: self.tools.workspace.grant_build("Gunslinger", full=True)),
            ])
            buttons([
                ("Starter Eng", lambda: self.tools.workspace.grant_build("Engineer", full=False)),
                ("Starter Vamp", lambda: self.tools.workspace.grant_build("Vampire", full=False)),
            ])
            buttons([
                ("Starter Ninja", lambda: self.tools.workspace.grant_build("Ninja", full=False)),
                ("Starter Gun", lambda: self.tools.workspace.grant_build("Gunslinger", full=False)),
            ])
            buttons([
                ("Reset Build+Shop", self.tools.workspace.clear_perk_state),
                ("Pick+Gold", self.tools.workspace.give_level_pending_gold),
            ])
        elif self.active_category == "Tuning":
            buttons([
                ("Prev", self.tools.workspace.select_previous_tuning),
                ("Next", self.tools.workspace.select_next_tuning),
                ("Reset", self.tools.workspace.reset_selected_tuning),
            ])
            buttons([
                ("- Step", lambda: self.tools.workspace.edit_selected_tuning(-1)),
                ("+ Step", lambda: self.tools.workspace.edit_selected_tuning(1)),
                ("+ Big", lambda: self.tools.workspace.edit_selected_tuning(1, True)),
            ])
            buttons([
                ("Reload", self.tools.workspace.reload_tuning),
                ("Save Snapshot", self.tools.workspace.save_snapshot),
                ("Preview Load", self.tools.workspace.preview_snapshot),
            ])
        elif self.active_category == "Benchmark":
            buttons([
                ("Horde 100", lambda: self.tools.workspace.spawn_benchmark_horde(100)),
                ("Horde 200", lambda: self.tools.workspace.spawn_benchmark_horde(200)),
                ("Horde 300", lambda: self.tools.workspace.spawn_benchmark_horde(300)),
            ])
            buttons([
                ("Horde 500", lambda: self.tools.workspace.spawn_benchmark_horde(500)),
                ("Clear Horde", self.tools.clear_horde_test),
                ("Sample", self.tools.workspace.run_short_benchmark_sample),
            ])
        elif self.active_category == "Audio":
            buttons([
                ("Next Audio", self.tools.workspace.select_next_audio),
                ("Play", self.tools.workspace.play_selected_audio),
                ("Stop", self.tools.workspace.stop_audio),
            ])
        elif self.active_category == "Logs":
            buttons([
                ("Clear Event", self.tools.clear_log),
                ("Pause Event", self.tools.toggle_log_pause),
                ("Save Snapshot", self.tools.workspace.save_snapshot),
            ])
        elif self.active_category == "Enemies":
            buttons([
                ("Enemy F8", self.tools.cycle_selected_enemy),
                ("Lab Prev", self.tools.cycle_selected_enemy_reverse),
                ("Lab Spawn", self.tools.spawn_lab_enemy),
            ])
            buttons([
                ("Lab Clear", self.tools.clear_lab_enemies),
                ("Nearest", self.tools.select_nearest_enemy),
                ("Focus Enemy", self.tools.focus_selected_enemy),
            ])
            buttons([
                ("Kill Normal", self.tools.kill_normal_enemies),
            ])
        elif self.active_category == "Waves" and self.wave_designer is not None:
            buttons([
                ("Wave Designer", self.wave_designer.toggle),
                ("Export Waves", self.wave_designer.export),
                ("Wave Debug", self.tools.toggle_wave_debug),
            ])
            buttons([
                ("Restart R1", self.tools.workspace.restart_room_one),
                ("Spawn Group", self.tools.workspace.spawn_selected_group_now),
                ("Skip Group", self.tools.workspace.skip_group),
            ])
            buttons([
                ("Pause/Resume", self.tools.workspace.toggle_wave_pause),
                ("Clear Enemies", self.tools.workspace.clear_enemies),
                ("Export R1", self.tools.workspace.export_room1_group_snapshot),
            ])
        elif self.active_category == "Rooms" and getattr(self.tools, "authoring", None) is not None:
            buttons([
                ("Author F11", self.tools.toggle_author_mode),
                ("Refresh Draft", self.tools.authoring.refresh_from_runtime),
            ])
        elif self.active_category == "Assets" and self.asset_browser is not None:
            buttons([
                ("Asset Browser", self.asset_browser.toggle),
                ("Asset Report", self.asset_browser.pipeline.export_report),
            ])
        return items

    def _category_layout(self):
        x = self.rect.x + PADDING
        y = self.rect.y + 66
        w = self.rect.w - PADDING * 2
        gap = 6
        button_w = (w - gap * (len(CATEGORIES) - 1)) // len(CATEGORIES)
        return [
            {
                "label": label,
                "rect": pygame.Rect(x + (button_w + gap) * index, y, button_w, 26),
            }
            for index, label in enumerate(CATEGORIES)
        ]

    def draw(self, surface):
        if not DEV_TOOLS_ENABLED or not self.active:
            return

        self.tools.draw_debug(surface)
        self._draw_author_banner(surface)

        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill((8, 11, 18, 224))
        surface.blit(panel, self.rect.topleft)
        pygame.draw.rect(surface, (70, 160, 230), self.rect, 2, border_radius=8)

        self._draw_text(surface, "BLUECUBE DEV TOOLS", self.rect.x + PADDING, self.rect.y + 12, (190, 230, 255), self.font)
        self._draw_text(surface, "F12 close | F4 exit | F6 god | F7 hitboxes | F8 enemy | F9 slow", self.rect.x + PADDING, self.rect.y + 38, (150, 170, 190), self.small_font)

        for item in self._category_layout():
            self._draw_category_button(surface, item)

        self._draw_active_category(surface)

        for item in self._layout():
            self._draw_button(surface, item)

        self._draw_text(surface, self.tools.message, self.rect.x + PADDING, self.rect.bottom - 28, (120, 245, 180), self.small_font)
        if self.active_category in ("Overview", "Gameplay", "Logs"):
            self._draw_inspector(surface)
            self._draw_event_log(surface)
        if self.active_category == "Enemies":
            self._draw_inspector(surface)
            self._draw_enemy_lab(surface)
        if self.active_category == "Rooms" and self.authoring_panel:
            self.authoring_panel.draw(surface)
        if self.active_category == "Waves" and self.wave_designer_panel:
            self.wave_designer_panel.draw(surface)
        if self.active_category == "Assets" and self.asset_browser:
            self.asset_browser.draw(surface)
        if self.search_active:
            self._draw_search(surface)

    def _draw_text(self, surface, text, x, y, color, font):
        surface.blit(font.render(text, True, color), (x, y))

    def _draw_button(self, surface, item):
        pygame.draw.rect(surface, (30, 45, 64), item["rect"], border_radius=5)
        pygame.draw.rect(surface, (72, 130, 170), item["rect"], 1, border_radius=5)
        text = self.small_font.render(item["label"], True, (230, 240, 250))
        surface.blit(text, text.get_rect(center=item["rect"].center))

    def _draw_category_button(self, surface, item):
        active = item["label"] == self.active_category
        fill = (55, 88, 120) if active else (24, 36, 52)
        border = (130, 210, 255) if active else (72, 130, 170)
        pygame.draw.rect(surface, fill, item["rect"], border_radius=5)
        pygame.draw.rect(surface, border, item["rect"], 1, border_radius=5)
        text = self.small_font.render(item["label"][:8], True, (235, 245, 255))
        surface.blit(text, text.get_rect(center=item["rect"].center))

    def _draw_active_category(self, surface):
        y = self.rect.y + 104
        self._draw_text(surface, self.active_category, self.rect.x + PADDING, y, (255, 235, 120), self.small_font)
        y += 24
        if self.active_category == "Builds":
            self._draw_perks_page(surface, y)
            return
        if self.active_category == "Tuning":
            lines = self.tools.workspace.tuning_lines()
        elif self.active_category == "Enemies":
            lines = self.tools.enemy_lab_lines()
        elif self.active_category == "Waves":
            lines = self.tools.workspace.wave_lines() + [
                f"Designer visible: {getattr(self.wave_designer, 'visible', False)}",
            ]
        elif self.active_category == "Rooms":
            lines = [
                f"Author mode: {'on' if self.tools.author_mode else 'off'}",
                f"Author active: {getattr(getattr(self.tools, 'authoring', None), 'active', False)}",
                f"Room: {self.game.room_number}",
                f"Exit open: {self.game.room_exit_open}",
                "F11 preserves Author Mode toggle",
            ]
        elif self.active_category == "Assets":
            pipeline = getattr(self.asset_browser, "pipeline", None)
            lines = self.tools.workspace.asset_lines()[:10] + [
                f"Asset browser visible: {getattr(self.asset_browser, 'visible', False)}",
                f"Assets loaded: {len(getattr(pipeline, 'assets', [])) if pipeline else '-'}",
                f"Filter: {getattr(pipeline, 'filter_type', '-') if pipeline else '-'}",
                f"Message: {getattr(pipeline, 'message', '-') if pipeline else '-'}",
            ]
        elif self.active_category == "Audio":
            lines = self.tools.workspace.audio_lines()
        elif self.active_category == "Benchmark":
            lines = self.tools.workspace.benchmark_lines()
        elif self.active_category == "Logs":
            lines = [
                f"Workspace logs bounded: {len(self.tools.workspace.logs)}/80",
                f"Last snapshot: {self.tools.workspace.last_snapshot_path or '-'}",
                "Recent workspace diagnostics:",
                *self.tools.workspace.logs[-14:],
            ]
        else:
            lines = self.tools.runtime_info()
            if self.active_category == "Overview":
                profiler = getattr(self.game, "profiler", None)
                if profiler is not None:
                    lines = lines[:10] + ["Profiler"] + profiler.lines(limit=7)
            toggles = [
                ("hitboxes", self.tools.show_hitboxes),
                ("spawn", self.tools.show_spawn_debug),
                ("camera", self.tools.show_camera_debug),
                ("collision", self.tools.show_collision_debug),
                ("wave", self.tools.show_wave_debug),
                ("god", self.tools.god_mode),
                ("slow", self.tools.slow_motion),
            ]
            lines = lines[:18] + ["Toggles: " + "  ".join(f"{name}={'on' if value else 'off'}" for name, value in toggles)]
        for line in lines[:18]:
            self._draw_text(surface, line, self.rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += ROW_H

    def _draw_perks_page(self, surface, y):
        self._draw_text(surface, "Keys: Left/Right select | Tab build | G/Enter grant | / search", self.rect.x + PADDING, y, (150, 170, 190), self.small_font)
        y += 22
        self._draw_text(surface, f"Build Filter: {self.tools.perk_build_filter}", self.rect.x + PADDING, y, (180, 230, 210), self.small_font)
        y += 22
        if self.perk_search_active:
            self._draw_text(surface, f"Search: {self.perk_search_text}", self.rect.x + PADDING, y, (255, 235, 120), self.small_font)
            y += 22
        for line in self.tools.selected_perk_lines():
            self._draw_text(surface, line[:66], self.rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += ROW_H
        y += 8
        self._draw_text(surface, "Available", self.rect.x + PADDING, y, (255, 235, 120), self.small_font)
        y += 20
        selected = self.tools.selected_perk_definition()
        selected_key = selected.get("key") if selected else None
        for definition in self.tools.perk_definitions()[:8]:
            color = (255, 235, 120) if definition.get("key") == selected_key else (190, 205, 220)
            label = f"{definition.get('key')} - {definition.get('name')}"
            self._draw_text(surface, label[:66], self.rect.x + PADDING, y, color, self.small_font)
            y += ROW_H

    def _draw_panel_box(self, surface, rect, title):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((8, 11, 18, 218))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (70, 160, 230), rect, 2, border_radius=8)
        self._draw_text(surface, title, rect.x + PADDING, rect.y + 12, (190, 230, 255), self.font)

    def _draw_inspector(self, surface):
        self._draw_panel_box(surface, self.inspector_rect, "INSPECTOR")
        y = self.inspector_rect.y + 42
        for line in self.tools.inspector_lines()[:18]:
            self._draw_text(surface, line, self.inspector_rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 19
        self._draw_text(surface, "Select: Shift+Left Click or Middle Click | Focus: F | Search: /", self.inspector_rect.x + PADDING, self.inspector_rect.bottom - 26, (150, 170, 190), self.small_font)

    def _draw_event_log(self, surface):
        self._draw_panel_box(surface, self.log_rect, "EVENT LOG")
        state = f"paused={'on' if self.tools.log_paused else 'off'} auto={'on' if self.tools.log_auto_scroll else 'off'} count={len(self.tools.event_log)}"
        self._draw_text(surface, state, self.log_rect.x + PADDING, self.log_rect.y + 40, (180, 230, 210), self.small_font)
        entries = self.tools.event_log[-14:] if self.tools.log_auto_scroll else self.tools.event_log[:14]
        y = self.log_rect.y + 64
        for entry in entries:
            self._draw_text(surface, entry[:70], self.log_rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 19

    def _draw_enemy_lab(self, surface):
        rect = pygame.Rect(570, 900, 520, 150)
        if self.search_active:
            rect.y = 740
        self._draw_panel_box(surface, rect, "ENEMY LAB")
        y = rect.y + 42
        for line in self.tools.enemy_lab_lines()[:5]:
            self._draw_text(surface, line[:70], rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 19

    def _draw_author_banner(self, surface):
        if not getattr(self.tools, "author_mode", False):
            return
        rect = pygame.Rect(0, 0, 380, 42)
        rect.centerx = surface.get_width() // 2
        rect.y = 18
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((80, 35, 0, 220))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, (255, 210, 80), rect, 2, border_radius=6)
        text = self.font.render("AUTHOR MODE PAUSED", True, (255, 245, 180))
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_search(self, surface):
        rect = pygame.Rect(570, 740, 520, 150)
        self._draw_panel_box(surface, rect, "SEARCH")
        self._draw_text(surface, f"> {self.search_text}", rect.x + PADDING, rect.y + 42, (255, 235, 120), self.small_font)
        y = rect.y + 66
        for _kind, _obj, label in self.tools.search_results[:4]:
            self._draw_text(surface, label[:70], rect.x + PADDING, y, (230, 235, 245), self.small_font)
            y += 19
