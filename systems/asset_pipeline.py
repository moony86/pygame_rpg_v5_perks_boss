import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import pygame

from settings import DEV_TOOLS_ENABLED
from systems.asset_loader import ASSET_ROOT, asset_load_stats, load_image


ASSET_REPORT_SCHEMA = "bluecube.asset_report.v1"
DEFAULT_REPORT_PATH = Path("asset_report.json")
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".ico", ".wav", ".ogg", ".mp3"}
TEXT_EXTENSIONS = {".py", ".json", ".md", ".txt", ".iss"}


class AssetPipeline:
    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).resolve().parents[1])
        self.assets_root = ASSET_ROOT
        self.assets = []
        self.selected_index = 0
        self.search_text = ""
        self.filter_type = "all"
        self.message = "Asset pipeline ready"
        self.last_scan = 0.0
        self.validation = {
            "missing_assets": [],
            "duplicate_assets": [],
            "unused_assets": [],
            "broken_references": [],
        }
        self.scan()

    def scan(self):
        if not DEV_TOOLS_ENABLED:
            return []
        references = self._find_references()
        load_stats = asset_load_stats()
        assets = []
        if self.assets_root.exists():
            for path in sorted(self.assets_root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in ASSET_EXTENSIONS:
                    continue
                rel = path.relative_to(self.assets_root).as_posix()
                info = self._asset_info(path, rel, references, load_stats.get(rel, load_stats.get(path.name)))
                assets.append(info)
        self.assets = assets
        self.validation = self._validate(assets, references)
        self.last_scan = time.time()
        self.selected_index = min(self.selected_index, max(0, len(self.filtered_assets()) - 1))
        self.message = f"scanned {len(assets)} assets"
        return assets

    def filtered_assets(self):
        assets = self.assets
        if self.filter_type != "all":
            assets = [asset for asset in assets if asset["asset_type"] == self.filter_type]
        if self.search_text:
            query = self.search_text.lower()
            assets = [asset for asset in assets if query in asset["path"].lower()]
        return assets

    def selected_asset(self):
        assets = self.filtered_assets()
        if not assets:
            return None
        self.selected_index = max(0, min(self.selected_index, len(assets) - 1))
        return assets[self.selected_index]

    def select_next(self):
        assets = self.filtered_assets()
        if assets:
            self.selected_index = (self.selected_index + 1) % len(assets)

    def select_previous(self):
        assets = self.filtered_assets()
        if assets:
            self.selected_index = (self.selected_index - 1) % len(assets)

    def set_search(self, text):
        self.search_text = text.strip()
        self.selected_index = 0

    def cycle_filter(self):
        filters = ("all", "image", "audio", "other")
        self.filter_type = filters[(filters.index(self.filter_type) + 1) % len(filters)]
        self.selected_index = 0
        self.message = f"filter {self.filter_type}"

    def reload_selected_asset(self):
        asset = self.selected_asset()
        if asset is None:
            return None
        if asset["asset_type"] == "image":
            image = load_image(asset["path"])
            self.message = f"reloaded {asset['path']}" if image else f"failed reload {asset['path']}"
        else:
            self.message = f"reload not supported for {asset['asset_type']}"
        self.scan()
        return asset

    def reload_all_assets(self):
        count = 0
        for asset in self.assets:
            if asset["asset_type"] == "image":
                load_image(asset["path"])
                count += 1
        self.scan()
        self.message = f"reloaded {count} images"
        return count

    def open_folder(self):
        asset = self.selected_asset()
        if asset is None:
            return None
        folder = str(Path(asset["absolute_path"]).parent)
        try:
            os.startfile(folder)
            self.message = f"opened {folder}"
        except OSError as error:
            self.message = f"open failed: {error}"
        return folder

    def copy_asset_path(self):
        asset = self.selected_asset()
        if asset is None:
            return None
        path = asset["absolute_path"]
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, path.encode("utf-8"))
            self.message = "asset path copied"
        except pygame.error:
            self.message = path
        return path

    def dependencies_for_selected(self):
        asset = self.selected_asset()
        if asset is None:
            return []
        return list(asset["references"])

    def report(self):
        return {
            "schema": ASSET_REPORT_SCHEMA,
            "generated_at": time.time(),
            "asset_root": str(self.assets_root),
            "asset_count": len(self.assets),
            "assets": self.assets,
            "validation": self.validation,
        }

    def export_report(self, path=DEFAULT_REPORT_PATH):
        export_path = Path(path)
        export_path.write_text(json.dumps(self.report(), indent=2), encoding="utf-8")
        self.message = f"exported {export_path}"
        return export_path

    def _asset_info(self, path, rel, references, stats):
        size = path.stat().st_size
        asset_type = self._asset_type(path)
        resolution = None
        broken = False
        if asset_type == "image":
            try:
                resolution = pygame.image.load(str(path)).get_size()
            except (pygame.error, OSError):
                broken = True
        return {
            "path": rel,
            "absolute_path": str(path),
            "asset_type": asset_type,
            "resolution": resolution,
            "memory_bytes": self._memory_bytes(path, resolution),
            "file_bytes": size,
            "load_count": stats.get("load_count", 0) if stats else 0,
            "last_loaded": stats.get("last_loaded") if stats else None,
            "references": references.get(rel, []) + references.get(path.name, []),
            "broken": broken,
        }

    def _validate(self, assets, references):
        asset_paths = {asset["path"] for asset in assets}
        asset_names = defaultdict(list)
        for asset in assets:
            asset_names[Path(asset["path"]).name.lower()].append(asset["path"])
        duplicate_assets = [paths for paths in asset_names.values() if len(paths) > 1]
        referenced = set(references)
        missing_assets = sorted(ref for ref in referenced if ref not in asset_paths and not (self.assets_root / ref).exists())
        unused_assets = sorted(asset["path"] for asset in assets if not asset["references"])
        broken = sorted(asset["path"] for asset in assets if asset["broken"])
        return {
            "missing_assets": missing_assets,
            "duplicate_assets": duplicate_assets,
            "unused_assets": unused_assets,
            "broken_references": broken,
        }

    def _find_references(self):
        references = defaultdict(list)
        pattern = re.compile(r"[\"']([^\"']+\.(?:png|jpg|jpeg|bmp|gif|ico|wav|ogg|mp3))[\"']", re.IGNORECASE)
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if any(part in {".git", "__pycache__", "dist", "build"} for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    text = path.read_text(encoding="latin-1")
                except UnicodeDecodeError:
                    continue
            for match in pattern.findall(text):
                rel = match.replace("\\", "/")
                if rel.startswith("assets/"):
                    rel = rel[len("assets/"):]
                references[rel].append(str(path.relative_to(self.root)))
        return references

    def _asset_type(self, path):
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".ico"}:
            return "image"
        if suffix in {".wav", ".ogg", ".mp3"}:
            return "audio"
        return "other"

    def _memory_bytes(self, path, resolution):
        if resolution is None:
            return path.stat().st_size
        return resolution[0] * resolution[1] * 4
