"""Data-backed class cues, independent of damage and targeting."""
import json
from systems.asset_loader import ASSET_ROOT

CUES = json.loads((ASSET_ROOT / 'data/class_audio.json').read_text(encoding='utf-8'))


def shoot_cue(player):
    return CUES.get(getattr(player, 'starter_build', ''), {}).get('shoot', 'shoot')


def impact_cue(shot):
    kind = getattr(shot, 'class_visual', '')
    if not kind and getattr(shot, 'source', '') == 'ninja_shuriken':
        kind = 'ninja'
    if not kind and getattr(shot, 'source', '') == 'engineer_drone':
        kind = 'engineer'
    for build, cues in CUES.items():
        if build.lower() == kind:
            return cues['impact']
    return 'hit'
