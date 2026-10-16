"""Generate smaller WebP variants of the public portal backgrounds."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    'login-tavern', 'header-castle', 'maps-dungeon-header', 'messages-letters-header',
    'news-noticeboard-header', 'memories-journal-hero', 'character-armory', 'dashboard-heroes',
    'profile-chamber', 'chronicle-archive', 'handouts-courier', 'news-herald-room',
    'memories-keepsakes', 'dm-planning-room', 'classes-guild-v1', 'species-travelers-v1',
    'origins-journey', 'codex-cover-2024', 'codex-cover-2014', 'codex-cover-spells',
    'codex-cover-homebrew', 'codex-parchment', 'lore-places-header-v1', 'lore-quests-header-v1',
    'lore-sessions-header-v1', 'lore-npcs-header-v1',
]

def main():
    before = after = 0
    for name in NAMES:
        source = ROOT / 'assets' / (name + '.png')
        target = source.with_suffix('.webp')
        with Image.open(source) as image:
            image.convert('RGB').save(target, 'WEBP', quality=86, method=6)
        before += source.stat().st_size
        after += target.stat().st_size
    print(f'{len(NAMES)} public backgrounds: {before:,} -> {after:,} bytes ({100*(1-after/before):.1f}% smaller).')

if __name__ == '__main__':
    main()
