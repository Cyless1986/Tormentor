"""Instant offline Cortana replies rendered from the user's saved voice."""
import json
from pathlib import Path

TEXTS = {
    'en': {'activation': 'Yes, Dungeon Master?', 'ready': 'All systems online. I am ready, Dungeon Master.'},
    'de': {'activation': 'Ja, Dungeonmaster?', 'ready': 'Alle Systeme sind online. Ich bin bereit, Dungeonmaster.'},
}


def reply(key, settings_path, root):
    try:
        settings = json.loads(Path(settings_path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        settings = {}
    language = settings.get('cortana_language', 'en')
    if language not in TEXTS:
        language = 'en'
    text = TEXTS[language][key]
    audio = Path(root) / 'sound' / 'cortana' / f'{language}-{key}.wav'
    if not audio.is_file():
        raise FileNotFoundError(f'Cortana-Antwort fehlt: {audio}')
    return text, str(audio)
