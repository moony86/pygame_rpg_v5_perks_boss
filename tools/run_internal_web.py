"""Build and serve private browser QA. Nothing is published or deployed."""
import importlib.util
import argparse
import subprocess
import sys
from pathlib import Path

from prepare_internal_web import OUTPUT, ROOT, prepare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if importlib.util.find_spec("pygbag") is None:
        raise SystemExit("Use .internal-web-venv/Scripts/python.exe after installing tools/internal_web/requirements.txt")
    stage = prepare()
    command = [sys.executable, "-m", "pygbag", "--build", "--no_opt", "--title", "BlueCube INTERNAL QA",
               "--icon", str(stage / "assets/blade_drone.png")]
    # Reuse a previously downloaded official template when available.
    templates = sorted(OUTPUT.glob("stage-*/build/web-cache/*.tmpl"))
    if templates:
        command.extend(["--template", str(templates[0])])
    command.append(str(stage))
    log_path = OUTPUT / "build.log"
    with log_path.open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit(f"Internal build failed. See {log_path}")
    print("Private QA build ready. No files have been published.", flush=True)
    if not args.build_only:
        subprocess.run([sys.executable, str(ROOT / "tools/internal_web/server.py"), "--stage", str(stage), "--port", str(args.port)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
