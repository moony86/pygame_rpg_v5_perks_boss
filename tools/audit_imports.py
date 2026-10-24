"""Read-only local import audit; unreachable does not mean safe to delete."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('entities', 'systems', 'states', 'ui', 'definitions', 'data')


def main():
    sources = list(ROOT.glob('*.py'))
    for package in (*PACKAGES, 'tools', 'tests'):
        sources.extend((ROOT / package).rglob('*.py'))
    modules = {p.relative_to(ROOT).with_suffix('').as_posix().replace('/', '.'): p
               for p in sources}
    edges = {}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
                imports.update(f'{node.module}.{alias.name}' for alias in node.names)
        edges[name] = imports & modules.keys()
    reachable, pending = set(), ['main']
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        pending.extend(edges.get(name, ()))
    candidates = sorted(name for name in modules if name.split('.')[0] in PACKAGES
                        and name not in reachable and not name.endswith('.__init__'))
    print(f'Parsed {len(modules)} modules; {len(reachable)} reachable from main by static imports.')
    print('Runtime modules not statically reached (review dynamic/editor use before moving):')
    for name in candidates:
        print(name)


if __name__ == '__main__':
    main()
