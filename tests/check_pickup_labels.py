"""Pickup identification and active-stop HUD render checks."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from systems.object_catalog import draw_object, definition
from entities.player import Player
from ui.hud import draw_hud


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_world_labels_below_both_pickups(self):
        for key in ('dash_refresh','time_stop'):
            for active in (False,True):
                image=pygame.Surface((300,200),pygame.SRCALPHA)
                self.assertTrue(draw_object(image,key,(150,70),active=active))
                self.assertGreater(image.subsurface((70,105,160,50)).get_bounding_rect().width,0)

    def test_time_stop_distinct_art_preserves_duration(self):
        self.assertNotEqual(definition('time_stop')['art'],definition('dash_refresh')['art'])
        self.assertEqual(definition('time_stop')['duration'],2)

    def test_active_timer_changes_hud_without_mutation(self):
        player=Player()
        player.enemy_time_stop_timer=1.5
        image=pygame.Surface((1920,1080),pygame.SRCALPHA)
        draw_hud(image,pygame.font.Font(None,26),player,1,0,39,4,'ROOM','Combat',5)
        # Countdown moved from the top HUD into the temporal overlay.
        self.assertEqual(image.subsurface((800,15,400,50)).get_bounding_rect().width,0)
        from systems.time_stop_presentation import draw
        idle=pygame.Surface((1920,1080),pygame.SRCALPHA)
        draw(idle,0,2,0)
        self.assertEqual(idle.get_bounding_rect().width,0)
        draw(idle,player.enemy_time_stop_timer,2,0)
        self.assertGreater(idle.get_bounding_rect().width,0)
        self.assertEqual(player.enemy_time_stop_timer,1.5)


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    image=pygame.Surface((600,260))
    image.fill((13,20,31))
    for x,key in ((150,'dash_refresh'),(450,'time_stop')):
        draw_object(image,key,(x,105),time=.3)
    pygame.image.save(image,str(ROOT/'debug_screenshots/pickup-labels.png'))


if __name__=='__main__':
    capture()
    unittest.main()
