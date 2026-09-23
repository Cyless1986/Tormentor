"""Create compatible copies and a video-only repair package; originals stay intact."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile
from export_media import collect

ROOT = Path(__file__).resolve().parent
FFMPEG = next((ROOT / 'tools/video-python/imageio_ffmpeg/binaries').glob('ffmpeg*.exe'))
OUT = ROOT / 'tablet_videos'
OUT.mkdir(exist_ok=True)

def convert(source, target):
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    stamp = target.with_suffix('.sha256')
    if not target.exists() or not stamp.exists() or stamp.read_text() != fingerprint:
        print(f'Konvertiere: {source}', flush=True)
        subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                        '-map', '0:v:0', '-an', '-vf',
                        'scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1,fps=30',
                        '-c:v', 'libx264', '-profile:v', 'baseline', '-level:v', '3.1',
                        '-pix_fmt', 'yuv420p', '-preset', 'fast', '-crf', '22', '-maxrate', '3M',
                        '-bufsize', '6M', '-threads', '2', '-movflags', '+faststart', str(target)], check=True)
        stamp.write_text(fingerprint)
    # Decode every frame, not just the container header.
    subprocess.run([str(FFMPEG), '-v', 'error', '-xerror', '-i', str(target), '-f', 'null', '-'], check=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == fingerprint

def prepare_app_assets():
    for name, source in [('intro', 'Intro.mp4'), ('home', 'background.mp4')]:
        convert(ROOT.parent / 'assets' / source, OUT / f'{name}.mp4')
        (ROOT / f'app/src/main/assets/{name}.mp4').write_bytes((OUT / f'{name}.mp4').read_bytes())
    (ROOT / 'app/src/main/assets/home.png').write_bytes((ROOT.parent / 'assets/background.png').read_bytes())

def main():
    manifest, sources, missing = collect()
    lookup = dict((name, path) for path, name in sources)
    repair = {'version': 1, 'replaceVideosByName': True, 'scenes': []}
    converted = {}
    for scene in manifest['scenes']:
        items = []
        for item in scene['items']:
            if lookup[item['path']].suffix.lower() != '.mp4':
                continue
            target = OUT / Path(item['path']).name
            convert(lookup[item['path']], target)
            converted[item['path']] = target
            items.append(item)
        if items:
            repair['scenes'].append({'name': scene['name'], 'items': items})
    prepare_app_assets()
    for filename, data, files in [
        ('Tablet-Videos.zip', repair, [(path, name) for name, path in converted.items()]),
        ('Medienpaket.zip', manifest, [(converted.get(name, path), name) for path, name in sources]),
    ]:
        target = ROOT / filename
        partial = target.with_suffix('.zip.partial')
        with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_STORED) as archive:
            archive.writestr('manifest.json', json.dumps(data, ensure_ascii=False))
            for path, name in files:
                archive.write(path, name)
        with zipfile.ZipFile(partial) as archive:
            assert archive.testzip() is None
        partial.replace(target)
        print(f'Fertig: {filename}, {target.stat().st_size} Bytes', flush=True)
    report = {'videos': len(converted), 'full_package_files': len(sources), 'missing': missing,
              'format': 'H.264 Baseline Level 3.1, yuv420p, <=1280x720, 30 fps, silent',
              'all_frames_decoded': True, 'original_video_hashes_unchanged': True}
    (ROOT / 'verification/tablet-videos.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

if __name__ == '__main__':
    import sys
    prepare_app_assets() if '--app-assets-only' in sys.argv else main()
