"""Stage a fresh private QA copy; never copy the repo or published EXE build."""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".internal-web"
SOURCE_DIRS = ("entities", "systems", "states", "ui", "definitions", "data")
MUSIC = {"hub.ogg", "combat.ogg", "boss.ogg", "boss_01.ogg"}


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    target = OUTPUT / f"stage-{uuid.uuid4().hex[:12]}"
    target.mkdir()
    manifest = {}

    def copy(source, relative):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest[relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()

    for source in ROOT.glob("*.py"):
        if source.name != "main.py":
            copy(source, Path(source.name))
    for directory in SOURCE_DIRS:
        for source in (ROOT / directory).rglob("*.py"):
            copy(source, source.relative_to(ROOT))
    for source in (ROOT / "assets").rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT)
        if source.suffix.lower() not in {".png", ".ico", ".wav", ".ogg", ".json"}:
            continue
        if source.parent.name == "music" and source.name not in MUSIC:
            continue
        copy(source, relative)
    copy(ROOT / "tools" / "internal_web" / "main.py", Path("main.py"))
    (OUTPUT / "source-manifest.json").write_text(json.dumps({
        "internal_test_only": True,
        "stage": str(target),
        "files": manifest,
    }, indent=2), encoding="utf-8")
    print(target)
    return target


if __name__ == "__main__":
    prepare()
