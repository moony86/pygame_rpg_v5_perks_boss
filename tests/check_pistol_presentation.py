"""Pistol grip/muzzle/recoil checks and native diagnostic renders."""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("BLUECUBE_DEV_TOOLS", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from entities.player import Player
from systems.camera import Camera
from systems.shooting_system import ShootingSystem
from systems.pistol_presentation import (
    pistol_pose, render_pistol, PISTOL_GRIP, PISTOL_MUZZLE, PISTOL_SIZE,
    PISTOL_RECOIL_PIXELS, PISTOL_SHOT_SECONDS, PISTOL_FLASH_SECONDS,
)

ANGLES = tuple(range(0, 360, 45))


class PistolPresentationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_grip_and_muzzle_follow_same_transform_in_eight_directions(self):
        for angle in ANGLES:
            aim = pygame.Vector2(1, 0).rotate(angle)
            pose = pistol_pose((200, 200), aim)
            for local, world in ((PISTOL_GRIP, pose.grip), (PISTOL_MUZZLE, pose.muzzle)):
                offset = pygame.Vector2(local) - pygame.Vector2(PISTOL_SIZE) / 2
                if pose.flip_vertical:
                    offset.y = -offset.y
                self.assertLess((pose.center + offset.rotate(pose.angle)).distance_to(world), 0.00001)
            self.assertGreater((pose.muzzle - pygame.Vector2(200, 200)).dot(aim), 30)

    def test_real_projectiles_start_at_rendered_muzzle_in_eight_directions(self):
        for angle in ANGLES:
            player = Player()
            player.rect.center = (500, 500)
            player.aim_direction = pygame.Vector2(1, 0).rotate(angle)
            projectiles = []
            self.assertTrue(ShootingSystem().try_shoot(player, projectiles))
            pose = pistol_pose(player.rect.center, player.aim_direction, player.gun_shoot_timer)
            self.assertLess(projectiles[0].pos.distance_to(pose.muzzle), 0.00001)
            self.assertLess(projectiles[0].direction.distance_to(player.aim_direction), 0.00001)

    def test_recoil_is_bounded_and_recovers_without_accumulating(self):
        center = pygame.Vector2(100, 100)
        for angle in ANGLES:
            aim = pygame.Vector2(1, 0).rotate(angle)
            idle = pistol_pose(center, aim)
            fired = pistol_pose(center, aim, PISTOL_SHOT_SECONDS)
            delta = idle.grip - fired.grip
            self.assertAlmostEqual(delta.length(), PISTOL_RECOIL_PIXELS)
            self.assertGreater(delta.dot(aim), 0)
            self.assertLess(pistol_pose(center, aim, 0).grip.distance_to(idle.grip), 0.00001)
        player = Player()
        for _ in range(50):
            player.trigger_gun_shot()
        self.assertEqual(player.gun_shoot_timer, PISTOL_SHOT_SECONDS)
        player.update(0.2, [])
        self.assertEqual(player.gun_shoot_timer, 0)

    def test_pixel_palette_and_size_preserved(self):
        player = Player()
        source = pygame.image.load(str(ROOT / "assets/gun.png"))
        palette = {tuple(source.get_at((x, y))) for x in range(source.get_width()) for y in range(source.get_height())}
        image = Player._gun_image
        self.assertEqual(image.get_size(), (32, 32))
        for x in range(32):
            for y in range(32):
                self.assertIn(tuple(image.get_at((x, y))), palette)

    def test_flash_is_brief_and_absent_while_idle(self):
        image = pygame.Surface((32, 32), pygame.SRCALPHA)
        for timer, expected in ((0, False), (PISTOL_SHOT_SECONDS, True),
                                (PISTOL_SHOT_SECONDS - PISTOL_FLASH_SECONDS - 0.001, False)):
            surface = pygame.Surface((120, 120), pygame.SRCALPHA)
            render_pistol(surface, image, pistol_pose((60, 60), (1, 0), timer), timer)
            self.assertEqual(surface.get_bounding_rect().width > 0, expected)

    def test_split_shots_share_one_muzzle_and_keep_damage_rules(self):
        player = Player()
        player.projectile_count = 3
        player.spread_degrees = 16
        projectiles = []
        ShootingSystem().try_shoot(player, projectiles)
        self.assertEqual(len(projectiles), 3)
        self.assertEqual({tuple(p.pos) for p in projectiles}, {tuple(player.weapon_muzzle_position())})
        self.assertEqual([p.damage for p in projectiles], [28, 28, 28])


def capture():
    player = Player()
    camera = Camera()
    camera.offset.update(0, 0)
    surface = pygame.Surface((960, 600))
    surface.fill((14, 18, 28))
    font = pygame.font.Font(None, 22)
    for index, angle in enumerate(ANGLES):
        x, y = index % 4 * 240, index // 4 * 300
        aim = pygame.Vector2(1, 0).rotate(angle)
        for column, timer in enumerate((0, PISTOL_SHOT_SECONDS)):
            player.rect.center = (x + 60 + column * 120, y + 110)
            player.aim_direction = aim
            player.gun_shoot_timer = timer
            player.draw(surface, camera)
            muzzle = player.weapon_muzzle_position()
            pygame.draw.circle(surface, (90, 225, 240), (round(muzzle.x), round(muzzle.y)), 2, 1)
        surface.blit(font.render(f"{angle} deg: idle / fired", True, (220, 225, 240)), (x + 24, y + 220))
    output = ROOT / "debug_screenshots/pistol_presentation"
    output.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(output / "eight_directions.png"))


if __name__ == "__main__":
    pygame.init()
    capture()
    unittest.main(verbosity=2)
