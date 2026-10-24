"""Milestone gate, route pressure, timed hazards and safe hub authoring."""
import os
import sys
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from game import Game
from game_state import GameState
from systems.hub_document import load,validate,save,colliders
from systems.stage_progression import difficulty
from systems.boss_encounter import TUNING
from entities.enemy import Enemy,EnemyType
from states.combat_state import handle_combat_events


class Checks(unittest.TestCase):
    def test_hub_validation_and_backup(self):
        doc=load()
        self.assertEqual(validate(doc),[])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'hub.json'
            save(doc,path)
            before=path.read_bytes()
            edited=copy.deepcopy(doc)
            edited['positions']['blacksmith'][0]+=10
            save(edited,path)
            self.assertEqual(path.with_suffix('.json.bak').read_bytes(),before)
            edited['colliders'].append([900,600,120,120])
            valid_bytes=path.read_bytes()
            with self.assertRaises(ValueError):
                save(edited,path)
            self.assertEqual(path.read_bytes(),valid_bytes)
        doc['positions']['blacksmith']=[10,10]
        self.assertTrue(validate(doc))

    def test_polygon_raster_collision_and_bad_input(self):
        doc=load()
        doc['polygons']=[[[600,400],[740,400],[670,500]]]
        self.assertTrue(any(r.collidepoint(670,430) for r in colliders(doc)))
        self.assertFalse(any(r.collidepoint(740,500) for r in colliders(doc)))
        doc['polygons']=[[[0,0],[1,1]]]
        self.assertTrue(validate(doc))

    def test_editor_hub_play_uses_validated_save_and_desktop_entry(self):
        import io,json
        from tools import level_editor
        handler=object.__new__(level_editor.Handler)
        payload=json.dumps({'document':load()}).encode()
        handler.headers={'X-Editor-Token':level_editor.TOKEN,'Content-Length':str(len(payload))}
        handler.rfile=io.BytesIO(payload)
        handler.path='/api/hub/play'
        responses=[]
        handler.response=lambda code,body:responses.append((code,body))
        with patch('systems.hub_document.save') as saved,patch.object(level_editor.subprocess,'Popen') as launch:
            handler.do_POST()
            self.assertEqual(responses[0][0],200)
            saved.assert_called_once()
            self.assertTrue(launch.call_args.args[0][-1].endswith('play_hub.py'))

    def test_runtime_uses_authored_hub_positions(self):
        from systems.scene_system import enter_hub
        doc=load()
        doc['positions']['blacksmith']=[400,430]
        doc['spawn']=[1000,650]
        with patch('systems.hub_presentation.load',return_value=doc):
            game=Game()
            enter_hub(game)
            self.assertEqual(game.player.rect.center,(1000,650))
            self.assertEqual(next(n.rect.topleft for n in game.npcs if n.role=='blacksmith'),(400,430))
        from systems.hub_presentation import reload_hub
        reload_hub()

    def test_depth_pressure_is_not_player_scaling(self):
        game=Game()
        game.stage.start_stage()
        start=difficulty(game.stage)
        game.player.damage_bonus=10000
        self.assertEqual(difficulty(game.stage),start)
        node=next(n for n in game.stage.nodes if n.neighbors and n.grid_pos!=(0,0))
        game.stage.current_pos=node.grid_pos
        self.assertGreater(difficulty(game.stage),start)
        before=difficulty(game.stage)
        for n in game.stage.nodes:
            if n.room.spawn_plan and not n.room.boss:
                n.cleared=True
        self.assertGreater(difficulty(game.stage),before)

    def test_boss_gate_requires_clears_and_two_inputs(self):
        game=Game()
        game.stage.start_stage()
        stage=game.stage
        stage.current_node.cleared=True
        self.assertFalse(stage.boss_unlocked)
        stage.game.player.rect.center=stage.boss_gate_rect().center
        event=pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)
        handle_combat_events(game,event)
        self.assertFalse(stage.current_node.room.boss)
        for n in stage.nodes:
            if n.room.spawn_plan and not n.room.boss:
                n.cleared=True
        self.assertTrue(stage.boss_unlocked)
        game.player.rect.center=stage.boss_gate_rect().center
        handle_combat_events(game,event)
        self.assertFalse(stage.current_node.room.boss)
        handle_combat_events(game,event)
        self.assertTrue(stage.current_node.room.boss)
        self.assertTrue(any(e.encounter for e in game.enemies))
        game.draw()
        output=ROOT/'debug_screenshots/progression'
        output.mkdir(parents=True,exist_ok=True)
        pygame.image.save(game.screen,str(output/'boss-entry.png'))

    def test_normal_routes_never_enter_boss_and_remain_connected(self):
        game=Game()
        game.stage.start_stage()
        stage=game.stage
        queue=[(0,0)]
        seen=set(queue)
        for p in queue:
            for target in stage.node_by_pos[p].neighbors.values():
                self.assertFalse(stage.node_by_pos[target].room.boss)
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        self.assertEqual(len(seen),len(stage.nodes)-1)

    def test_hazards_expire_freeze_and_keep_escape_sectors(self):
        game=Game()
        game.stage.start_stage()
        boss=Enemy(960,400,EnemyType.BOSS)
        encounter=boss.encounter
        encounter.phase=2
        encounter.state='exposed'
        encounter.spawn_turrets(game.player)
        self.assertEqual(len(encounter.turrets),TUNING['turret_count'])
        bullets=[]
        for _ in range(180):
            encounter.tick_hazards(1/60,game.player,bullets)
        self.assertTrue(bullets)
        self.assertTrue(all(b.speed==TUNING['turret_speed'] for b in bullets))
        timers=[t['timer'] for t in encounter.turrets]
        game.enemies=[boss]
        game.player.enemy_time_stop_timer=2
        game.update(.05)
        self.assertEqual([t['timer'] for t in encounter.turrets],timers)
        encounter.tick_hazards(20,game.player,bullets)
        self.assertFalse(encounter.turrets)
        bullets=[]
        encounter.emit_ring(bullets,pygame.Vector2(1,0))
        self.assertEqual(len(bullets),12)
        angles=[round(pygame.Vector2(1,0).angle_to(b.direction))%360 for b in bullets]
        self.assertFalse(any(60<=a<120 or 240<=a<300 for a in angles))
        encounter.spawn_turrets(game.player)
        encounter.state='transition'
        encounter.tick_hazards(.01,game.player,bullets)
        self.assertFalse(encounter.turrets)

    def test_boss_visual_and_speed_asset(self):
        game=Game()
        game.stage.start_stage()
        boss=Enemy(960,400,EnemyType.BOSS)
        boss.encounter.phase=boss.phase=2
        boss.encounter.state='exposed'
        boss.encounter.spawn_turrets(game.player)
        game.enemies=[boss]
        game.player.ghost_timer=1
        game.draw()
        output=ROOT/'debug_screenshots/progression'
        output.mkdir(parents=True,exist_ok=True)
        pygame.image.save(game.screen,str(output/'siege-turrets.png'))
        from systems.object_catalog import sprite
        self.assertIsNotNone(sprite('boss_turret'))
        self.assertIsNotNone(sprite('fx_speed_wake'))


if __name__=='__main__':
    unittest.main(verbosity=2)
