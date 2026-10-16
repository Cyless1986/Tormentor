import json
import tempfile
import unittest
from pathlib import Path
from cortana_voice import reply


class CortanaVoiceTests(unittest.TestCase):
    def test_language_selection_and_missing_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'sound/cortana'
            folder.mkdir(parents=True)
            for language in ('en', 'de'):
                (folder / f'{language}-activation.wav').write_bytes(b'test')
            settings = root / 'settings.json'
            self.assertEqual(reply('activation', settings, root)[0], 'Yes, Dungeon Master?')
            settings.write_text(json.dumps({'cortana_language': 'de'}))
            self.assertEqual(reply('activation', settings, root)[0], 'Ja, Dungeonmaster?')
            settings.write_text(json.dumps({'cortana_language': '../../invalid'}))
            self.assertEqual(Path(reply('activation', settings, root)[1]).name, 'en-activation.wav')
            with self.assertRaises(FileNotFoundError):
                reply('ready', settings, root)


if __name__ == '__main__':
    unittest.main()
