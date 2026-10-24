# BlueCube — desktop roguelite demo

نسخة تطوير مستقلة عن النسخة السابقة: قتال سريع، أربع هويات بناء، مراحل متفرعة، أصول قابلة للتعديل وLevel Studio. المصدر المعتمد `main.py`، وليس EXE قديمًا.

## التشغيل على جهاز آخر — Windows / Python 3.12

```powershell
git clone --branch codex/bluecube-demo-overhaul --single-branch https://github.com/moony86/pygame_rpg_v5_perks_boss.git
cd pygame_rpg_v5_perks_boss
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

بعد التثبيت شغّل `Play Game.bat` لتجربة اللاعب دون أدوات المطور. لا تثبّت `pygame` القديمة بجانب `pygame-ce` داخل نفس البيئة. `assets/` مضمّن في المستودع ومطلوب للتشغيل.

للتحديث لاحقًا داخل نسخة هذا الفرع:

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### التحكم

WASD للحركة، الماوس للتصويب والإطلاق، Space للقدرة/الداش عند إفلاته، E للتفاعل، Escape للإيقاف، وTab للإحصاءات والخريطة. شاشة How to Play داخل اللعبة مرجع التحكم.

## التطوير والأصول

- جديد: [محرر الهوب والتقدم والبوس](readme/SANCTUARY_AND_PROGRESSION.md). افتح `Level Editor.bat` ثم «محرر الهوب» لرسم الحواجز المخفية وتحريك الشخصيات، بدون تعديل الخلفية أو الكود.
- [تقرير اختبارات البلدات الأربع](readme/PLAYTEST_2026-10-25.md) يوضح النتائج والقيود؛ ليس شهادة توازن بشري أو جاهزية نشر نهائية.

- `Level Editor.bat`: محرر محلي للمراحل والعوائق والبوابات وربط الرسومات والمنطق، يستخدم `.venv` إن وجدت. لا يحتاج Node أو pygbag للتشغيل المعتاد.
- `python main.py` من المصدر يُبقي أدوات التطوير مفعلة افتراضيًا. ضع `BLUECUBE_DEV_TOOLS=0` لتجربة اللاعب.
- [Level Studio](readme/LEVEL_STUDIO.md) · [مكتبة العناصر](readme/OBJECT_LIBRARY.md) · [الأصول والكروت](readme/VISUAL_LIBRARY.md).
- المتصفح QA داخلي اختياري فقط، وليس منصة إصدار معتمدة. تبعياته منفصلة في `tools/internal_web/requirements.txt`.

## التنظيم

```text
main.py, game.py, game_state.py  الدخول والتنسيق العام
settings.py, config.py          إعدادات اللعب وتفضيلات المستخدم
entities/                      اللاعب والأعداء والمقذوفات واللوت
states/                        حالات اللعبة
systems/                       منطق اللعب والعرض وأدوات المطور
definitions/, data/            التعريفات والحوار
ui/                            واجهات اللاعب والمطور
assets/                        الصور والصوت وJSON المراحل والربط البصري
tests/                         فحوص الانحدار والمشغّل الموحد
tools/                         المحرر والقياسات والتوليد وQA الاختياري
readme/                        أدلة الأنظمة
readme/audits/                  تقارير المراجعة التاريخية
readme/design/                  وثيقة التصميم القديمة كمرجع
archive/notes/                 ملاحظات غير مستخدمة أثناء اللعب
```

مخرجات البناء والبيئات واللقطات ونسخ الضبط المحلية مستبعدة من Git. فحص الاستيراد وجد جميع وحدات Runtime مرتبطة بنقطة الدخول، بما فيها وحدات أدوات المطور؛ لم تُنقل أو تُحذف عشوائيًا.

## الاختبارات

```powershell
.\.venv\Scripts\python.exe tests/run_all.py
.\.venv\Scripts\python.exe tools/audit_imports.py
```

كل حزمة تعمل بعملية مستقلة وإعدادات مؤقتة. الصور الناتجة محلية في `debug_screenshots/`. الجولات الآلية والقياسات الطويلة منفصلة: `tools/run_attempt_smoke.py` و`tools/benchmark_game_render.py`.

## حالة النسخة

نسخة للاختبار وليست إعلان جاهزية تجارية. المسدس سلاح البداية المؤقت لكل البلدات، وبدائل الداش القديمة في متجر المعالج ما زالت موجودة. راجع [القيود ومراجعة البلدات](readme/BOSS_ASCENT_AND_BUILD_AUDIT.md).

[تفاصيل التغييرات](CHANGELOG.md) · [بناء Windows](readme/BUILD_GAME.md) · [مصدر الأصول وحدود مراجعة التراخيص](CREDITS.md)

## بناء EXE بنظام مجلد كامل

شغّل `build.bat` بعد تثبيت Python 3.12 x64. يجهّز بيئة بناء منفصلة، ويفحص
المشروع، ثم ينشئ `dist/windows-تاريخ/BlueCube/` باستخدام PyInstaller onedir.
الملف `dist/latest-windows.txt` يدلّك على آخر مجلد ناجح. انسخ المجلد كاملًا،
وليس EXE وحده. راجع [دليل البناء والـHub](readme/HUB_AND_WINDOWS_BUILD.md).
