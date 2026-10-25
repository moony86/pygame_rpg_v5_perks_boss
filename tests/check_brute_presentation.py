"""Heavy enemy visual state/event synchronization regression."""
import os
import sys
from pathlib import Path
from unittest.mock import patch
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.enemy import Enemy,EnemyType
from systems.brute_presentation import pose
from systems.object_catalog import sprite
from systems.camera import Camera


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_charge_payload_duration_and_stop_sync(self):
        enemy=Enemy(600,500,EnemyType.BRUTE)
        enemy._start_windup(.46,pygame.Vector2(1,0),'brute_charge')
        with patch.object(enemy,'_has_line_of_sight',return_value=True):
            event=enemy.update(.46,pygame.Rect(850,500,32,32))
        self.assertEqual(event,{'type':'brute_charge'})
        self.assertEqual(enemy.leap_timer,.42)
        self.assertEqual(enemy.brute_stop_timer,0)
        enemy.update(.42,pygame.Rect(850,500,32,32))
        self.assertEqual(enemy.leap_timer,0)
        self.assertEqual(enemy.brute_stop_timer,1.15)

    def test_cancelled_attack_does_not_fake_charge(self):
        enemy=Enemy(600,500,EnemyType.BRUTE)
        enemy._start_windup(.46,pygame.Vector2(1,0),'brute_charge')
        with patch.object(enemy,'_has_line_of_sight',return_value=False):
            self.assertIsNone(enemy.update(.46,pygame.Rect(850,500,32,32)))
        self.assertEqual(enemy.leap_timer,0)
        self.assertEqual(enemy.brute_stop_timer,0)

    def test_gait_tracks_displacement_only(self):
        enemy=Enemy(600,500,EnemyType.BRUTE)
        enemy._move_vector(pygame.Vector2())
        self.assertEqual(enemy.brute_stride,0)
        enemy._move_vector(pygame.Vector2(10,0))
        self.assertAlmostEqual(enemy.brute_stride,1.2)
        self.assertTrue(enemy.brute_moving)

    def test_render_preserves_logic(self):
        enemy=Enemy(600,500,EnemyType.BRUTE)
        enemy._start_windup(.46,pygame.Vector2(-1,0),'brute_charge')
        before=(enemy.rect.copy(),enemy.health,enemy.speed,enemy.windup_timer)
        enemy.draw(pygame.Surface((1920,1080)),Camera())
        self.assertEqual(before,(enemy.rect,enemy.health,enemy.speed,enemy.windup_timer))


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    sheet=pygame.Surface((1000,280))
    sheet.fill((14,20,30))
    font=pygame.font.Font(None,24)
    for i,state in enumerate(('idle','move','prepare','charge','stop')):
        tile=sheet.subsurface((i*200,0,200,280))
        enemy=Enemy(100,115,EnemyType.BRUTE)
        enemy.rect.center=(100,115)
        enemy.windup_direction.update(1,0)
        if state=='move':
            enemy.brute_moving=True
            enemy.brute_stride=1.3
        if state=='prepare':
            enemy._start_windup(.46,pygame.Vector2(1,0),'brute_charge')
            enemy.windup_timer=.08
        if state=='charge':
            enemy.leap_timer=.2
        if state=='stop':
            enemy.brute_stop_timer=.2
        enemy.draw(tile,Camera())
        tile.blit(font.render(state,True,'white'),(65,215))
    pygame.image.save(sheet,str(ROOT/'debug_screenshots/brute-states.png'))


if __name__=='__main__':
    capture()
    unittest.main()
