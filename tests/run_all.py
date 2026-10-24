"""Run each regression suite in isolation with disposable user settings."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    suites = [ROOT / 'tests' / 'headless_checks.py',
              *sorted((ROOT / 'tests').glob('check_*.py'))]
    (ROOT / 'debug_screenshots').mkdir(exist_ok=True)
    failures = []
    with tempfile.TemporaryDirectory(prefix='bluecube-tests-') as temporary:
        env = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy',
               'BLUECUBE_SETTINGS_PATH': str(Path(temporary) / 'settings.json')}
        for suite in suites:
            print(f'\n=== {suite.name} ===', flush=True)
            try:
                result = subprocess.run([sys.executable, str(suite)], cwd=ROOT,
                                        env=env, timeout=180)
                if result.returncode:
                    failures.append(suite.name)
            except subprocess.TimeoutExpired:
                failures.append(f'{suite.name} (timeout)')
    print(f'\n{len(suites) - len(failures)}/{len(suites)} suites passed.')
    if failures:
        print('FAILED: ' + ', '.join(failures))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
