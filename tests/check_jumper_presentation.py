"""Jumper event/pose regression and source-rendered visual fixture."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.enemy import Enemy,EnemyType
from settings import JUMPER_LEAP_TIME
from systems.jumper_presentation import pose
from systems.object_catalog import sprite
from systems.camera import Camera


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_all_variants_keep_real_leap_duration_and_land_on_completion(self):
        for kind,scale in ((EnemyType.JUMPER,1),(EnemyType.JUMPER_FAST,.88),(EnemyType.JUMPER_HEAVY,1.15)):
            enemy=Enemy(500,500,kind)
            enemy._start_windup(.3,pygame.Vector2(1,0),'enemy_jump')
            self.assertEqual(pose(enemy,sprite('enemy_'+kind.name.lower()))[2],'prepare')
            event=enemy.update(.3,pygame.Rect(700,500,32,32))
            self.assertEqual(event,{'type':'enemy_jump'})
            self.assertAlmostEqual(enemy.leap_timer,JUMPER_LEAP_TIME*scale)
            self.assertEqual(enemy.jumper_landing_timer,0)
            enemy.update(enemy.leap_timer,pygame.Rect(700,500,32,32))
            self.assertEqual(enemy.leap_timer,0)
            self.assertEqual(enemy.jumper_landing_timer,.22)

    def test_draw_never_moves_collision_or_advances_landing(self):
        enemy=Enemy(500,500,EnemyType.JUMPER)
        enemy.jumper_landing_timer=.2
        before=(enemy.rect.copy(),enemy.health,enemy.speed,enemy.jumper_landing_timer)
        for _ in range(5):
            enemy.draw(pygame.Surface((900,600)),Camera())
        self.assertEqual(before,(enemy.rect,enemy.health,enemy.speed,enemy.jumper_landing_timer))

    def test_air_pose_has_bounded_height_and_restores_at_end(self):
        enemy=Enemy(500,500,EnemyType.JUMPER)
        enemy.jumper_flight_total=.5
        image=sprite('enemy_jumper')
        for remaining in (.5,.4,.25,.1,.001):
            enemy.leap_timer=remaining
            _,offset,state=pose(enemy,image)
            self.assertEqual(state,'air')
            self.assertGreaterEqual(offset[1],-12)
            self.assertLessEqual(offset[1],0)


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    sheet=pygame.Surface((1000,260))
    sheet.fill((14,20,30))
    font=pygame.font.Font(None,24)
    for i,state in enumerate(('move','prepare','air','land')):
        tile=sheet.subsurface((i*250,0,250,260))
        enemy=Enemy(125,100,EnemyType.JUMPER)
        enemy.rect.center=(125,100)
        if state=='prepare':
            enemy._start_windup(.3,pygame.Vector2(1,0),'enemy_jump')
            enemy.windup_timer=.05
        if state=='air':
            enemy.jumper_flight_total=.5
            enemy.leap_timer=.25
            enemy.leap_velocity.update(800,0)
        if state=='land':
            enemy.jumper_landing_timer=.15
        enemy.draw(tile,Camera())
        tile.blit(font.render(state,True,'white'),(95,185))
    pygame.image.save(sheet,str(ROOT/'debug_screenshots/jumper-states.png'))


if __name__=='__main__':
    capture()
    unittest.main()
