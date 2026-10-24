"""Sanctuary assets, contextual purchases, geometry and native render captures."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS', '0')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from game import Game
from systems.scene_system import enter_hub
from systems.hub_presentation import HUB, art, background
from ui.hub import handle_click, shop_rows
from states.hub_state import handle_hub_events


class Checks(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        enter_hub(self.game)
        self.output = ROOT / 'debug_screenshots/hub'
        self.output.mkdir(parents=True, exist_ok=True)

    def approach(self, role):
        npc = next(n for n in self.game.npcs if n.role == role)
        self.game.player.rect.midtop = (npc.rect.centerx, npc.rect.bottom + 8)
        return npc

    def test_real_art_transparency_and_bounded_cache(self):
        self.assertIsNotNone(background((1920,1080)))
        for role in ('blacksmith','healer','seer','tea_vendor'):
            source = pygame.image.load(str(ROOT / 'assets' / HUB['npcs'][role]['art']))
            self.assertTrue(source.get_flags() & pygame.SRCALPHA)
            self.assertEqual(source.get_at((0,0)).a,0)
            self.assertIs(art(role), art(role))

    def test_context_required_and_keyboard_matches_click(self):
        npc = self.approach('blacksmith')
        self.game.player.gold = 100
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=shop_rows(self.game,npc.role)[0].center)
        self.assertFalse(handle_click(self.game,event))
        handle_hub_events(self.game,pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
        self.assertTrue(handle_click(self.game,event))
        self.assertEqual(self.game.player.gold,70)
        self.assertEqual(self.game.upgrades.get_level('power_rounds'),1)

    def test_broke_click_has_no_effect(self):
        npc = self.approach('healer')
        self.game.player.gold=0
        self.game.player.health=30
        self.game.dialogue.show(npc.name,'Prepare')
        handle_click(self.game,pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=shop_rows(self.game,npc.role)[0].center))
        self.assertEqual(self.game.player.health,30)
        self.assertEqual(self.game.player.gold,0)

    def test_all_actor_interaction_approaches_are_free(self):
        solids=self.game.collision.get_colliders()
        for npc in self.game.npcs:
            approach=pygame.Rect(npc.rect.centerx-20,npc.rect.bottom+8,40,40)
            self.assertFalse(any(approach.colliderect(s) for s in solids),npc.role)
        self.assertFalse(any(self.game.player.rect.colliderect(s) for s in solids))

    def test_all_panels_render_without_mutation(self):
        before=(self.game.player.gold,self.game.player.health)
        self.game.draw()
        pygame.image.save(self.game.screen,str(self.output/'sanctuary.png'))
        for role in ('blacksmith','healer','seer','tea_vendor','portal'):
            npc=self.approach(role)
            self.game.dialogue.show(npc.name,'Ready when you are. Press E to close.')
            self.game.draw()
            pygame.image.save(self.game.screen,str(self.output/f'{role}.png'))
        self.assertEqual(before,(self.game.player.gold,self.game.player.health))


if __name__ == '__main__':
    unittest.main(verbosity=2)
