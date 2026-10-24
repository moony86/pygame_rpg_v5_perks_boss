"""Front-end, settings persistence, time-stop lifecycle and restart smoke checks."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
import config
from game import Game
from game_state import GameState
from states.menu_state import handle_menu_events
from states.end_state import handle_end_screen_events
from states.pause_state import handle_pause_mouse
from systems.effects import EffectsSystem
from systems import time_stop_presentation as stop
from ui.front_end import draw_menu


class Checks(unittest.TestCase):
    def test_window_identity_and_left_facing_menu_pistol(self):
        game = Game()
        self.assertEqual(pygame.display.get_caption()[0], 'Blue Cube — Demo')
        self.assertIsNotNone(game.window_icon)
        from ui.front_end import draw_scene
        from systems.object_catalog import sprite
        surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        with patch('ui.front_end.sprite', side_effect=lambda key, **kwargs:
                   sprite(key, **kwargs) if key == 'pistol' else None):
            draw_scene(surface, 0)
        expected = pygame.transform.flip(sprite('pistol', size=(94, 70)), True, False)
        rect = expected.get_rect(center=(1225, 710))
        composited = pygame.Surface(expected.get_size(), pygame.SRCALPHA)
        composited.blit(expected, (0, 0))
        self.assertEqual(pygame.image.tobytes(surface.subsurface(rect), 'RGBA'),
                         pygame.image.tobytes(composited, 'RGBA'))
        output = ROOT / 'debug_screenshots' / 'menu-identity'
        output.mkdir(parents=True, exist_ok=True)
        for size in ((1920, 1080), (1440, 900)):
            draw_menu(game.screen, game)
            pygame.image.save(pygame.transform.smoothscale(game.screen, size),
                              str(output / f'menu-{size[0]}x{size[1]}.png'))

    def setUp(self):
        self.saved=config.CONFIG.copy()
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'debug_screenshots')
        self.env=patch.dict(os.environ,{'BLUECUBE_SETTINGS_PATH':str(Path(self.temp.name)/'settings.json')})
        self.env.start()

    def tearDown(self):
        config.CONFIG.update(self.saved)
        self.env.stop()
        self.temp.cleanup()

    def test_menu_keyboard_and_controls_return(self):
        game=Game()
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_DOWN))
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertEqual(game.menu_page,'settings')
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(game.menu_page,'main')
        rect=game.menu_buttons['controls']
        handle_menu_events(game,pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center))
        self.assertEqual(game.menu_page,'controls')
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertEqual(game.state,GameState.HUB)

    def test_settings_roundtrip_and_invalid_values(self):
        config.CONFIG['master_volume']=.35
        config.CONFIG['reduced_flashes']=True
        self.assertTrue(config.save_preferences())
        config.CONFIG['master_volume']=.9
        config.CONFIG['reduced_flashes']=False
        config.load_preferences()
        self.assertEqual(config.CONFIG['master_volume'],.35)
        self.assertTrue(config.CONFIG['reduced_flashes'])
        config.settings_path().write_text('{"master_volume":2,"aim_assist":"yes"}',encoding='utf-8')
        before=config.CONFIG.copy()
        config.load_preferences()
        self.assertEqual(config.CONFIG,before)
        config.settings_path().write_text('broken',encoding='utf-8')
        config.load_preferences()

    def test_settings_slider_and_toggle_use_actual_actions(self):
        game=Game()
        game.menu_page='settings'
        rect=game.menu_option_rects['master_volume']
        handle_menu_events(game,pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(rect.x+380,rect.centery)))
        handle_menu_events(game,pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=rect.center))
        self.assertEqual(config.CONFIG['master_volume'],.5)
        game.menu_focus=5
        previous=config.CONFIG['reduced_flashes']
        handle_menu_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertNotEqual(config.CONFIG['reduced_flashes'],previous)
        self.assertTrue(config.settings_path().exists())

    def test_stop_draw_cached_and_preserves_timers(self):
        pygame.init()
        pygame.display.set_mode((1,1))
        fx=EffectsSystem()
        fx.time_stop_trigger((960,540),2)
        surface=pygame.Surface((1920,1080))
        for reduced in (False,True):
            config.CONFIG['reduced_flashes']=reduced
            for _ in range(3):
                fx.draw_time_stop_overlay(surface)
            self.assertEqual(fx.time_stop_overlay_timer,2)
        self.assertIs(stop.layers((1920,1080)),stop.layers((1920,1080)))
        fx.update(1.99)
        fx.update(.02)
        self.assertEqual(fx.time_stop_overlay_timer,0)
        self.assertGreater(fx.time_stop_release_flash,0)
        fx.reset()
        self.assertEqual(fx.time_stop_release_flash,0)

    def test_death_and_restart_clear_build_and_transients(self):
        game=Game()
        game.reset_run()
        game.stage.start_stage()
        game.player.gold=987
        game.player.engineer_gun_level=4
        game.player.enemy_time_stop_timer=2
        game.effects.time_stop_trigger(game.player.rect.center,2)
        game.player.health=0
        game.update(1/60)
        self.assertEqual(game.state,GameState.GAME_OVER)
        handle_end_screen_events(game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertEqual(game.state,GameState.HUB)
        self.assertEqual(game.player.health,game.player.max_health)
        self.assertEqual(game.player.gold,0)
        self.assertEqual(game.player.engineer_gun_level,0)
        self.assertEqual(game.player.enemy_time_stop_timer,0)
        self.assertEqual(game.effects.time_stop_overlay_timer,0)
        self.assertFalse(game.projectiles)

    def test_menu_render_pages_do_not_mutate_gameplay(self):
        game=Game()
        before=(game.state,game.player.health,game.player.gold)
        output=ROOT/'debug_screenshots/front-end'
        output.mkdir(parents=True,exist_ok=True)
        for page in ('main','settings','controls'):
            game.menu_page=page
            draw_menu(game.screen,game)
            pygame.image.save(game.screen,str(output/f'{page}.png'))
        self.assertEqual(before,(game.state,game.player.health,game.player.gold))
        for remaining,name in ((2.,'entry'),(1.2,'sustain')):
            game.stage.start_stage()
            game.effects.time_stop_overlay_timer=remaining
            game.effects.time_stop_overlay_duration=2.
            game.draw()
            pygame.image.save(game.screen,str(output/f'time-stop-{name}.png'))


if __name__=='__main__':
    unittest.main(verbosity=2)
