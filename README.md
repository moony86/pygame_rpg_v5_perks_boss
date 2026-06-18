# Blue Cube v5 - Perk Cards + Room Types + Boss Rework

هذه نسخة أكبر من v4 وفيها أنظمة لعب فعلية أكثر:

## الجديد

- إزالة Auto Aim بالكامل.
- Manual Aim + Aim Assist فقط.
- Perk Cards عند كل Level Up: اختر 1 من 3.
- أنواع غرف:
  - Combat
  - Survival
  - Elite
  - Treasure
  - Curse
- قدرة خاصة Q: Dash مع Cooldown وحصانة قصيرة.
- مؤثرات بصرية:
  - Damage Numbers
  - Floating Text
  - Explosion/Ring Effects
  - Projectile Trail
- مؤثرات صوتية مولدة بالكود:
  - Shoot
  - Hit
  - Death
  - Level Up
  - Room Clear
  - Boss Phase
  - Dash
- زعيم بثلاث أنماط:
  - Cone Shot
  - Bullet Ring
  - Leap/Summon
  - Phase 2 عند نصف الدم

## التشغيل

```bash
pip install pygame
python main.py
```

## التحكم

- WASD: حركة
- Mouse: تصويب
- Hold Left Click: إطلاق
- Q: Dash
- E: تفاعل / دخول بوابة
- 1 / 2 / 3: اختيار Perk أو شراء ترقية من NPC
- Enter: بدء / إعادة
- Esc: خروج

## ملاحظة مهمة

الصوتيات هنا مولدة بالكود عبر pygame.sndarray. إذا لم تكن numpy مثبتة سيتم تعطيل الصوت تلقائياً وتشتغل اللعبة بدون مشكلة.
