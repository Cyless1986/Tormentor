"""Compact, player-friendly spell index. Summaries are original, not rule text."""
from html import escape
import json
from pathlib import Path

SPELLS = [
    dict(name='Feuerpfeil', level=0, school='Hervorrufung', classes='Magier, Zauberer', time='1 Aktion', range='36 m', components='V, S', duration='sofort', effect='Ein Feuerstrahl trifft ein Ziel; bei einem Treffer entsteht Feuerschaden.'),
    dict(name='Licht', level=0, school='Hervorrufung', classes='Barde, Kleriker, Magier, Zauberer', time='1 Aktion', range='Berührung', components='V, M', duration='1 Stunde', effect='Ein Gegenstand leuchtet hell und verbreitet zusätzlich gedämpftes Licht.'),
    dict(name='Magierhand', level=0, school='Beschwörung', classes='Barde, Magier, Zauberer', time='1 Aktion', range='9 m', components='V, S', duration='1 Minute', effect='Eine schwebende Hand kann einfache Gegenstände greifen und bewegen.'),
    dict(name='Schild', level=1, school='Bannmagie', classes='Magier, Zauberer', time='1 Reaktion', range='Selbst', components='V, S', duration='1 Runde', effect='Deine Verteidigung steigt kurzzeitig stark; der Zauber kann einen magischen Geschosszauber abfangen.'),
    dict(name='Magisches Geschoss', level=1, school='Hervorrufung', classes='Magier, Zauberer', time='1 Aktion', range='36 m', components='V, S, M', duration='sofort', effect='Mehrere magische Geschosse treffen gewählte Ziele zuverlässig und verursachen Kraftschaden.'),
    dict(name='Heilendes Wort', level=1, school='Hervorrufung', classes='Barde, Kleriker, Druide', time='1 Bonusaktion', range='18 m', components='V', duration='sofort', effect='Eine Kreatur erhält aus der Entfernung Heilung.'),
    dict(name='Segen', level=1, school='Verzauberung', classes='Barde, Kleriker, Paladin', time='1 Aktion', range='9 m', components='V, S, M', duration='Konzentration, bis 1 Minute', effect='Bis zu drei Verbündete erhalten einen Bonus auf Angriffe und Rettungswürfe.'),
    dict(name='Brennende Hände', level=1, school='Hervorrufung', classes='Magier, Zauberer', time='1 Aktion', range='Selbst', components='V, S', duration='sofort', effect='Ein kurzer Feuerkegel verursacht Feuerschaden; ein Reflexionswurf kann den Schaden verringern.'),
    dict(name='Unsichtbarkeit', level=2, school='Illusion', classes='Barde, Magier, Zauberer', time='1 Aktion', range='Berührung', components='V, S, M', duration='Konzentration, bis 1 Stunde', effect='Eine berührte Kreatur wird unsichtbar, bis sie angreift oder zaubert.'),
    dict(name='Misty Step', level=2, school='Beschwörung', classes='Hexenmeister, Magier, Zauberer', time='1 Bonusaktion', range='Selbst', components='V', duration='sofort', effect='Du teleportierst dich an einen freien sichtbaren Ort in der Nähe.'),
    dict(name='Spiegelbild', level=2, school='Illusion', classes='Barde, Magier, Zauberer', time='1 Aktion', range='Selbst', components='V, S', duration='1 Minute', effect='Illusorische Doppelgänger erschweren Treffer gegen dich.'),
    dict(name='Heilung', level=3, school='Hervorrufung', classes='Barde, Kleriker, Druide', time='1 Aktion', range='18 m', components='V, S', duration='sofort', effect='Eine Kreatur erhält eine größere Menge Heilung; der Zauber wirkt nicht auf Untote oder Konstrukte.'),
    dict(name='Feuerball', level=3, school='Hervorrufung', classes='Magier, Zauberer', time='1 Aktion', range='45 m', components='V, S, M', duration='sofort', effect='Eine Explosion fügt Kreaturen in einem Bereich Feuerschaden zu; ein Geschicklichkeitswurf halbiert den Schaden.'),
    dict(name='Gegenzauber', level=3, school='Bannmagie', classes='Hexenmeister, Magier, Zauberer', time='1 Reaktion', range='18 m', components='S', duration='sofort', effect='Du unterbrichst einen Zauber, der gerade gewirkt wird; die Stärke des gegnerischen Zaubers kann einen Gegenwurf erfordern.'),
    dict(name='Fliegen', level=3, school='Verwandlung', classes='Hexenmeister, Magier, Zauberer', time='1 Aktion', range='Berührung', components='V, S, M', duration='Konzentration, bis 10 Minuten', effect='Eine Kreatur erhält eine Flugbewegung. Beim Ende des Zaubers muss sie sicher landen.'),
]

_SCHOOLS = {'abjuration':'Bannmagie','conjuration':'Beschwörung','divination':'Erkenntnismagie','enchantment':'Verzauberung','evocation':'Hervorrufung','illusion':'Illusion','necromancy':'Nekromantie','transmutation':'Verwandlung'}
_CLASSES = {'Bard':'Barde','Cleric':'Kleriker','Druid':'Druide','Paladin':'Paladin','Ranger':'Waldläufer','Sorcerer':'Zauberer','Warlock':'Hexenmeister','Wizard':'Magier','Fighter':'Kämpfer','Rogue':'Schurke'}

# Häufige SRD-Formulierungen werden beim Import ins Deutsche übertragen.
_PHRASES = {
    'A beam of crackling energy': 'Ein knisternder Energiestrahl',
    'A bright streak flashes': 'Ein heller Lichtblitz',
    'The spell ends': 'Der Zauber endet',
    'the target': 'das Ziel', 'targets': 'Ziele', 'target': 'Ziel',
    'a creature': 'eine Kreatur', 'creatures': 'Kreaturen', 'creature': 'Kreatur',
    'you can see': 'die du sehen kannst', 'within range': 'in Reichweite',
    'make a': 'führt einen', 'saving throw': 'Rettungswurf', 'ability check': 'Attributswurf',
    'takes damage': 'erleidet Schaden', 'take damage': 'erleiden Schaden',
    'hit points': 'Trefferpunkte', 'attack roll': 'Angriffswurf', 'weapon attack': 'Waffenangriff',
    'bonus action': 'Bonusaktion', 'reaction': 'Reaktion', 'one action': 'eine Aktion',
    'concentration, up to': 'Konzentration, bis zu', 'instantaneous': 'sofort',
    'The spell deals': 'Der Zauber verursacht', 'damage': 'Schaden',
}

def _german_effect(parts):
    text = ' '.join(parts or [])
    for source, target in _PHRASES.items():
        text = text.replace(source, target).replace(source.lower(), target)
    return text

def _load_srd():
    path = Path(__file__).parent / 'assets/srd/spells-2014-de.json'
    if not path.is_file(): return
    try: raw = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError): return
    loaded = []
    memberships = json.loads((path.parent / 'spell-classes-de.json').read_text(encoding='utf-8'))
    aliases = {'Identifizie ren': 'Identifizieren', 'Widerstand (Resistenz*)': 'Widerstand'}
    for item in raw:
        name = aliases.get(item['name'], item['name'])
        assigned = memberships[name]
        loaded.append(dict(item, name=name, classes=', '.join(assigned), school={'Bann':'Bannmagie','Erkenntnis':'Erkenntnismagie'}.get(item['school'], item['school'])))
    if loaded: SPELLS[:] = loaded

_load_srd()

def index(term='', level='', school='', class_name=''):
    term = term.casefold().strip()
    # Search aliases do not replace German rule text with word-by-word translations.
    search_term = {'animal shapes': 'tierform', 'animal shape': 'tierform'}.get(term, term)
    def match(s):
        return (not search_term or search_term in ' '.join((s['name'], s['effect'], s['classes'], s['school'])).casefold()) and (level == '' or str(s['level']) == level) and (not school or s['school'] == school) and (not class_name or class_name.casefold() in [c.strip().casefold() for c in s['classes'].split(',')])
    selected = [s for s in SPELLS if match(s)]
    schools = sorted({s['school'] for s in SPELLS})
    classes = sorted({c.strip() for s in SPELLS for c in s['classes'].split(',') if c.strip()} or set(_CLASSES.values()))
    levels = ''.join(f'<option value="{i}"' + (' selected' if level == str(i) else '') + '>' + ('Zaubertrick' if i == 0 else 'Grad '+str(i)) + '</option>' for i in range(10))
    body = '<div class="book"><h2>Zauberlexikon</h2><p>Deutsche Zauberbeschreibungen aus dem SRD 5.1.</p><form><label>Suchen<input name="q" value="'+escape(term)+'" placeholder="Feuerball, Heilung, …"></label><label>Grad<select name="level"><option value="">Alle Grade</option>'+levels+'</select></label><label>Schule<select name="school"><option value="">Alle Schulen</option>'+''.join('<option'+(' selected' if school == x else '')+'>'+escape(x)+'</option>' for x in schools)+'</select></label><button>Suchen</button></form><p><small>Klassenfilter folgt nach geprüfter Zuordnung.</small></p></div>'
    class_control = '<label>Klasse<select name="class"><option value="">Alle Klassen</option>' + ''.join('<option value="'+escape(c)+'"'+(' selected' if class_name == c else '')+'>'+escape(c)+'</option>' for c in classes) + '</select></label>'
    body = body.replace('<button>Suchen</button>', class_control + '<button>Suchen</button>').replace('<p><small>Klassenfilter folgt nach geprüfter Zuordnung.</small></p>', '<p><small>Regelfassung 2014 · SRD 5.1 · Grundklassenlisten; zusätzliche Unterklassenzauber sind nicht enthalten.</small></p>')
    if term in ('tiergestalt', 'tiergestalten', 'wild shape'):
        body += '<section class="card"><h2>Tiergestalt · Druidenfähigkeit</h2><p>Ab Stufe 2 kann sich der Druide mit seiner Klassenfähigkeit selbst in ein Tier verwandeln. Tiergestalt ist kein Zauber und benötigt keinen Zauberplatz. Die Regeln hängen von der verwendeten Ausgabe und der Unterklasse ab.</p><p><a href="/codex/2014/klasse/druide">Druide · Regeln 2014</a> · <a href="/codex/2024/klasse/druide">Druide · Regeln 2024</a></p><p>Der Zauber Tierform (Animal Shapes, Grad 8) verwandelt dagegen andere bereitwillige Kreaturen.</p></section>'
    body += f'<p>{len(selected)} Treffer</p>'
    for s in selected:
        body += f'<article class="card"><h2>{escape(s["name"])}</h2><p><b>{"Zaubertrick" if s["level"] == 0 else "Grad "+str(s["level"])}</b> · {escape(s["school"])} · {escape(s["classes"])}</p><p>{escape(s["effect"])}</p><dl><dt>Wirkzeit</dt><dd>{escape(s["time"])}</dd><dt>Reichweite</dt><dd>{escape(s["range"])}</dd><dt>Komponenten</dt><dd>{escape(s["components"])}</dd><dt>Dauer</dt><dd>{escape(s["duration"])}</dd></dl></article>'
    return body + ('<p>Keine passenden Zauber gefunden.</p>' if not selected else '') + '<p><a href="/codex">Zurück zum Codex</a></p>'
