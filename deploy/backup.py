"""Consistent database and campaign-media backup; service is paused by the timer."""
import json
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

root = Path('/srv/tormentor')
destination = Path('/var/backups/tormentor')
destination.mkdir(mode=0o700, parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
archive = destination / f'tormentor-{stamp}.tar.gz'
with tempfile.TemporaryDirectory(dir=destination) as tmp:
    stage = Path(tmp)
    with sqlite3.connect(root / 'portal.sqlite3') as source:
        with sqlite3.connect(stage / 'portal.sqlite3') as target:
            source.backup(target)
            assert target.execute('pragma integrity_check').fetchone()[0] == 'ok'
    for name in ('portal_maps', 'portal_lore', 'private_lore'):
        if (root / name).exists():
            shutil.copytree(root / name, stage / name)
    with tarfile.open(archive, 'w:gz') as output:
        for item in stage.iterdir():
            output.add(item, arcname=item.name)
    # Verify the database recovered from the actual archive.
    with tarfile.open(archive) as saved:
        restored = stage / 'restored.sqlite3'
        with saved.extractfile('portal.sqlite3') as src, restored.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        with sqlite3.connect(restored) as check:
            assert check.execute('pragma integrity_check').fetchone()[0] == 'ok'
archive.chmod(0o600)
for old in sorted(destination.glob('tormentor-*.tar.gz'))[:-7]:
    old.unlink()
print(json.dumps({'backup': str(archive), 'restore_check': 'ok'}))
