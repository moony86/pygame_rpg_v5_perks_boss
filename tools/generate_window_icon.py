"""Rebuild the Windows ICO from existing hero art, without extra dependencies."""
import io
from pathlib import Path
import struct
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from systems.object_catalog import sprite


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = []
    for size in sizes:
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        hero = sprite('hero', size=(size, size))
        if hero is None:
            raise SystemExit('Hero art is required for the application icon.')
        canvas.blit(hero, hero.get_rect(center=(size // 2, size // 2)))
        stream = io.BytesIO()
        pygame.image.save(canvas, stream, 'icon.png')
        images.append(stream.getvalue())
    offset = 6 + 16 * len(images)
    entries = []
    for size, image in zip(sizes, images):
        entries.append(struct.pack('<BBBBHHII', size % 256, size % 256,
                                   0, 0, 1, 32, len(image), offset))
        offset += len(image)
    (ROOT / 'assets/cube.ico').write_bytes(
        struct.pack('<HHH', 0, 1, len(images)) + b''.join(entries) + b''.join(images))
    pygame.quit()


if __name__ == '__main__':
    main()
