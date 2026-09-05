import json
import os
from pathlib import Path

PROFILES_DIR = Path.home() / ".config" / "snd3600-scanner" / "profiles"

def get_default_profiles():
    return ["Default", "B&W", "Fuji Superia", "Kodak Gold", "Portra", "Slide Film"]

def load_profiles():
    if not PROFILES_DIR.exists():
        return {}
    profiles = {}
    for f in PROFILES_DIR.glob("*.json"):
        try:
            with open(f, 'r') as fp:
                profiles[f.stem] = json.load(fp)
        except Exception:
            pass
    return profiles

def save_profile(name, params):
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_DIR / f"{name}.json", 'w') as fp:
        json.dump(params, fp, indent=4)
