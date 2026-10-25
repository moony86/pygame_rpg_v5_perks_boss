"""Four cosmetic identities, identical firing mechanics and safe pool reuse."""
import os
import sys
import random
import unittest
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from entities.player import Player
from systems.shooting_system import ShootingSystem
from systems.camera import Camera
from systems.class_weapon_presentation import BUILDS, identity
from systems.object_catalog import sprite, catalog, validate_catalog


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_cosmetics_do_not_change_real_firing(self):
        baseline = None
        for build in ('', *BUILDS):
            player = Player()
            player.starter_build = build
            player.projectile_count = 3
            player.crit_chance = .5
            player.pierce = 2
            shooting = ShootingSystem()
            shots = []
            random.seed(42)
            self.assertTrue(shooting.try_shoot(player, shots))
            result = (shooting.shoot_timer, [(shot.damage, tuple(shot.pos), tuple(shot.direction),
                      shot.speed, shot.pierce_remaining, shot.critical, shot.source,
                      shot.explosive, tuple(shot.rect)) for shot in shots])
            if baseline is None:
                baseline = result
            self.assertEqual(result, baseline)
            self.assertTrue(all(shot.class_visual == identity(player) for shot in shots))

    def test_each_family_uses_generated_atlas_and_real_hit_feedback(self):
        from systems.effects import EffectsSystem
        from entities.enemy import Enemy, EnemyType
        camera = Camera()
        output = ROOT / 'debug_screenshots' / 'class-weapons'
        output.mkdir(parents=True, exist_ok=True)
        sheet = pygame.Surface((1100, 640))
        sheet.fill((15, 24, 35))
        for row, build in enumerate(BUILDS):
            player = Player()
            player.starter_build = build
            shots = []
            ShootingSystem().try_shoot(player, shots)
            shot = shots[0]
            effects = EffectsSystem()
            target = Enemy(700, row * 155 + 70, EnemyType.CHASER)
            effects.projectile_hit(shot, (420, row * 155 + 85), target)
            self.assertEqual(effects.shot_effects[-1].class_visual, BUILDS[build])
            effects.update(.03)
            effects.draw(sheet, camera, pygame.font.Font(None, 24))
            for prefix in ('weapon_', 'shot_', 'launch_', 'trail_', 'impact_', 'target_'):
                key = prefix + BUILDS[build]
                self.assertIn('weapons/', catalog()['objects'][key]['art'])
                self.assertGreater(pygame.mask.from_surface(sprite(key), 1).count(), 10)
            effects.projectile_hit(shot, (900, row * 155 + 85), target, shield=True)
            self.assertEqual(effects.shot_effects[-1].class_visual, '')
            effects.update(3.)
            self.assertFalse(effects.shot_effects)
        pygame.image.save(sheet, output / 'impacts-v2.png')

    def test_pool_reuse_and_player_reset_forget_visual_identity(self):
        player = Player()
        player.starter_build = 'Ninja'
        shooting = ShootingSystem()
        from systems.projectile_pool import ProjectilePool
        shooting.projectile_pool = ProjectilePool(1)
        shots = []
        shooting.try_shoot(player, shots)
        shot = shots[0]
        self.assertEqual(shot.class_visual, 'ninja')
        shooting.projectile_pool.release(shot)
        reused = shooting.projectile_pool.acquire(0, 0, (1, 0), 10, speed=500)
        self.assertIs(reused, shot)
        self.assertEqual(reused.class_visual, '')
        player.reset()
        self.assertEqual(identity(player), '')

    def test_four_families_in_real_game_scene(self):
        from game import Game
        game = Game()
        game.reset_run()
        game.prototype_room.enter()
        game.prototype_room.spawn_plan = ()
        game.prototype_room.pending.clear()
        output = ROOT / 'debug_screenshots' / 'class-weapons'
        output.mkdir(parents=True, exist_ok=True)
        for build, kind in BUILDS.items():
            game.player.starter_build = build
            game.player.rect.center = (960, 540)
            game.player.aim_direction.update(1, 0)
            game.player.anim_time = .1
            game.projectiles.clear()
            game.effects.reset()
            game.shooting.shoot_timer = 0
            game.shooting.try_shoot(game.player, game.projectiles)
            for shot in game.projectiles:
                shot.update(.07)
                game.effects.projectile_hit(shot, (1150, 540))
            game.draw()
            pygame.image.save(game.screen, output / f'in-game-{kind}-v2.png')

    def test_all_identities_draw_in_both_directions_and_animate(self):
        self.assertEqual(validate_catalog(catalog()), [])
        output = ROOT / 'debug_screenshots' / 'class-weapons'
        output.mkdir(parents=True, exist_ok=True)
        camera = Camera()
        font = pygame.font.Font(None, 26)
        for frame, time in enumerate((.05, .18)):
            sheet = pygame.Surface((1100, 640))
            sheet.fill((15, 24, 35))
            for row, build in enumerate(BUILDS):
                y = row * 155
                sheet.blit(font.render(build, True, (215, 240, 250)), (24, y + 20))
                art = sprite('weapon_' + BUILDS[build], size=(64, 64))
                self.assertGreater(pygame.mask.from_surface(art, 1).count(), 20)
                sheet.blit(art, art.get_rect(center=(220, y + 72)))
                for column, direction in enumerate((1, -1)):
                    player = Player()
                    player.starter_build = build
                    player.rect.center = (400 + column * 350, y + 75)
                    player.aim_direction.update(direction, 0)
                    player.anim_time = time
                    shots = []
                    shooting = ShootingSystem()
                    shooting.try_shoot(player, shots)
                    before = (player.health, player.damage_bonus, player.rect.copy())
                    player.draw(sheet, camera)
                    for shot in shots:
                        shot.update(time)
                        state = (shot.pos.copy(), shot.damage, shot.rect.copy())
                        shot.draw(sheet, camera)
                        self.assertEqual(state, (shot.pos, shot.damage, shot.rect))
                    self.assertEqual(before, (player.health, player.damage_bonus, player.rect))
            pygame.image.save(sheet, output / f'preview-{frame}.png')


if __name__ == '__main__':
    unittest.main(verbosity=2)
