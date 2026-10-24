"""Coverage and visual/gameplay separation for every actor family."""
import os
import sys
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.enemy import Enemy,EnemyType
from entities.player import Player
from entities.npc import NPC
from systems.camera import Camera
from systems.effects import EffectsSystem


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_every_enemy_renders_idle_move_hit_and_attack_without_logic_mutation(self):
        screen=pygame.Surface((1920,1080))
        camera=Camera()
        for kind in EnemyType:
            for action in (None,'hunter_homing','elite_cross','boss_laser','boss_ring','boss_summon_leap'):
                enemy=Enemy(600,500,kind)
                enemy.visual_moving=True
                enemy.visual_stride=1.2
                enemy.hit_flash=.04
                if action:
                    enemy._start_windup(.5,pygame.Vector2(1,0),action)
                before=(enemy.rect.copy(),enemy.health,enemy.speed,enemy.windup_timer,enemy.visual_release_timer)
                for _ in range(2):
                    enemy.draw(screen,camera)
                self.assertEqual(before,(enemy.rect,enemy.health,enemy.speed,enemy.windup_timer,enemy.visual_release_timer))

    def test_all_death_echoes_expire_and_do_not_change_rewards(self):
        for kind in EnemyType:
            enemy=Enemy(600,500,kind)
            fx=EffectsSystem()
            fx.actor_death(enemy)
            self.assertEqual(len(fx.sprite_effects),1)
            fx.sprite_effects[0].update(.4)
            self.assertFalse(fx.sprite_effects[0].alive)

    def test_boss_all_phases_render(self):
        enemy=Enemy(600,500,EnemyType.BOSS)
        for phase in (1,2,3):
            enemy.phase=phase
            enemy.draw(pygame.Surface((1920,1080)),Camera())
            fx=EffectsSystem()
            fx.actor_death(enemy)
            self.assertEqual(len(fx.sprite_effects),1)

    def test_hero_hurt_reset_and_weapon_geometry(self):
        player=Player()
        player.take_damage(1)
        self.assertEqual(player.visual_hurt_timer,.12)
        before=(player.rect.copy(),player.weapon_muzzle_position().copy(),player.health)
        player.move_direction.update(1,0)
        player.anim_time=.2
        player.draw(pygame.Surface((1920,1080)),Camera())
        self.assertEqual(before,(player.rect,player.weapon_muzzle_position(),player.health))
        player.reset()
        self.assertEqual(player.visual_hurt_timer,0)

    def test_npc_draw_does_not_advance_animation(self):
        for role in ('blacksmith','healer','seer','portal','tea_vendor'):
            npc=NPC(600,500,role,role,role)
            npc.update(.2)
            npc.draw(pygame.Surface((1920,1080)),Camera())
            self.assertEqual(npc._anim,.2)


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    sheet=pygame.Surface((1200,800))
    sheet.fill((14,20,30))
    font=pygame.font.Font(None,22)
    for i,kind in enumerate(EnemyType):
        tile=sheet.subsurface(((i%5)*240,(i//5)*240,240,240))
        enemy=Enemy(120,95,kind)
        enemy.rect.center=(120,95)
        enemy._anim=.4
        enemy.visual_stride=1.2
        enemy.visual_moving=True
        enemy.brute_stride=1.2
        enemy.brute_moving=True
        enemy.draw(tile,Camera())
        tile.blit(font.render(kind.name,True,'white'),(14,190))
    player=Player()
    player.rect.center=(80,760)
    player.move_direction.update(1,0)
    player.anim_time=.2
    player.draw(sheet,Camera())
    sheet.blit(font.render('HERO',True,'white'),(120,748))
    pygame.image.save(sheet,str(ROOT/'debug_screenshots/all-actor-motion.png'))


if __name__=='__main__':
    capture()
    unittest.main()
