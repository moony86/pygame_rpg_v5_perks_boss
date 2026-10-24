"""Fixed route pressure; never secretly scales against player DPS or perks."""
import json
from systems.asset_loader import ASSET_ROOT
TUNING = json.loads((ASSET_ROOT/'data/progression.json').read_text(encoding='utf-8'))


def depth(stage):
    start = (0,0)
    distances = {start:0}
    queue = [start]
    for pos in queue:
        node = stage.node_by_pos.get(pos)
        if node is None:
            continue
        for target in node.neighbors.values():
            if target not in distances:
                distances[target] = distances[pos]+1
                queue.append(target)
    return distances.get(stage.current_pos,0)


def difficulty(stage):
    cleared = sum(n.cleared and not n.room.boss and bool(n.room.spawn_plan) for n in stage.nodes)
    return min(TUNING['max_difficulty'], 1 + depth(stage)*TUNING['depth_difficulty'] + cleared*TUNING['clear_difficulty'])


def apply(enemy, stage):
    enemy.damage_multiplier = min(enemy.damage_multiplier, TUNING['max_contact_multiplier'])
    enemy.route_depth = depth(stage)
