"""Concise sourced introductions and original Tormentor roleplaying guidance.

Introductions: D&D Beyond public species catalogue, retrieved 2026-09-14.
The longer character concepts below are original suggestions, not official lore.
"""
from html import escape

ILLUSTRATIONS = {
    'species-drachenbluetiger': 'Bronzeschuppiger Drachenblütiger auf Reisen zwischen alten Ruinen',
    'species-elf': 'Silberhaarige Elfin in grünen Gewändern in einer Waldruine',
    'species-gnom': 'Erwachsener Felsengnom mit einem kleinen Uhrwerk in seiner Werkstatt',
    'species-goliath': 'Grauhäutiger Goliath mit steinartigen Hautzeichnungen auf einem Bergpass',
    'species-halbelf': 'Halbelfischer Reisender mit leicht spitzen Ohren und besticktem Mantel',
    'species-halbling': 'Lockige Halblingsreisende auf einem ländlichen Weg',
    'species-halbork': 'Halborkische Entdeckerin mit geflochtenem Haar und kleinen Hauern',
    'species-mensch': 'Menschliche Abenteurerin in Reisekleidung vor einem Stadttor',
    'species-tiefling': 'Tieflinggelehrter mit gebogenen Hörnern und langem Schwanz',
    'species-zwerg': 'Stämmiger Zwergenreisender mit geflochtenem roten Bart am Bergtor',
    'homebrew-myzelgeborene': 'Mooslicht, eine pilzgestaltige wandernde Druidin mit Setzlingen',
    'srd-barde': 'Tiefling-Bardin mit Laute',
    'srd-druide': 'Zwergischer Druide mit Naturstab und Eichhörnchen',
    'srd-kaempfer': 'Drachengeborener Kämpfer mit Schwert und Schild',
    'srd-kleriker': 'Halblings-Klerikerin mit Sonnenamulett',
    'srd-magier': 'Gnomischer Magier mit Zauberbuch',
    'srd-moench': 'Tabaxi-Mönchin mit Schneeleopardenfell',
    'srd-hexenmeister': 'Tiefling-Hexenmeister mit türkisfarbener Paktmagie',
    'srd-paladin': 'Silberne drachengeborene Paladin mit Banner und Schild',
    'srd-schurke': 'Elfische Schurkin mit Schloss und Dietrich',
    'srd-waldlaeufer': 'Orkischer Waldläufer mit Wolf',
    'srd-zauberer': 'Goliath-Zauberin mit goldener Magie',

    'srd-barbar': 'Zwergische Barbarin mit Zweihandaxt auf einem Gebirgspfad',
    'rthw-college-of-spirits': 'Bardin des Kollegiums der Geister mit Erinnerungsbuch und geisterhaften Zuhörern',
    'rthw-grave-domain': 'Kleriker der Grabesdomäne mit Abschiedsbriefen und Kerzenlicht',
    'rthw-hollow-warden': 'Wächterin der finsteren Wildnis mit Bogen im uralten Hain',
    'rthw-phantom': 'Tiefling als Phantom-Schurke in einer alten Druckerei',
    'rthw-shadow-sorcery': 'Drachengeborener mit Schattenmagie und Laterne vor einem Theater',
    'rthw-undead-patron': 'Zwergische Hexenmeisterin mit Verträgen und einem untoten Schutzherrn',
    'rthw-reanimator': 'Magieschmiedin als Wiederbeleberin mit ihrem erschaffenen Begleiter',
    'motm-tabaxi': 'Tabaxi-Entdecker mit Reisemantel und Notizbuch auf einem Waldpfad',
    'rthw-dhampir': 'Dhampir-Nachtwächterin mit Laterne vor einem gotischen Tor',
    'rthw-hexblood': 'Hexenblut mit Zweigkrone und Porträtalbum in einem verwilderten Garten',
    'rthw-lupin': 'Lupin-Kurier mit Reisetasche vor einem verschneiten Dorf',
    'rthw-reborn': 'Wiedergeborene Uhrmacherin mit Taschenuhr vor ihrer Werkstatt',
}

def illustration(key, name):
    if key not in ILLUSTRATIONS:
        return ''
    return (f'<section class="book codex-art-page"><h2>{escape(name)}</h2>'
            f'<img class="codex-illustration" src="/media/codex/{key}.png" alt="{escape(ILLUSTRATIONS[key])}" width="1024" height="1536">'
            '<p><small>Originalillustration für Tormentor, erstellt mit ChatGPT/Kodex. Eigene künstlerische Interpretation.</small></p></section>')

PROFILES = {
    'motm-tabaxi': {
        'intro': 'Tabaxi verbinden katzenartige und humanoide Eigenschaften. Die Buchfassung aus Monsters of the Multiverse führt ihre Herkunft auf den Cat Lord zurück.',
        'motif': 'Spuren, Geschichten und Entdeckungen',
        'concepts': [
            ('Die Kartenzeichnerin', 'Du kartierst keine Straßen, sondern die Orte, an denen Menschen ihre Meinung geändert haben. Deine nächste Karte beginnt mit dem ersten gemeinsamen Abenteuer der Gruppe.'),
            ('Der Hüter verlorener Lieder', 'Du lernst in jeder Siedlung eine Melodie. Ein Lied enthält eine Wegbeschreibung, doch seine letzte Strophe kennt nur eine verschwundene Person.'),
            ('Die ehemalige Hofbotin', 'Du hast eine wichtige Nachricht nie zugestellt. Jetzt reist du mit Menschen, die von ihrem Inhalt betroffen sein könnten.'),
        ],
        'tips': [
            'Gib deiner Neugier ein konkretes Ziel: eine verschwundene Person, ein Rätsel oder eine Sammlung. So entstehen Anlässe für gemeinsame Abenteuer.',
            'Spiele Körpersprache sparsam: ein stillstehender Schwanz oder nach vorn gerichtete Ohren können mehr ausdrücken als ständiges Miauen.',
            'Frage vor einem Alleingang, wie die anderen mitwirken können. Eine Entdeckung wird spannender, wenn die ganze Gruppe etwas dazu beiträgt.',
        ],
        'questions': 'Was möchtest du unbedingt entdecken? Welches Versprechen hält dich bei der Gruppe? Welche Geschichte erzählst du absichtlich falsch?',
        'looks': 'Für deine eigene Figur: geflecktes Fell, ein geflickter Reisemantel und ein Notizbuch voller fremder Handschriften. Aussehen und Requisiten verleihen keine zusätzlichen Regelvorteile.',
    },
    'rthw-dhampir': {
        'intro': 'Dhampire sind lebende Personen mit vampirischen Kräften und einem unheimlichen Hunger.',
        'motif': 'Hunger, Selbstbeherrschung und Vertrauen',
        'concepts': [
            ('Die Nachtwächterin', 'Du hältst Wache vor einer Herberge, deren Besitzer dir einst Schutz gab. Als er verschwindet, folgst du seiner letzten Nachricht.'),
            ('Der Erbe ohne Einladung', 'Du hast ein Haus geerbt, doch die Dienerschaft erkennt einen anderen Menschen als rechtmäßigen Erben an.'),
            ('Die Sammlerin von Schuldbriefen', 'Du bezahlst alte Schulden fremder Menschen. Eine davon verbindet dich mit einem Mitglied der Gruppe.'),
        ],
        'tips': ['Lege gemeinsam mit der Runde fest, wie deutlich der Hunger ausgespielt wird.', 'Gib deiner Figur eine verlässliche Grenze, an der ihre Verbündeten Vertrauen aufbauen können.', 'Nutze den inneren Konflikt für Entscheidungen, ohne anderen Figuren ihre Handlungsfreiheit zu nehmen.'],
        'questions': 'Wer kennt dein Geheimnis? Wem vertraust du in einer Krise? Was bedeutet Menschlichkeit für dich?',
        'looks': 'Eigene Gestaltungsidee: ein dunkler Reisemantel, sorgfältig geflickte Handschuhe und ein silberner Schlüssel als Erinnerungsstück.',
    },
    'rthw-hexblood': {
        'intro': 'Hexenblüter sind von Feenmagie oder geheimnisvoller Hexerei geprägt.',
        'motif': 'Versprechen, Verwandlung und Zugehörigkeit',
        'concepts': [
            ('Die Porträtrestauratorin', 'Auf einem Familienbild erscheint jedes Jahr ein neuer Name. Diesmal steht dort der Name eines Gruppenmitglieds.'),
            ('Der Zeuge des Handels', 'Du erinnerst dich an einen Handel, den alle anderen vergessen haben. Ein unscheinbarer Knopf ist dein einziger Beweis.'),
            ('Die Gärtnerin der letzten Rose', 'Du trägst einen vertrockneten Rosenstock durch die Welt. Jemand hat dir versprochen, dass er am richtigen Ort wieder blüht.'),
        ],
        'tips': ['Wähle ein wiederkehrendes Märchenmotiv, etwa drei Versprechen oder einen verbotenen Namen.', 'Unheimliche Eigenheiten wirken stärker, wenn sie eine persönliche Bedeutung haben.', 'Lass die Gruppe entscheiden, ob sie deinem Geheimnis nachgehen möchte; mache daraus ein Angebot für ein Abenteuer.'],
        'questions': 'Welches Versprechen bindet dich? Was möchtest du an dir bewahren? Wer sieht in dir mehr als ein seltsames Omen?',
        'looks': 'Eigene Gestaltungsidee: moosgrüner Mantel, getrocknete Blüten und ein Reisealbum mit übermalten Gesichtern.',
    },
    'rthw-lupin': {
        'intro': 'Lupins können aus Begegnungen mit Werwölfen hervorgehen, bei denen die Lykanthropie nicht vollständig Fuß fasst.',
        'motif': 'Instinkt, Schutz und Selbstbestimmung',
        'concepts': [
            ('Der heimliche Beschützer', 'Ein Dorf hat dich verstoßen. Trotzdem markierst du nachts sichere Wege für seine Reisenden.'),
            ('Die Kurierin im Winter', 'Du bringst Post zu einem abgeschnittenen Grenzort. Seit Wochen erhältst du Antworten auf Briefe, die niemand geschrieben hat.'),
            ('Der Glockenhüter', 'Du suchst die gestohlene Glocke deiner Heimat. Ihr Klang ist die letzte Erinnerung an eine Person, die du verloren hast.'),
        ],
        'tips': ['Wähle, wen deine Figur beschützen will und wann sie Hilfe annimmt.', 'Instinkt kann sich in Aufmerksamkeit oder Ungeduld zeigen; er muss nicht ständig zu Aggression führen.', 'Leite zusätzliche Verwandlungen oder Immunitäten nicht aus der Erzählidee ab. Dafür gilt ausschließlich die gewählte Buchfassung.'],
        'questions': 'Wann hörst du auf deinen Instinkt? Was beruhigt dich? Wer hat dir bewiesen, dass du dazugehören darfst?',
        'looks': 'Eigene Gestaltungsidee: wetterfeste Reisekleidung, ein alter Kurierbeutel und eine sorgsam aufbewahrte Dorfmarke.',
    },
    'rthw-reborn': {
        'intro': 'Wiedergeborene haben den Tod erlebt und leben dennoch weiter.',
        'motif': 'Erinnerung, Identität und ein zweiter Anfang',
        'concepts': [
            ('Die fremde Handschrift', 'Ein gesuchter Verbrecher schreibt genau wie du. Du suchst herauszufinden, ob du seine Vergangenheit teilst.'),
            ('Der unbekannte Trauergast', 'In mehreren Städten findest du Zeichnungen derselben Beerdigung. Du bist auf jeder zu sehen, aber immer an einer anderen Stelle.'),
            ('Die Uhrmacherin', 'Eine stehen gebliebene Taschenuhr läuft nur an Orten, die du wiedererkennst. Gemeinsam mit der Gruppe suchst du den Ursprung dieser Verbindung.'),
        ],
        'tips': ['Vereinbare mit dem DM, welche Erinnerungen du selbst festlegst und welche gemeinsam entdeckt werden.', 'Gib deiner Figur auch Wünsche für ihre Zukunft, damit sie mehr als ein Rätsel ihrer Vergangenheit ist.', 'Verknüpfe Erinnerungsfragmente mit den Abenteuern der Gruppe, ohne jede Szene auf deine Vorgeschichte zu lenken.'],
        'questions': 'Welchen Namen hast du selbst gewählt? Was möchtest du neu lernen? Welche Wahrheit darf zunächst ungeklärt bleiben?',
        'looks': 'Eigene Gestaltungsidee: sorgfältig reparierte Kleidung, ein unvollständiges Namensschild und eine Uhr mit gesprungenem Glas.',
    },
}

def render(key):
    item = PROFILES.get(key)
    if item is None:
        return ''
    concepts = ''.join(f'<h3>{escape(title)}</h3><p>{escape(body)}</p>' for title, body in item['concepts'])
    tips = ''.join(f'<li>{escape(tip)}</li>' for tip in item['tips'])
    return (f'<section class="codex-profile"><h2>Kurzporträt</h2><p>{escape(item["intro"])}</p>'
            '<p><small>Kurze eigene Zusammenfassung nach dem <a href="https://www.dndbeyond.com/species">offiziellen D&D-Beyond-Spezieskatalog</a>, geprüft am 14.09.2026. Keine vollständige Regelbeschreibung.</small></p>'
            f'<h2>Deine Figur am Spieltisch</h2><p><b>Erzählthemen:</b> {escape(item["motif"])}</p><p>{escape(item["looks"])}</p>'
            f'<h2>Drei Charakterkonzepte</h2>{concepts}<h2>Tipps fürs Rollenspiel</h2><ul>{tips}</ul>'
            f'<h2>Fragen vor der ersten Session</h2><p>{escape(item["questions"])}</p>'
            '<p><small>Alle Konzepte, Gestaltungsideen und Rollenspieltipps sind eigene Tormentor-Inhalte. Sie ergänzen keine Merkmale oder Spielwerte.</small></p></section>')
