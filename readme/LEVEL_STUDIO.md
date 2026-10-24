# Cube Level Studio — محرر المراحل

## التشغيل

اضغط مرتين على `Level Editor.bat` في مجلد المشروع. يتطلب Python 3.12 وبيئة
المشروع التي تحتوي pygame-ce. تفتح أداة محلية عند `http://127.0.0.1:8770`.
هذه واجهة تطوير محلية، وليست نسخة متصفح من اللعبة ولا خدمة منشورة.
أغلق نافذة الأوامر عند الانتهاء لإيقاف الخادم. إذا كان المنفذ مشغولاً:

```powershell
py -3.12 tools/level_editor.py --port 8771
```

## تصميم المرحلة بلا تعديل الكود

1. اختر الغرفة من القائمة. كل غرفة لها اسم ونوع وزعيم اختياري ومكافآت.
2. «رسم حاجز»: اسحب على المشهد. «تحديد/سحب»: حرّكه، أو اسحب المقبض الأخضر
   أسفل اليمين لتغيير حجمه. يمكن ضبط X/Y/العرض/الارتفاع بالأرقام أيضاً.
3. اسحب الأبواب على حافتها. الأبواب هي أيضاً مصادر ظهور الأعداء.
4. أضف نقاط المكافآت بأداة النقطة. هي نقاط نظام movement pickups الحالي،
   وليست تحديداً لنوع عنصر جديد.
5. جدول الظهور: حدّد الوقت بالثواني والباب ونوع العدو. انقر صفاً لتعديله،
   أو × لحذفه. ظهور الزعيم مستقل عبر مربع «غرفة الزعيم».
6. افتح «مسار المرحلة». اسحب الغرف على الشبكة؛ التجاور الأفقي/العمودي
   ينشئ اتصالاً ثنائي الاتجاه تلقائياً. البداية ثابتة عند (0,0).
   يمكن إضافة/حذف غرف (2–32)، ويجب وجود زعيم واحد ومسار متصل.
7. «فحص» يكشف أخطاء البيانات، تداخل الحواجز، سد الأبواب ونقطة البداية،
   المكافآت داخل الحواجز، وفصل الأبواب عن الوسط على شبكة ملاحة 40px.
   هذه فحوص هندسية تقريبية وليست ضماناً لتوازن المرحلة أو سهولتها.
8. «حفظ للعبة» يعتمد الملف في الجولات الجديدة. «حفظ وتجربة الغرفة» يفتح
   **اللعبة المكتبية الفعلية** عند الغرفة المختارة. لا يعيد بناء EXE.

Ctrl+Z تراجع، Ctrl+Y إعادة، Ctrl+S حفظ عندما لا يكون التركيز داخل حقل،
Delete حذف العنصر المحدد. تصدير/استيراد JSON لنقل مراحل أو حفظ نسخ منفصلة.
الحذف والاستعادة قابلان للتراجع قبل إغلاق المحرر.

## الملفات والتكامل

- `assets/levels/stage_one.json`: المرحلة المعتمدة، 1920×1080 بكسل لكل غرفة.
- ملف `.json.bak` يحتفظ بالحفظ السابق، والحفظ استبدال ذري بعد التحقق.
- `systems/stage_document.py`: المخطط والتحقق والتحويل إلى StageRoom/StageMapNode.
- عند عدم وجود الملف أو رفضه، تستخدم اللعبة التوليد السابق وتطبع سبب الرفض.
- `BLUECUBE_STAGE_FILE` يمكن أن يحدد ملف مرحلة مختلفاً للاختبار.
- المسارات الحالية متجاورة تلقائياً، دون بوابات بعيدة أو روابط أحادية الاتجاه.
- لا يشمل هذا المحرر سكربتات قصصية أو تصميم أنيميشن أو تغيير منطق العدو.
- يتطلب بناء EXE لاحقاً تضمين مجلد assets كاملاً، بما فيه levels وenvironment.

## الفن

`assets/environment/cube_dungeon_atlas_v1.png` أصل PNG مولّد بأداة ImageGen
المدمجة، محفوظ في المشروع. لم تُنزّل أصول تجارية أو تُستبدل الصور القديمة.
تستخدم الأرضية الربع العلوي الأيسر، والحواجز الربع العلوي الأيمن مع nine-slice،
والجدار شريطاً من الربع السفلي الأيسر. الربع الرابع محفوظ للمراجعة الفنية.
التصادم هو مستطيل الحاجز كما يظهر في المحرر؛ الظل تجميلي فقط.
أرضية المعركة مخزنة مؤقتاً لتجنب إعادة تركيبها كل إطار. الـHub لم يتغير.

### نص التوليد المستخدم (built-in ImageGen)

Use case: stylized-concept. Asset type: production game environment texture atlas
for a top-down pixel art action roguelite with a bright blue cube hero. Generate
a square 1024x1024 PNG atlas, exact 2 by 2 grid of four 512x512 square tiles,
no gutters, no text. Top-left: seamless dark desaturated blue slate dungeon floor,
subtle large rectangular stone slabs, very low contrast, uncluttered, no objects.
Top-right: single solid rectangular raised charcoal stone cover block filling
tile edge to edge, bevelled cool slate top and thick darker southern front face,
small blue inlaid details, readable silhouette, fully opaque square. Bottom-left:
horizontal dungeon perimeter parapet tile filling square, layered carved dark
stone rim with subtle teal inlay, top down orthographic. Bottom-right: corner
junction of matching dark stone perimeter, readable stone bevel, subtle weathering.
Consistent crisp hand-placed pixel-art look, limited palette navy charcoal slate
muted teal, lighting upper left. No characters, no weapons, no grid overlays,
no UI, no perspective tilt, no letters, no watermark. Designed to be sampled as
texture tiles in a playable game, NOT a screenshot or mockup. Keep decorative
contrast restrained so bullets/enemies are prominent.

المولّد أخرج 1254×1254 بدلاً من المقاس المطلوب؛ التحميل يحسب الأرباع من
حجم الصورة الفعلي. جميع أجزاء العرض مشتقة من الصورة، وليست مستطيلات بديلة.
