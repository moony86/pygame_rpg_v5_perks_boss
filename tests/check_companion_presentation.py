"""Direction and companion rendering regressions; no gameplay mutations."""
import os
import sys
from pathlib import Path
from unittest.mock import patch
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from entities.player import Player
from systems.camera import Camera
from systems import object_catalog


class CompanionPresentationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_authored_left_facing_hero_follows_aim_not_stale_movement(self):
        art = pygame.Surface((6, 4), pygame.SRCALPHA)
        art.set_at((0, 0), (255, 0, 0, 255))
        player = Player()
        for x in (-1, 1):
            player.facing_x = -x
            player.aim_direction = pygame.Vector2(x, 0)
            with patch('entities.player.object_sprite', return_value=art):
                shown = player._current_player_sprite()
            expected = art if x < 0 else pygame.transform.flip(art, True, False)
            self.assertEqual(pygame.image.tobytes(shown, 'RGBA'),
                             pygame.image.tobytes(expected, 'RGBA'))

    def test_companions_use_valid_editable_assets(self):
        self.assertEqual(object_catalog.validate_catalog(object_catalog.catalog()), [])
        for key in ('companion_drone', 'companion_blade', 'companion_bomber', 'companion_bat', 'companion_blood'):
            self.assertIsNotNone(object_catalog.sprite(key), key)

    def test_three_drone_silhouettes_have_independent_bindings(self):
        keys = ('companion_drone', 'companion_blade', 'companion_bomber')
        self.assertEqual(len({object_catalog.definition(k)['art'] for k in keys}), 3)
        for key in keys:
            self.assertIn(key, object_catalog.FIELDS)
            self.assertIn('tint', object_catalog.FIELDS[key])
            art = object_catalog.sprite(key)
            self.assertTrue(art.get_flags() & pygame.SRCALPHA)
            self.assertEqual(art.get_at((0, 0)).a, 0)

    def test_cached_poses_and_opacity_do_not_mutate_source(self):
        from systems import companion_presentation as visual
        key = 'companion_bomber'
        original = pygame.image.tobytes(object_catalog.sprite(key), 'RGBA')
        first = visual.pose(key, 0, left=True, flash=True, alpha=125)
        self.assertIs(first, visual.pose(key, 0, left=True, flash=True, alpha=125))
        self.assertEqual(original, pygame.image.tobytes(object_catalog.sprite(key), 'RGBA'))
        for angle in range(0, 3600, 5):
            visual.pose('companion_blade', 0, angle=angle)
        self.assertLessEqual(len(visual._poses), visual.MAX_POSES)
        self.assertLessEqual(visual._bytes, visual.MAX_BYTES)

    def test_bomber_keeps_its_art_during_cooldown(self):
        from systems import companion_presentation as visual
        player = Player()
        player.engineer_bomber_max_runs = 1
        player.engineer_bomber_state = 'cooldown'
        player.engineer_bomber_timer = 2
        player.engineer_bomber_cooldown = 5
        with patch.object(visual, 'draw', wraps=visual.draw) as draw:
            player._draw_engineer_bomber(pygame.Surface((1920,1080)), Camera())
        self.assertEqual(draw.call_args.args[1], 'companion_bomber')
        self.assertTrue(draw.call_args.kwargs['cooling'])

    def test_scene_reset_forgets_visual_aim(self):
        player = Player()
        player.engineer_drone_visual_directions = [pygame.Vector2(-1, 0)]
        player.reset_engineer_scene_state()
        self.assertEqual(player.engineer_drone_visual_directions, [])

    def test_real_companion_draw_paths_keep_gameplay_state(self):
        player = Player()
        player.engineer_helper_enabled = True
        player.engineer_blade_positions = [pygame.Vector2(900, 500)]
        player.engineer_bomber_max_runs = 1
        player.engineer_bomber_state = 'flying'
        player.vampire_max_blood = 40
        player.vampire_blood = 20
        player.vampire_bat_enabled = True
        player.vampire_bat_state = 'returning'
        player.vampire_blood_orbs = [{'pos': pygame.Vector2(950, 540)}]
        before = (player.rect.copy(), player.health, player.vampire_blood)
        surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        camera = Camera()
        for t in (0, .125, .25):
            player.anim_time = t
            player._draw_engineer_drone(surface, camera)
            player._draw_engineer_blades(surface, camera)
            player._draw_engineer_bomber(surface, camera)
            player._draw_blood_bat(surface, camera)
            player._draw_blood_pickups(surface, camera)
            player._draw_blood_orb(surface, player.rect)
        self.assertEqual(before, (player.rect, player.health, player.vampire_blood))


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_mode((1, 1))
    canvas = pygame.Surface((1000, 480))
    canvas.fill((17, 23, 34))
    font = pygame.font.Font(None, 25)
    camera = Camera()
    for i, direction in enumerate((-1, 1)):
        player = Player()
        player.rect.center = (200+i*400, 110)
        player.aim_direction = pygame.Vector2(direction, 0)
        player.facing_x = -direction
        player.draw(canvas, camera)
        canvas.blit(font.render('Aim left' if direction < 0 else 'Aim right', True, 'white'), (140+i*400, 160))
    for i, key in enumerate(('companion_drone','companion_blade','companion_bomber','companion_bat','companion_blood')):
        art = object_catalog.sprite(key)
        canvas.blit(art, art.get_rect(center=(100+i*200, 245)))
        canvas.blit(font.render(key.replace('companion_',''), True, 'white'), (65+i*200, 290))
    from systems import companion_presentation as visual
    for i, key in enumerate(('companion_drone','companion_blade','companion_bomber')):
        art = visual.pose(key, 0)
        enlarged = pygame.transform.scale(art, (art.get_width()*3, art.get_height()*3))
        canvas.blit(enlarged, enlarged.get_rect(center=(170+i*320, 390)))
    output = ROOT/'debug_screenshots/companion-presentation.png'
    pygame.image.save(canvas, str(output))
    unittest.main()
