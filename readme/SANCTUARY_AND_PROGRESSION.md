# محرر الهوب وتصاعد التحدي — 2026-10-25

## فتح المحرر

شغّل `Level Editor.bat` ثم اضغط **محرر الهوب** في الشريط العلوي. المحرر محلي فقط، ولا يحتاج حسابًا أو Node للتشغيل العادي. لا تشغّل نسختين على المنفذ نفسه. مكتبة الأصول والمراحل تبقى كما هي.

- اسحب لرسم حاجز مستطيل مخفي، أو اختر المضلع وانقر زواياه ثم Enter. Escape يلغي الرسم.
- اختر شخصية من القائمة أو جسمها في المشهد واسحبها. الإحداثيات قابلة للكتابة؛ الأسهم خطوة 1px وShift+الأسهم 10px. توجد محاذاة حرة/8/16px.
- موضع الشخصية هو أعلى يسار جسمها 46×46، والرسم مثبت عند القدمين. لتوسيطها أفقيًا اجعل X=937؛ نقطة ظهور اللاعب تستخدم المركز، فتوسيطها X=960. رسم البوابة مستقل عن نقطة تفاعلها.
- Delete يحذف الحاجز فقط؛ الشخصيات الأساسية لا تحذف بالخطأ. التراجع والإعادة يحتفظان حتى 80 خطوة.
- أخفِ طبقة التصادم لتراجع الفن. اختبار المشي داخل المحرر بـWASD معاينة تقريبية؛ «حفظ وتجربة» يشغّل اللعبة المكتبية الفعلية، وهو المرجع النهائي للحركة والداش.
- الحفظ يفحص الحدود ونقطة الظهور وأجسام الشخصيات ومسار الوصول لكل تفاعل. الفحص محافظ، وقد يرفض ممرًا ضيقًا لا يناسب جسم اللاعب.
- الحفظ ذري إلى `assets/data/hub.json`، مع ملف `.json.bak` سابق. التعديلات تُحمّل عند دخول الهوب مجددًا؛ لا تعدل صورة الخلفية.
- المضلعات تتحول وقت التحميل إلى مستطيلات تصادم بدقة محافظة 8px، وتستخدم نظام التصادم نفسه للمشي والداش.

**خلفية الهوب والمواضع والحواجز القديمة لم تتغير في هذا التحديث.** رسم الحدود الدقيقة حول المياه والجدران قرار ترك للمطور حسب طلبه؛ بناء الديمو لا يحتوي تلقائيًا خريطة حواجز جديدة قبل حفظها من المحرر وإعادة البناء.

## مسار البوس

المطلوب افتراضيًا تحرير جميع الغرف التي تحتوي موجات قتال، وليس غرف الكنز أو ممر العبور. التقدم يظهر بعد تحرير الغرفة، والعرّاف يشرح الشرط. بعد تحقيقه تظهر بوابة مميزة داخل الغرفة المحررة الحالية، ويمكن الرجوع لها من أي غرفة محررة أخرى. E أولًا للتنبيه، ثم E ثانية خلال خمس ثوانٍ للدخول. الأبواب العادية لا تدخل البوس.

مكان حلبة البوس في ملف المرحلة لا يعود نقطة دخول ثابتة؛ مكانها القديم ممر عبور بلا استدعاء كنز أو مكافأة إضافية. الحلبة الأصلية نفسها تستخدم للمواجهة المنفصلة. هذا يحافظ على الفروع التي كانت تمر عبر موقع البوس القديم.

## إعدادات التحدي

`assets/data/progression.json`:

- الصعوبة = 1 + عمق المسار × 0.42 + غرف القتال المحررة × 0.12، بحد 3.8.
- لا تقرأ DPS اللاعب أو كروته لمطابقة قوته. الغرفة الأولى تبقى نقطة البداية، والمتانة وسلوك العدو يستفيدان من نظام difficulty الموجود.
- ضرر التلامس محدود بمعامل 1.85. لا يضمن هذا أن المقذوفات أو كل مهارة تتبع المعامل نفسه؛ لكل هجمة منطقها.
- `required_combat_fraction=1.0` يعني كل غرف القتال لفتح البوس. تغيير الملف يحتاج إعادة تشغيل/بناء، وليس ضبطًا سريًا أثناء الجولة.

`assets/data/boss_trial.json`:

- تقليل الانتظار بين الهجمات وتحريك البوس خلال الاستعداد وجزء من التعافي. سرعة الاقتراب تتصاعد بين الفيزات، مع إبقاء قفل اتجاه الإنذار في آخر 350ms.
- انفجار شعاعي ذو ممرات هروب متقابلة، ومتابعة مؤجلة في الفيزات المتأخرة.
- الاستدعاء 5 ثم 6 أعداء من تشكيلة أقوى، وليس 10 متراكبين من أقوى نوع. الاستدعاء محدود بزمن لمنع تعليق الجولة.
- تورّتان مؤقتتان غير قابلتين للاستهداف، غير صلبتين، بمقذوفات بطيئة وإنذار اتجاه ثابت. تدومان 12 ثانية، وتنتهيان عند انتقال الفيز؛ ليستا أعداء يجب قتلهم ولا مصدر XP/ذهب. شريط صغير يوضح زمنهما المتبقي.
- التورّات والمتابعة تتوقف مع Time Stop والـPause. لا زيادة في HP البوس أو مدة حصانته.

## الأصول والتفاعلات

التورّت `assets/visuals/boss_turret_v1.png` ومؤثر السرعة `assets/visuals/speed_wake_v1.png` صورتان PNG شفافّتان مولدتان بأداة ImageGen المدمجة. ربطهما في `assets/data/visual_defaults.json` باسمَي `boss_turret` و`fx_speed_wake`، ويمكن تعديلهما عبر مكتبة الأصول. صور الوحوش اللونية لم تتغير.

الشاهي يوضح زر T ويعمل كتفاعل هادئ وأنيميشن، **وليس ترقية قتال جديدة**. الحداد والمعالج يحتفظان بالوظائف الفعلية الحالية، والعرّاف يشرح نظام فتح البوس. لم نفرض إعادة تصميم اقتصادية كاملة لوظائف الشخصيات ضمن هذا المرور.

### Generation prompts — built-in ImageGen, transparent originals preserved

Turret:

```text
Use case: stylized-concept. Asset type: standalone top-down action roguelite enemy turret sprite on genuinely transparent background. Primary request: one original immovable magical fortress turret, dark slate and steel pedestal with four small angular feet and a red-orange glowing core, squat barrel directed toward lower left. Style: polished crisp pixel art consistent with a blue-cyan dark dungeon game, isometric three-quarter top-down view, readable at 72 pixels. Single isolated object fully visible with generous transparent margins, no scene, no floor, no text, no circles around it, no logos, no trademark. Menacing red accents distinguish enemy from blue player. This is the new timed boss-phase turret.
```

Speed wake:

```text
Use case: stylized-concept. Asset type: one reusable game speed-boost VFX sprite, actual transparent background. Primary request: a compact cluster of three cyan-blue magical wind streaks sweeping backward toward upper right, luminous icy shards and tapering wisps around an EMPTY center where a small cube character will be drawn. Pixel-art dungeon roguelite style, crisp shapes visible at 90 pixels. Single isolated effect, no character, no floor, no ring, no concentric circles, no lettering or logos, no background. Dynamic directional speed wake, restrained glow. Square framing.
```
