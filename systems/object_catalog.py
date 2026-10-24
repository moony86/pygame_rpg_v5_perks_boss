"""Safe data-backed object prefabs shared by the game and Level Studio."""
import copy
import json
import math
import re
from collections import OrderedDict
from pathlib import Path
import pygame
from systems.asset_loader import ASSET_ROOT, load_image

CATALOG_PATH = ASSET_ROOT / "data/game_objects.json"
_document = None
_sprites = {}
_source_frames = OrderedDict()
_source_bytes = 0
_source_stamps = {}
MAX_SOURCE_FRAMES=64
MAX_SOURCE_BYTES=128*1024*1024
_visual_revision = 0
_pickup_font = None
RANGES = {
    "width": (4, 1024), "height": (4, 1024), "health": (1, 2000), "speed": (50, 900),
    "damage": (1, 500), "cooldown": (.055, 5), "projectile_speed": (100, 2000),
    "pulse": (0, .15), "dash_damage": (1, 500), "chain_range": (50, 600), "chain_hops": (0, 8),
    "small": (1, 500), "medium": (1, 500), "large": (1, 500),
    "drop_chance": (0, 1), "respawn": (0, 120), "duration": (.1, 15), "charges": (1, 3),
    "opacity": (0,255), "frames": (1,16), "columns": (1,16), "rows": (1,16), "fps": (1,30),
    "life": (.05, 2), "art_size": (32,128), "art_y": (80,160), "title_y": (120,260), "desc_y": (160,320), "line_height": (20,36),
}
VISUAL_DEFAULTS = json.loads((ASSET_ROOT/'data/visual_defaults.json').read_text(encoding='utf-8'))['objects']
COMMON = {'tint':'#ffffff','opacity':255,'frames':1,'columns':1,'rows':1,'fps':10}
COLORS = {'tint','body','text','description','gunslinger','engineer','ninja','vampire','shared','legendary'}


def with_visual_defaults(doc):
    doc = copy.deepcopy(doc)
    if not isinstance(doc,dict) or not isinstance(doc.get('objects'),dict):
        return doc
    for key, value in VISUAL_DEFAULTS.items():
        doc['objects'].setdefault(key, copy.deepcopy(value))
        if isinstance(doc['objects'][key],dict):
            if key=='card_style' and 'art_y' not in doc['objects'][key]:
                doc['objects'][key]['art_y']=98
            for field,default in value.items():
                doc['objects'][key].setdefault(field,copy.deepcopy(default))
    for value in doc['objects'].values():
        if isinstance(value,dict):
            for field, default in COMMON.items():
                value.setdefault(field,default)
    return doc
FIELDS = {
    "hero": ("health", "speed"), "portal": ("pulse",),
    "pistol": ("damage", "cooldown", "projectile_speed"),
    "sword": ("dash_damage", "chain_range", "chain_hops"),
    "heal_potion": ("small", "medium", "large", "drop_chance", "respawn"),
    "dash_refresh": ("duration", "charges", "respawn"),
    "time_stop": ("duration", "drop_chance", "respawn"),
}
for _key, _visual in VISUAL_DEFAULTS.items():
    FIELDS[_key] = tuple(field for field in _visual if field not in ('name','art','cell','width','height') and field not in COMMON)
for _key in FIELDS:
    FIELDS[_key] = FIELDS[_key] + tuple(COMMON)


def validate_catalog(doc):
    doc = with_visual_defaults(doc)
    errors = []
    if not isinstance(doc, dict) or doc.get("schema") != "bluecube.objects.v1":
        return ["Invalid objects schema"]
    objects = doc.get("objects")
    if not isinstance(objects, dict) or set(objects) != set(FIELDS):
        return ["Catalog contains missing or unsupported object IDs"]
    for key, fields in FIELDS.items():
        o = objects[key]
        if not isinstance(o, dict):
            errors.append(f"{key}: expected object")
            continue
        if not isinstance(o.get("name"), str) or not o["name"].strip():
            errors.append(f"{key}: name required")
        art = o.get("art")
        if not isinstance(art, str) or Path(art).is_absolute() or ".." in Path(art).parts or not art.lower().endswith('.png'):
            errors.append(f"{key}: art must be a PNG path inside assets")
        elif not (ASSET_ROOT / art).is_file():
            errors.append(f"{key}: image not found: {art}")
        if type(o.get("cell")) is not int or not -1 <= o['cell'] <= 5:
            errors.append(f"{key}: cell must be -1 (whole image) or 0..5 (3x2 atlas)")
        for field in ("width", "height") + fields:
            v = o.get(field)
            if field in COLORS:
                if not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v):
                    errors.append(f'{key}.{field}: expected #RRGGBB')
                continue
            low, high = RANGES[field]
            if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
                errors.append(f"{key}.{field}: expected {low}..{high}")
        for field in ("width", "height", "health", "chain_hops", "charges", "small", "medium", "large", "damage", "dash_damage", "opacity", "frames", "columns", "rows", "art_size", "art_y", "title_y", "desc_y", "line_height"):
            if field in o and type(o[field]) is not int:
                errors.append(f"{key}.{field}: integer required")
        if all(type(o.get(f)) is int for f in ('frames','columns','rows')) and o['frames'] > o['columns']*o['rows']:
            errors.append(f'{key}: frames exceed sheet cells')
        if key == 'card_style' and all(type(o.get(f)) in (int,float) for f in ('title_y','desc_y','art_size','art_y')):
            if o['desc_y'] < o['title_y']+28 or o['title_y'] < o['art_y']+o['art_size']/2+12:
                errors.append('card_style: title / description overlap the art slot')
        if type(o.get('width')) is int and type(o.get('height')) is int:
            if key == 'card_style':
                if not 330 <= o['width'] <= 420 or not 440 <= o['height'] <= 620:
                    errors.append('card_style: dimensions must be 330..420 by 440..620')
            elif max(o['width'],o['height']) > 256:
                errors.append(f'{key}: sprite dimensions limited to 256px')
    style = objects.get('card_style',{})
    if not isinstance(style,dict):
        return errors
    if all(type(style.get(f)) is int for f in ('art_size','title_y','art_y')):
        heights = [min(128,round(value['height']*style['art_size']/96)) for key,value in objects.items()
                   if key.startswith('card_') and key!='card_style' and isinstance(value,dict) and type(value.get('height')) is int]
        if heights and style['title_y'] < style['art_y']+max(heights)/2+12:
            errors.append('card_style: title overlaps a configured card image; increase title_y')
    return errors


def catalog():
    global _document
    if _document is None:
        try:
            doc = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
            errors = validate_catalog(doc)
            if errors:
                raise ValueError('; '.join(errors))
            _document = with_visual_defaults(doc)
        except (OSError, ValueError) as error:
            import warnings
            warnings.warn(f'Object catalog rejected; using defaults: {error}')
            _document = with_visual_defaults(json.loads((ASSET_ROOT / 'data/game_objects.defaults.json').read_text(encoding='utf-8')))
    return _document


def reload_catalog():
    global _document
    previous=_document
    _document = None
    loaded=catalog()
    changed=previous!=loaded
    if not changed:
        for art,stamp in _source_stamps.items():
            try:
                stat=(ASSET_ROOT/art).stat()
                current=(stat.st_mtime_ns,stat.st_size)
            except OSError:
                current=None
            if current!=stamp:
                changed=True
                break
    if changed:
        clear_visual_caches()
    return loaded


def revision():
    return _visual_revision


def clear_visual_caches():
    global _visual_revision,_source_bytes
    _visual_revision+=1
    _sprites.clear()
    _source_frames.clear()
    _source_stamps.clear()
    _source_bytes=0
    import sys
    presentation=sys.modules.get('systems.shot_presentation')
    if presentation is not None:
        presentation.clear_caches()


def definition(key):
    return catalog()["objects"][key]


def save_catalog(doc):
    doc = with_visual_defaults(doc)
    errors = validate_catalog(doc)
    if errors:
        raise ValueError('\n'.join(errors))
    import shutil
    if CATALOG_PATH.exists():
        shutil.copy2(CATALOG_PATH, CATALOG_PATH.with_suffix('.json.bak'))
    temp = CATALOG_PATH.with_suffix('.json.tmp')
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(CATALOG_PATH)
    global _document
    _document = copy.deepcopy(doc)
    clear_visual_caches()


def sprite(key, size=None, frame=0):
    global _source_bytes
    o = definition(key)
    size = tuple(size or (o['width'], o['height']))
    frame = int(frame) % o['frames']
    cache_key = (key, size, o['art'], o['cell'], frame, o['columns'], o['rows'], o['tint'], o['opacity'])
    if cache_key in _sprites:
        return _sprites[cache_key]
    source_key=(o['art'],o['cell'],frame,o['columns'],o['rows'],o['frames'])
    image=_source_frames.get(source_key)
    if image is not None:
        _source_frames.move_to_end(source_key)
    if image is None:
        # Decode and trim once, not again for every tint/size/rotation variant.
        image=load_image(o['art'])
        if image is None:
            return None
        stat=(ASSET_ROOT/o['art']).stat()
        _source_stamps[o['art']]=(stat.st_mtime_ns,stat.st_size)
        if o['cell'] >= 0:
            w,h=image.get_width()//3,image.get_height()//2
            image=image.subsurface(((o['cell']%3)*w,(o['cell']//3)*h,w,h))
        elif o['frames']>1:
            w,h=image.get_width()//o['columns'],image.get_height()//o['rows']
            image=image.subsurface(((frame%o['columns'])*w,(frame//o['columns'])*h,w,h))
        bounds=image.get_bounding_rect(min_alpha=16)
        if bounds.width and bounds.height:
            image=image.subsurface(bounds)
        _source_frames[source_key]=image
        parent=image.get_abs_parent()
        _source_bytes+=parent.get_pitch()*parent.get_height()
        while len(_source_frames)>MAX_SOURCE_FRAMES or _source_bytes>MAX_SOURCE_BYTES:
            _,old=_source_frames.popitem(last=False)
            parent=old.get_abs_parent()
            _source_bytes-=parent.get_pitch()*parent.get_height()
    ratio = min(size[0]/image.get_width(), size[1]/image.get_height())
    dimensions = size if key=='card_style' else (max(1,round(image.get_width()*ratio)), max(1,round(image.get_height()*ratio)))
    image = pygame.transform.scale(image, dimensions)
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(image, image.get_rect(center=(size[0]//2, size[1]//2)))
    if o['tint'].lower() != '#ffffff':
        tint = pygame.Color(o['tint'])
        # Preserve saturated highlights (red enemies must not turn muddy brown).
        for x in range(result.get_width()):
            for y in range(result.get_height()):
                pixel = result.get_at((x,y))
                if pixel.a:
                    value = max(pixel.r,pixel.g,pixel.b)
                    result.set_at((x,y),(value*tint.r//255,value*tint.g//255,value*tint.b//255,pixel.a))
    result.set_alpha(o['opacity'])
    _sprites[cache_key] = result
    return result


def draw_object(surface, key, center, time=0, active=True, size=None):
    global _pickup_font
    image = sprite(key, size, int(time*definition(key)['fps']))
    if image is None:
        return False
    if not active:
        image = image.copy()
        image.fill((85, 95, 110, 170), special_flags=pygame.BLEND_RGBA_MULT)
    if key == 'portal':
        pulse = 1 + math.sin(time*3)*definition('portal')['pulse'] if active else 1
        image = pygame.transform.scale(image, (round(image.get_width()*pulse), round(image.get_height()*pulse)))
    offset = math.sin(time*3)*2 if key in ('heal_potion','dash_refresh','time_stop') else 0
    rect = image.get_rect(center=(round(center[0]),round(center[1]+offset)))
    surface.blit(image, rect)
    if key in ('dash_refresh', 'time_stop'):
        if _pickup_font is None:
            _pickup_font = pygame.font.Font(None, 20)
        color = (90,225,255) if key=='dash_refresh' else (220,190,255)
        if not active:
            color=(125,140,155)
        label = _pickup_font.render('DASH' if key=='dash_refresh' else 'TIME STOP',True,color)
        label_rect=label.get_rect(midtop=(rect.centerx,rect.bottom+12))
        back=pygame.Surface((label_rect.width+10,label_rect.height+4),pygame.SRCALPHA)
        back.fill((5,10,20,205))
        surface.blit(back,(label_rect.x-5,label_rect.y-2))
        surface.blit(label,label_rect)
        if key=='dash_refresh':
            # Double chevron below the pickup: direction/motion, not another crystal.
            for dx in (-7,1):
                pygame.draw.lines(surface,color,False,[(rect.centerx+dx-3,rect.bottom+2),
                    (rect.centerx+dx+2,rect.bottom+6),(rect.centerx+dx-3,rect.bottom+10)],2)
    return True
