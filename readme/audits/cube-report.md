# تقرير مشروع The Cube / BlueCube

> نطاق الفحص: قراءة ملفات المشروع فقط. لم يُعدَّل أي ملف برمجي. هذا التقرير يصف حالة المستودع وقت الفحص.

## 1) نظرة عامة

**النوع والفكرة:**

BlueCube لعبة **Action Roguelite** سريعة بمنظور علوي. اللاعب يتحكم بـ«المكعب الأزرق»/الشخصية داخل Hub ثم يدخل غرف قتال، يقتل الأعداء، يجمع XP والذهب، ويختار Perk cards عند رفع المستوى. الهدف من كل Run هو تكوين هوية قتالية مختلفة، لا مجرد رفع أرقام: Gunslinger أو Ninja أو Engineer أو Vampire. تنتهي الجولة بمواجهة Boss بعد سلسلة غرف.

النص الرسمي في تصميم المشروع يقول حرفياً:

```text
BlueCube is a fast-paced action roguelite where every run gradually evolves into a unique combat identity.

Cards exist to shape identity.

Numbers exist only to support identity.
```

**التقنية والمنصة:** Python + **Pygame** (سطح مكتب Windows)، مع بناء توزيع Windows عبر Nuitka (`dist_nuitka_demo/main.dist/BlueCube.exe`). ليست Unity أو Godot أو React أو HTML Canvas.

**الشاشة واللغة:** الدقة الداخلية الثابتة `1920×1080`، والعرض window قابل للتحجيم ثم يُعمل له `smoothscale`. الاتجاه أفقي (Landscape، 16:9). واجهة اللعبة الحالية إنجليزية LTR؛ توجد تعليقات برمجية عربية، لكن لا توجد واجهة عربية أو RTL أو خط عربي مخصص.

الكود المسؤول حرفياً:

```python
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
```

```python
self.window = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.RESIZABLE
)
self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
```

## 2) كيف تتحمّل الأصول حالياً

### شجرة مجلد الأصول المصدرية

> `dist_nuitka_demo/main.dist/assets/` نسخة مبنية مكررة من `assets/` وليست مصدر الأصول الذي ينبغي تعديله.

```text
assets/
├── Archer/
│   ├── Archer_Idle.png
│   ├── Archer_Run.png
│   ├── Archer_Shoot.png
│   └── Arrow.png
├── Warrior/
│   ├── Warrior_Attack1.png
│   ├── Warrior_Attack2.png
│   ├── Warrior_Guard.png
│   ├── Warrior_Idle.png
│   └── Warrior_Run.png
├── engineer/
│   ├── blade_hit.png
│   └── blade_impact.png
├── music/
│   ├── boss.ogg
│   ├── boss_01.ogg
│   ├── combat.ogg
│   ├── Crown_of_Broken_Stone.mp3
│   ├── hub.ogg
│   ├── Lanterns_in_the_Hall.mp3
│   ├── Steel_Teeth.mp3
│   ├── The_Iron_Siege.mp3
│   ├── The_Keeper_s_Quiet_Hall.mp3
│   ├── The_Weight_of_Steel.mp3
│   └── Under_the_Needle.mp3
├── sounds/
│   ├── 16. Battle Theme III (intro).ogg
│   ├── 16. Battle Theme III (loop).ogg
│   ├── boss_death.wav
│   ├── boss_phase.wav
│   ├── boss_spawn.wav
│   ├── coin_pickup.wav
│   ├── dash.wav
│   ├── enemy_death.wav
│   ├── GUNPis_Pistol Fire Longer Tail_05.wav
│   ├── hit.wav
│   ├── hub2.ogg
│   ├── LASRGun_Classic Blaster A Fire_03.wav
│   ├── level_up.wav
│   ├── menu_select.wav
│   ├── peckcard.wav
│   ├── portal_open.wav
│   ├── room_clear.wav
│   ├── shoot.wav
│   ├── tea_drink.wav
│   ├── upgrade_buy.wav
│   ├── wave_clear.wav
│   ├── wave_start.wav
│   └── xp_pickup.wav
├── ChatGPT Image 26 يونيو 2026، 02_02_40 ص.png
├── E-bullet.png
├── blade_drone.png
├── block.png
├── box.png
├── bulit anime.png
├── bullet.png
├── coin.png
├── cube.ico
├── enamy1.png
├── enamyIdle.png
├── enamyRange.png
├── enamyRangeWepaon.png
├── gun.png
├── gun_will_shoting.png
├── hero (1).png
├── hero.png
├── knife_animation.png
├── soward.png
├── sowrd-hit.png
├── stap_fram.png
├── tea_drink.png
├── tea_full.png
├── tea_shop.png
├── underPlayer.png
├── underPlayer1.png
├── wepone knife.png
├── xp.png
└── تنزيل.png
```

### الصيغ المستخدمة

* صور: `.png` و`.ico` فقط في `assets/` المصدرية. لا يوجد `.svg` أو `.jpg` أو `.webp` كمصدر حالياً.
* صوت: `.wav` و`.ogg` و`.mp3`.
* معظم الشاشة/الإطار/الخلفية والأيقونات الحالية ليست ملفات؛ تُرسم كـprimitives بواسطة Pygame (`draw.rect` / `draw.circle` / `draw.line`) أو نصوص.
* لا توجد emoji كأصل رسومي. الرمز `◆` في المتجر محرف نصي.

### طريقة تحميل الصورة وعرضها

المسؤول المباشر هو [`systems/asset_loader.py`](systems/asset_loader.py)، وهذا الجزء كاملاً:

```python
from pathlib import Path
import time

import pygame


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
ASSET_LOAD_STATS = {}


def _record_load(name, path, asset_type, success):
    key = str(name)
    stats = ASSET_LOAD_STATS.setdefault(key, {
        "name": key,
        "path": str(path),
        "asset_type": asset_type,
        "load_count": 0,
        "last_loaded": None,
        "success": False,
    })
    stats["path"] = str(path)
    stats["asset_type"] = asset_type
    stats["load_count"] += 1
    stats["last_loaded"] = time.time()
    stats["success"] = success


def asset_load_stats():
    return {key: value.copy() for key, value in ASSET_LOAD_STATS.items()}


def load_image(name, size=None):
    path = ASSET_ROOT / name
    if not path.exists():
        _record_load(name, path, "image", False)
        return None

    try:
        image = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
    except (pygame.error, OSError):
        _record_load(name, path, "image", False)
        return None

    if size is not None and image.get_size() != size:
        image = pygame.transform.smoothscale(image, size)
    _record_load(name, path, "image", True)
    return image


def load_sheet_frames(name, frame_size, max_frames=None, scale=None):
    sheet = load_image(name)
    if sheet is None:
        return []

    frame_w, frame_h = frame_size
    frames = []
    for y in range(0, sheet.get_height() - frame_h + 1, frame_h):
        for x in range(0, sheet.get_width() - frame_w + 1, frame_w):
            frame = pygame.Surface(frame_size, pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(x, y, frame_w, frame_h))
            if scale is not None:
                frame = pygame.transform.smoothscale(frame, scale)
            frames.append(frame)
            if max_frames is not None and len(frames) >= max_frames:
                return frames
    return frames
```

**SVG / gradients / filters / SVG animations:** لا. لا توجد ملفات SVG ولا SVG renderer ولا أي معالجة لـ`viewBox` أو gradients أو filters أو animations داخل SVG. قائمة الامتدادات التي يمسحها pipeline هي:

```python
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".ico", ".wav", ".ogg", ".mp3"}
```

### قواعد التسمية الحالية

لا توجد قاعدة موحّدة أو ربط تلقائي باسم الكرت. الأمثلة الفعلية تشمل `enamyRangeWepaon.png` و`bulit anime.png` و`wepone knife.png` و`ChatGPT Image 26 يونيو 2026، 02_02_40 ص.png`، أي مسافات وأخطاء إملائية وتسمية عربية/إنجليزية مختلطة. الاستثناء الأكثر اتساقاً هو spritesheets داخل `Archer/` و`Warrior/` بصيغة `<Character>_<State>.png`، مع تعريف صريح للمسار في Python.

## 3) نظام الكروت (Perks)

### بنية البيانات الكاملة

لا يوجد `class Card` أو typed schema؛ كل كرت `dict`. التعريف المصدر يضم الحقول النصية التالية:

| الحقل | النوع | المعنى |
|---|---|---|
| `key` | `str` | المعرّف الفريد للكرت |
| `name` | `str` | الاسم المعروض |
| `desc` | `str` | الوصف العادي المعروض |
| `legendary_desc` | `str` | الوصف عند Legendary |
| `tags` | `list[str]` | كلمات اللعب/التآزر |
| `build` | `str` | البناء الرئيسي |
| `build_roles` | `list[str]` اختياري | أدوار hybrid؛ غير موجود لمعظم الكروت |

عند التشغيل، `_build_perks()` ينسخ كل قاموس ويضيف `apply` و`legendary_apply` (دوال Python). وعند تكوين option للاعب يضيف `taken: int` و`limit: int` و`legendary: bool` و`synergy: str` و`build_label: str` و`hybrid_builds: list[str]`، وربما `starter: bool`.

الكود حرفياً:

```python
def _build_perks():
    perks = []
    for definition in PERK_DEFINITIONS:
        perk = dict(definition)
        apply_effect, legendary_effect = PERK_EFFECTS[perk["key"]]
        perk["apply"] = apply_effect
        perk["legendary_apply"] = legendary_effect
        perks.append(perk)
    return perks
```

```python
def _option_for_player(self, perk, player):
    option = dict(perk)
    taken = player.perk_counts.get(perk["key"], 0) if player is not None else 0
    option["taken"] = taken
    option["limit"] = PERK_PICK_LIMIT
    option["legendary"] = taken >= 3
    option["synergy"] = _synergy_label(perk, player) if player is not None else ""
    option["build"] = perk.get("build", "Shared/Utility")
    option["build_label"] = _primary_build(perk).upper()
    option["hybrid_builds"] = _hybrid_builds(perk)
    if option["legendary"]:
        option["name"] = "Legendary " + perk["name"]
        option["desc"] = perk.get("legendary_desc", perk["desc"])
    return option
```

### خمسة كروت كاملة، من أنواع مختلفة — منسوخة حرفياً

```python
{"key": "rapid_fire", "name": "Fire Rate Boost", "desc": "+30% faster shooting", "legendary_desc": "+55% faster shooting", "tags": ["offense", "fire_rate", "gunslinger"], "build": "Gunslinger"},
{"key": "blade_drone", "name": "Blade Drone", "desc": "Unlocks an orbiting close-range machine zone", "legendary_desc": "Second synchronized blade and faster contact control", "tags": ["offense", "utility", "engineer"], "build": "Engineer"},
{"key": "vital_core", "name": "Vital Core", "desc": "+48 max health, heal 24, increases Blood capacity", "legendary_desc": "+110 max health, full heal, more Blood capacity", "tags": ["defense", "health", "vampire", "shared"], "build": "Vampire"},
{"key": "phantom_step", "name": "Phantom Step", "desc": "+20 movement speed, -20 max health, improves dash-strike", "legendary_desc": "+50 movement speed, +0.20s dash invulnerability, dash cooldown restore", "tags": ["mobility", "speed", "dash", "tradeoff", "ninja"], "build": "Ninja"},
{"key": "glass_cannon", "name": "Blood Pact", "desc": "+25 bullet damage, -40 max health, feeds Blood on risky combat", "legendary_desc": "+60 bullet damage, -40 max health, improves Blood overflow", "tags": ["offense", "damage", "tradeoff", "vampire", "shared"], "build": "Shared/Utility", "build_roles": ["Vampire", "Shared/Utility"]},
```

### العدد والأنواع والندرات

* العدد الكلي: **21** تعريف Perk.
* التصنيف القتالي الفعلي: 7 Gunslinger، 5 Engineer، 4 Ninja، 4 Vampire، وBlood Pact واحد Shared/Utility (مع Vampire hybrid).
* لا يوجد حقل `rarity` في البيانات ولا نظام ندرة مستقل. اللون الأزرق/البنفسجي/الذهبي يتحدد **بفهرس موقع الكرت في الثلاثة المعروضة** (`i % 3`) وليس بنوعه أو ندرته. الـLegendary حالة اختيار بعد الحصول على الكرت 3 مرات (`taken >= 3`)، مع حد اختيارات `PERK_PICK_LIMIT = 4`.

الكود الحرفي الذي يثبت ذلك:

```python
PERK_COLORS = [
    (80,  160, 255),   # blue  – card 0
    (180, 80,  255),   # purple – card 1
    (255, 160, 40),    # gold   – card 2
]
```

```python
col      = PERK_COLORS[i % len(PERK_COLORS)]
```

```python
option["legendary"] = taken >= 3
```

### كيف يُرسم الكرت الآن

المكوّن المسؤول هو [`ui/perk_screen.py`](ui/perk_screen.py) والدالة `draw_perk_select`. لا يوجد CSS أو مكوّن ويب. يُنشأ `pygame.Surface` داكن شفاف، شريط علوي ملون، border، badge نصي، ثم بديل icon هندسي، فالاسم والوصف والعداد والزر.

الكود الكامل المسؤول عن جسم الكرت وموضعه:

```python
card_w, card_h = 248, 268
gap     = 30
start_x = SCREEN_WIDTH // 2 - (card_w * 3 + gap * 2) // 2

for i, perk in enumerate(options):
    col      = PERK_COLORS[i % len(PERK_COLORS)]
    x        = start_x + i * (card_w + gap)
    y        = 190
    rect     = pygame.Rect(x, y, card_w, card_h)
    card_rects.append(rect)

    hovered  = rect.collidepoint(mouse_pos)
    bob      = int(math.sin(t * 2.0 + i * 1.2) * 4) if hovered else 0
    draw_y   = y - bob

    # card shadow
    sh_surf = pygame.Surface((card_w + 12, card_h + 12), pygame.SRCALPHA)
    sh_a    = 100 if hovered else 60
    pygame.draw.rect(sh_surf, (0, 0, 0, sh_a),
                     (0, 0, card_w + 12, card_h + 12), border_radius=14)
    surface.blit(sh_surf, (x - 6, draw_y + 6))

    # card body
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    bg_a      = 230 if hovered else 200
    pygame.draw.rect(card_surf, (14, 16, 28, bg_a),
                     (0, 0, card_w, card_h), border_radius=12)

    # top colour band
    band_h = 6
    pygame.draw.rect(card_surf, col,
                     (0, 0, card_w, band_h), border_radius=12)
    pygame.draw.rect(card_surf, (0, 0, 0), (0, band_h, card_w, 1))

    # border
    brd_w = 3 if hovered else 1
    brd_a = 220 if hovered else 120
    pygame.draw.rect(card_surf, (*col, brd_a),
                     (0, 0, card_w, card_h), brd_w, border_radius=12)

    surface.blit(card_surf, (x, draw_y))
```

### أبعاد الكرت وArt slot

* أبعاد الكرت بالضبط: **248×268 px** (نسبة 0.925:1). الفجوة بين الكروت 30 px؛ الصف يبدأ عند `y=190`.
* لا يوجد Art slot مخصص ولا `Rect` صورة ولا تحميل image للكرت.
* البديل الحالي هو icon هندسي في المركز `(x + 124, draw_y + 70)` بنصف قطر `28 px`، وحلقة متذبذبة تقريباً 24–32 px. المنطقة المرئية المفهومة للـart هي دائرة قطرها **56 px** حول هذه النقطة، وليست مستطيلاً/نسبة محددة. هذا يعني أن قياس art slot المطلوب في الوضع الحالي هو: **غير موجود**.
* الموجود في الخانة الآن: شكل هندسي مرسوم بالـPygame حسب ترتيب العرض: Diamond للكرت 0، Hexagon للكرت 1، Star للكرت 2. هذا ليس حسب id ولا type ولا rarity.

الكود حرفياً:

```python
# icon placeholder – geometric shape per card
icon_cx = x + card_w // 2
icon_cy = draw_y + 70
icon_r  = 28
# pulsing ring
pulse_r = icon_r + int(4 * math.sin(t * 3 + i))
pygame.draw.circle(surface, (*col, 60), (icon_cx, icon_cy), pulse_r, 2)

if i == 0:
    # diamond
    pts = [(icon_cx, icon_cy - icon_r),
           (icon_cx + icon_r, icon_cy),
           (icon_cx, icon_cy + icon_r),
           (icon_cx - icon_r, icon_cy)]
    pygame.draw.polygon(surface, col, pts)
    pygame.draw.polygon(surface, (200, 200, 255), pts, 2)
elif i == 1:
    # hexagon
    pts = [(icon_cx + int(icon_r * math.cos(math.pi / 3 * k - math.pi / 6)),
            icon_cy + int(icon_r * math.sin(math.pi / 3 * k - math.pi / 6)))
           for k in range(6)]
    pygame.draw.polygon(surface, col, pts)
    pygame.draw.polygon(surface, (220, 180, 255), pts, 2)
else:
    # star
    pts = []
    for k in range(5):
        outer_a = math.pi / 2 + 2 * math.pi / 5 * k
        inner_a = outer_a + math.pi / 5
        pts.append((icon_cx + int(icon_r * math.cos(outer_a)),
                     icon_cy - int(icon_r * math.sin(outer_a))))
        pts.append((icon_cx + int((icon_r * 0.45) * math.cos(inner_a)),
                     icon_cy - int((icon_r * 0.45) * math.sin(inner_a))))
    pygame.draw.polygon(surface, col, pts)
    pygame.draw.polygon(surface, (255, 220, 100), pts, 2)
```

## 4) قائمة كل الكروت التي تحتاج رسماً

كل الـ21 أدناه تحتاج Art أصلياً؛ لا يوجد حالياً ملف art مرتبط بأي منها. **الندرة: غير معرّفة في البيانات** لكل الصفوف. حالة Legendary تأتي عند الاختيار الرابع للكرت، وليست rarity مخزنة.

| id | الاسم | النوع / build | الندرة | الوصف/التأثير | الكلمات المفتاحية |
|---|---|---|---|---|---|
| `rapid_fire` | Fire Rate Boost | Gunslinger | غير معرّفة | +30% faster shooting / Legendary: +55% faster shooting | offense, fire_rate, gunslinger |
| `power_rounds` | Power Rounds | Gunslinger | غير معرّفة | +14 bullet damage, -10% fire rate / Legendary: +32 bullet damage, restores fire rate | offense, damage, gunslinger |
| `hollow_point` | Hollow Point | Gunslinger | غير معرّفة | +20 bullet damage, pierce becomes 0 / Legendary: +45 bullet damage, pierce 0, +0.25 crit damage | offense, damage, crit, tradeoff, gunslinger |
| `glass_cannon` | Blood Pact | Shared/Utility; Vampire hybrid | غير معرّفة | +25 bullet damage, -40 max health, feeds Blood on risky combat / Legendary: +60 bullet damage, -40 max health, improves Blood overflow | offense, damage, tradeoff, vampire, shared |
| `split_shot` | Extra Projectile | Gunslinger | غير معرّفة | +1 bullet per shot, lower bullet damage / Legendary: +1 bullet per shot, improves split damage | offense, projectile, gunslinger |
| `needle_rounds` | Piercing Bullets | Gunslinger | غير معرّفة | +1 enemy pierced per bullet / Legendary: +3 pierce, +8 bullet damage | offense, pierce, gunslinger |
| `kinetic_rounds` | Kinetic Tuning | Engineer; Gunslinger hybrid | غير معرّفة | +8 bullet damage, +70 bullet speed, improves helper damage if deployed / Legendary: +24 bullet damage, +180 bullet speed, stronger helper shots | offense, damage, speed, engineer, gunslinger |
| `critical_spark` | Critical Spark | Gunslinger | غير معرّفة | +30% critical hit chance / Legendary: +80% critical chance, +0.35 crit damage | offense, crit, gunslinger |
| `overclock` | Overclock | Engineer; Ninja/Gunslinger hybrid | غير معرّفة | +40% faster shooting, faster helper cadence, builds Ninja momentum, -15 max health / Legendary: +70% faster shooting, faster helper cadence, -20% skill cooldown | offense, fire_rate, tradeoff, engineer, ninja, gunslinger |
| `explosive_rounds` | Explosive Rounds | Gunslinger; Engineer hybrid | غير معرّفة | Explosive bullets; later picks improve blast radius and splash / Legendary: Bigger, stronger explosions and restores fire rate | offense, explosive, tradeoff, gunslinger, engineer |
| `impact_drive` | Impact Drone | Engineer | غير معرّفة | +45% bullet pushback and deploys a slow auto-helper / Legendary: +120% bullet pushback, +8 bullet damage, helper fires faster | offense, utility, engineer |
| `blade_drone` | Blade Drone | Engineer | غير معرّفة | Unlocks an orbiting close-range machine zone / Legendary: Second synchronized blade and faster contact control | offense, utility, engineer |
| `bomber_drone` | Bomber Drone | Engineer | غير معرّفة | Unlocks a rebuilding anti-group bomber machine / Legendary: Larger blast and a bounded second bombing run | offense, explosive, engineer |
| `vital_core` | Vital Core | Vampire | غير معرّفة | +48 max health, heal 24, increases Blood capacity / Legendary: +110 max health, full heal, more Blood capacity | defense, health, vampire, shared |
| `battle_recovery` | Blood Recovery | Vampire | غير معرّفة | +24 room healing, gain Blood and heal on kills; unlocks Feast bursts / Legendary: +70 room healing, +35 max health, stronger Blood healing and Feast | defense, regen, heal, vampire |
| `scout_boots` | Scout Boots | Ninja | غير معرّفة | +30 movement speed and light dash-strike damage / Legendary: +70 movement speed, resets dash cooldown, stronger dash reward | mobility, speed, dash, ninja |
| `phantom_step` | Phantom Step | Ninja | غير معرّفة | +20 movement speed, -20 max health, improves dash-strike / Legendary: +50 movement speed, +0.20s dash invulnerability, dash cooldown restore | mobility, speed, dash, tradeoff, ninja |
| `shadow_shuriken` | Shadow Shuriken | Ninja | غير معرّفة | Dash hits throw a quick shuriken and improve momentum / Legendary: Stronger shuriken and higher Dash refund cap | mobility, dash, projectile, ninja |
| `sanguine_rounds` | Sanguine Rounds | Vampire | غير معرّفة | Projectile hits wound enemies; wounded deaths drop Blood Orbs / Legendary: More wound stacks, Blood from bosses, and better orb yield | offense, heal, vampire |
| `blood_bat` | Blood Bat | Vampire | غير معرّفة | A single bat seeks wounded targets and returns carried Blood / Legendary: Bat dives faster, feeds harder, and rests for less time | offense, summon, vampire |
| `blood_trail` | Blood Trail | Vampire | غير معرّفة | Dashing through wounded enemies harvests Blood once per dash / Legendary: Improves harvest cap and unlocks Blood Moon surges | mobility, dash, vampire |

## 5) أصول ثانية ناقصة / تستخدم نصاً أو placeholder وتحتاج رسماً

| الفئة | الموجود الآن | المقاس الحالي/المطلوب في الواجهة | ملاحظة |
|---|---|---:|---|
| Art الكروت | Diamond/Hexagon/Star مرسومة برمجياً | لا يوجد slot؛ البديل دائرة قطر 56 px في مركز `(124,70)` محلياً | كل الـ21 كرت تحتاج رسماً |
| إطارات الكروت | `draw.rect` فقط | 248×268 px | لا يوجد PNG/SVG frame |
| خلفية اختيار الكروت | fill داكن + 3 ellipses متحركة | 1920×1080 | لا توجد صورة خلفية |
| خلفية القائمة | grid/glow مرسوم | 1920×1080 | لا توجد صورة خلفية |
| HUD icons (HP, XP, Gold, Damage, Crit, Dash) | نصوص وأشرطة فقط | لوحة اليسار 242×188؛ dash bar 112×8 تقريباً | لا تستخدم `xp.png` أو `coin.png` كأيقونات HUD هنا |
| أيقونة الذهب في المتجر | الحرف النصي `◆` | ضمن panel 480 px عرض | تحتاج أيقونة عملة إن أريد استبدال النص |
| أزرار القائمة | مستطيلات مرسومة | 200×50 px | New Run / Quit |
| إطارات المتجر | مستطيلات/Badges مرسومة | panel 480×(44+28×عدد الخيارات)؛ badge 22×22 | لا توجد أصول |
| pause menu | overlay/panel/sliders مرسومة | panel 400×380؛ slider track بعرض 340 | لا توجد أصول |
| end/win screens | glow والنص فقط | 1920×1080 | لا توجد رسمة انتصار/هزيمة |
| بوابة الخروج | دوائر ملونة مرسومة | قطر خارجي متذبذب 192–204 px | لا يوجد sprite للبوابة |
| minimap | rectangles/primitives | 150×150 px | لا توجد tiles/icons |
| world backgrounds | draw calls، لا texture/background image | 1920×1080 viewport | تحتاج بيئات مرسومة إذا كان المطلوب visual art |

## 6) الستايل البصري

### Palette / theme

لا يوجد ملف CSS ولا theme variables؛ الألوان موزعة بين `settings.py` وملفات UI. الألوان العامة المعلنة حرفياً:

```python
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (45, 45, 45)
LIGHT_GRAY = (225, 225, 225)
DARK_GRAY = (18, 18, 18)
BLUE = (0, 110, 255)
GREEN = (0, 190, 100)
YELLOW = (255, 220, 0)
RED = (220, 55, 55)
PURPLE = (150, 70, 220)
ORANGE = (245, 150, 45)
CYAN = (50, 220, 240)
GOLD = (235, 180, 40)
PINK = (255, 90, 170)
```

والأسلوب UI الفعلي: خلفيات كحلية/بنفسجية شديدة الظلمة، حدود/Glow أزرق كهربائي، أخضر للنجاح، ذهبي لـXP أو level up، أحمر للصحة/الخطر، وبنفسجي للكروت المعروضة في الموضع الثاني.

### الخطوط

اللعبة تستخدم خط نظام **Arial** فقط:

```python
self.font = pygame.font.SysFont("Arial", 22)
self.big_font = pygame.font.SysFont("Arial", 48)
```

### أفضل الأصول الموجودة لتمثيل الستايل

لا توجد SVGs لإرسال كودها. أفضل ثلاثة مرشحين بصريين موجودين كـPNG هم:

1. `assets/hero.png` — 2048×2048، أكبر صورة شخصية/Concept ظاهرة في المشروع.
2. `assets/Warrior/Warrior_Idle.png` — spritesheet بحجم 1536×192؛ يمثل لغة الشخصيات pixel/sprite القتالية.
3. `assets/Archer/Archer_Shoot.png` — spritesheet بحجم 1536×192؛ يمثل الحركة/الهجوم البعيد.

### الجو والقصة

الجو **geometric roguelite** داكن مستقبلي/Arcade: شبكة متحركة داكنة وneon glow، مع قتال dungeon وغرف وBoss. القائمة تصفه حرفياً بـ`geometric roguelite  |  WASD + Mouse`. القصة الملمّح لها: Gatekeeper يقول إن الـdungeon استيقظ؛ اللاعب يدخل وينجو من الغرف ويعود أقوى. لا يوجد نص سردي موسع أو cinematic في الملفات المقروءة.

## 7) القيود التقنية للأصول الجديدة

* لا يوجد حد لحجم الملف محدد في الكود ولا Asset budget موثق.
* التحميل يمر عبر `pygame.image.load` ثم `convert_alpha()`؛ لذلك PNG بخلفية شفافة مدعوم ومناسب.
* SVG ليس مدعوماً حالياً، وبالتالي لا يوجد `viewBox` مطلوب. يجب rasterize إلى PNG قبل الاستخدام، ما لم يُضاف دعم برمجي جديد.
* لا يوجد حالياً مسار تلقائي مثل `cards/<id>.png` ولا ربط الكرت بالصورة باستخدام `key`. إضافة ملف باسم `rapid_fire.png` وحدها **لن تجعله يظهر**؛ ينبغي تعديل تعريف/رسم الكرت، وهو خارج نطاق هذا التقرير.
* تحميل spritesheets يفترض frame sizes صريحة. الشخصيات الحالية تستخدم `SPRITE_FRAME_SIZE = (192, 192)` وتُقصّ من الـsheet بهذا المقاس.
* للـcard art تحديداً لا يوجد مقاس تقني مفروض. بناءً على البديل الحالي، مرجع التصميم الأقرب هو Icon مربع/شفاف 56×56 px (أو أعلى ثم يُصغّر)، لكن لا يمكن ربطه تلقائياً بلا تعديل كود.
* الموقع المصدر للأصول: `assets/`، وليس `dist_nuitka_demo/main.dist/assets/` لأنه ناتج build.

## 8) وصف الشاشات الرئيسية

| الشاشة / الحالة | الوصف |
|---|---|
| Menu | خلفية كحلية داكنة ذات grid متحرك وglow في الزوايا. عنوان `BLUE CUBE v5`، سطر التحكم، زرّا New Run وQuit. |
| Hub | العالم قبل القتال. اللاعب/NPCs والبوابة، HUD، حوارات Gatekeeper وtea vendor والمتجر لدى blacksmith/healer. الضغط E قرب البوابة يبدأ الـdungeon. |
| Room | قتال غرفة بمنظور علوي: خلفية العالم وعوائق، أعداء ومقذوفات وpickups، HUD للصحة/XP/ذهب/stats، هدف الغرفة وminimap وبوابة خروج عند الإتمام. |
| Boss | نفس إطار القتال تقريباً مع هدف Boss HP وصحة Boss بدلاً من kills، وينتهي بالفوز عند هزيمته. |
| Perk Select | شاشة LEVEL UP مستقلة بخلفية داكنة و3 كروت 248×268، كل منها badge بناء، placeholder هندسي، الاسم والوصف والـtaken counter وزر reroll. |
| Pause | world خلف overlay داكن، panel مركزي 400×380، Resume/Return hints وsliders لـMaster/Music/SFX. |
| Game Over | شاشة داكنة مع glow أحمر نابض، `GAME OVER`، الغرف التي وصل إليها اللاعب، وإعادة تشغيل بـEnter. |
| Win | النسخة الخضراء من end screen: `BOSS DEFEATED`، المستوى والذهب والقتل، وإعادة تشغيل. |
| Dev/Authoring/Asset browser | أدوات مطور إضافية محلية موجودة في المشروع عند تفعيل `BLUECUBE_DEV_TOOLS`، وليست شاشة لعب أساسية. |

## تحديث ربط رسومات الكروت — batch 1

تمت إضافة الرسومات المصدرية المتاحة في `assets/cards/` وحفظ ملفات SVG المرجعية في `assets/cards/src/`:

* `rapid_fire`
* `blade_drone`
* `vital_core`
* `phantom_step`
* `glass_cannon`

واجهة Perk Select تحمل صورة `assets/cards/<key>.png` عبر `load_image` وتحتفظ بالـplaceholder الهندسي عندما لا يوجد ملف. القيمة النهائية هي `CARD_ART_SIZE = 72`، ومركز الرسم المحلي هو `(124, 76)` داخل كرت `248×268`. اختيرت 72×72 بدلاً من 112×112 كي تبقى الرسمة بين شارة البناء (تنتهي عند y=38) وعنوان الكرت (يبدأ قرب y=115) من دون تداخل.

أمر التحقق: `python tools/check_card_art.py`. الحزمة الحالية لا تغطي 16 من أصل 21 كرتاً؛ يعرض السكربت معرّفاتها بدلاً من أن يفشل العرض داخل اللعبة.

## ملحق: قائمة أحجام الصور المصدرية الحالية

| الأصل | الحجم px |
|---|---:|
| `تنزيل.png` | 832×3456 |
| `blade_drone.png`, `block.png`, `box.png`, `bullet.png`, `E-bullet.png`, `enamyIdle.png`, `tea_full.png`, `underPlayer.png` | 32×32 |
| `bulit anime.png` | 96×128 |
| `coin.png`, `enamy1.png`, `tea_drink.png` | 64×96 |
| `cube.ico` | 32×32 |
| `ChatGPT Image 26 يونيو 2026، 02_02_40 ص.png` | 1254×1254 |
| `enamyRange.png`, `enamyRangeWepaon.png` | 256×256 |
| `gun_will_shoting.png` | 192×256 |
| `gun.png`, `soward.png`, `xp.png`, `Archer/Arrow.png`, `engineer/blade_hit.png` | 64×64 |
| `hero (1).png` | 192×192 |
| `hero.png` | 2048×2048 |
| `knife_animation.png` | 640×640 |
| `sowrd-hit.png`, `underPlayer1.png` | 128×192 / 64×128 |
| `stap_fram.png`, `tea_shop.png` | 384×384 |
| `wepone knife.png` | 128×128 |
| `Archer/Archer_Idle.png` | 1152×192 |
| `Archer/Archer_Run.png` | 768×192 |
| `Archer/Archer_Shoot.png` | 1536×192 |
| `Warrior/Warrior_Attack1.png`, `Warrior/Warrior_Attack2.png` | 768×192 |
| `Warrior/Warrior_Guard.png`, `Warrior/Warrior_Run.png` | 1152×192 |
| `Warrior/Warrior_Idle.png` | 1536×192 |
