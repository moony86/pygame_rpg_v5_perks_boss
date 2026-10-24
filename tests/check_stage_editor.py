"""Stage document, navigation, persistence and artwork regression checks."""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import io
import json
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("BLUECUBE_DEV_TOOLS", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from systems.stage_document import default_document, validate_document, document_nodes, save_document, load_document


class StageEditorChecks(unittest.TestCase):
    def setUp(self):
        self.doc = default_document()

    def test_default_eight_room_design_valid(self):
        self.assertEqual(validate_document(self.doc), [])
        self.assertEqual(len(document_nodes(self.doc)), 8)

    def test_runtime_geometry_waves_and_graph_match_document(self):
        nodes = document_nodes(self.doc)
        for node, room in zip(nodes, self.doc["rooms"]):
            self.assertEqual(node.room.layout.obstacles[0].x, room["obstacles"][0]["x"])
            self.assertEqual(len(node.room.spawn_plan), len(room["spawns"]))
            for direction, pos in node.neighbors.items():
                self.assertTrue(any(n.grid_pos == pos for n in nodes))

    def test_save_load_and_recoverable_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stage.json"
            save_document(self.doc, path)
            self.doc["name"] = "Edited"
            save_document(self.doc, path)
            self.assertEqual(load_document(path)["name"], "Edited")
            self.assertNotEqual(load_document(path.with_suffix('.json.bak'))["name"], "Edited")

    def test_invalid_save_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stage.json"
            save_document(self.doc, path)
            before = path.read_bytes()
            self.doc["rooms"][1]["position"] = [30,30]
            with self.assertRaises(ValueError):
                save_document(self.doc, path)
            self.assertEqual(before, path.read_bytes())

    def test_reject_invalid_enemy_and_nonfinite_time(self):
        spawn = self.doc["rooms"][0]["spawns"][0]
        spawn["enemy"] = "TYPO"
        spawn["delay"] = float('nan')
        self.assertGreaterEqual(len(validate_document(self.doc)), 2)

    def test_reject_cover_at_spawn_and_blocked_entry(self):
        self.doc["rooms"][0]["obstacles"] = [{"id":"bad", "x":900,"y":500,"width":120,"height":120}]
        self.assertTrue(any('centre' in e for e in validate_document(self.doc)))

    def test_reject_disconnected_route_and_missing_boss(self):
        self.doc["rooms"][-1]["position"] = [20,20]
        self.doc["rooms"][-1]["boss"] = False
        errors = validate_document(self.doc)
        self.assertTrue(any('disconnected' in e for e in errors))
        self.assertTrue(any('boss' in e for e in errors))

    def test_closed_wall_detected_by_navigation(self):
        self.doc["rooms"][0]["obstacles"] = [{"id":"wall","x":160,"y":40,"width":120,"height":1000}]
        self.assertTrue(any('isolated' in e for e in validate_document(self.doc)))

    def test_environment_assets_render_at_game_resolution(self):
        pygame.init()
        pygame.display.set_mode((1,1))
        from systems.environment_art import floor_image, cover_image
        self.assertEqual(floor_image((1920,1080)).get_size(), (1920,1080))
        self.assertEqual(cover_image((160,260)).get_size(), (160,260))
        from systems.environment_art import tiles
        self.assertIsNotNone(tiles())

    def test_gui_play_saves_and_launches_real_desktop_entry(self):
        from tools import level_editor
        handler = object.__new__(level_editor.Handler)
        payload = json.dumps({"document": self.doc, "room": 2}).encode()
        handler.headers = {"X-Editor-Token": level_editor.TOKEN, "Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.path = "/api/play"
        replies = []
        handler.response = lambda code, body: replies.append((code, body))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'stage.json'
            with patch.object(level_editor, 'DEFAULT_STAGE', path), patch.object(level_editor.subprocess, 'Popen') as launch:
                handler.do_POST()
                self.assertEqual(replies[0][0], 200)
                self.assertEqual(load_document(path), self.doc)
                self.assertEqual(launch.call_args.args[0][-1], '2')
                self.assertTrue(launch.call_args.args[0][-2].endswith('play_stage.py'))

    def test_gui_rejects_missing_authentication(self):
        from tools import level_editor
        handler = object.__new__(level_editor.Handler)
        handler.headers = {}
        replies = []
        handler.response = lambda code, body: replies.append(code)
        handler.do_POST()
        self.assertEqual(replies, [403])


if __name__ == '__main__':
    unittest.main(verbosity=2)
