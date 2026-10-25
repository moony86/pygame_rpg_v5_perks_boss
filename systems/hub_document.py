"""Validated sanctuary authoring shared by Level Studio and desktop runtime."""
import copy
import json
import os
from pathlib import Path
import pygame
from systems.asset_loader import ASSET_ROOT

PATH = ASSET_ROOT / 'data/hub.json'
DEFAULT_POSITIONS = {'blacksmith': [250,390], 'healer': [1625,390],
                     'portal': [937,245], 'seer': [255,840], 'tea_vendor': [1625,840]}


def load():
    doc = json.loads(PATH.read_text(encoding='utf-8'))
    doc.setdefault('positions', copy.deepcopy(DEFAULT_POSITIONS))
    doc.setdefault('spawn', [960,660])
    doc.setdefault('gate', [915,105])
    doc.setdefault('polygons', [])
    doc.setdefault('walkable', [])
    return doc


def colliders(doc):
    result = [pygame.Rect(r) for r in doc['colliders']]
    # Conservative 8px rasterization supports concave, editable polygon walls.
    if doc.get('polygons') or doc.get('walkable'):
        surface = pygame.Surface((240,135), pygame.SRCALPHA)
        if doc.get('walkable'):
            surface.fill((255,255,255))
            pygame.draw.polygon(surface,(0,0,0,0),[(x//8,y//8) for x,y in doc['walkable']])
        for polygon in doc['polygons']:
            pygame.draw.polygon(surface, (255,255,255), [(x//8,y//8) for x,y in polygon])
        mask = pygame.mask.from_surface(surface)
        previous = {}
        for y in range(135):
            runs = {}
            x = 0
            while x < 240:
                if not mask.get_at((x,y)):
                    x += 1
                    continue
                start = x
                while x < 240 and mask.get_at((x,y)):
                    x += 1
                key = (start,x)
                rect = previous.get(key)
                if rect is None:
                    rect = pygame.Rect(start*8,y*8,(x-start)*8,8)
                    result.append(rect)
                else:
                    rect.height += 8
                runs[key] = rect
            previous = runs
    return result


def validate(doc):
    errors = []
    try:
        if doc['background'] != 'hub/sanctuary_v1.png':
            errors.append('Keep the sanctuary background; use the asset library for other art.')
        if set(doc['positions']) != set(DEFAULT_POSITIONS):
            errors.append('All five keeper positions are required.')
        if set(doc['npcs']) != set(DEFAULT_POSITIONS):
            errors.append('All five keeper definitions are required.')
        for config in doc['npcs'].values():
            if not all(isinstance(config[k],str) and 0<len(config[k])<=100 for k in ('label','action')):
                errors.append('Keeper labels and actions must be short text.')
            if not isinstance(config['color'],list) or len(config['color'])!=3 or any(type(v) is not int or not 0<=v<=255 for v in config['color']):
                errors.append('Keeper color must be RGB.')
            art = config['art']
            path = (ASSET_ROOT / art).resolve()
            if art and (not path.is_relative_to(ASSET_ROOT.resolve()) or path.suffix.lower()!='.png' or not path.is_file()):
                errors.append('Keeper artwork must be a project PNG.')
            if not isinstance(config['size'],list) or len(config['size'])!=2 or any(type(v) is not int or not 0<=v<=256 for v in config['size']):
                errors.append('Invalid keeper size.')
        def point(p):
            return isinstance(p,list) and len(p)==2 and all(type(v) is int for v in p) and 0<=p[0]<1920 and 0<=p[1]<1080
        if not all(point(p) for p in [doc['spawn'],doc['gate'],*doc['positions'].values()]):
            errors.append('Positions must be integer coordinates inside 1920 x 1080.')
        if len(doc['colliders'])>128 or len(doc['polygons'])>32:
            errors.append('At most 128 rectangles and 32 polygons.')
        for r in doc['colliders']:
            if not isinstance(r,list) or len(r)!=4 or any(type(v) is not int for v in r) or not (r[0]>=0 and r[1]>=0 and r[2]>0 and r[3]>0 and r[0]+r[2]<=1920 and r[1]+r[3]<=1080):
                errors.append('Invalid collider rectangle.')
        def polygon_point(p):
            return isinstance(p,list) and len(p)==2 and all(type(v) is int for v in p) and 0<=p[0]<=1920 and 0<=p[1]<=1080
        polygons=list(doc['polygons'])
        if doc.get('walkable'):
            polygons.append(doc['walkable'])
        for p in polygons:
            if not isinstance(p,list) or not 3<=len(p)<=512 or not all(polygon_point(v) for v in p):
                errors.append('المضلع يحتاج 3 إلى 512 نقطة داخل المشهد.')
            elif abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))<128:
                errors.append('مساحة المضلع صغيرة جدًا أو نقاطه على خط واحد.')
        if errors:
            return errors
        solids = colliders(doc)
        for role,p in doc['positions'].items():
            if any(pygame.Rect(*p,46,46).colliderect(r) for r in solids):
                errors.append(f'{role}: keeper body is inside a wall.')
        spawn = pygame.Rect(0,0,40,40)
        spawn.center = doc['spawn']
        if any(spawn.colliderect(r) for r in solids):
            errors.append('Player spawn is inside a wall.')
        # Flood-fill a player-sized grid; every keeper must have an approach.
        blockers = solids + [pygame.Rect(*p,46,46) for p in doc['positions'].values()] + [pygame.Rect(*doc['gate'],90,90)]
        free = {(x,y) for y in range(1,54) for x in range(1,96)
                if not any(pygame.Rect(x*20-20,y*20-20,40,40).colliderect(r) for r in blockers)}
        if not free:
            return ['No walkable floor remains.']
        start = min(free, key=lambda p:(p[0]*20-doc['spawn'][0])**2+(p[1]*20-doc['spawn'][1])**2)
        reached = {start}
        queue = [start]
        for x,y in queue:
            for nxt in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if nxt in free and nxt not in reached:
                    reached.add(nxt)
                    queue.append(nxt)
        for role,(x,y) in doc['positions'].items():
            if not any((cx*20-x-23)**2+(cy*20-y-23)**2<110**2 for cx,cy in reached):
                errors.append(f'{role}: no reachable interaction approach.')
    except (KeyError, TypeError, ValueError, AttributeError, pygame.error):
        errors.append('Malformed hub document.')
    return errors


def save(doc, path=PATH):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    path = Path(path)
    if path.exists():
        path.with_suffix('.json.bak').write_bytes(path.read_bytes())
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf-8')
    os.replace(temporary,path)
