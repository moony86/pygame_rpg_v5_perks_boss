"""Coverage, rendering and visual/logic separation checks for the art library."""
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from systems import object_catalog as visuals
from entities.enemy import Enemy,EnemyType
from definitions.perk_definitions import PERK_DEFINITIONS
from systems.camera import Camera


class VisualLibraryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_every_enemy_card_and_xp_tier_has_valid_asset(self):
        doc=visuals.catalog()
        self.assertEqual(visuals.validate_catalog(doc),[])
        keys=['enemy_'+e.name.lower() for e in EnemyType]
        keys+=['card_'+p['key'] for p in PERK_DEFINITIONS]
        keys+=['visual_xp_tier_'+str(i) for i in range(1,6)]
        keys+=['enemy_boss_phase_2','enemy_boss_phase_3','fx_impact','fx_ring','fx_explosion','fx_slash','card_style']
        for key in keys:
            self.assertIn(key,doc['objects'])
            self.assertIsNotNone(visuals.sprite(key),key)

    def test_all_enemy_types_render_without_changing_collision_or_health(self):
        surface=pygame.Surface((1920,1080),pygame.SRCALPHA)
        camera=Camera()
        for kind in EnemyType:
            enemy=Enemy(960,540,kind)
            before=(enemy.rect.copy(),enemy.health,enemy.speed)
            enemy.draw(surface,camera)
            enemy.hit_flash=.1
            enemy.draw(surface,camera)
            self.assertEqual((enemy.rect,enemy.health,enemy.speed),before)
            if kind==EnemyType.BOSS:
                for phase in (2,3):
                    enemy.phase=phase
                    enemy.draw(surface,camera)

    def test_all_cards_have_independent_bindings(self):
        from ui.perk_screen import get_card_art
        for perk in PERK_DEFINITIONS:
            self.assertIsNotNone(get_card_art(perk['key']),perk['key'])
        self.assertEqual(len(PERK_DEFINITIONS),21)

    def test_animation_sheet_selects_distinct_frames(self):
        doc=copy.deepcopy(visuals.catalog())
        doc['objects']['hero'].update(frames=2,columns=2,rows=1,tint='#ffffff')
        sheet=pygame.Surface((32,16),pygame.SRCALPHA)
        sheet.fill((255,0,0),(0,0,16,16))
        sheet.fill((0,0,255),(16,0,16,16))
        with patch.object(visuals,'_document',doc),patch.object(visuals,'load_image',return_value=sheet):
            visuals._sprites.clear()
            a=visuals.sprite('hero',(16,16),frame=0)
            b=visuals.sprite('hero',(16,16),frame=1)
            self.assertNotEqual(a.get_at((8,8)),b.get_at((8,8)))
        visuals._sprites.clear()

    def test_reject_invalid_tint_animation_and_card_overlap(self):
        doc=copy.deepcopy(visuals.catalog())
        doc['objects']['enemy_chaser'].update(tint='red',frames=9,columns=1,rows=1)
        doc['objects']['card_style']['desc_y']=170
        self.assertGreaterEqual(len(visuals.validate_catalog(doc)),3)

    def test_legacy_stats_survive_visual_migration(self):
        doc={'schema':'bluecube.objects.v1','objects':{
            key:copy.deepcopy(value) for key,value in visuals.catalog()['objects'].items()
            if key in ('hero','portal','pistol','sword','heal_potion','dash_refresh','time_stop')}}
        doc['objects']['hero']['health']=180
        expanded=visuals.with_visual_defaults(doc)
        self.assertEqual(expanded['objects']['hero']['health'],180)
        self.assertIn('card_blood_trail',expanded['objects'])

    def test_effect_assets_expire_without_changing_gameplay_timers(self):
        from systems.effects import EffectsSystem
        effects=EffectsSystem()
        effects.damage_number(20,(960,540))
        effects.impact((960,540))
        effects.ring((960,540))
        effects.slash((920,500),(1000,560))
        self.assertTrue(effects.sprite_effects)
        surface=pygame.Surface((1920,1080),pygame.SRCALPHA)
        font=pygame.font.Font(None,24)
        effects.draw(surface,Camera(),font)
        effects.update(3)
        self.assertFalse(effects.sprite_effects)
        self.assertFalse(effects.rings)
        self.assertFalse(effects.slashes)


if __name__=='__main__':
    unittest.main(verbosity=2)
