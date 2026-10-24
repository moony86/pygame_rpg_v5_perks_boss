"""Performance correctness: visual reference, dead-shot recycling, cache invalidation."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.projectile import Projectile
from entities.enemy_bullet import EnemyBullet
from entities.player import Player
from systems.projectile_pool import ProjectilePool,clear_world_projectiles
from systems.camera import Camera
from systems import object_catalog as objects
from systems import shot_presentation as visual


def reference_trail(surface,camera,shot):
    """Original renderer retained in tests, not in the production loop."""
    kind=visual.style(shot)
    points=shot.visual_trail+[(shot.pos,0.)]
    key='fx_trail_hostile' if hasattr(shot,'owner_id') else 'fx_trail_'+kind
    for i in range(len(points)-1):
        start,age=points[i]
        end,_=points[i+1]
        delta=end-start
        length=delta.length()
        if length<1: continue
        config=objects.definition(key)
        width=max(4,min(96,round((length+4)*config['width']/(48 if kind=='metal' else 56)/4)*4))
        image=visual.transformed(key,(width,config['height']),-delta.as_polar()[1])
        if image is not None:
            image=image.copy()
            image.set_alpha(round(155*max(0.,1-age/.12)*config['opacity']/255))
            surface.blit(image,image.get_rect(center=camera.apply_pos((start+end)*.5)))


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def test_dead_projectile_is_reused_without_duplicate_returns(self):
        pool=ProjectilePool(1)
        original=None
        for _ in range(1000):
            shot=pool.acquire(100,100,(1,0),10,speed=750)
            original=original or shot
            self.assertIs(shot,original)
            shot.kill()
            pool.release(shot)
            pool.release(shot)
        self.assertEqual(pool._created_count,1)
        self.assertEqual(len(pool._available),1)

    def test_overflow_reset_and_scene_clear_preserve_all_gameplay_shots(self):
        pool=ProjectilePool(2)
        shots=[pool.acquire(100,100,(1,0),10,speed=750) for _ in range(30)]
        self.assertEqual(len({id(shot) for shot in shots}),30)
        self.assertTrue(all(shot.alive for shot in shots))
        game=SimpleNamespace(projectiles=shots,shooting=SimpleNamespace(projectile_pool=pool))
        clear_world_projectiles(game)
        self.assertEqual(game.projectiles,[])
        self.assertEqual(len(pool._available),30)
        for _ in range(30): pool.acquire(100,100,(1,0),10,speed=750)
        self.assertEqual(pool._created_count,30)

    def test_hit_effect_slots_are_reused_after_expiry(self):
        from systems.effects import EffectsSystem
        effects=EffectsSystem()
        slots={id(item) for item in effects._shot_pool}
        shot=Projectile(100,100,(1,0),10)
        for _ in range(8):
            for _ in range(130): effects.projectile_hit(shot,shot.pos)
            self.assertEqual({id(item) for item in effects.shot_effects},slots)
            effects.update(1.)
            self.assertEqual({id(item) for item in effects._shot_pool},slots)
        effects.reset()
        self.assertEqual(len(effects._shot_pool),96)

    def test_unchanged_reload_keeps_prepared_assets(self):
        objects.reload_catalog()
        visual.transformed('fx_trail_magic',(20,12))
        before=objects.revision()
        cached=len(visual._poses)
        objects.reload_catalog()
        self.assertEqual(objects.revision(),before)
        self.assertEqual(len(visual._poses),cached)

    def test_offscreen_skip_never_kills_gameplay_shots(self):
        shot=Projectile(4000,4000,(1,0),10)
        before=(shot.pos.copy(),shot.alive,shot.damage)
        shot.draw(pygame.Surface((800,600)),Camera())
        self.assertEqual(before,(shot.pos,shot.alive,shot.damage))
        shot.update(.02)
        self.assertTrue(shot.alive)
        self.assertGreater(shot.pos.x,before[0].x)

    def test_body_rotation_is_reused_but_turning_invalidates_it(self):
        shot=Projectile(300,300,(1,0),10)
        screen=pygame.Surface((800,600))
        shot.draw(screen,Camera())
        first=shot._body_image
        shot.draw(screen,Camera())
        self.assertIs(first,shot._body_image)
        shot.direction.update(0,1)
        shot.draw(screen,Camera())
        self.assertIsNot(first,shot._body_image)

    def test_image_source_decoded_once_for_different_sizes(self):
        objects.reload_catalog()
        objects.clear_visual_caches()
        with patch('systems.object_catalog.load_image',wraps=objects.load_image) as loader:
            objects.sprite('fx_trail_magic',size=(16,12))
            objects.sprite('fx_trail_magic',size=(24,12))
            self.assertEqual(loader.call_count,1)

    def test_warm_ribbon_reuses_surface_and_reload_invalidates(self):
        shot=Projectile(300,100,(1,0),10,source='engineer_drone')
        for _ in range(8): shot.update(1/60)
        first=visual.ribbon(shot)
        self.assertIs(first[0],visual.ribbon(shot)[0])
        self.assertLessEqual(len(visual._ribbons),visual.MAX_RIBBONS)
        self.assertLessEqual(visual._ribbon_bytes,visual.MAX_RIBBON_BYTES)
        objects.definition('fx_trail_magic')['width']+=1
        objects.reload_catalog()
        self.assertEqual(len(visual._ribbons),0)
        self.assertIsNot(first[0],visual.ribbon(shot)[0])

    def test_straight_and_curved_trail_visual_reference(self):
        camera=Camera()
        images=[]
        for index,angle in enumerate((0,37,123,213)):
            shot=Projectile(350,150,pygame.Vector2(1,0).rotate(angle),10,source='engineer_drone')
            for _ in range(8): shot.update(1/60)
            if index==3:
                player=Player()
                player.rect.center=(500,50)
                shot=EnemyBullet(350,150,(1,0),10,homing_target=player,turn_rate=4)
                for _ in range(8): shot.update(.016)
            old=pygame.Surface((700,300))
            new=pygame.Surface((700,300))
            old.fill((14,20,30));new.fill((14,20,30))
            reference_trail(old,camera,shot)
            visual.draw_trail(new,camera,shot)
            base=700*300*(14+20+30)
            old_energy=sum(pygame.image.tobytes(old,'RGB'))-base
            new_energy=sum(pygame.image.tobytes(new,'RGB'))-base
            self.assertLess(abs(new_energy-old_energy)/max(1,old_energy),.06)
            images.append((old,new))
        sheet=pygame.Surface((1400,1200))
        for row,(old,new) in enumerate(images):
            sheet.blit(old,(0,row*300));sheet.blit(new,(700,row*300))
        output=ROOT/'debug_screenshots/performance/trail-reference.png'
        output.parent.mkdir(parents=True,exist_ok=True)
        pygame.image.save(sheet,str(output))


if __name__=='__main__': unittest.main()
