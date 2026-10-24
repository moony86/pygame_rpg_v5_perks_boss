"""Render diagnostic contact sheets from real runtime sprite bindings."""
import math
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from systems.object_catalog import catalog,sprite


def main():
    pygame.init()
    pygame.display.set_mode((1,1))
    output=ROOT/'debug_screenshots/visual_library'
    output.mkdir(parents=True,exist_ok=True)
    font=pygame.font.Font(None,28)
    for name,prefix in [('enemies','enemy_'),('cards','card_'),('effects','fx_'),('projectiles','bullet_')]:
        keys=[key for key in catalog()['objects'] if key.startswith(prefix) and key!='card_style']
        surface=pygame.Surface((1440,math.ceil(len(keys)/6)*240))
        surface.fill((12,20,31))
        for i,key in enumerate(keys):
            x=(i%6)*240+120
            y=(i//6)*240+100
            image=sprite(key,(160,160))
            if image is not None:
                surface.blit(image,image.get_rect(center=(x,y)))
            text=font.render(key.replace(prefix,''),True,(220,233,244))
            surface.blit(text,text.get_rect(center=(x,y+110)))
        pygame.image.save(surface,str(output/(name+'.png')))
    print(output)


if __name__=='__main__':
    main()
