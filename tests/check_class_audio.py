import os
import sys
import wave
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from entities.player import Player
from systems.audio_system import AudioSystem
from systems.class_audio import CUES, shoot_cue, impact_cue
from systems.shooting_system import ShootingSystem


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_assets_distinct_loadable_and_short(self):
        audio = AudioSystem()
        hashes = set()
        for values in CUES.values():
            for cue in (values['shoot'], values['impact']):
                path = ROOT / 'assets/sounds' / (cue + '.wav')
                hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
                with wave.open(str(path), 'rb') as source:
                    self.assertEqual(source.getnchannels(), 1)
                    self.assertEqual(source.getsampwidth(), 2)
                    self.assertLess(source.getnframes()/source.getframerate(), .3)
                self.assertIn(cue, audio.sounds)
        self.assertEqual(len(hashes), 8)

    def test_actual_fire_routes_one_cue_not_one_per_pellet(self):
        for build, cues in CUES.items():
            player = Player()
            player.starter_build = build
            player.projectile_count = 3
            calls = []
            audio = SimpleNamespace(play=calls.append)
            shooting = ShootingSystem()
            shots = []
            self.assertTrue(shooting.try_shoot(player, shots, audio))
            self.assertEqual(calls, [cues['shoot']])
            self.assertEqual(impact_cue(shots[0]), cues['impact'])
            self.assertFalse(shooting.try_shoot(player, shots, audio))
            self.assertEqual(len(calls), 1)

    def test_game_event_and_fallbacks(self):
        from game import Game
        game = Game()
        calls = []
        game.audio.play = calls.append
        for build, cues in CUES.items():
            game.player.starter_build = build
            game.events.emit('player_shoot', {'player': game.player})
            self.assertEqual(calls[-1], cues['shoot'])
        self.assertEqual(shoot_cue(None), 'shoot')
        self.assertEqual(impact_cue(SimpleNamespace(source='engineer_drone')), 'impact_engineer')
        self.assertEqual(impact_cue(SimpleNamespace(source='ninja_shuriken')), 'impact_ninja')


if __name__ == '__main__':
    unittest.main(verbosity=2)
