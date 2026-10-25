"""Regression checks for actual impact events and transient world-space visuals."""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from entities.player import Player
from entities.enemy import Enemy, EnemyType
from systems.combat_system import CombatSystem
from systems.effects import EffectsSystem
from systems import speed_presentation


class FeedbackChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_bomber_impact_survives_return_and_draws_immediately(self):
        player = Player()
        player.engineer_bomber_pos.update(300, 250)
        player.engineer_bomber_damage = 10
        player.engineer_bomber_radius = 96
        enemy = Enemy(300, 250, EnemyType.CHASER)
        enemy.rect.center = (300, 250)
        enemy.health = 100
        effects = EffectsSystem()
        CombatSystem()._explode_engineer_bomber(player, [enemy], effects)
        self.assertEqual(enemy.health, 90)
        blast = next(fx for fx in effects.sprite_effects if fx.visual_key == 'fx_explosion')
        player.engineer_bomber_pos.update(100, 100)
        player.engineer_bomber_state = 'cooldown'
        self.assertEqual(blast.pos, pygame.Vector2(300, 250))
        camera = type('Camera', (), {'apply_pos': lambda self, p: pygame.Vector2(p)})()
        frame = pygame.Surface((600, 500), pygame.SRCALPHA)
        blast.draw(frame, camera)
        self.assertGreater(pygame.mask.from_surface(frame, 1).count(), 100)
        output = Path(__file__).resolve().parents[1] / 'artifacts' / 'visual-feedback'
        output.mkdir(parents=True, exist_ok=True)
        preview = pygame.Surface((600, 500))
        preview.fill((16, 24, 35))
        effects.draw(preview, camera, pygame.font.Font(None, 20))
        pygame.image.save(preview, output / 'bomber-impact.png')
        effects.update(1.)
        self.assertEqual(effects.sprite_effects, [])

    def test_speed_trail_is_world_space_bounded_and_fades_at_rest(self):
        player = Player()
        player.ghost_timer = 3.
        player.rect.center = (300, 300)
        for _ in range(30):
            previous = player.rect.center
            player.rect.x += 8
            speed_presentation.update(player, .04, previous)
        self.assertLessEqual(len(player._speed_wakes), 6)
        self.assertGreater(len(player._speed_wakes), 0)
        for _ in range(8):
            speed_presentation.update(player, .04, player.rect.center)
        self.assertEqual(player._speed_wakes, [])

    def test_exit_grace_expires_without_refresh(self):
        player = Player()
        player.invulnerable_timer = 0.
        player.ninja_chain_active = True
        player.finish_ninja_chain()
        self.assertAlmostEqual(player.invulnerable_timer, .35)
        player.update(.2)
        self.assertGreater(player.invulnerable_timer, 0.)
        player.update(.2)
        self.assertEqual(player.invulnerable_timer, 0.)

    def test_ninja_and_vampire_events_create_renderable_feedback(self):
        from systems.perk_system import PERK_EFFECTS
        camera = type('Camera', (), {'apply_pos': lambda self, p: pygame.Vector2(p)})()
        for build in ('ninja', 'vampire'):
            player = Player()
            player.rect.center = (300, 250)
            enemy = Enemy(300, 250, EnemyType.CHASER)
            enemy.rect.center = player.rect.center
            enemy.health = 1000
            effects = EffectsSystem()
            combat = CombatSystem()
            if build == 'ninja':
                PERK_EFFECTS['phantom_step'][0](player)
                player.try_active_skill()
                combat._update_dash_strike(player, [], [enemy], effects=effects)
                self.assertTrue(effects.slashes)
            else:
                player.vampire_wound_stacks_per_hit = 1
                player.vampire_wound_max_stacks = 4
                combat._apply_sanguine_wound(player, enemy, effects)
                self.assertTrue(effects.rings)
            effects.update(.04)
            frame = pygame.Surface((600, 500), pygame.SRCALPHA)
            effects.draw(frame, camera, pygame.font.Font(None, 20))
            self.assertGreater(pygame.mask.from_surface(frame, 1).count(), 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
