"""Actual attack event / visual synchronization and native rendering checks."""
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
from systems.ranged_presentation import pose, is_ranged, draw_telegraph
from systems.object_catalog import sprite
from systems.camera import Camera
from systems.effects import EffectsSystem


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_release_starts_on_real_event_not_during_charge(self):
        enemy=Enemy(500,500,EnemyType.RANGED)
        enemy._start_windup(.25,pygame.Vector2(1,0),'enemy_shoot')
        self.assertEqual(pose(enemy,sprite('enemy_ranged'))[2],'prepare')
        target=pygame.Rect(650,500,32,32)
        self.assertIsNone(enemy.update(.1,target))
        self.assertEqual(enemy.ranged_release_timer,0)
        event=enemy.update(.15,target)
        self.assertEqual(event['type'],'enemy_shoot')
        self.assertEqual(event['shot_count'],2)
        self.assertEqual(pose(enemy,sprite('enemy_ranged'))[2],'release')
        enemy.update(.13,target)
        self.assertEqual(pose(enemy,sprite('enemy_ranged'))[2],'recover')

    def test_variants_preserve_payload_and_collision(self):
        for name,count in (('RANGED',2),('RANGED_THREE',3),('RANGED_FIVE',5),('RANGED_RAIN',None)):
            enemy=Enemy(500,500,EnemyType[name])
            self.assertTrue(is_ranged(enemy))
            action='enemy_rain' if count is None else 'enemy_shoot'
            enemy._start_windup(.3,pygame.Vector2(-1,0),action)
            before=(enemy.rect.copy(),enemy.health,enemy.speed,enemy.attack_cooldown)
            image=pygame.Surface((1920,1080))
            enemy.draw(image,Camera())
            self.assertEqual(before,(enemy.rect,enemy.health,enemy.speed,enemy.attack_cooldown))
            event=enemy._finish_windup()
            self.assertEqual(event['type'],action)
            if count is not None:
                self.assertEqual(event['shot_count'],count)

    def test_hit_pose_and_draw_do_not_advance_time(self):
        enemy=Enemy(500,500,EnemyType.RANGED)
        enemy.hit_flash=.08
        enemy.ranged_release_timer=.2
        self.assertEqual(pose(enemy,sprite('enemy_ranged'))[2],'hit')
        for _ in range(10):
            enemy.draw(pygame.Surface((800,600)),Camera())
        self.assertEqual(enemy.ranged_release_timer,.2)

    def test_death_echo_expires(self):
        fx=EffectsSystem()
        enemy=Enemy(500,500,EnemyType.RANGED)
        fx.ranged_death(enemy)
        self.assertEqual(len(fx.sprite_effects),1)
        fx.sprite_effects[0].update(.3)
        self.assertFalse(fx.sprite_effects[0].alive)

    def test_arcane_path_handles_all_directions_and_offscreen(self):
        for angle in range(0,360,45):
            direction=pygame.Vector2(1,0).rotate(angle)
            screen=pygame.Surface((800,600),pygame.SRCALPHA)
            draw_telegraph(screen,(400,300),direction,650,.1,.3,.2)
            self.assertGreater(screen.get_bounding_rect().width,0)
        draw_telegraph(screen,(-1000,-1000),pygame.Vector2(-1,0),650,.1,.3,.2)

    def test_telegraph_disappears_on_release_and_is_not_orange(self):
        screen=pygame.Surface((800,200),pygame.SRCALPHA)
        draw_telegraph(screen,(70,100),pygame.Vector2(1,0),650,0,.3,.2)
        self.assertEqual(screen.get_bounding_rect().width,0)
        draw_telegraph(screen,(70,100),pygame.Vector2(1,0),650,.1,.3,.2)
        self.assertNotEqual(screen.get_at((400,100)),pygame.Color(255,120,40))


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    image=pygame.Surface((1000,300))
    image.fill((14,20,30))
    font=pygame.font.Font(None,25)
    for i,state in enumerate(('move','prepare','release','recover','hit')):
        enemy=Enemy(100+i*200,100,EnemyType.RANGED)
        enemy.rect.center=(100+i*200,100)
        enemy._anim=.2
        if state!='move':
            enemy._start_windup(.3,pygame.Vector2(1,0),'enemy_shoot')
            enemy.windup_timer=.05
        if state in ('release','recover'):
            enemy._finish_windup()
            enemy.windup_timer=0
            enemy.ranged_release_timer=.3 if state=='release' else .1
        enemy.hit_flash=.08 if state=='hit' else 0
        enemy.draw(image,Camera())
        image.blit(font.render(state,True,'white'),(65+i*200,190))
    pygame.image.save(image,str(ROOT/'debug_screenshots/ranged-states.png'))
    path=pygame.Surface((900,300))
    path.fill((14,20,30))
    enemy=Enemy(100,150,EnemyType.RANGED)
    enemy.rect.center=(100,150)
    enemy._anim=.2
    enemy._start_windup(.3,pygame.Vector2(1,0),'enemy_shoot')
    enemy.windup_timer=.08
    enemy.draw(path,Camera())
    pygame.image.save(path,str(ROOT/'debug_screenshots/ranged-arcane-path.png'))


if __name__=='__main__':
    capture()
    unittest.main()
