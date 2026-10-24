"""Shot VFX regressions: real hits, curve history, pool reset, no fake burn damage."""
import os
import sys
import random
import gc
import weakref
from pathlib import Path
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.projectile import Projectile
from entities.enemy_bullet import EnemyBullet
from entities.enemy import Enemy,EnemyType
from entities.player import Player
from systems.camera import Camera
from systems.effects import EffectsSystem
from systems.combat_system import CombatSystem
from systems.projectile_pool import ProjectilePool
from systems.shot_presentation import ShotHit,draw_charge,style
from systems.object_catalog import catalog,validate_catalog


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_catalog_and_distinct_styles(self):
        self.assertEqual(validate_catalog(catalog()),[])
        self.assertEqual(style(Projectile(0,0,(1,0),10)),'metal')
        self.assertEqual(style(Projectile(0,0,(1,0),10,explosive=True)),'fire')
        self.assertEqual(style(Projectile(0,0,(1,0),10,source='engineer_drone')),'magic')

    def test_curve_history_and_draw_preserve_geometry(self):
        player=Player()
        player.rect.center=(500,500)
        shot=EnemyBullet(100,100,(1,0),10,homing_target=player,turn_rate=3)
        for _ in range(15):
            shot.update(.016)
        self.assertLessEqual(len(shot.visual_trail),8)
        self.assertTrue(all(age<.12 for _,age in shot.visual_trail))
        before=(shot.pos.copy(),shot.rect.copy(),shot.remaining_life,shot.damage)
        shot.draw(pygame.Surface((800,600)),Camera())
        self.assertEqual(before,(shot.pos,shot.rect,shot.remaining_life,shot.damage))

    def test_pool_reinitialization_clears_visual_state(self):
        pool=ProjectilePool(1)
        shot=pool.acquire(100,100,(1,0),10,speed=400)
        shot.update(.03)
        shot.visual_style='fire'
        pool.release(shot)
        reused=pool.acquire(200,200,(0,1),10,speed=400)
        self.assertIs(shot,reused)
        self.assertEqual(reused.visual_trail,[])
        self.assertIsNone(reused.visual_style)

    def test_real_fire_hit_and_cosmetic_effect_expiry(self):
        player=Player()
        player.rect.center=(200,200)
        enemy=Enemy(500,500,EnemyType.CHASER)
        enemy.rect.center=(500,500)
        enemy.health=1000
        shot=Projectile(500,500,(1,0),10,explosive=True)
        effects=EffectsSystem()
        CombatSystem().update(.016,player,[shot],[enemy],[],effects=effects)
        self.assertEqual(enemy.health,990)
        self.assertEqual(len(effects.shot_effects),1)
        self.assertEqual(effects.shot_effects[0].kind,'fire')
        effects.update(1.)
        self.assertEqual(effects.shot_effects,[])
        self.assertEqual(enemy.health,990)

    def test_impact_has_no_gameplay_rng_and_does_not_retain_target(self):
        enemy=Enemy(500,500)
        reference=weakref.ref(enemy)
        shot=Projectile(500,500,(1,0),10)
        state=random.getstate()
        effect=ShotHit(shot,shot.pos,enemy)
        effect.draw(pygame.Surface((800,600)),Camera())
        self.assertEqual(state,random.getstate())
        del enemy
        gc.collect()
        self.assertIsNone(reference())

    def test_piercing_hit_does_not_repeat_damage_or_vfx_on_same_enemy(self):
        player=Player()
        player.rect.center=(200,200)
        enemy=Enemy(500,500)
        enemy.rect.center=(500,500)
        enemy.health=1000
        shot=Projectile(500,500,(1,0),10,pierce=2)
        effects=EffectsSystem()
        combat=CombatSystem()
        combat.update(.016,player,[shot],[enemy],[],effects=effects)
        combat.update(.016,player,[shot],[enemy],[],effects=effects)
        self.assertEqual(enemy.health,990)
        self.assertEqual(len(effects.shot_effects),1)

    def test_legacy_shield_hit_has_no_attached_fire(self):
        player=Player()
        player.rect.center=(200,200)
        boss=Enemy(500,500,EnemyType.BOSS)
        boss.encounter=None  # Explicit legacy fallback, not the current Warden gate.
        boss.rect.center=(500,500)
        boss.shield=100
        boss.phase=1
        original=boss.health
        shot=Projectile(500,500,(1,0),10,explosive=True)
        effects=EffectsSystem()
        CombatSystem().update(.016,player,[shot],[boss],[],effects=effects)
        self.assertEqual(boss.shield,90)
        self.assertEqual(boss.health,original)
        self.assertEqual(effects.shot_effects[0].kind,'magic')
        self.assertIsNone(effects.shot_effects[0].target)

    def test_caps_reset_and_shield_does_not_apply_fire(self):
        effects=EffectsSystem()
        shot=Projectile(500,500,(1,0),10,explosive=True)
        for _ in range(120):
            effects.projectile_hit(shot,shot.pos,shield=True)
        self.assertEqual(len(effects.shot_effects),96)
        self.assertEqual(effects.shot_effects[0].kind,'magic')
        self.assertIsNone(effects.shot_effects[0].target)
        effects.reset()
        self.assertEqual(effects.shot_effects,[])


def capture():
    pygame.init()
    pygame.display.set_mode((1,1))
    canvas=pygame.Surface((960,540))
    canvas.fill((14,20,30))
    font=pygame.font.Font(None,26)
    camera=Camera()
    for row,kind in enumerate(('metal','magic','fire')):
        y=90+row*170
        shot=Projectile(260,y,(1,0),10)
        shot.visual_style=kind
        for _ in range(5):
            shot.update(.016)
        draw_charge(canvas,(140,y),pygame.Vector2(1,0),.9,kind)
        shot.draw(canvas,camera)
        enemy=Enemy(680,y,EnemyType.BRUTE)
        enemy.rect.center=(680,y)
        enemy.draw(canvas,camera)
        effect=ShotHit(shot,(660,y),enemy)
        effect.update(.06)
        effect.draw(canvas,camera)
        canvas.blit(font.render(kind.upper(),True,'white'),(20,y-10))
    pygame.image.save(canvas,str(ROOT/'debug_screenshots/shot-vfx-preview.png'))


if __name__=='__main__':
    capture()
    unittest.main()
