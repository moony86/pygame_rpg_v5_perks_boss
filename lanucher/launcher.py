import os
from pathlib import Path
import subprocess
import sys

import requests

VERSION_URL = "https://raw.githubusercontent.com/moony86/BlueCube-Game/refs/heads/main/version.txt"
GAME_EXE_URL = "https://github.com/moony86/BlueCube-Game/releases/latest/download/BlueCubeDemo.exe"

LOCAL_GAME_NAME = "BlueCubeDemo.exe"
LOCAL_VERSION_FILE = "version.txt"


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
LOCAL_GAME_PATH = APP_DIR / LOCAL_GAME_NAME
LOCAL_VERSION_PATH = APP_DIR / LOCAL_VERSION_FILE


def read_local_version():
    if not LOCAL_VERSION_PATH.exists():
        return "0"
    return LOCAL_VERSION_PATH.read_text(encoding="utf-8").strip()


def update_game():
    try:
        print("Checking for updates...")
        response = requests.get(VERSION_URL, timeout=12)
        response.raise_for_status()
        latest_version = response.text.strip()

        local_version = read_local_version()
        if latest_version == local_version and LOCAL_GAME_PATH.exists():
            print("Game is already up to date.")
            return

        print(f"Downloading Blue Cube {latest_version}...")
        download = requests.get(GAME_EXE_URL, timeout=60)
        download.raise_for_status()

        temp_path = LOCAL_GAME_PATH.with_suffix(".exe.download")
        temp_path.write_bytes(download.content)
        os.replace(temp_path, LOCAL_GAME_PATH)
        LOCAL_VERSION_PATH.write_text(latest_version, encoding="utf-8")
        print("Update complete.")

    except Exception as error:
        print(f"Update check failed: {error}")
        if not LOCAL_GAME_PATH.exists():
            print("Error: game executable was not found.")
            return False
    return True


if update_game():
    print("Starting game...")
    subprocess.Popen([str(LOCAL_GAME_PATH)], cwd=str(APP_DIR))
