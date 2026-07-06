| اسم الكرت | الملف/المصدر | التأثير الحالي | ينتمي إلى | رقم فقط أم هوية؟ | القرار | ملاحظة |
|---|---|---|---|---|---|---|
| rapid_fire | definitions/perk_definitions.py | +0.30 fire_rate؛ legendary +0.55 fire_rate | Gunslinger | هوية | يبقى كما هو | يدعم إطلاق النار المستمر |
| heavy_rounds | definitions/perk_definitions.py | +14 damage و -0.10 fire_rate؛ legendary +32 damage و +0.12 fire_rate | Gunslinger | رقم | يحتاج إعادة تصميم | التأثير الحالي أرقام مع tradeoff |
| power_core | definitions/perk_definitions.py | +12 damage؛ legendary +35 damage | لا ينتمي | رقم | يُدمج مع: heavy_rounds | زيادة ضرر مباشرة فقط |
| hollow_point | definitions/perk_definitions.py | +20 damage و pierce=0؛ legendary +45 damage و +0.25 crit_multiplier | Gunslinger | هوية | يبقى كما هو | يحدد أسلوب رصاصة ثقيلة بلا اختراق |
| glass_cannon | definitions/perk_definitions.py | +25 damage و -40 max_health؛ legendary +60 damage و -40 max_health | Ninja | هوية | يبقى كما هو | خطر مقابل ضرر قريب من فلسفة اللعب الخطر |
| split_shot | definitions/perk_definitions.py | +1 projectile و +spread؛ legendary +1 projectile و +0.25 split_damage_multiplier | Gunslinger | هوية | يبقى كما هو | يحقق امتلاء الغرفة بالرصاص |
| needle_rounds | definitions/perk_definitions.py | +1 pierce؛ legendary +3 pierce و +8 damage | Gunslinger | هوية | يبقى كما هو | يدعم اختراق المقذوفات |
| kinetic_rounds | definitions/perk_definitions.py | +8 damage و +70 projectile_speed؛ legendary +24 damage و +180 projectile_speed | Gunslinger | رقم | يحتاج إعادة تصميم | يجمع رقم ضرر مع سرعة مقذوف |
| critical_spark | definitions/perk_definitions.py | +0.30 crit_chance؛ legendary +0.80 crit_chance و +0.35 crit_multiplier | Gunslinger | رقم | يحتاج إعادة تصميم | crit الحالي أرقام ضرر فقط |
| overclock | definitions/perk_definitions.py | +0.40 fire_rate و -15 max_health؛ legendary +0.70 fire_rate و skill cooldown x0.80 | Gunslinger | هوية | يبقى كما هو | يدعم إيقاع إطلاق عالي مع مخاطرة |
| explosive_rounds | definitions/perk_definitions.py | explosive_rounds=True و -0.15 fire_rate؛ legendary +0.15 fire_rate و +10 damage | لا ينتمي | هوية | يحتاج إعادة تصميم | لا يطابق أي هوية رسمية حاليًا |
| impact_drive | definitions/perk_definitions.py | +0.45 knockback_power؛ legendary +1.20 knockback_power و +8 damage | لا ينتمي | هوية | يحتاج إعادة تصميم | دفع المقذوفات أداة بلا هوية رسمية |
| vital_core | definitions/perk_definitions.py | +48 max_health و heal 24؛ legendary +110 max_health و full heal | Vampire | رقم | يحتاج إعادة تصميم | صحة مباشرة لا تعبر عن التغذي من القتال |
| battle_recovery | definitions/perk_definitions.py | +24 regen_on_room_clear؛ legendary +70 regen و +35 max_health و heal 35 | Vampire | هوية | يبقى كما هو | sustain بعد القتال وليس أثناءه |
| second_wind | definitions/perk_definitions.py | +20 max_health و +10 regen؛ legendary +55 max_health و +30 regen و heal 40 | Vampire | هوية | يُدمج مع: battle_recovery | يتداخل مع شفاء نهاية الغرفة |
| scout_boots | definitions/perk_definitions.py | +30 speed؛ legendary +70 speed و reset dash cooldown | Ninja | هوية | يبقى كما هو | يدعم الحركة والداش |
| phantom_step | definitions/perk_definitions.py | +20 speed و -20 max_health؛ legendary +50 speed و +0.20 dash_invuln_bonus | Ninja | هوية | يبقى كما هو | سرعة مع مخاطرة واضحة |
| damage | definitions/upgrade_definitions.py | shop: +5 damage لكل مستوى؛ max 6 | لا ينتمي | رقم | يُدمج مع: power_core | ترقية ضرر مباشرة فقط |
| pierce | definitions/upgrade_definitions.py | shop: +1 pierce لكل مستوى؛ max 3 | Gunslinger | هوية | يُدمج مع: needle_rounds | يكرر مسار الاختراق |
| firerate | definitions/upgrade_definitions.py | shop: +0.12 fire_rate لكل مستوى؛ max 4 | Gunslinger | هوية | يُدمج مع: rapid_fire | يكرر مسار سرعة الإطلاق |
| weapon_double | definitions/upgrade_definitions.py | shop: weapon_damage_multiplier=2.0؛ max 1 | Gunslinger | رقم | يحتاج إعادة تصميم | مضاعف ضرر عام |
| explosive_rounds | definitions/upgrade_definitions.py | shop: explosive_rounds=True؛ max 1 | لا ينتمي | هوية | يُدمج مع: explosive_rounds | يكرر نفس مفتاح البيرك |
| knockback | definitions/upgrade_definitions.py | shop: +0.55 knockback_power لكل مستوى؛ max 4 | لا ينتمي | هوية | يُدمج مع: impact_drive | يكرر دفع المقذوفات |
| heal | definitions/upgrade_definitions.py | shop: heal 45 | Vampire | رقم | يحتاج إعادة تصميم | شفاء مباشر وليس lifesteal |
| maxhp | definitions/upgrade_definitions.py | shop: +18 max_health و heal 18 لكل مستوى؛ max 6 | Vampire | رقم | يُدمج مع: vital_core | يكرر مسار الصحة |
| regen | definitions/upgrade_definitions.py | shop: +12 regen_on_room_clear لكل مستوى؛ max 4 | Vampire | هوية | يُدمج مع: battle_recovery | يكرر شفاء نهاية الغرفة |
| skill_blast | definitions/upgrade_definitions.py | shop: active_skill='blast' | Ninja | هوية | يحتاج إعادة تصميم | دفع قريب لكنه ليس dash واضح |
| skill_surge | definitions/upgrade_definitions.py | shop: active_skill='surge' | Gunslinger | هوية | يبقى كما هو | يدعم اندفاع إطلاق النار |
| skill_ghost | definitions/upgrade_definitions.py | shop: active_skill='ghost' | Ninja | هوية | يبقى كما هو | يدعم المراوغة والحركة |

1. عدد الكروت المصنفة "رقم فقط": 10.
2. عدد الكروت المقترح دمجها: 9 (power_core مع heavy_rounds، second_wind مع battle_recovery، damage مع power_core، pierce مع needle_rounds، firerate مع rapid_fire، explosive_rounds shop مع explosive_rounds perk، knockback مع impact_drive، maxhp مع vital_core، regen مع battle_recovery).
3. عدد الكروت التي لا تنتمي لأي Build رسمي: 6.
