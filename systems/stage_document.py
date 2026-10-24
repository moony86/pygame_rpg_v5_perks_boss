"""Versioned, validated stage documents consumed by GUI and runtime."""
import json
import math
import os
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE = ROOT / "assets" / "levels" / "stage_one.json"
SCHEMA = "bluecube.stage.v1"
WIDTH, HEIGHT = 1920, 1080


def default_document():
    from systems.stage_system import build_stage_map
    nodes = build_stage_map(seed=42)
    doc = {"schema": SCHEMA, "name": "The Slate Trial", "rooms": [
        {"id": f"room_{n.room.index}", "position": list(n.grid_pos),
         "type": n.room.room_type.name, "label": n.room.label,
         "boss": n.room.boss, "active_cap": n.room.active_cap,
         "release_threshold": n.room.release_threshold,
         "reward_gold": n.room.reward_gold, "reward_xp": n.room.reward_xp,
         "obstacles": [{"id": o.id, "x": o.x, "y": o.y, "width": o.width, "height": o.height} for o in n.room.layout.obstacles],
         "doors": [{"id": d.id, "x": d.x, "y": d.y, "facing": d.facing} for d in n.room.layout.doors],
         "pickups": [{"id": p.id, "x": p.x, "y": p.y} for p in n.room.layout.movement_pickups],
         "spawns": [{"delay": s.delay, "door": s.door_id, "enemy": s.enemy_type.name} for s in n.room.spawn_plan]}
        for n in nodes]}
    patterns = (
        ((430, 320, 160, 260), (820, 700, 280, 100), (1330, 450, 160, 260)),
        ((460, 280, 260, 100), (1180, 700, 260, 100), (1120, 340, 140, 200)),
        ((440, 400, 150, 260), (880, 250, 150, 160), (1330, 650, 150, 200)),
    )
    for i, r in enumerate(doc["rooms"]):
        pattern = ((360, 400, 160, 220), (1400, 400, 160, 220)) if r["boss"] else patterns[i % len(patterns)]
        r["obstacles"] = [{"id": f"slate_cover_{j+1}", "x": x, "y": y, "width": w, "height": h}
                          for j, (x, y, w, h) in enumerate(pattern)]
        r["pickups"] = [{"id": "lower_cache", "x": 650, "y": 780}, {"id": "upper_cache", "x": 1270, "y": 280}]
        r["release_threshold"] = min(r["release_threshold"], max(0, r["active_cap"]-1))
    return doc


def validate_document(doc):
    from entities.enemy import EnemyType
    from systems.room_system import RoomType
    errors = []
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        return ["Unsupported stage document schema"]
    rooms = doc.get("rooms")
    if not isinstance(rooms, list) or not 2 <= len(rooms) <= 32:
        return ["A stage needs 2 to 32 rooms"]
    positions, ids = set(), set()
    bosses = 0
    for i, r in enumerate(rooms):
        prefix = f"Room {i+1}: "
        try:
            for field, limit in (("doors", 4), ("obstacles", 128), ("pickups", 64), ("spawns", 512)):
                if not isinstance(r[field], list) or len(r[field]) > limit:
                    raise ValueError(f"{field} must be a list with at most {limit} entries")
            if not isinstance(r["id"], str) or not r["id"] or r["id"] in ids:
                errors.append(prefix + "unique non-empty id required")
            ids.add(r["id"])
            pos = r["position"]
            if len(pos) != 2 or any(type(v) is not int or abs(v) > 32 for v in pos):
                raise ValueError("position needs two integers (-32..32)")
            pos = tuple(pos)
            if pos in positions:
                errors.append(prefix + "overlapping route position")
            positions.add(pos)
            if i == 0 and pos != (0, 0):
                errors.append(prefix + "first room must stay at route origin (0,0)")
            if r["type"] not in RoomType.__members__:
                errors.append(prefix + "unknown room type")
            if not isinstance(r["label"], str) or not r["label"].strip():
                errors.append(prefix + "room label required")
            if type(r["boss"]) is not bool:
                errors.append(prefix + "boss must be true/false")
            bosses += bool(r["boss"])
            if r["boss"] and i == 0:
                errors.append(prefix + "entry cannot be boss")
            for field, low, high in (("active_cap", 0, 40), ("release_threshold", 0, 39), ("reward_gold", 0, 10000), ("reward_xp", 0, 10000)):
                if type(r[field]) is not int or not low <= r[field] <= high:
                    errors.append(prefix + f"invalid {field} ({low}..{high})")
            if r["active_cap"] and r["release_threshold"] >= r["active_cap"]:
                errors.append(prefix + "release threshold must be below active cap")
            door_ids = set()
            for d in r["doors"]:
                if d["id"] not in ("north", "south", "east", "west") or d["id"] in door_ids:
                    errors.append(prefix + "four unique cardinal doors required")
                door_ids.add(d["id"])
                if not 44 <= d["x"] <= WIDTH-44 or not 44 <= d["y"] <= HEIGHT-44:
                    errors.append(prefix + "door outside safe room area")
                if d["facing"] not in ("north", "south", "east", "west"):
                    errors.append(prefix + "invalid door facing")
            if len(door_ids) != 4:
                errors.append(prefix + "all four doors required")
            rects = []
            object_ids = set()
            for o in r["obstacles"]:
                if o["id"] in object_ids:
                    errors.append(prefix + "duplicate obstacle id")
                object_ids.add(o["id"])
                values = [o[k] for k in ("x", "y", "width", "height")]
                if any(type(v) is not int for v in values):
                    raise ValueError("obstacle coordinates must be integers")
                rect = pygame.Rect(*values)
                if rect.width < 32 or rect.height < 32 or not pygame.Rect(40, 40, WIDTH-80, HEIGHT-80).contains(rect):
                    errors.append(prefix + "obstacle outside bounds or smaller than 32px")
                if any(rect.colliderect(other) for other in rects):
                    errors.append(prefix + "overlapping obstacles")
                if rect.colliderect(pygame.Rect(WIDTH//2-48, HEIGHT//2-48, 96, 96)):
                    errors.append(prefix + "centre spawn must be clear")
                for d in r["doors"]:
                    if rect.colliderect(pygame.Rect(d["x"]-72, d["y"]-72, 144, 144)):
                        errors.append(prefix + f"obstacle blocks {d['id']} entry")
                rects.append(rect)
            for p in r["pickups"]:
                if p.get('kind', 'dash_refresh') not in ('dash_refresh', 'heal_potion', 'time_stop'):
                    errors.append(prefix + 'unknown pickup kind')
                if not 48 <= p["x"] <= WIDTH-48 or not 48 <= p["y"] <= HEIGHT-48:
                    errors.append(prefix + "pickup outside bounds")
                if any(rect.inflate(40, 40).collidepoint(p["x"], p["y"]) for rect in rects):
                    errors.append(prefix + "pickup inside cover")
            if not _doors_reachable(rects, r["doors"]):
                errors.append(prefix + "an entry is isolated from centre (40px navigation clearance)")
            for s in r["spawns"]:
                if s["enemy"] not in EnemyType.__members__ or s["enemy"] == "BOSS" or s["door"] not in door_ids:
                    errors.append(prefix + "invalid wave enemy or door (boss uses boss flag)")
                if type(s["delay"]) not in (int, float) or not math.isfinite(s["delay"]) or not 0 <= s["delay"] <= 600:
                    errors.append(prefix + "spawn time must be 0..600 seconds")
            if r["spawns"] and r["active_cap"] == 0:
                errors.append(prefix + "waves need positive active cap")
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            errors.append(prefix + str(error))
    if bosses != 1:
        errors.append("Exactly one boss room required")
    reached, pending = set(), [(0, 0)]
    while pending:
        pos = pending.pop()
        if pos in reached or pos not in positions:
            continue
        reached.add(pos)
        pending.extend((pos[0]+x, pos[1]+y) for x,y in ((1,0),(-1,0),(0,1),(0,-1)))
    if reached != positions:
        errors.append("Route disconnected: place rooms in adjacent grid cells")
    return errors


def _doors_reachable(rects, doors):
    # Conservative 40px nav grid, body radius 22px, bounded 1296 cells.
    step = 40
    blocked = { (x, y) for x in range(48) for y in range(27)
                if any(r.inflate(44, 44).collidepoint(x*step+20, y*step+20) for r in rects) }
    reached, pending = set(), [(24, 13)]
    while pending:
        p = pending.pop()
        if p in reached or p in blocked or not (1 <= p[0] <= 46 and 1 <= p[1] <= 25):
            continue
        reached.add(p)
        pending.extend((p[0]+x,p[1]+y) for x,y in ((1,0),(-1,0),(0,1),(0,-1)))
    return all((min(46,max(1,int(d["x"])//step)), min(25,max(1,int(d["y"])//step))) in reached for d in doors)


def save_document(doc, path):
    errors = validate_document(doc)
    if errors:
        raise ValueError("\n".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep one recoverable previous save, and atomically replace complete files.
    if path.exists():
        import shutil
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_document(path=DEFAULT_STAGE):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_document(doc)
    if errors:
        raise ValueError("\n".join(errors))
    return doc


def document_nodes(doc):
    from systems.stage_system import StageRoom, StageMapNode, DOOR_STEP
    from definitions.prototype_room_definitions import PrototypeRoomLayout, PrototypeDoor, PrototypeObstacle, PrototypePickupPoint, PrototypeSpawn
    from systems.room_system import RoomType
    from entities.enemy import EnemyType
    errors = validate_document(doc)
    if errors:
        raise ValueError("\n".join(errors))
    result = []
    positions = {tuple(r["position"]) for r in doc["rooms"]}
    for index, r in enumerate(doc["rooms"], 1):
        layout = PrototypeRoomLayout(r["id"], tuple(PrototypeDoor(**d) for d in r["doors"]),
            tuple(PrototypeObstacle(**o) for o in r["obstacles"]), tuple(PrototypePickupPoint(**p) for p in r["pickups"]))
        plan = tuple(PrototypeSpawn(s["delay"], s["door"], EnemyType[s["enemy"]]) for s in sorted(r["spawns"], key=lambda s:s["delay"]))
        room = StageRoom(index, RoomType[r["type"]], r["label"], plan, r["active_cap"], r["release_threshold"], r["reward_xp"], r["reward_gold"], r["boss"], layout)
        pos = tuple(r["position"])
        neighbors = {direction: (pos[0]+step[0], pos[1]+step[1]) for direction, step in DOOR_STEP.items()
                     if (pos[0]+step[0], pos[1]+step[1]) in positions}
        result.append(StageMapNode(room, pos, neighbors, discovered=index==1))
    return tuple(result)


def playable_nodes(fallback):
    path = Path(os.environ.get("BLUECUBE_STAGE_FILE", str(DEFAULT_STAGE)))
    if not path.exists():
        return fallback()
    try:
        return document_nodes(load_document(path))
    except (ValueError, OSError) as error:
        import warnings
        warnings.warn(f"Stage rejected; using built-in rooms: {error}")
        return fallback()
