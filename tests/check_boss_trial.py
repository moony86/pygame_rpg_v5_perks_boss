"""Boss gates, objectives, fair tells, actual reflected projectiles and audio cues."""
import os
import sys
import wave
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.enemy import Enemy,EnemyType
from entities.enemy_bullet import EnemyBullet
from entities.player import Player
from entities.projectile import Projectile
from systems.boss_encounter import TUNING
from systems.combat_system import CombatSystem
from systems.audio_system import AudioSystem,SOUND_FILES,CUE_CHANNELS
from systems.loot_system import LootSystem
from entities.pickup import Pickup
from systems.room_bounds import set_room_bounds,RoomBounds
from ui.cube_health import cell_fractions


class AudioLog:
    def __init__(self): self.played=[]
    def play(self,key): self.played.append(key)


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))

    def setUp(self):
        set_room_bounds(RoomBounds(0,0,1920,1080))
        self.boss=Enemy(1100,500,EnemyType.BOSS)
        self.enc=self.boss.encounter
        self.player=Player()
        self.player.rect.center=(500,500)

    def test_hp_not_inflated_and_burst_cannot_skip_phases(self):
        self.assertEqual(self.boss.max_health,5040)
        self.enc.state='exposed'
        initial=self.boss.health
        for _ in range(100):
            self.boss.take_damage(999999)
        self.assertAlmostEqual(initial-self.boss.health,self.boss.max_health*TUNING['exposed_budget_ratio'])
        for _ in range(100):
            self.enc.advance_damage_budget(.25)
            self.boss.take_damage(999999)
        self.assertEqual(self.enc.state,'transition')
        self.assertEqual(self.enc.phase,1)
        self.assertEqual(self.boss.health,3360)
        self.assertTrue(self.boss.alive)

    def test_guard_chip_is_lower_and_shared_with_direct_damage(self):
        self.enc.state='guard'
        before=self.boss.health
        self.boss.take_damage(999999)
        guarded=before-self.boss.health
        self.assertEqual(guarded,0)
        self.enc.advance_damage_budget(.25)
        self.enc.state='exposed'
        before=self.boss.health
        self.boss.take_damage(999999)
        self.assertGreater(before-self.boss.health,guarded*10)

    def test_two_bounded_summons_and_landing_opening(self):
        self.enc.started=True
        enemies=[self.boss]
        for phase,count in ((1,5),(2,6)):
            self.enc.phase=phase
            self.enc.next_phase=phase+1
            self.enc.state='transition'
            self.enc.timer=0
            for dt,event in ((.01,'rise'),(.66,'summon_warning'),(.86,'reinforcements')):
                action=self.enc.update(dt,self.player.rect)
                self.assertEqual(action['event'],event)
                self.enc.resolve(action,enemies,[],None,None,self.player)
            self.assertEqual(len(self.enc.living_guards()),count)
            self.assertTrue(all(g.is_boss_guard for g in self.enc.guards))
            health=self.boss.health
            self.enc.damage(999999,reflected=True)
            self.assertEqual(self.boss.health,health)
            self.assertIsNone(self.enc.update(1.,self.player.rect))
            action=self.enc.update(14.,self.player.rect)
            self.assertEqual(action['event'],'landing')
            self.assertFalse(self.enc.living_guards())
            action=self.enc.update(.66,self.player.rect)
            self.assertEqual(action['event'],'phase')
            self.assertEqual(self.enc.phase,phase+1)
            self.assertEqual(self.enc.state,'exposed')
            self.assertEqual(self.enc.lift,0)
        self.assertEqual(self.enc.summon_count,2)

    def test_every_air_state_is_immune_and_guard_flag_resets(self):
        for state in ('ascending','summoning','airborne','landing','windup','guard'):
            self.enc.state=state
            health=self.boss.health
            self.boss.take_damage(999999)
            self.assertEqual(self.boss.health,health)
        guard=Enemy(300,300,EnemyType.CHASER)
        guard.is_boss_guard=True
        xp,gold=self.player.xp,self.player.gold
        CombatSystem()._reward_enemy_kill(self.player,guard,[],1,None)
        self.assertEqual((xp,gold),(self.player.xp,self.player.gold))
        guard.__init__(300,300,EnemyType.CHASER)
        self.assertFalse(guard.is_boss_guard)

    def test_eyes_heal_are_targetable_and_must_die(self):
        self.enc.phase=self.boss.phase=2
        self.enc.started=True
        self.enc.state='exposed'
        self.enc.timer=2.
        solids=(pygame.Rect(250,100,300,300),pygame.Rect(1100,600,300,300))
        self.enc.arena_solids=solids
        self.boss.player_rect=self.player.rect
        enemies=[self.boss]
        self.enc.spawn_eyes(enemies)
        self.assertEqual(len(self.enc.eyes),3)
        for eye in self.enc.eyes:
            self.assertTrue(eye.is_boss_eye)
            self.assertFalse(any(eye.rect.colliderect(s) for s in solids))
            self.assertFalse(eye.rect.colliderect(self.player.rect.inflate(120,120)))
        self.boss.health=2000
        self.enc.update(.1,self.player.rect)
        self.assertGreater(self.boss.health,2000)
        self.boss.health=1681
        self.enc.damage(99999,reflected=True)
        self.assertNotEqual(self.enc.state,'transition')
        for eye in self.enc.eyes:
            eye.take_damage(9999)
        self.enc.damage(100,reflected=True)
        self.assertEqual(self.enc.state,'transition')
        self.assertEqual(self.enc.next_phase,3)

    def test_objective_death_has_no_reward_or_pool_contamination(self):
        from systems.enemy_pool import EnemyPool
        eye=Enemy(300,300,EnemyType.RANGED)
        eye.is_boss_eye=True
        gold,xp=self.player.gold,self.player.xp
        CombatSystem()._reward_enemy_kill(self.player,eye,[],1,None)
        self.assertEqual((gold,xp),(self.player.gold,self.player.xp))
        pool=EnemyPool()
        before=len(pool._available[EnemyType.RANGED])
        pool.release(eye)
        self.assertEqual(before,len(pool._available[EnemyType.RANGED]))

    def test_fair_windup_precedes_pattern_and_owns_all_bullets(self):
        self.enc.started=True
        self.enc.state='guard'
        self.enc.timer=.01
        action=self.enc.update(.02,self.player.rect)
        self.assertEqual(action['event'],'warning')
        bullets=[]
        audio=AudioLog()
        self.enc.resolve(action,[self.boss],bullets,None,audio,self.player)
        self.assertFalse(bullets)
        self.assertIn('boss_warning',audio.played)
        self.assertIsNone(self.enc.update(.5,self.player.rect))
        action=self.enc.update(.6,self.player.rect)
        self.assertEqual(action['event'],'attack')
        self.enc.resolve(action,[self.boss],bullets,None,audio,self.player)
        self.assertTrue(bullets)
        self.assertTrue(all(b.owner_id==id(self.boss) for b in bullets))
        self.assertEqual(self.enc.state,'exposed')

    def test_ninja_directional_timed_parry_creates_return_projectile(self):
        self.enc.phase=self.boss.phase=3
        self.enc.state='exposed'
        self.enc.timer=2
        self.player.enable_ninja_dash_charges()
        self.player.ninja_parry_timer=.12
        self.player.dash_direction=pygame.Vector2(1,0)
        bullet=EnemyBullet(540,500,(-1,0),24,owner_id=id(self.boss))
        bullet.parryable=True
        shots=[]
        audio=AudioLog()
        combat=CombatSystem()
        combat._parry_boss_orbs(self.player,shots,[self.boss],[bullet],None,audio,None)
        self.assertFalse(bullet.alive)
        self.assertEqual(len(shots),1)
        self.assertEqual(shots[0].source,'boss_parry')
        self.assertIn('ninja_parry',audio.played)
        before=self.boss.health
        shots[0].rect.center=self.boss.rect.center
        combat.update(0,self.player,shots,[self.boss],[],audio=audio)
        self.assertAlmostEqual(before-self.boss.health,self.boss.max_health*.08)

    def test_non_ninja_and_wrong_direction_do_not_reflect(self):
        combat=CombatSystem()
        bullet=EnemyBullet(540,500,(-1,0),24,owner_id=id(self.boss))
        bullet.parryable=True
        shots=[]
        self.player.ninja_parry_timer=.12
        for ninja,direction in ((False,(1,0)),(True,(-1,0))):
            self.player.ninja_dash_charges_enabled=ninja
            self.player.dash_direction=pygame.Vector2(direction)
            combat._parry_boss_orbs(self.player,shots,[self.boss],[bullet],None,None,None)
            self.assertTrue(bullet.alive)
            self.assertFalse(shots)

    def test_pickup_audio_is_distinct_and_clock_lifecycle(self):
        audio=AudioLog()
        loot=LootSystem()
        for kind in ('heal_potion','time_stop'):
            loot._collect(Pickup(500,500,kind,2),self.player,None,audio)
        self.assertEqual(audio.played,['heal_pickup','time_stop_pickup'])
        engine=AudioSystem()
        with patch.object(engine,'play') as play:
            self.player.enemy_time_stop_timer=2
            engine.update_context(self.player,'ROOM',.2)
            engine.update_context(self.player,'ROOM',.38)
            self.player.enemy_time_stop_timer=0
            engine.update_context(self.player,'ROOM',.01)
            self.assertEqual([c.args[0] for c in play.call_args_list],['time_stop_tick','time_stop_tock','time_stop_end'])
            engine.update_context(self.player,'PAUSED',.5)
            self.assertFalse(engine._time_active)

    def test_map_boost_uses_distinct_audio(self):
        from game import Game
        game=Game()
        game.audio=AudioLog()
        game.movement_pickups=[{'alive':True,'type':'dash_refresh','rect':game.player.rect.copy(),
                                'duration':1.8,'respawn_delay':0}]
        game.update_movement_pickups(.01)
        self.assertEqual(game.audio.played,['boost_pickup'])
        self.assertGreater(game.player.ghost_timer,0)

    def test_sound_assets_and_reserved_warning_channel(self):
        for key in ('heal_pickup','boost_pickup','time_stop_pickup','time_stop_tick','time_stop_end','ninja_parry'):
            with wave.open(str(ROOT/'assets/sounds'/SOUND_FILES[key])) as wav:
                self.assertEqual(wav.getnchannels(),1)
                self.assertEqual(wav.getsampwidth(),2)
                self.assertGreater(wav.getnframes(),100)
        self.assertNotEqual(CUE_CHANNELS['boss_warning'],CUE_CHANNELS['boss_guard'])

    def test_health_cells_fractional_and_clamped(self):
        self.assertEqual(sum(cell_fractions(125,125)),10)
        self.assertEqual(sum(cell_fractions(62.5,125)),5)
        self.assertEqual(sum(cell_fractions(-1,125)),0)
        self.assertAlmostEqual(sum(cell_fractions(8,125)),.64)
        self.assertEqual(sum(cell_fractions(999,125)),10)

    def test_telegraph_locks_last_350ms_and_freeze_budget_remains_available(self):
        self.enc.started=True
        self.enc.state='guard'
        self.enc.timer=0
        self.enc.update(.01,self.player.rect)
        self.enc.timer=.30
        locked=self.boss.windup_direction.copy()
        self.player.rect.move_ip(0,200)
        self.enc.update(.05,self.player.rect)
        self.assertEqual(self.boss.windup_direction,locked)
        self.enc.state='exposed'
        self.boss.take_damage(999999)
        health=self.boss.health
        # Combat advances the shared damage budget even when AI is time-stopped.
        CombatSystem().update(.25,self.player,[],[self.boss],[])
        self.boss.take_damage(999999)
        self.assertLess(self.boss.health,health)

    def test_health_art_renders_full_partial_empty_without_state_mutation(self):
        from ui.cube_health import draw
        surface=pygame.Surface((700,330))
        surface.fill((10,18,30))
        font=pygame.font.SysFont('Arial',24)
        for index,health in enumerate((125,87,8,0)):
            self.player.health=health
            draw(surface,self.player,30,25+index*75)
            surface.blit(font.render(f'{health} / 125',True,(225,235,245)),(340,25+index*75))
            self.assertEqual(self.player.health,health)
        pygame.image.save(surface,str(ROOT/'debug_screenshots/cube-health-states.png'))


if __name__=='__main__':
    unittest.main(verbosity=2)
