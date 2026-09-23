"""Create a tablet import package, reading the laptop files without changing them."""
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(__file__).resolve().parent / "Medienpaket.zip"
EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".jpg", ".jpeg", ".png", ".webp", ".mp4"}


def collect(root=ROOT):
    settings_path = Path(os.environ.get("LOCALAPPDATA", str(root))) / "Tormentor" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8-sig")) if settings_path.is_file() else {}
    audio = {
        "Rätsel": [root / "sound" / f"Rätsel{i}.mp3" for i in (1, 2)],
        "Taverne": [root / "sound" / f"tavern{i}.mp3" for i in range(1, 5)],
        "Dungeon": [root / "sound" / f"Dungeon{i}.mp3" for i in (1, 2)],
        "Wald": [root / "sound" / f"Wald{i}.mp3" for i in range(1, 4)],
        "Höhle": [root / "sound" / f"Höhle{i}.mp3" for i in range(1, 4)],
        "Bosskampf": [root / "sound" / f"Bossfight{i}.mp3" for i in range(1, 5)],
    }
    backgrounds = {name: {"type": "folder", "path": str(root / "assets" / "videos" / folder)} for name, folder in
                   [("Rätsel", "ratsel"), ("Taverne", "taverne"), ("Dungeon", "dungeon"), ("Wald", "wald"), ("Höhle", "hoehle"), ("Bosskampf", "bosskampf")]}
    # Existing user-managed category maps take precedence, including deleted defaults.
    audio = settings.get("sounds", audio)
    backgrounds = settings.get("backgrounds", backgrounds)
    sources, scenes, missing = [], [], []
    for name in dict.fromkeys([*audio, *backgrounds]):
        paths = [Path(p) for p in audio.get(name, [])]
        info = backgrounds.get(name, {})
        if info.get("path"):
            path = Path(info["path"])
            if not path.is_absolute():
                path = root / path
            if info.get("type") == "folder":
                paths.extend(sorted(path.iterdir()) if path.is_dir() else [])
                if not path.is_dir():
                    missing.append(str(path))
            else:
                paths.append(path)
        items = []
        seen = set()
        for path in paths:
            if not path.is_absolute():
                path = root / path
            if path.suffix.lower() not in EXTENSIONS or path in seen:
                continue
            seen.add(path)
            if not path.is_file():
                missing.append(str(path))
                continue
            archive_path = f"media/{len(sources):05d}{path.suffix.lower()}"
            items.append({"name": path.name, "path": archive_path})
            sources.append((path, archive_path))
        scenes.append({"name": name, "items": items})
    return {"version": 1, "scenes": scenes}, sources, missing


def main():
    manifest, sources, missing = collect()
    temp = OUTPUT.with_suffix(".zip.partial")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
        for path, archive_path in sources:
            print(f"Kopiere: {path.name}", flush=True)
            archive.write(path, archive_path)
    temp.replace(OUTPUT)
    report = {"files": len(sources), "bytes": OUTPUT.stat().st_size, "missing": missing,
              "categories": {scene["name"]: len(scene["items"]) for scene in manifest["scenes"]}}
    OUTPUT.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
