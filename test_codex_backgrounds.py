import sqlite3
import unittest
from html.parser import HTMLParser

import codex_backgrounds
import portal


class DetailsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        if tag == 'details':
            self.ids.append(dict(attrs)['id'])


class BackgroundsTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.execute('CREATE TABLE codex_entries(id INTEGER, title TEXT, kind TEXT, edition TEXT, source TEXT, published INTEGER, deleted INTEGER)')
        self.addCleanup(self.db.close)

    def test_complete_sections_without_duplicate_empty_cards(self):
        body = portal.backgrounds_page(self.db, None)
        self.assertEqual(body.count('<h2>Regelfassung 2014</h2>'), 1)
        self.assertEqual(body.count('<h2>Regelfassung 2024</h2>'), 1)
        parser = DetailsParser()
        parser.feed(body)
        self.assertEqual(len(parser.ids), 29)
        self.assertEqual(len(set(parser.ids)), 29)
        for edition, count in [('2014', 13), ('2024', 16)]:
            section = body.split('id="backgrounds-' + edition + '"', 1)[1].split('</section>', 1)[0]
            self.assertEqual(section.count('<details '), count)
            self.assertNotIn('Noch keine Herkünfte', section)
            self.assertNotIn('Spieltipp', section)
        self.assertIn('Startausrüstung', body)

    def test_editions_have_distinct_rules(self):
        old = {d['key']: d for d in codex_backgrounds.entries('2014')}
        new = {d['key']: d for d in codex_backgrounds.entries('2024')}
        self.assertEqual(old['criminal']['skills'], 'Täuschen, Heimlichkeit')
        self.assertEqual(new['criminal']['skills'], 'Fingerfertigkeit, Heimlichkeit')
        self.assertEqual(old['sailor']['skills'], 'Athletik, Wahrnehmung')
        self.assertEqual(new['sailor']['skills'], 'Akrobatik, Wahrnehmung')
        self.assertEqual(new['acolyte']['feat'], 'cleric')
        self.assertIn('Zwei nach Wahl', old['acolyte']['languages'])
        self.assertNotIn('Option B:', codex_backgrounds.render_edition('2014'))
        self.assertEqual(codex_backgrounds.render_edition('2024').count('Option B:'), 16)

    def test_custom_visibility_does_not_hide_builtin_backgrounds(self):
        for ident, title, edition, published, deleted in [
            (1, 'Öffentlich <Test>', '2014', 1, 0),
            (2, 'Privat', '2024', 0, 0),
            (3, 'Gelöscht', 'Homebrew', 1, 1),
        ]:
            self.db.execute('INSERT INTO codex_entries VALUES(?,?,\'Hintergrund\',?,\'Eigene Quelle\',?,?)', (ident, title, edition, published, deleted))
        public = portal.backgrounds_page(self.db, None)
        dm = portal.backgrounds_page(self.db, {'role': 'dm'})
        self.assertIn('Öffentlich &lt;Test&gt;', public)
        self.assertNotIn('>Privat</a>', public)
        self.assertIn('>Privat</a>', dm)
        self.assertNotIn('Gelöscht', dm)
        self.assertEqual(public.count('<details '), 29)
        self.assertEqual(dm.count('<details '), 29)


if __name__ == '__main__':
    unittest.main()
