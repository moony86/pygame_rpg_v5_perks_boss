"""Cosmetic outfits plus executable checks for the documented Vampire behavior."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from entities.player import Player
from entities.enemy import Enemy, EnemyType
from systems.class_appearance import hero_key, SKINS
from systems.object_catalog import sprite, validate_catalog, catalog
from systems.camera import Camera
from systems.perk_system import PERK_EFFECTS
from systems.combat_system import CombatSystem


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_bindings_and_hybrid_perks_do_not_change_outfit(self):
        self.assertEqual(validate_catalog(catalog()), [])
        images = []
        for build, key in SKINS.items():
            player = Player()
            player.starter_build = build
            self.assertEqual(hero_key(player), key)
            PERK_EFFECTS['vital_core'][0](player)
            self.assertEqual(hero_key(player), key)
            image = sprite(key)
            self.assertEqual(image.get_size(), sprite('hero').get_size())
            self.assertGreater(pygame.mask.from_surface(image, 1).count(), 100)
            images.append(pygame.image.tobytes(image, 'RGBA'))
            player.reset()
            self.assertEqual(hero_key(player), 'hero')
        self.assertEqual(len(set(images)), 4)

    def test_outfit_mirrors_and_dash_ghost_uses_selected_skin(self):
        player = Player()
        player.starter_build = 'Ninja'
        player.aim_direction.update(-1, 0)
        left = player._current_player_sprite()
        player.aim_direction.update(1, 0)
        right = player._current_player_sprite()
        self.assertEqual(pygame.image.tobytes(right, 'RGBA'),
                         pygame.image.tobytes(pygame.transform.flip(left, True, False), 'RGBA'))
        player.dash_timer = .2
        player._update_dash_ghosts(.01)
        self.assertTrue(player.dash_ghosts)
        expected = player._current_player_sprite()
        self.assertEqual(pygame.image.tobytes(player.dash_ghosts[0]['image'], 'RGBA'),
                         pygame.image.tobytes(expected, 'RGBA'))

    def test_real_draw_gallery_preserves_collision_and_stats(self):
        output = ROOT / 'debug_screenshots' / 'class-outfits'
        output.mkdir(parents=True, exist_ok=True)
        camera = Camera()
        font = pygame.font.Font(None, 26)
        for frame, time in enumerate((0., .15)):
            sheet = pygame.Surface((1100, 620))
            sheet.fill((15, 24, 35))
            for row, (build, key) in enumerate(SKINS.items()):
                sheet.blit(font.render(build, True, (215, 240, 250)), (24, row*150+20))
                art = sprite(key, size=(100, 100))
                sheet.blit(art, art.get_rect(center=(230, row*150+75)))
                for column, direction in enumerate((-1, 1)):
                    player = Player()
                    player.starter_build = build
                    player.rect.center = (480 + column*300, row*150+75)
                    player.aim_direction.update(direction, 0)
                    player.anim_time = time
                    player.move_direction.update(direction, 0)
                    before = (player.rect.copy(), player.health, player.speed, player.damage_bonus)
                    player.draw(sheet, camera)
                    self.assertEqual(before, (player.rect, player.health, player.speed, player.damage_bonus))
            pygame.image.save(sheet, output / f'gallery-{frame}.png')

    def test_vampire_starter_is_wounds_and_feed_not_automatic_healing(self):
        player = Player()
        player.health = 50
        PERK_EFFECTS['sanguine_rounds'][0](player)
        enemy = Enemy(300, 300, EnemyType.CHASER)
        combat = CombatSystem()
        combat._apply_sanguine_wound(player, enemy)
        for _ in range(3):
            combat._apply_vampire_hit_feed(player, enemy)
        self.assertEqual(enemy.vampire_wound_stacks, 1)
        self.assertEqual(player.vampire_blood, 1)
        self.assertEqual(player.health, 50)
        self.assertFalse(player.vampire_bat_enabled)
        self.assertFalse(player.vampire_feast_unlocked)
        fresh_enemy = Enemy(300, 300, EnemyType.CHASER)
        fresh_enemy.take_damage(fresh_enemy.health)
        combat._apply_sanguine_wound(player, fresh_enemy)
        self.assertEqual(getattr(fresh_enemy, 'vampire_wound_stacks', 0), 0)

    def test_documented_full_tank_stalls_feast_and_trail_does_not_require_dash(self):
        player = Player()
        PERK_EFFECTS['sanguine_rounds'][0](player)
        PERK_EFFECTS['battle_recovery'][0](player)
        player.vampire_blood = player.vampire_max_blood
        before = player.vampire_feast_progress
        self.assertEqual(player.add_blood(2), 0)
        self.assertEqual(player.vampire_feast_progress, before)
        PERK_EFFECTS['blood_trail'][0](player)
        player.vampire_blood = 0
        player.move_direction.update(1, 0)
        player.dash_timer = 0
        enemy = Enemy(0, 0, EnemyType.CHASER)
        enemy.rect.center = player.rect.center
        enemy.vampire_wound_stacks = 1
        CombatSystem()._update_vampire_trail(.1, player, [enemy])
        self.assertGreater(player.vampire_blood, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
