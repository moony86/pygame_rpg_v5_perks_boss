import os
import sys
import unittest
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from systems.object_catalog import sprite, catalog, validate_catalog
from systems.sigil_presentation import draw, pose
from systems.effects import EffectsSystem
from entities.player import Player


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_assets_and_real_draw_paths(self):
        self.assertEqual(validate_catalog(catalog()), [])
        camera = type('Camera', (), {'apply_pos': lambda self, p: pygame.Vector2(p)})()
        output = ROOT / 'debug_screenshots' / 'sigils'
        output.mkdir(parents=True, exist_ok=True)
        for step, time in enumerate((.05, .25)):
            surface = pygame.Surface((1000, 420))
            surface.fill((16, 25, 36))
            font = pygame.font.Font(None, 24)
            player = Player()
            player.engineer_bomber_max_runs = 1
            player.engineer_bomber_state = 'ready'
            player.engineer_airstrike_state = 'telegraph'
            player.engineer_airstrike_target_pos.update(370, 210)
            player.engineer_airstrike_radius = 100
            player.engineer_bomber_pos.update(-300, -300)
            player.anim_time = time
            before = (player.health, player.engineer_airstrike_radius)
            EffectsSystem().draw_dash_charge(surface, camera, (130, 210), .5 + time)
            player._draw_engineer_bomber(surface, camera)
            draw(surface, 'fx_time_sigil', (620, 210), 220 + time * 80)
            player.vampire_blood_moon_timer = 2
            player._draw_vampire_states(surface, pygame.Rect(840, 185, 46, 46))
            self.assertEqual(before, (player.health, player.engineer_airstrike_radius))
            for x, title in ((65, 'DASH CHARGE'), (300, 'AIRSTRIKE'), (550, 'TIME SIGIL'), (800, 'BLOOD MOON')):
                surface.blit(font.render(title, True, (210, 240, 250)), (x, 30))
            pygame.image.save(surface, output / f'preview-{step}.png')
        for key in ('fx_dash_charge', 'fx_airstrike_target', 'fx_time_sigil', 'fx_vampire_aura'):
            self.assertGreater(pygame.mask.from_surface(sprite(key), 1).count(), 50)

    def test_cache_bound_and_source_opacity_unchanged(self):
        source = sprite('fx_dash_charge')
        alpha = source.get_alpha()
        for i in range(300):
            draw(pygame.Surface((10, 10)), 'fx_dash_charge', (5, 5), 8 + i * 4, i % 255)
        self.assertLessEqual(pose.cache_info().currsize, 192)
        self.assertEqual(source.get_alpha(), alpha)

    def test_airstrike_target_without_bomber_upgrade(self):
        player = Player()
        player.engineer_bomber_max_runs = 0
        player.engineer_bomber_state = 'inactive'
        player.engineer_airstrike_state = 'telegraph'
        player.engineer_airstrike_target_pos.update(200, 200)
        player.engineer_airstrike_radius = 90
        camera = type('Camera', (), {'apply_pos': lambda self, p: pygame.Vector2(p)})()
        surface = pygame.Surface((400, 400), pygame.SRCALPHA)
        player._draw_engineer_bomber(surface, camera)
        self.assertGreater(pygame.mask.from_surface(surface, 1).count(), 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
