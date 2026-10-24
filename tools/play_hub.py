"""Play the authored sanctuary using the real desktop runtime."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game import Game
from systems.scene_system import enter_hub
game = Game()
enter_hub(game)
game.run()
