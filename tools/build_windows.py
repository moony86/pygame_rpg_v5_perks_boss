"""Versioned Windows onedir builds. No onefile mode, no deletion of old builds."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-tests', action='store_true', help='Local iteration only; recorded in manifest')
    args = parser.parse_args()
    if sys.platform != 'win32' or sys.version_info[:2] != (3, 12) or sys.maxsize < 2**32:
        raise SystemExit('Build on Windows with Python 3.12, using requirements-build.txt.')
    if importlib.metadata.version('pyinstaller') != '6.21.0':
        raise SystemExit('Install requirements-build.txt in this build environment first.')
    required = sum(p.stat().st_size for p in (ROOT / 'assets').rglob('*') if p.is_file()) * 2 + 100 * 1024**2
    if shutil.disk_usage(ROOT).free < required:
        raise SystemExit(f'Not enough free disk space; reserve at least {required // 1024**2} MiB before building.')
    if not args.skip_tests:
        subprocess.run([sys.executable, str(ROOT / 'tests/run_all.py')], cwd=ROOT, check=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    output = ROOT / 'dist' / f'windows-{stamp}'
    if output.exists():
        raise SystemExit('This output already exists; wait one second and retry.')
    work = ROOT / 'build' / f'windows-{stamp}'
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir',
               '--windowed', '--name', 'BlueCube', '--contents-directory', '_internal',
               '--icon', str(ROOT / 'assets/cube.ico'), '--distpath', str(output),
               '--workpath', str(work / 'work'), '--specpath', str(work),
               '--add-data', f'{ROOT / "assets"};assets',
               '--add-data', f'{ROOT / "data"};data', str(ROOT / 'main.py')]
    subprocess.run(command, cwd=ROOT, check=True)
    bundle = output / 'BlueCube'
    for name in ('CREDITS.md', 'RIGHTS_AND_NOTICES.md'):
        shutil.copy2(ROOT / name, bundle / name)
    shutil.copy2(ROOT / 'readme/WINDOWS_PLAYER_README.txt', bundle / 'READ_ME_FIRST.txt')
    notices = bundle / 'licenses'
    notices.mkdir()
    # Preserve license material installed with each redistributed dependency.
    for package in ('pygame-ce', 'pyinstaller'):
        dist = importlib.metadata.distribution(package)
        for relative in dist.files or ():
            if any(token in str(relative).lower() for token in ('license', 'copying', 'copyright', 'lgpl')):
                source = Path(dist.locate_file(relative))
                if source.is_file():
                    destination = notices / package / str(relative).replace('..', '_up_')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license, notices / 'PYTHON-LICENSE.txt')
    report = bundle / 'smoke-test.json'
    subprocess.run([str(bundle / 'BlueCube.exe'), '--smoke-test', '--smoke-report', str(report)],
                   cwd=bundle, check=True, timeout=180)
    if not json.loads(report.read_text(encoding='utf-8')).get('ok'):
        raise SystemExit(f'Frozen smoke failed: {report}')
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        source_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision = 'unknown'
        source_dirty = True
    files = {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in bundle.rglob('*') if p.is_file()}
    manifest = {'built_at_utc': stamp, 'source_commit': revision, 'source_may_have_uncommitted_changes': source_dirty,
                'mode': 'onedir', 'python': sys.version, 'pyinstaller': '6.21.0',
                'regression_tests_run': not args.skip_tests, 'frozen_smoke_passed': True,
                'files_sha256': files}
    (bundle / 'build-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Small locator; the actual distribution always stays a full directory.
    (ROOT / 'dist/latest-windows.txt').write_text(str(bundle), encoding='utf-8')
    print(f'\nONEDIR READY: {bundle}\nCopy the ENTIRE BlueCube folder, not just its EXE.')


if __name__ == '__main__':
    main()
