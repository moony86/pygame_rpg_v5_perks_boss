"""Bake editable SVG sources to the PNG runtime format; no external dependency."""
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]
for name in ('airstrike_target', 'dash_charge', 'time_sigil', 'weapon_shuriken',
             'weapon_screwdriver', 'weapon_blood_orb', 'weapon_rifle'):
    source = ROOT / 'assets' / 'visuals' / (name + '.svg')
    pygame.image.save(pygame.image.load(str(source)), str(source.with_suffix('.png')))
