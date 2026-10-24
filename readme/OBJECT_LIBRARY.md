# مكتبة العناصر — Level Studio

افتح `Level Editor.bat` ثم «العناصر والأصول» أعلى الشاشة. المكتبة منفصلة عن
مواضع المرحلة: تعريف العنصر يحدد صورته وقيمه؛ الغرفة تحدد أين يوضع.

## القيم القابلة للتعديل فعلياً

| العنصر | الاستخدام | الخصائص المرتبطة باللعبة |
|---|---|---|
| hero | الشخصية الرئيسية | الصحة والسرعة الأساسية وحجم الرسم |
| portal | بوابة الـHub والخروج وأبواب المراحل | الصورة وحجم الرسم ونبض التفعيل؛ البوابة المغلقة معتمة |
| pistol | السلاح الأساسي | الضرر، الفاصل بين الطلقات، سرعة الرصاصة، الصورة والحجم |
| sword | سيف ضربة النينجا | ضرر Phantom Step العادي الأساسي، مدى السلسلة، أقصى انتقالات، الصورة والحجم |
| heal_potion | سقوط من الأعداء أو وضع مباشر | علاج صغير/متوسط/كبير، احتمال السقوط، إعادة ظهور النسخة الموضوعة |
| dash_refresh | بلورة اندفاع موضوعة في الغرفة | عدد الشحنات، مدة السرعة والحماية، إعادة الظهور |
| time_stop | سقوط أو وضع مباشر | مدة إيقاف الأعداء، احتمال السقوط، إعادة ظهور النسخة الموضوعة |

المسدس يظل السلاح الوحيد المجهز. لم يُفتح تبديل السيف/السكين ولم يتغير نظام
الكروت إلى نظام جديد. ترقية Phantom Step الأسطورية وبقية الكروت تحتفظ بقيمها
الخاصة؛ المكتبة ليست محرر كروت. سرعة بوست الداش تستخدم معامل Ghost الموجود.

## وضع العناصر واستخدامها

اختر من «العنصر المراد وضعه» بوشن/بلورة اندفاع/وقت، ثم أداة «نقطة مكافأة»
وانقر في الغرفة. يمكن تغيير نوع نقطة موجودة من خصائص العنصر المحدد.
البوشن الموضوع يستخدم مقدار العلاج المتوسط. `respawn = 0` يعني مرة واحدة
في زيارة الغرفة، وليس إعادة ظهور فورية. النقاط الموضوعة تستخدم الجمع باللمس؛
اللووت الساقط يحتفظ بنظام الطيران والمغناطيس الحالي. إعدادات احتمال السقوط
تخص الأعداء فقط، ولا تمنع العنصر الموضوع يدوياً من الظهور.

الموضع يُحفظ مع المرحلة، بينما «حفظ خصائص العناصر» يحفظ المكتبة العامة.
التعديلات تُقرأ عند بدء جولة جديدة أو تشغيل تجربة غرفة جديدة؛ لا تُطبّق
على جولة حية لتجنب تغيير الصحة/الضرر أثناء القتال.

## أصول الصور

كل عنصر يمكن ربطه بملف PNG موجود داخل `assets` من قائمة الملفات، دون تعديل
الكود. انسخ صورتك إلى هذا المجلد، وأعد فتح المكتبة لتظهر في القائمة.
اختر `cell = -1` للصورة المنفردة. القيم 0..5 لأطلس منتظم 3 أعمدة × صفين.
الشفافية مطلوبة للصور المنفردة، وتقص الهوامش الشفافة آلياً عند العرض.
الأبعاد تخص الرسم فقط ولا توسع Hitbox الشخصية أو موضع تصادم الحاجز.
موضع قبضة/فوهة المسدس يظل معايراً لصورة أفقية إلى اليمين داخل مربع 32px؛
تغيير حجم الصورة يقيّس نفس معايرة الفوهة، أما صور بتكوين مختلف فتحتاج معايرة.

- `assets/data/game_objects.json`: التعريفات الفعالة.
- `assets/data/game_objects.defaults.json`: قيم استرجاع عند رفض ملف معطوب.
- `systems/object_catalog.py`: تحقق القيم، التحميل، التخزين المؤقت، الصور.
- الحفظ ذري ومعه نسخة `.json.bak`. المسارات الخارجة عن assets والقيم غير
  المحدودة أو خارج النطاق تُرفض. منطق العناصر قائمة محددة وليست تنفيذ كود من JSON.

## مصدر الفن وطريقة التوليد

الأصول مولّدة بأداة ImageGen المدمجة، وليست رسومات مستطيلات بديلة.
تمت تجربة أطلسين أوليين (`cube_objects_v1/v2`)؛ اكتُشف قص وتداخل عند حدود
الخانات، لذلك جرى توليد كل أصل نهائي كصورة مستقلة، مع الاحتفاظ بمسودات الأطلس.

نص طلب الصورة المستقلة، مع استبدال SUBJECT أدناه حرفياً:

> Extract ONLY SUBJECT from the reference into a standalone game sprite PNG.
> Preserve its original pixel art design and colours. Exactly ONE isolated object
> centred on a genuinely transparent alpha background, generous empty padding,
> no other objects or neighbouring sprite fragments. Remove all broad atmospheric
> background haze. Keep only a tight edge glow. Fully opaque sprite interior.
> No text or labels. Important: This is a single production sprite, NOT an atlas,
> not a grid. Clear silhouette readable at 32 to 64 px.

SUBJECT لكل ملف:

- hero_v1.png: `the blue cube hero in the TOP MIDDLE cell`
- portal_v1.png: `the cyan stone arch portal in the TOP LEFT cell`
- pistol_v1.png: `the silver pistol pointing RIGHT in the TOP RIGHT cell`
- sword_v1.png: `the katana pointing RIGHT in the BOTTOM LEFT cell`
- heal_potion_v1.png: `the green health potion in the BOTTOM MIDDLE cell`
- dash_refresh_v1.png: `the cyan dash crystal with gold lightning medallion in the BOTTOM RIGHT cell`

الصورة المرجعية: `assets/objects/cube_objects_v1.png`، بخلفية شفافة في كل طلب.
