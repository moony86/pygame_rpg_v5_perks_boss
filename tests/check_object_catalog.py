"""Object catalog, gameplay bindings and pickup placement checks."""
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from systems import object_catalog as objects
from entities.player import Player
from systems.shooting_system import ShootingSystem
from systems.stage_document import default_document, validate_document, document_nodes


class ObjectCatalogChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def setUp(self):
        self.doc=copy.deepcopy(objects.catalog())

    def test_catalog_is_valid_and_art_transparent(self):
        self.assertEqual(objects.validate_catalog(self.doc),[])
        for key in self.doc['objects']:
            sprite=objects.sprite(key)
            self.assertIsNotNone(sprite)
            self.assertTrue(sprite.get_flags() & pygame.SRCALPHA)

    def test_reject_unsafe_art_and_nonfinite_stats(self):
        self.doc['objects']['hero']['art']='../private.png'
        self.doc['objects']['hero']['speed']=float('nan')
        self.assertGreaterEqual(len(objects.validate_catalog(self.doc)),2)

    def test_character_stats_are_live_definitions(self):
        self.doc['objects']['hero'].update(health=180,speed=420)
        with patch.object(objects,'_document',self.doc):
            p=Player()
            self.assertEqual((p.health,p.speed),(180,420))
            p.reset()
            self.assertEqual((p.health,p.speed),(180,420))

    def test_pistol_stats_drive_real_projectiles(self):
        self.doc['objects']['pistol'].update(damage=61,cooldown=.7,projectile_speed=900)
        with patch.object(objects,'_document',self.doc):
            player=Player()
            projectiles=[]
            shooting=ShootingSystem()
            self.assertTrue(shooting.try_shoot(player,projectiles))
            self.assertEqual(projectiles[0].damage,61)
            self.assertAlmostEqual(shooting.shoot_timer,.7)

    def test_drop_settings_drive_potion_and_time_stop(self):
        from systems.loot_system import LootSystem
        self.doc['objects']['heal_potion']['drop_chance']=1
        self.doc['objects']['heal_potion'].update(small=29,medium=29,large=29)
        with patch.object(objects,'_document',self.doc):
            loot=LootSystem()
            loot.spawn_special_enemy_drop((300,300))
            self.assertEqual((loot.pickups[0].pickup_type,loot.pickups[0].value),('heal_potion',29))

    def test_stage_serializes_placed_pickup_kind(self):
        doc=default_document()
        doc['rooms'][0]['pickups'][0]['kind']='heal_potion'
        self.assertEqual(validate_document(doc),[])
        self.assertEqual(document_nodes(doc)[0].room.layout.movement_pickups[0].kind,'heal_potion')
        doc['rooms'][0]['pickups'][0]['kind']='invented_effect'
        self.assertTrue(validate_document(doc))

    def test_placed_potion_heals_and_does_not_respawn(self):
        from game import Game
        game=Game()
        game.player.health=50
        rect=game.player.rect.copy()
        game.stage._add_movement_pickup(rect,'heal_potion')
        game.update_movement_pickups(.01)
        self.assertEqual(game.player.health,50+objects.definition('heal_potion')['medium'])
        game.update_movement_pickups(20)
        self.assertFalse(game.movement_pickups)

    def test_placed_time_stop_uses_configured_duration(self):
        from game import Game
        game=Game()
        game.stage._add_movement_pickup(game.player.rect.copy(),'time_stop')
        game.update_movement_pickups(.01)
        self.assertEqual(game.player.enemy_time_stop_timer,objects.definition('time_stop')['duration'])

    def test_dash_charge_restores_resource_and_uses_buff_duration(self):
        from game import Game
        game=Game()
        game.player.enable_ninja_dash_charges()
        game.player.dash_charges=0
        game.player.dash_cooldown_timer=3
        game.stage._add_movement_pickup(game.player.rect.copy(),'dash_refresh')
        game.update_movement_pickups(.01)
        config=objects.definition('dash_refresh')
        self.assertEqual(game.player.dash_charges,config['charges'])
        self.assertEqual(game.player.ghost_timer,config['duration'])
        self.assertEqual(game.player.invulnerable_timer,config['duration'])
        self.assertEqual(game.player.dash_cooldown_timer,0)


if __name__=='__main__':
    unittest.main(verbosity=2)
