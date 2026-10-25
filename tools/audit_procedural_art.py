"""Reproducible inventory, not a claim that every call is visible at runtime."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = []
for folder in ('', 'entities', 'systems', 'ui'):
    paths = ROOT.glob('*.py') if not folder else (ROOT / folder).rglob('*.py')
    for path in sorted(paths):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for method in ast.walk(tree):
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)
                     and ast.unparse(node.func).startswith('pygame.draw.')]
            if calls:
                rows.append((path.relative_to(ROOT).as_posix(), method.name,
                             ', '.join(str(node.lineno) for node in calls)))
header = '''# جرد الرسم البرمجي

## ما حُوّل في هذه الدفعة

| العنصر | رابط الأصل | المصدر القابل للتحرير |
|---|---|---|
| شحن الداش | fx_dash_charge | assets/visuals/dash_charge.svg |
| تحديد Airstrike | fx_airstrike_target | assets/visuals/airstrike_target.svg |
| ظهور رمز إيقاف الزمن | fx_time_sigil | assets/visuals/time_sigil.svg |
| هالة Feast / Blood Moon | fx_vampire_aura | إعادة استخدام ring.png بلون مستقل |

اللعبة تقرأ نسخ PNG، والمصادر SVG قابلة للتعديل. شغّل tools/bake_sigil_assets.py بعد تعديل SVG.
الربط في assets/data/visual_defaults.json، ويظهر ضمن كتالوج العناصر في المحرر.
التحريك والشفافية والتدوير تظل برمجية؛ لم تتغير مدد المهارات أو الضرر.

## التصنيف والقرار

- إبقاء برمجي: تقدم الصحة/الخبرة/التبريد، الخريطة وخطوط اتصالها، حدود نطاق الإصابة الدقيقة، أدوات التطوير والتحديد، النصوص والتظليل العام للشاشة.
- احتياطي: جسم اللاعب والسلاح والمرافقون وبعض الأعداء عند غياب صورهم. وجود draw لا يعني ظهور شكل بدائي في التشغيل الطبيعي. لا نحذف مسارات الأمان عشوائيًا.
- يحتاج متابعة فنية: زخرفة موجة إيقاف الزمن وحوافها، بعض إشارات الهجوم والنطاقات، ومؤثرات فرعية في الحالات الخاصة. لم تُحوّل كل هذه العناصر في هذه الدفعة.
- هجين مقصود: صور المقذوفات والأشباح والانفجارات تتحرك وتتلاشى وتتمدد بالكود؛ هذا لا يجعلها رسومات مؤقتة.

## القائمة الكاملة لاستدعاءات pygame.draw داخل مجلدات التشغيل

هذه قائمة آلية بالمواقع، لا تصنيف مؤكد لظهورها. تُستثنى أدوات التطوير والاختبارات خارج مجلدات التشغيل. يمكن إعادة توليدها بعد كل تعديل.

| الملف | الدالة | الأسطر |
|---|---|---|
'''
target = ROOT / 'docs' / 'procedural-art-audit.md'
target.parent.mkdir(exist_ok=True)
target.write_text(header + '\n'.join(f'| {p} | {m} | {lines} |' for p, m, lines in rows) + '\n', encoding='utf-8')
print(f'{len(rows)} drawing functions inventoried: {target}')
