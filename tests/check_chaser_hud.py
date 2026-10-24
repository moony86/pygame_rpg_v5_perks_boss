"""Visual-only animation regression and native render contact sheet."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.enemy import Enemy, EnemyType, CHASER_BURST_THRESHOLD
from entities.player import Player
from systems.chaser_presentation import pose
from systems.object_catalog import sprite
from systems.effects import EffectsSystem
from systems.camera import Camera
from ui.hud import draw_hud


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_pose_states_leave_logic_unchanged(self):
        enemy=Enemy(500,500,EnemyType.CHASER)
        art=sprite('enemy_chaser')
        for state in ('move','prepare','burst','hit'):
            enemy.chase_pressure_timer=CHASER_BURST_THRESHOLD*.9 if state=='prepare' else 0
            enemy.chaser_burst_timer=.2 if state=='burst' else 0
            enemy.hit_flash=.08 if state=='hit' else 0
            before=(enemy.rect.copy(),enemy.health,enemy.speed,enemy.chaser_burst_timer)
            self.assertEqual(pose(enemy,art)[2],state)
            self.assertEqual(before,(enemy.rect,enemy.health,enemy.speed,enemy.chaser_burst_timer))

    def test_death_effect_expires_without_retaining_enemy(self):
        fx=EffectsSystem()
        enemy=Enemy(500,500)
        before=enemy.health
        fx.chaser_death(enemy)
        self.assertEqual(len(fx.sprite_effects),1)
        effect=fx.sprite_effects[0]
        effect.update(.3)
        self.assertFalse(effect.alive)
        self.assertEqual(enemy.health,before)

    def test_hud_render_with_and_without_vampire(self):
        player=Player()
        screen=pygame.Surface((1920,1080))
        font=pygame.font.Font(None,26)
        for blood in (0,40):
            player.vampire_max_blood=blood
            draw_hud(screen,font,player,1,12,39,4,'ROOM','Combat',8,run_timer=10,room_total=9)


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    image=pygame.Surface((900,260))
    image.fill((14,20,30))
    font=pygame.font.Font(None,26)
    camera=Camera()
    for i,state in enumerate(('move','prepare','burst','hit')):
        enemy=Enemy(100+i*220,105)
        enemy.rect.center=(100+i*220,105)
        enemy.chase_pressure_timer=CHASER_BURST_THRESHOLD*.9 if state=='prepare' else 0
        enemy.chaser_burst_timer=.2 if state=='burst' else 0
        enemy.hit_flash=.08 if state=='hit' else 0
        enemy._anim=.16
        enemy.draw(image,camera)
        image.blit(font.render(state,True,'white'),(65+i*220,180))
    pygame.image.save(image,str(ROOT/'debug_screenshots/chaser-states.png'))


if __name__=='__main__':
    capture()
    unittest.main()
