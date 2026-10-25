"""Simulation checks for the first Brute/Elite identity prototype."""
import os
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from entities.enemy import Enemy, EnemyType
from entities.player import Player
from systems.champion_encounters import sync_escorts, guards_alive
from systems.combat_action_resolver import CombatActionResolver
from systems.effects import EffectsSystem
from systems.camera import Camera


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def enemy(self, kind):
        enemy = Enemy(500, 400, kind)
        enemy.rect.center = (500, 400)
        return enemy

    def test_brute_shared_gate_and_short_exposure(self):
        enemy = self.enemy(EnemyType.BRUTE)
        health = enemy.health
        for amount in (15, 80, 10000):
            self.assertFalse(enemy.take_damage(amount))
            self.assertEqual(enemy.health, health)
        enemy._start_windup(.46, pygame.Vector2(1, 0), 'brute_charge')
        enemy.take_damage(10)
        self.assertEqual(enemy.health, health-10)
        enemy.windup_action = None
        enemy.brute_stop_timer = 1.15
        self.assertTrue(enemy.take_damage(10000))

    def test_brute_approaches_charges_and_slam_has_warning(self):
        enemy = self.enemy(EnemyType.BRUTE)
        enemy.attack_cooldown = 0
        events = []
        for _ in range(140):
            event = enemy.update(.01, pygame.Rect(770, 380, 40, 40), [])
            if event:
                events.append(event)
        self.assertIn('brute_charge', [event['type'] for event in events])
        self.assertIn('champion_slam', [event['type'] for event in events])
        self.assertGreater(enemy.brute_stop_timer, 0)

    def test_guards_finite_and_break_reduction_then_stagger(self):
        elite = self.enemy(EnemyType.ELITE)
        enemies = [elite]
        sync_escorts(enemies, [])
        self.assertEqual(len(guards_alive(elite)), 2)
        health = elite.health
        elite.take_damage(40)
        self.assertEqual(elite.health, health-10)
        elite.update(.01, pygame.Rect(900, 400, 30, 30), [])
        for guard in guards_alive(elite):
            guard.take_damage(10000)
        elite.update(.01, pygame.Rect(900, 400, 30, 30), [])
        self.assertEqual(elite.elite_state, 'stagger')
        sync_escorts(enemies, [])
        self.assertEqual(len(enemies), 3)
        health = elite.health
        elite.take_damage(40)
        self.assertEqual(elite.health, health-40)

    def test_elite_has_two_separate_warned_attacks(self):
        elite = self.enemy(EnemyType.ELITE)
        elite.attack_cooldown = 0
        states, events = set(), []
        for _ in range(200):
            event = elite.update(.01, pygame.Rect(720, 380, 40, 40), [])
            states.add(elite.elite_state)
            if event:
                events.append(event)
        self.assertTrue({'warn_one', 'warn_two', 'strike_one', 'strike_two', 'recover'} <= states)
        self.assertEqual(len(events), 2)

    def test_slam_deals_damage_and_respects_dash_invulnerability(self):
        enemy = self.enemy(EnemyType.BRUTE)
        player = Player()
        player.rect.center = enemy.rect.center
        player.invulnerable_timer = 0
        game = SimpleNamespace(player=player, effects=EffectsSystem(), audio=SimpleNamespace(play=lambda *args: None))
        action = {'type': 'champion_slam', 'enemy': enemy, 'radius': 110}
        before = player.health
        CombatActionResolver().handle(action, game)
        self.assertLess(player.health, before)
        before = player.health
        CombatActionResolver().handle(action, game)
        self.assertEqual(player.health, before)

    def test_render_states_without_mutating_combat(self):
        output = ROOT / 'debug_screenshots' / 'champions'
        output.mkdir(parents=True, exist_ok=True)
        for index, opened in enumerate((False, True, True)):
            surface = pygame.Surface((1000, 600))
            surface.fill((15, 24, 35))
            brute = self.enemy(EnemyType.BRUTE)
            brute.rect.center = (260, 280)
            if opened:
                brute._start_windup(.46, pygame.Vector2(1, 0), 'brute_charge')
            elite = self.enemy(EnemyType.ELITE)
            elite.rect.center = (720, 280)
            enemies = [brute, elite]
            sync_escorts(enemies, [])
            if index == 2:
                brute.windup_action = None
                brute.brute_stop_timer = 1.15
                brute.brute_slam_pending = .28
                for guard in elite.escort_guards:
                    guard.alive = False
                elite.elite_state = 'warn_two'
                elite.elite_timer = .3
                elite.windup_direction.update(-1, 0)
            before = [(enemy.health, enemy.rect.copy()) for enemy in enemies]
            for enemy in enemies:
                if enemy.alive:
                    enemy.draw(surface, Camera())
            self.assertEqual(before, [(enemy.health, enemy.rect) for enemy in enemies])
            pygame.image.save(surface, output / f'prototype-{index}.png')

    def test_real_game_loop_spawns_escort_once_and_renders(self):
        from game import Game
        game = Game()
        game.reset_run()
        game.prototype_room.enter()
        game.prototype_room.spawn_plan = ()
        game.prototype_room.total_spawns = 0
        game.prototype_room.pending.clear()
        elite = self.enemy(EnemyType.ELITE)
        brute = self.enemy(EnemyType.BRUTE)
        elite.rect.center = (980, 400)
        brute.rect.center = (1250, 600)
        game.enemies = [elite, brute]
        for _ in range(10):
            game.update(.016)
        self.assertTrue(elite.escort_spawned)
        self.assertEqual(len(elite.escort_guards), 2)
        self.assertEqual(len(game.enemies), 4)
        game.draw()
        output = ROOT / 'debug_screenshots' / 'champions'
        output.mkdir(parents=True, exist_ok=True)
        pygame.image.save(game.screen, output / 'in-game.png')


if __name__ == '__main__':
    unittest.main(verbosity=2)
