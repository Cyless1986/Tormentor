"""Original roleplaying prompts for the verified Ravenloft subclass index."""
from html import escape

SOURCE = 'https://www.dndbeyond.com/posts/2191-become-the-monster-in-the-shadows-with-7'
PROFILES = {
    'rthw-reanimator': {
        'question': 'Was unterscheidet für dich eine gelungene Erfindung von einem Lebewesen?',
        'concept': 'Die Ärztin mit dem leeren Krankenbuch',
        'story': 'Du reist mit einem sorgfältig gebundenen Krankenbuch, aus dem sämtliche Namen entfernt wurden. Ein ehemaliger Patient erkennt dich wieder und bittet dich, eine Behandlung rückgängig zu machen. Deine Gefährten sollen entscheiden können, ob sie dir bei der Suche nach den fehlenden Seiten helfen.',
        'tips': ['Gib deinem Begleiter eine unverwechselbare, leise Eigenheit: Er sortiert Knöpfe oder hält Fremden Türen auf.', 'Besprich mit der Runde, wie viel Körperhorror zu eurem Spiel passt. Eine makabre Erfindung kann auch durch Geräusche und Andeutungen wirken.', 'Bereite die Aktionen deiner Figur und deines Begleiters gemeinsam vor, damit dein Zug übersichtlich bleibt.'],
        'bond': 'Ein Gruppenmitglied hat dir bei einem früheren Unfall geholfen. Du möchtest diese Schuld begleichen, ohne es zum Gegenstand deiner Experimente zu machen.',
        'look': 'Geflickter Reisekittel, kupferne Instrumente und handgeschriebene Etiketten; ein Begleiter mit sorgfältig ausgebessertem Mantel.',
    },
    'rthw-college-of-spirits': {
        'question': 'Welche Geschichte erzählst du nicht, obwohl ihr Geist dich darum bittet?',
        'concept': 'Die Erzählerin der vergessenen Namen',
        'story': 'Du sammelst Namen, die aus Grabsteinen geschlagen wurden. An jedem Lagerfeuer erzählst du eine kurze Geschichte über einen davon. Eines Abends korrigiert ein Zuhörer deine Erzählung: Er behauptet, selbst dabei gewesen zu sein.',
        'tips': ['Bereite drei kurze Stimmen oder Erzählweisen vor, statt für jede Begegnung eine lange Rede zu improvisieren.', 'Frage andere Figuren nach ihren Familiengeschichten und baue deren Antworten in dein Spiel ein.', 'Halte spontane Geisterbotschaften als Vermutung deiner Figur fest, solange der DM sie nicht als Tatsache bestätigt.'],
        'bond': 'Du versprichst einem Gruppenmitglied, die Geschichte einer vermissten Person zu bewahren — auch wenn ihr sie nicht retten könnt.',
        'look': 'Ein Reiseinstrument mit geflicktem Bezug, ein Album mit Namen und eine Sammlung kleiner Erinnerungsstücke.',
    },
    'rthw-grave-domain': {
        'question': 'Wann bedeutet Fürsorge für dich Festhalten, und wann Loslassen?',
        'concept': 'Der Hüter der letzten Briefe',
        'story': 'Du überbringst Abschiedsbriefe, die nie zugestellt wurden. Ein Umschlag ist an dich selbst adressiert und trägt das Datum eines kommenden Tages. Du suchst Rat bei deinen Gefährten, bevor du ihn öffnest.',
        'tips': ['Zeige deine Überzeugungen durch kleine Handlungen: eine würdige Bestattung oder das Merken eines Namens.', 'Sprich mit der Gruppe darüber, was eure Figuren im Ernstfall füreinander entscheiden dürfen.', 'Lass Raum für andere Glaubensvorstellungen. Ein ernstes Gespräch kann interessanter sein als eine sofortige Verurteilung.'],
        'bond': 'Eine andere Figur hat dich bei einer schweren Entscheidung unterstützt. Ihr habt ein gemeinsames Ritual, um danach wieder zu euch zu finden.',
        'look': 'Schlichte Reisekleidung, helle Stoffbänder und eine Tasche für versiegelte Briefe.',
    },
    'rthw-hollow-warden': {
        'question': 'Welchen Ort schützt du, obwohl andere ihn für verflucht halten?',
        'concept': 'Die Wächterin des stillen Hains',
        'story': 'In deinem Heimatwald fehlen seit einem Winter sämtliche Vogelstimmen. Du bewachst einen Pfad, der trotzdem frische Fußspuren trägt. Als diese Spuren vor der Unterkunft der Gruppe enden, bittest du sie um Hilfe.',
        'tips': ['Wähle ein Naturmotiv für deine Beschreibungen: knarrende Wurzeln, Frost oder welke Blätter.', 'Zeige auch die fürsorgliche Seite deiner Figur, damit das Unheimliche einen persönlichen Gegenpol hat.', 'Lege vorab eine knappe Beschreibung besonderer Veränderungen fest, damit sie im Kampf nicht jedes Mal den Ablauf unterbrechen.'],
        'bond': 'Die Gruppe hat einen Reisenden gerettet, den du selbst nicht rechtzeitig erreichen konntest. Seitdem hältst du ihr den Rückweg frei.',
        'look': 'Wettergegerbter Mantel, dunkles Holz, an Ästen geflickte Riemen und ein einzelner grüner Trieb.',
    },
    'rthw-phantom': {
        'question': 'Welche Erinnerung würdest du lieber zurückgeben als besitzen?',
        'concept': 'Der Dieb des eigenen Nachrufs',
        'story': 'Du findest deinen Nachruf in einem gestohlenen Bündel Zeitungen. Darin wird ein Gruppenmitglied als Zeuge genannt. Gemeinsam sucht ihr die Druckerei, deren Adresse seit Jahrzehnten nicht mehr existiert.',
        'tips': ['Gib deiner Figur eine Arbeit oder Gewohnheit außerhalb ihrer düsteren Kräfte.', 'Nutze heimliche Erkundung, um der Gruppe konkrete Möglichkeiten zu eröffnen, und kehre mit Informationen zurück.', 'Behandle Hinweise aus deiner Vorgeschichte als Fragen an den DM, nicht als automatische Lösung eines Rätsels.'],
        'bond': 'Ein Gefährte kennt deinen echten Namen und hat ihn selbst unter Druck nicht verraten.',
        'look': 'Unauffällige Reisekleidung, ein winziger Druckstock und ein Notizblatt mit immer wieder gestrichenen Namen.',
    },
    'rthw-shadow-sorcery': {
        'question': 'Was gibt dir Sicherheit, wenn du deinen eigenen Sinnen nicht vertraust?',
        'concept': 'Die Beleuchterin des leeren Theaters',
        'story': 'Du hast einst die Lampen eines Wandertheaters betreut. Heute erkennst du dessen Bühnenbilder in fremden Häusern wieder. Eine Person aus der Gruppe besitzt eine Eintrittskarte für die letzte Vorstellung.',
        'tips': ['Wähle ein wiederkehrendes Detail deiner Magie, etwa gedämpfte Farben oder einen kurzen Moment unnatürlicher Stille.', 'Besprich Positionierung und Sicht mit der Gruppe, bevor du Effekte einsetzt, die ihren Plan beeinflussen können.', 'Lass deine Figur neben Furcht auch Humor oder Neugier zeigen. Das macht die dunkleren Momente wirkungsvoller.'],
        'bond': 'Ein Gruppenmitglied kennt ein Lied, das du aus deiner Kindheit erinnerst. Ihr versucht gemeinsam herauszufinden, woher es stammt.',
        'look': 'Indigofarbener Mantel, kleine Theaterrequisiten und eine Laterne mit geschwärztem Glas.',
    },
    'rthw-undead-patron': {
        'question': 'Welche Verpflichtung hast du verstanden — und welche nur zu verstehen geglaubt?',
        'concept': 'Die Archivarin des unmöglichen Vertrags',
        'story': 'Du hast einen Vertrag unterschrieben, dessen letzte Seite bei jedem Lesen anders aussieht. Du sammelst Abschriften früherer Fassungen. Eine davon wurde von der Hand eines Gruppenmitglieds angefertigt.',
        'tips': ['Vereinbare mit dem DM, wie oft dein Patron ins Spiel eingreift und welche Fragen zunächst offenbleiben.', 'Formuliere ein eigenes Ziel jenseits des Pakts. Deine Figur braucht Gründe, mit der Gruppe zu reisen.', 'Spiele Forderungen des Patrons als Entscheidungskonflikte; sie geben dir keine Entscheidungsgewalt über andere Spielerfiguren.'],
        'bond': 'Du hast deinen Gefährten versprochen, jede neue Forderung offenzulegen, bevor du auf sie eingehst.',
        'look': 'Dunkler Reisemantel, sorgfältig verschnürte Vertragsabschriften und ein Siegel mit abgeschliffenem Wappen.',
    },
}

def render(key):
    p = PROFILES.get(key)
    if p is None:
        return ''
    tips = ''.join(f'<li>{escape(t)}</li>' for t in p['tips'])
    return (f'<section><h2>Ein Charakterkonzept</h2><h3>{escape(p["concept"])}</h3><p>{escape(p["story"])}</p>'
            f'<h2>Verbindung zur Gruppe</h2><p>{escape(p["bond"])}</p><h2>Am Spieltisch</h2><ul>{tips}</ul>'
            f'<h2>Aussehen und Stimmung</h2><p>{escape(p["look"])}</p><h2>Deine zentrale Frage</h2><p>{escape(p["question"])}</p>'
            '<p><small>Eigene Tormentor-Konzepte und Spieltipps. Aus diesen Erzählideen entstehen keine zusätzlichen Regeln oder Fähigkeiten.</small></p>'
            f'<p><a href="{SOURCE}">Offizielle Vorstellung der sieben Unterklassen · D&D Beyond</a></p></section>')
