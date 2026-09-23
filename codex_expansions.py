"""Source-index book pages with original Tormentor character prompts."""
from html import escape
import re
import unicodedata
import codex_profiles
import codex_subclasses
import codex_subclass_catalogue

# Editorial German labels; original names remain stable for URLs and sources.
GERMAN = {
    'Alchemist': 'Alchemist', 'Armorer': 'Rüstungsschmied', 'Artillerist': 'Artillerist',
    'Battle Smith': 'Kampfschmied', 'Circle of Spores': 'Zirkel der Sporen',
    'Circle of Stars': 'Zirkel der Sterne', 'Circle of Wildfire': 'Zirkel des Wildfeuers',
    'Soulknife': 'Seelenklinge',
    'Artificer': 'Magieschmied', 'Reanimator': 'Wiederbeleber',
    'College of Spirits': 'Kollegium der Geister', 'Grave Domain': 'Grabesdomäne',
    'Hollow Warden': 'Wächter der finsteren Wildnis', 'Shadow Sorcery': 'Schattenmagie',
    'Undead Patron': 'Untoter Schutzherr', 'Hexblood': 'Hexenblut', 'Reborn': 'Wiedergeborene',
    'Bugbear': 'Grottenschrat', 'Changeling': 'Wandelwesen', 'Shifter': 'Wandler',
    'Warforged': 'Kriegsgeschmiedete', 'Tortle': 'Schildkrötenvolk',
    'Plasmoid': 'Plasmoide',
}

def german(name):
    return GERMAN.get(name, name)

def searchable(entry):
    return ' '.join((entry['name'], german(entry['name']), entry['source'], entry['kind'], entry.get('parent_original', ''))).casefold()

RAVENLOFT = 'Ravenloft: The Horrors Within'
TASHA = 'Tashas Kessel mit Allem'
TASHA_OPTIONS = [('Magieschmied','Alchemist'),('Magieschmied','Armorer'),('Magieschmied','Artillerist'),('Magieschmied','Battle Smith'),('Druide','Circle of Spores'),('Druide','Circle of Stars'),('Druide','Circle of Wildfire'),('Schurke','Phantom'),('Schurke','Soulknife')]
GERMAN.update({'Path of the Beast': 'Pfad der Bestie', 'Path of Wild Magic': 'Pfad der wilden Magie', 'College of Creation': 'Kollegium der Schöpfung', 'College of Eloquence': 'Kollegium der Beredsamkeit', 'Order Domain': 'Domäne der Ordnung', 'Peace Domain': 'Domäne des Friedens', 'Twilight Domain': 'Domäne des Zwielichts', 'Psi Warrior': 'Psi-Krieger', 'Rune Knight': 'Runenritter', 'Way of Mercy': 'Weg der Gnade', 'Way of the Astral Self': 'Weg des Astralen Selbst', 'Oath of Glory': 'Schwur des Ruhms', 'Oath of the Watchers': 'Schwur der Wächter', 'Fey Wanderer': 'Feenwanderer', 'Swarmkeeper': 'Schwarmhüter', 'Aberrant Mind': 'Aberranter Geist', 'Clockwork Soul': 'Uhrwerkseele', 'The Fathomless': 'Der Unergründliche', 'The Genie': 'Der Dschinn', 'Bladesinging': 'Klingengesang', 'Order of Scribes': 'Orden der Schreiber'})
TASHA_OPTIONS += [('Barbar', 'Path of the Beast'), ('Barbar', 'Path of Wild Magic'), ('Barde', 'College of Creation'), ('Barde', 'College of Eloquence'), ('Kleriker', 'Order Domain'), ('Kleriker', 'Peace Domain'), ('Kleriker', 'Twilight Domain'), ('Kämpfer', 'Psi Warrior'), ('Kämpfer', 'Rune Knight'), ('Mönch', 'Way of Mercy'), ('Mönch', 'Way of the Astral Self'), ('Paladin', 'Oath of Glory'), ('Paladin', 'Oath of the Watchers'), ('Waldläufer', 'Fey Wanderer'), ('Waldläufer', 'Swarmkeeper'), ('Zauberer', 'Aberrant Mind'), ('Zauberer', 'Clockwork Soul'), ('Hexenmeister', 'The Fathomless'), ('Hexenmeister', 'The Genie'), ('Magier', 'Bladesinging'), ('Magier', 'Order of Scribes')]
SUBCLASSES = [
    ('Artificer', 'Reanimator', 'Nekromantische Erfindungen und ein erschaffener Begleiter.'),
    ('Barde', 'College of Spirits', 'Geister verleihen Geschichten übernatürliche Kraft.'),
    ('Kleriker', 'Grave Domain', 'Göttliche Macht an der Grenze zum Tod.'),
    ('Waldläufer', 'Hollow Warden', 'Unheimliche Wildnis und monströse Verwandlung.'),
    ('Schurke', 'Phantom', 'Geisterhafte Kräfte und das Wissen Verstorbener.'),
    ('Zauberer (Sorcerer)', 'Shadow Sorcery', 'Zauberkraft aus Dunkelheit und Schatten.'),
    ('Hexenmeister', 'Undead Patron', 'Ein Pakt mit einem untoten Wesen.'),
]
SOURCES = {
    TASHA: ('2014', 'tcoe'),
    'Mordenkainen: Monsters of the Multiverse': ('2014', 'motm'),
    'Spelljammer: Adventures in Space': ('2014', 'sais'),
    'Van Richten’s Guide to Ravenloft': ('2014', 'vrgtr'),
    'Eberron: Rising from the Last War': ('2014', 'erftlw'),
    RAVENLOFT: ('2024', 'rthw'),
}

GERMAN.update({name: label for _, _, _, _, name, label in codex_subclass_catalogue.rows()})
SOURCES.update({source: (edition, code) for edition, code, source, _ in codex_subclass_catalogue.BOOKS})


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()).strip('-')

def catalogue(groups):
    result = []
    for source, names in {**groups, RAVENLOFT: ['Dhampir', 'Hexblood', 'Lupin', 'Reborn']}.items():
        edition, code = SOURCES[source]
        for name in names:
            result.append(dict(name=name, kind='Spezies', edition=edition, source=source, code=code, key=f'{code}-{slug(name)}', theme=''))
    for parent, name, theme in SUBCLASSES:
        result.append(dict(name=name, kind=f'Unterklasse · {german(parent)}', parent_original=parent, edition='2024', source=RAVENLOFT, code='rthw', key=f'rthw-{slug(name)}', theme=theme))
    result.append(dict(name='Artificer',kind='Klasse',edition='2014',source=TASHA,code='tcoe',key='tcoe-artificer',theme='Quellen-Steckbrief zur Klasse aus Tashas Kessel mit Allem.'))
    for parent,name in TASHA_OPTIONS:
        result.append(dict(name=name,kind=f'Unterklasse · {parent}',edition='2014',source=TASHA,code='tcoe',key=f'tcoe-{slug(name)}',theme='Quellen-Steckbrief · Diese Buchfassung gehört zur Regelausgabe 2014.'))
    for edition, code, source, parent, name, _ in codex_subclass_catalogue.rows():
        result.append(dict(name=name, kind=f'Unterklasse · {parent}', parent_original=parent,
                           edition=edition, source=source, code=code, key=f'{code}-{slug(name)}',
                           theme=f'Unterklasse für {parent} aus {source}. Verwende die Klassenregeln der Ausgabe {edition}.'))
    return result

def links(entries, edition=None, term='', subclasses=False):
    selected = [e for e in entries if (edition is None or e['edition'] == edition) and term.casefold() in searchable(e) and (not subclasses or e['kind'].startswith('Unterklasse'))]
    return '<ul>' + ''.join(f'<li><a href="/codex/quelle/{e["key"]}">{escape(german(e["name"]))}</a> <small>{"(" + escape(e["name"]) + ")" if german(e["name"]) != e["name"] else ""}</small> · {escape(e["kind"])} · {e["edition"]} <small>({escape(e["source"])})</small></li>' for e in selected) + '</ul>' if selected else '<p>Keine passenden Einträge.</p>'

def subclass_index(entries, term=''):
    selected = [e for e in entries if e['kind'].startswith('Unterklasse') and term.casefold() in searchable(e)]
    body = ('<div class="book"><h2>Unterklassen</h2><p>Spielerhandbücher 2014 und 2024, Xanathars Ratgeber, Tashas Kessel und Ravenloft: The Horrors Within. '
            'Nach Regelfassung und Klasse geordnet. Weitere Bücher sind noch nicht vollständig erfasst. '
            'Die Quellen-Steckbriefe enthalten keine vollständigen Merkmals- und Stufenregeln.</p>'
            '<form><label>Unterklasse oder Klasse suchen<input name="q" value="' + escape(term) +
            '" placeholder="Druide, Phantom, …"></label><button>Suchen</button></form></div>')
    for edition in ('2024', '2014'):
        items = [e for e in selected if e['edition'] == edition]
        if not items:
            continue
        body += '<section class="book"><h2>Regelfassung ' + edition + f'</h2><p>{len(items)} Unterklassen-Einträge</p>'
        for kind in sorted({e['kind'] for e in items}):
            body += '<h3>' + escape(kind.split(' · ', 1)[1]) + '</h3>' + links(sorted([e for e in items if e['kind'] == kind], key=lambda e: (german(e['name']).casefold(), e['source'])))
        body += '</section>'
    if not selected:
        body += '<p>Keine passenden Unterklassen gefunden.</p>'
    return body + '<p><a href="/codex">Zurück zum Codex</a></p>'


def class_subclasses(entries, name, edition):
    selected = [e for e in entries if e['edition'] == edition and e['kind'].startswith('Unterklasse · ')
                and e['kind'].split(' · ', 1)[1].split(' (', 1)[0] == name]
    body = '<section id="unterklassen"><h2>Unterklassen · ' + escape(name) + '</h2>'
    body += '<p>Wähle eine Unterklasse, um ihren Quellen-Steckbrief zu öffnen. Regelfassung ' + edition + '.</p>'
    for source in dict.fromkeys(e['source'] for e in selected):
        body += '<h3>' + escape(source) + '</h3>' + links(sorted([e for e in selected if e['source'] == source], key=lambda e: german(e['name']).casefold()))
    return body + '</section>'


def parent_link(entry):
    if not entry['kind'].startswith('Unterklasse · '):
        return ''
    name = entry['kind'].split(' · ', 1)[1].split(' (', 1)[0]
    keys = {'Barbar': 'barbar', 'Barde': 'barde', 'Druide': 'druide', 'Hexenmeister': 'hexenmeister',
            'Kämpfer': 'kaempfer', 'Kleriker': 'kleriker', 'Magier': 'magier', 'Mönch': 'moench',
            'Paladin': 'paladin', 'Schurke': 'schurke', 'Waldläufer': 'waldlaeufer', 'Zauberer': 'zauberer'}
    if name in keys:
        return f'<p><a href="/codex/{entry["edition"]}/klasse/{keys[name]}#unterklassen">← Zur Klasse {escape(name)}</a></p>'
    if name == 'Magieschmied' and entry['edition'] == '2014':
        return '<p><a href="/codex/quelle/tcoe-artificer#unterklassen">← Zur Klasse Magieschmied</a></p>'
    return ''


def index(entries, term=''):
    body = '<div class="book"><h2>Weitere offizielle Spezies</h2><p>Quellen-Steckbriefe · getrennte Regelfassungen 2014 und 2024</p><form><label>Suchen<input name="q" value="'+escape(term)+'" placeholder="Tabaxi, Ravenloft, …"></label><button>Suchen</button></form></div>'
    for source in SOURCES:
        selected = [e for e in entries if e['source'] == source and e['kind'] == 'Spezies']
        if not selected: continue
        if term and not any(term.casefold() in searchable(e) for e in selected):
            continue
        body += '<section class="card"><h2>'+escape(source)+'</h2>'+links(selected, term=term)+'</section>'
    return body

def detail(entry, entries):
    e = entry
    original = f'<p><small>Originalname: {escape(e["name"])} · Deutsche Bezeichnung redaktionell für Tormentor.</small></p>' if german(e["name"]) != e["name"] else ""
    theme = '<p>'+escape(e['theme'])+'</p>' if e['theme'] else ''
    ideas = {
        'Tabaxi': 'Du sammelst die letzten Worte verschwundener Entdecker in einem zerlesenen Notizbuch. Welche Spur führt dich zur Gruppe?',
        'Tortle': 'In deinem Reisegepäck liegt ein Brief, den du seit Jahren nicht zu öffnen wagst. Wer soll ihn am Ende deiner Reise erhalten?',
        'Dhampir': 'Du bewachst nachts eine Herberge und suchst die Person, die dich einst gerettet hat. Was schuldest du ihr?',
        'Hexblood': 'Jeden Winter erscheint ein fremder Name auf deinem alten Familienporträt. Dieses Jahr ist es der Name eines Gruppenmitglieds.',
        'Lupin': 'Ein Dorf hat dich verstoßen; dennoch kehrst du heimlich zurück, um seine Reisenden vor einer Gefahr zu warnen.',
        'Reborn': 'Du erkennst die Handschrift eines gesuchten Verbrechers als deine eigene. Du weißt jedoch nicht mehr, wann du diesen Brief geschrieben hast.',
    }
    idea = ideas.get(e['name'], 'Du trägst den Schlüssel zu einem Haus, das auf keiner Karte steht. Ein anderes Gruppenmitglied besitzt eine Zeichnung seiner Tür. Findet gemeinsam heraus, was euch verbindet.')
    family = [x for x in entries if x['source'] == e['source'] and x['kind'].startswith(e['kind'].split(' · ')[0])]
    pos = family.index(e)
    nav = ''.join(f'<a href="/codex/quelle/{family[i]["key"]}">{label} {escape(german(family[i]["name"]))}</a> · ' for i, label in ((pos-1,'←'),(pos+1,'→')) if 0 <= i < len(family))
    return (codex_profiles.illustration(e['key'], german(e['name'])) + f'<article class="book"><p>{escape(e["kind"])} · Regelfassung {e["edition"]} · Quellen-Steckbrief</p><h2>{escape(german(e["name"]))}</h2>{original}{theme}'
            f'<p>Quelle: <a href="https://www.dndbeyond.com/sources/dnd/{e["code"]}">{escape(e["source"])}</a> · Wizards of the Coast.</p>'
            '<p>Dieser Eintrag verweist auf eine offizielle Spieloption. Die vollständigen Merkmale, Werte und Stufenregeln findest du in der verlinkten Buchquelle; sie sind hier noch nicht enthalten. Der Buchzugang kann einen Kauf erfordern.</p>'
            + (codex_profiles.render(e['key']) or codex_subclasses.render(e['key']) or f'<h2>Charakteridee für deine Runde</h2><p>{escape(idea)}</p><p><small>Eigene Tormentor-Erzählidee, keine offizielle Hintergrundgeschichte oder zusätzliche Regel.</small></p>') +
            '<h2>Mit dem DM festlegen</h2><p>Wähle eine persönliche Motivation, eine Verbindung zur Gruppe und ein Geheimnis. Übernimm Spielwerte aus der angegebenen Regelfassung und halte die ausgewählte Quelle im Charakterprofil fest.</p>'
            + parent_link(e)
            + (class_subclasses(entries, german(e['name']), e['edition']) if e['kind'] == 'Klasse' else '') +
            f'<p>{nav}<a href="/codex/{e["edition"]}">Inhaltsverzeichnis</a> · <a href="/codex">Buch schließen ↩</a></p></article>')
