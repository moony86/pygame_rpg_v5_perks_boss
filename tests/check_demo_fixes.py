"""Regression checks for the playable source demo; no interactive window required."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("BLUECUBE_DEV_TOOLS", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from entities.player import Player
from entities.pickup import Pickup
from game import Game
from game_state import GameState
from systems.loot_system import LootSystem
from systems.shooting_system import ShootingSystem
from systems.perk_system import PerkSystem, PERKS, _synergy_label
from states.combat_state import handle_combat_events
from states.pause_state import handle_pause_events
from ui.perk_screen import draw_perk_select


class DemoRegressionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_special_loot_collects_once_without_crash(self):
        player = Player()
        player.health = 40
        loot = LootSystem()
        loot.pickups = [Pickup(100, 100, kind, value) for kind, value in
                        (("gold", 8), ("xp", 20), ("heal_potion", 15), ("time_stop", 2))]
        result = loot.collect_remaining(player)
        self.assertEqual(result, {"gold": 8, "xp": 20, "heal_potion": 15, "time_stop": 2})
        self.assertEqual(player.health, 55)
        self.assertEqual(player.enemy_time_stop_timer, 2)
        self.assertFalse(loot.pickups)
        self.assertEqual(loot.collect_remaining(player), {"gold": 0, "xp": 0})

    def test_fire_rate_upgrades_change_real_firing(self):
        counts = []
        for multiplier in (1.0, 1.3, 10.0):
            player = Player()
            player.fire_rate_multiplier = multiplier
            shooting = ShootingSystem()
            projectiles = []
            count = 0
            for _ in range(1200):
                player.weapon_cooldown_timer = max(0, player.weapon_cooldown_timer - 1 / 120)
                shooting.update(1 / 120)
                if player.try_weapon_attack() is not None:
                    count += int(shooting.try_shoot(player, projectiles))
            counts.append(count)
        self.assertLess(counts[0], counts[1])
        self.assertGreater(counts[2], counts[0] * 5)

    def test_pistol_only_including_ninja_and_reset(self):
        player = Player()
        for key in ("knife", "sword"):
            player.switch_weapon(key)
            self.assertEqual(player.active_weapon_key, "pistol")
        system = PerkSystem()
        perk = next(p for p in PERKS if p["key"] == "phantom_step")
        option = system._option_for_player(perk, player)
        player.starter_choice_active = True
        system.current_options = [option]
        system.apply(player, 0)
        self.assertEqual(player.active_weapon_key, "pistol")
        self.assertGreater(player.max_dash_charges, 1)
        player.reset()
        self.assertEqual(player.active_weapon_key, "pistol")

    def test_exit_requires_cleared_room_and_valid_door(self):
        game = Game()
        game.reset_run()
        game.stage.start_stage()
        game.loot.spawn_gold((10, 10), 8)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        handle_combat_events(game, event)
        self.assertEqual(game.player.gold, 0)
        game.stage.mark_current_room_cleared()
        handle_combat_events(game, event)
        self.assertEqual(game.player.gold, 0)
        before = game.stage.current_pos
        _, _, rect = game.stage.open_doors()[0]
        game.player.rect.center = rect.center
        handle_combat_events(game, event)
        self.assertEqual(game.player.gold, 8)
        self.assertNotEqual(game.stage.current_pos, before)

    def test_grace_and_boss_music(self):
        game = Game()
        game.reset_run()
        game.stage.start_stage()
        game.prototype_room.update(0.5)
        self.assertFalse(game.prototype_room.pending)
        self.assertFalse(game.enemies)
        boss_node = next(n for n in game.stage.nodes if n.room.boss)
        game.stage.current_pos = boss_node.grid_pos
        game.stage._enter_current_room()
        self.assertEqual(game.music.current_key, "boss")

    def test_pause_return_to_menu(self):
        game = Game()
        game.reset_run()
        game.state = GameState.PAUSED
        handle_pause_events(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(game.state, GameState.MENU)

    def test_dash_release_without_press_after_restart_is_ignored(self):
        game = Game()
        game.reset_run()
        game.stage.start_stage()
        handle_combat_events(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
        self.assertEqual(game.player.dash_timer, 0)
        handle_combat_events(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        handle_combat_events(game, pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
        self.assertGreater(game.player.dash_timer, 0)

    def test_synergy_requires_specific_matching_tags(self):
        player = Player()
        player.perk_counts = {"rapid_fire": 1}
        pierce = next(p for p in PERKS if p["key"] == "needle_rounds")
        power = next(p for p in PERKS if p["key"] == "power_rounds")
        self.assertEqual(_synergy_label(pierce, player), "")
        self.assertIn("DPS SYNERGY", _synergy_label(power, player))

    def test_build_reset_removes_effects_and_shop_upgrades(self):
        game = Game()
        game.reset_run()
        game.player.gold = 1000
        game.player.damage_bonus = 100
        game.player.engineer_blade_level = 4
        game.upgrades.buy(game.player, "blacksmith", 0)
        gold = game.player.gold
        with patch("settings.DEV_TOOLS_ENABLED", True):
            self.assertTrue(game.dev_tools.workspace.clear_perk_state())
        self.assertEqual(game.player.damage_bonus, 0)
        self.assertEqual(game.player.engineer_blade_level, 0)
        self.assertEqual(game.player.gold, gold)
        self.assertFalse(any(game.upgrades.levels.values()))

    def test_window_pointer_mapping(self):
        game = Game()
        for size in ((1280, 720), (1440, 900), (390, 844), (360, 740)):
            game.resize_window(size)
            target = (960, 540)
            pos = (game.viewport_rect.x + target[0] * game.render_scale,
                   game.viewport_rect.y + target[1] * game.render_scale)
            mapped = game.window_to_game_pos(pos)
            self.assertLessEqual(abs(mapped[0] - target[0]), 1)
            self.assertLessEqual(abs(mapped[1] - target[1]), 1)

    def test_all_perk_variants_render_and_capture(self):
        game = Game()
        game.reset_run()
        output = ROOT / "debug_screenshots" / "demo_fixes"
        output.mkdir(parents=True, exist_ok=True)
        game.draw()
        pygame.image.save(game.screen, str(output / "hub.png"))
        system = PerkSystem()
        for count in (0, 3):
            game.player.perk_counts = {perk["key"]: count for perk in PERKS}
            for start in range(0, len(PERKS), 3):
                options = [system._option_for_player(p, game.player) for p in PERKS[start:start + 3]]
                cards, buttons = draw_perk_select(game.screen, game.big_font, game.font, options, (0, 0), player=game.player)
                self.assertTrue(all(game.screen.get_rect().contains(rect) for rect in cards + buttons))
                if start == 0:
                    pygame.image.save(game.screen, str(output / f"cards_{count}.png"))
        game.player.perk_counts.clear()
        game.stage.start_stage()
        game.prototype_room.open_exit()
        game.draw()
        pygame.image.save(game.screen, str(output / "room.png"))
        game.rooms.banner_timer = 0
        game.wave_notice_timer = 0
        game.state = GameState.PERK_SELECT
        game.perks.current_options = [system._option_for_player(next(p for p in PERKS if p["key"] == key), game.player)
                                      for key in ("rapid_fire", "blade_drone", "vital_core")]
        for size in ((1280, 720), (1440, 900), (390, 844), (360, 740)):
            game.resize_window(size)
            game.draw()
            pygame.image.save(game.window, str(output / f"cards_{size[0]}x{size[1]}.png"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
