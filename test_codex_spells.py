import unittest
import codex_spells


class SpellFilterTests(unittest.TestCase):
    def test_srd_membership_and_controls(self):
        spells = {s['name']: s for s in codex_spells.SPELLS}
        self.assertEqual(len(spells), 318)
        self.assertIn('Druide', spells['Rindenhaut']['classes'])
        self.assertNotIn('Magier', spells['Rindenhaut']['classes'])
        self.assertNotIn('Druide', spells['Feuerball']['classes'])
        self.assertIn('Kleriker', spells['Segnen']['classes'])
        self.assertNotIn('Barde', spells['Segnen']['classes'])
        self.assertTrue(all(s['classes'] for s in spells.values()))
        body = codex_spells.index(class_name='Druide', level='2')
        self.assertIn('<h2>Rindenhaut</h2>', body)
        self.assertNotIn('<h2>Feuerball</h2>', body)
        self.assertIn('value="Druide" selected', body)
        self.assertIn('name="class"', body)
        self.assertIn('0 Treffer', codex_spells.index('Feuerball', class_name='Druide'))
        self.assertIn('<h2>Tierform</h2>', codex_spells.index('Animal Shapes'))
        self.assertIn('Deine Magie verwandelt andere in Tiere.', codex_spells.index('Animal Shapes'))
        for term in ('Tiergestalt', ' TIERGESTALT ', 'Wild Shape'):
            body = codex_spells.index(term, class_name='Druide')
            self.assertIn('Tiergestalt · Druidenfähigkeit', body)
            self.assertIn('/codex/2014/klasse/druide', body)
            self.assertNotIn('<h2>Tierform</h2>', body)


if __name__ == '__main__':
    unittest.main()
