"""A/B full Game.draw workload. Static stress scene, not gameplay/native-window FPS."""
import os
import json
import sys
import time
import statistics
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from game import Game
from entities.enemy import Enemy,EnemyType
from entities.projectile import Projectile
from systems import shot_presentation as visual
from tools.check_render_performance import reference_trail

def main():
    game=Game()
    game.resize_window((1280,720))
    start=time.perf_counter()
    game.reset_run()
    preparation=(time.perf_counter()-start)*1000
    game.stage.start_stage()
    game.enemies=[Enemy(200+i%8*200,260+i//8*220,list(EnemyType)[i%len(EnemyType)]) for i in range(24)]
    game.projectiles=[]
    for i in range(200):
        shot=Projectile(130+i%20*70,130+i//20*70,(1,.25),10,source='engineer_drone')
        for _ in range(8): shot.update(1/60)
        game.projectiles.append(shot)
    for i in range(32):
        shot=Projectile(500,500,(1,0),10,explosive=True)
        game.effects.projectile_hit(shot,game.enemies[i%24].rect.center,game.enemies[i%24])
    game.effects.update(.1)
    original=visual.draw_trail
    result={'note':'Full render only, static stress scene, SDL dummy. Not gameplay or display FPS.',
            'world':[1920,1080],'window':[1280,720],'projectiles':200,'enemies':24,'hits':32,
            'prepare_ms':round(preparation,3),'modes':{}}
    for name,renderer in (('original_trail_reference',reference_trail),('cached_ribbons',original)):
        visual.draw_trail=renderer
        for _ in range(6): game.draw()
        samples=[]
        for _ in range(40):
            start=time.perf_counter()
            game.draw()
            samples.append((time.perf_counter()-start)*1000)
        result['modes'][name]={'median_ms':round(statistics.median(samples),3),
                             'p95_ms':round(sorted(samples)[37],3)}
    visual.draw_trail=original
    result['cache_bytes']={'poses':visual._pose_bytes,'fades':visual._faded_bytes,'ribbons':visual._ribbon_bytes}
    output=ROOT/'debug_screenshots/performance/full-frame.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    pygame.image.save(game.screen,str(output.with_suffix('.png')))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
