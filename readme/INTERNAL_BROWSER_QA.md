# تشغيل المتصفح للفحص الداخلي فقط

هذا ليس إصدار ويب للاعبين ولا نسخة جوال. مصدر اللعبة ونسخة Windows من main.py هما الأصل. لا يوجد نشر أو hosting عام أو تحكم لمس.

## ما الذي تغيّر؟

- Game.run_frame(dt) ينفذ خطوة الإدخال والتحديث والرسم نفسها لكل من desktop وأداة الفحص. main.py وحلقة desktop ما زالا يعملان كالمعتاد.
- tools/internal_web/main.py مدخل asyncio منفصل يستسلم للمتصفح كل إطار، ويعطل أدوات المطور. لا يعدّل صحة اللاعب أو ضرره أو مواضعه لتزوير نتيجة الإدخال.
- tools/prepare_internal_web.py ينسخ فقط مصادر Python المطلوبة وصور/صوت اللعبة إلى مجلد generated جديد. لا ينسخ .git أو التقارير أو EXE القديم أو ملفات شخصية.
- source-manifest.json يسجل hashes للملفات المنسوخة. أي تعديل لاحق يحتاج إعادة التحضير والبناء كي يبقى الفحص مطابقاً للمصدر.
- المخرجات والبيئة والأدلة في .internal-web/ و.internal-web-venv/، وكلاهما مستثنى من Git. بناء سطح المكتب يضم assets وdata فقط؛ أدوات الفحص منفصلة في tools.
- window.__cubeProbe يعرض بيانات قراءة فقط: الحالة والموقع والصحة والسلاح والمقذوفات والأعداء وعدادي الإطلاق والاندفاع. التحكم يأتي من لوحة المفاتيح والماوس في المتصفح.

## الإعداد والتشغيل

من مجلد المشروع، مرة أولى:

```powershell
& 'C:\Users\abdulkrem\AppData\Local\Programs\Python\Python312\python.exe' -m venv .internal-web-venv
& '.\.internal-web-venv\Scripts\python.exe' -m pip install -r tools\internal_web\requirements.txt
```

لتحضير أحدث مصدر وبنائه وفتح خادم loopback محلي:

```powershell
& '.\.internal-web-venv\Scripts\python.exe' tools\run_internal_web.py
```

الخادم على http://127.0.0.1:8766 فقط. Ctrl+C يوقفه. --build-only يبني دون خدمة؛ --port يختار منفذاً آخر. سجل البناء في .internal-web/build.log، وآخر staging في .internal-web/source-manifest.json.

يحتاج أول إعداد تنزيل Pygbag والقالب وملفات Python/WebAssembly الرسمية. خادم الفحص يتضمن مخزناً محلياً محدود المصدر لـhttps://pygame-web.github.io/ حتى يستطيع المتصفح المعزول استخدام ملفات التشغيل. لا يرفع أي ملف للمشروع. بعد التخزين يعيد استخدام الموارد المنزلة.

المتصفح المعزول في هذه الجلسة لم يصل إلى CDN مباشرة، كما أعاد fetch لحزمة اللعبة استجابة فارغة. tools/internal_web/browser_smoke.cjs يعيد نفس استجابات CDN عبر مخزن loopback، ويقدم كامل حزمة اللعبة عبر Playwright route؛ لا يستبدل منطق اللعب ولا يرسم mockup.

مثال باستخدام الأدوات الموجودة على الجهاز:

```powershell
& 'C:\Users\abdulkrem\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' tools\internal_web\browser_smoke.cjs --modules 'C:\Users\abdulkrem\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules' --browser 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

الخيار --url يقبل loopback فقط. الاختبار يفتح جلسة متصفح منفصلة ويغلقها بعد الفحص. الأدلة في .internal-web/evidence/.

## نتيجة التحقق في 23 أكتوبر 2026

أولاً تحكم الوكيل مباشرة عبر المتصفح وشاهد النتيجة بين الإدخالات:

1. فتح القائمة ثم النقر على New Run والوصول إلى HUB.
2. تحريك الشخصية بـW من [960,660] إلى [960,417] والاقتراب من Gatekeeper.
3. إطلاق المسدس بالماوس: shots=2 مع مقذوفات ظاهرة.
4. الضغط E مرتين للدخول إلى ROOM عند [960,540].
5. D مع ضغط/رفع Space: dashes=1 وdash_timer≈0.215، مع تغير الموقع.
6. إيقاف واستئناف القتال بـEscape، ثم إطلاق المزيد؛ ظهرت الأعداء وأرقام الضرر وتحقق قتل في الصورة المحفوظة browser-combat.png. بقيت الصحة الطبيعية 125 دون god mode.

ثانياً أعيد السيناريو باختبار مستقل محفوظ: INTERNAL_BROWSER_SMOKE_OK. يتضمن القائمة، بداية الجولة، الحركة، دخول الغرفة، Dash، الإطلاق مع أعداء، Pause، وEnter للرجوع للقائمة. البيانات في smoke-results.json والصورة في smoke-combat.png.

اجتازت فحوص المصدر headless_checks وعددها 23 مجموعة، وcheck_demo_fixes وعددها 11 اختباراً بعد فصل run_frame.

## حدود الاستخدام

- هذه تجربة تفاعلية قصيرة واختبار قابل للتكرار، وليست إكمال Run أو تقييم توازن كامل.
- المتصفح يتيح الملاحظة والتفاعل المتتابع، لكنه لا يمنح الوكيل ردود فعل بشرية مستمرة.
- runtime المتصفح الذي نزله Pygbag استخدم pygame-ce 2.5.0.dev1 وPython 3.12.2، مقابل pygame-ce 2.5.7 وPython 3.12.7 محلياً. المصدر واحد، لكن أداء/صوت WebAssembly لا يمثل Windows بدقة.
- حلقة الفحص تحد dt بـ50ms لتجنب قفزة محاكاة عند استئناف تبويب متوقف؛ لا تعتمد قياساتها لتحديد FPS أو زمن ضغط عادل للمنافسات.
- ظهور خط بديل أو حدود الصفحة أو نص التحميل خصائص للأداة الداخلية؛ لا نعدل UI سطح المكتب لإرضائها.
- يمكن استخدام ?scene=arena للدخول مباشرة إلى أول غرفة في الاختبار، دون تغيير main.py الخاص بسطح المكتب.
- لوحظ أثناء الفحص تداخل نص بداية الـHub مع صندوق الحوار قرب الأسفل. سُجل للمراجعة اللاحقة؛ هذه الدفعة تختص بإتاحة الرؤية والتحكم فقط.

الخطوة التالية المحددة: اختبار وتحسين إحساس الشخصية بالمسدس، بنفس ساحة القتال والمدخلات، بعد أن أصبحت المشاهدة والتحكم ممكنين.
