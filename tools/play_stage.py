"""Launch the real desktop game at the selected authored room for QA."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["BLUECUBE_STAGE_FILE"] = str(ROOT / "assets/levels/stage_one.json")
from game import Game

game = Game()
game.reset_run()
game.stage.start_stage()
index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
game.stage.current_pos = game.stage.nodes[index].grid_pos
game.stage._enter_current_room()
game.run()
