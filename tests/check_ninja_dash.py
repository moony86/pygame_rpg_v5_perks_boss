"""Deterministic ninja finisher checks against the actual player/combat code."""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("BLUECUBE_DEV_TOOLS", "0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from entities.player import Player
from entities.enemy import Enemy, EnemyType
from systems.combat_system import CombatSystem
from systems.perk_system import PERK_EFFECTS
from systems.ninja_dash import next_chain_target, CHAIN_MAX_HOPS
from systems.shooting_system import ShootingSystem


class NinjaChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def setUp(self):
        self.player = Player()
        self.player.rect.center = (400, 300)
        PERK_EFFECTS["phantom_step"][0](self.player)
        self.player.try_active_skill()
        self.combat = CombatSystem()

    def enemy(self, x, y=300, health=1, kind=EnemyType.CHASER):
        enemy = Enemy(x, y, kind)
        enemy.rect.center = (x, y)
        enemy.health = health
        return enemy

    def test_chain_kills_four_enemies_with_one_charge(self):
        enemies = [self.enemy(x) for x in (480, 610, 740, 870)]
        charges = self.player.dash_charges
        kills = []
        for _ in range(100):
            p = self.player
            p.velocity = p.dash_direction * 900 * p.dash_speed_multiplier if p.dash_timer > 0 else pygame.Vector2()
            p.update(0.01)
            kills.extend(self.combat._update_dash_strike(p, [], enemies))
        self.assertEqual(len(kills), 4)
        self.assertEqual(len({id(e) for e in kills}), 4)
        self.assertEqual(self.player.ninja_chain_hops, 3)
        self.assertEqual(self.player.dash_charges, charges)
        self.assertEqual(self.player.active_weapon_key, "pistol")

    def test_targeting_rejects_behind_off_lane_boss_and_wall(self):
        p = self.player
        valid = self.enemy(600)
        wrong = [self.enemy(350), self.enemy(550, 450), self.enemy(500, kind=EnemyType.BOSS)]
        self.assertIs(next_chain_target(p, wrong + [valid], []), valid)
        self.assertIsNone(next_chain_target(p, wrong + [valid], [pygame.Rect(510, 260, 20, 80)]))

    def test_survivor_does_not_start_chain_or_take_duplicate_hits(self):
        enemy = self.enemy(400, health=1000)
        self.combat._update_dash_strike(self.player, [], [enemy])
        health = enemy.health
        self.combat._update_dash_strike(self.player, [], [enemy])
        self.assertEqual(enemy.health, health)
        self.assertEqual(self.player.ninja_chain_hops, 0)

    def test_limit_wall_cancel_and_scene_reset(self):
        p = self.player
        p.ninja_chain_hops = CHAIN_MAX_HOPS
        self.assertIsNone(next_chain_target(p, [self.enemy(500)], []))
        p.ninja_chain_active = True
        p._dash_wall_bounce("x")
        self.assertEqual(p.dash_timer, 0)
        self.assertFalse(p.ninja_chain_active)
        p.reset_ninja_scene_state()
        self.assertEqual(p.ninja_chain_hops, 0)
        self.assertEqual(p.sword_attack_timer, 0)

    def test_swept_strike_catches_enemy_between_frames(self):
        p = self.player
        p.dash_previous_center = (400, 300)
        p.rect.center = (550, 300)
        enemy = self.enemy(475)
        self.assertEqual(self.combat._update_dash_strike(p, [], [enemy]), [enemy])

    def test_gun_is_silent_during_sword_dash_and_returns(self):
        shooting = ShootingSystem()
        self.assertFalse(shooting.try_shoot(self.player, []))
        self.player.dash_timer = 0
        self.assertTrue(shooting.try_shoot(self.player, []))

    def test_automatic_leg_stops_at_survivor(self):
        p = self.player
        p.ninja_chain_active = True
        enemy = self.enemy(400, health=1000)
        self.combat._update_dash_strike(p, [], [enemy])
        self.assertEqual(p.dash_timer, 0)
        self.assertFalse(p.ninja_chain_active)
        self.assertTrue(enemy.alive)

    def test_expired_chain_releases_movement(self):
        p = self.player
        p.ninja_chain_active = True
        p.dash_timer = 0.001
        p.update(0.01)
        self.assertFalse(p.ninja_chain_active)


if __name__ == "__main__":
    unittest.main(verbosity=2)
