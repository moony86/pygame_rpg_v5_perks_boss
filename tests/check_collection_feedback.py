"""Collection values remain authoritative; feedback merges, expires and stays bounded."""
import os
import sys
import random
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.player import Player
from entities.pickup import Pickup
from systems.effects import EffectsSystem
from systems.loot_system import LootSystem
from systems.pickup_presentation import KINDS
from systems.camera import Camera


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_gold_xp_merge_without_changing_inventory(self):
        player=Player()
        loot=LootSystem()
        fx=EffectsSystem()
        loot.pickups=[Pickup(500,500,'gold',10) for _ in range(20)]
        loot.pickups += [Pickup(500,500,'xp',5) for _ in range(8)]
        result=loot.collect_remaining(player,fx)
        self.assertEqual(result,{'gold':200,'xp':40})
        self.assertEqual(player.gold,200)
        self.assertEqual(len(fx.collection_effects),2)
        self.assertEqual(fx.collection_effects[0].value,200)
        self.assertEqual(fx.collection_effects[1].value,40)
        self.assertEqual(fx.floating_texts,[])

    def test_actual_healing_and_full_health_label(self):
        player=Player()
        player.health=player.max_health-5
        loot=LootSystem()
        fx=EffectsSystem()
        loot.pickups=[Pickup(500,500,'heal_potion',35)]
        loot.collect_remaining(player,fx)
        self.assertEqual(fx.collection_effects[0].value,5)
        self.assertEqual(player.health,player.max_health)
        fx.reset()
        loot.pickups=[Pickup(500,500,'heal_potion',35)]
        loot.collect_remaining(player,fx)
        self.assertEqual(fx.collection_effects[0].label(),'HP FULL')

    def test_bound_expiry_reset_and_no_gameplay_rng(self):
        fx=EffectsSystem()
        before=random.getstate()
        for _ in range(100):
            for kind in KINDS:
                fx.collect_pickup(kind,1,(500,500))
            fx.update(.02)
        self.assertLessEqual(len(fx.collection_effects),6)
        self.assertEqual(before,random.getstate())
        fx.update(1.)
        self.assertEqual(fx.collection_effects,[])
        fx.collect_pickup('gold',10,(500,500))
        fx.reset()
        self.assertEqual(fx.collection_effects,[])

    def test_feedback_draw_has_no_player_mutation(self):
        player=Player()
        fx=EffectsSystem()
        for kind in KINDS:
            fx.collect_pickup(kind,5,player.rect.center)
        before=(player.rect.copy(),player.health,player.gold,player.xp)
        fx.draw(pygame.Surface((1920,1080)),Camera(),pygame.font.Font(None,26))
        self.assertEqual(before,(player.rect,player.health,player.gold,player.xp))

    def test_time_stop_still_activates(self):
        player=Player()
        loot=LootSystem()
        fx=EffectsSystem()
        loot.pickups=[Pickup(500,500,'time_stop',2)]
        loot.collect_remaining(player,fx)
        self.assertEqual(player.enemy_time_stop_timer,2)
        self.assertEqual(fx.time_stop_overlay_timer,2)
        self.assertEqual(fx.collection_effects[0].kind,'time_stop')


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    sheet=pygame.Surface((1200,680))
    sheet.fill((14,20,30))
    font=pygame.font.Font(None,26)
    for i,kind in enumerate(KINDS):
        tile=sheet.subsurface((i%3*400,i//3*340,400,340))
        player=Player()
        player.rect.center=(200,240)
        player.draw(tile,Camera())
        fx=EffectsSystem()
        fx.collect_pickup(kind,25,(200,240))
        fx.update(.12)
        fx.draw(tile,Camera(),font)
    pygame.image.save(sheet,str(ROOT/'debug_screenshots/collection-feedback.png'))


if __name__=='__main__':
    capture()
    unittest.main()
