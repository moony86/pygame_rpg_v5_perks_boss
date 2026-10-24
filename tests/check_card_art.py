from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from definitions.perk_definitions import PERK_DEFINITIONS
import pygame
from ui.perk_screen import get_card_art


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    missing = [
        perk["key"]
        for perk in PERK_DEFINITIONS
        if get_card_art(perk['key']) is None
    ]

    if missing:
        print("Missing card art:")
        for key in missing:
            print(key)
        return 1

    print("All perk card art files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
