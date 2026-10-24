"""Repeatable native SDL-dummy rendering benchmark; not end-user gameplay FPS."""
import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('BLUECUBE_DEV_TOOLS','0')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from entities.projectile import Projectile
from systems.camera import Camera
from systems import shot_presentation as vfx
from systems.object_catalog import reload_catalog

def benchmark(count,mixed):
    reload_catalog()
    objects_clear=__import__('systems.object_catalog',fromlist=['clear_visual_caches'])
    objects_clear.clear_visual_caches()
    start=time.perf_counter()
    if hasattr(vfx,'prepare'):
        vfx.prepare()
    prepare_ms=(time.perf_counter()-start)*1000
    screen=pygame.Surface((1920,1080))
    camera=Camera()
    shots=[]
    for i in range(count):
        direction=pygame.Vector2(1,0).rotate(i*17) if mixed else pygame.Vector2(1,.25)
        shot=Projectile(120+(i%20)*70,120+(i//20)*70,direction,10,source='engineer_drone')
        for _ in range(8):
            shot.update(1/60)
        shots.append(shot)
    def draw():
        for shot in shots:
            shot.draw(screen,camera)
    start=time.perf_counter()
    draw()
    first=(time.perf_counter()-start)*1000
    for _ in range(6): draw()
    samples=[]
    for _ in range(60):
        start=time.perf_counter()
        draw()
        samples.append((time.perf_counter()-start)*1000)
    return dict(count=count,mixed=mixed,prepare_ms=round(prepare_ms,3),first_ms=round(first,3),
                median_ms=round(statistics.median(samples),3),p95_ms=round(sorted(samples)[56],3))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    pygame.init()
    pygame.display.set_mode((1,1))
    result={'renderer':'native pygame / SDL dummy','viewport':[1920,1080],
            'note':'Rendering workload only; not gameplay or native-window FPS',
            'scenes':[benchmark(200,False),benchmark(120,True)]}
    path=ROOT/args.output
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
