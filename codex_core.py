"""German SRD 5.2.1 summaries, licensed CC BY 4.0; Tormentor additions."""
import json
from pathlib import Path
from html import escape
import codex_profiles
import codex_spell_help

CLASSES=json.loads((Path(__file__).parent/'assets/srd/classes-2024.json').read_text(encoding='utf-8'))
CLASS_LEVELS=json.loads((Path(__file__).parent/'assets/srd/levels-2024.json').read_text(encoding='utf-8'))
SOURCE='https://media.dndbeyond.com/compendium-images/srd/5.2/DE_SRD_CC_v5.2.1.pdf'
ATTRIBUTION='Dieses Werk enthält Material aus dem Systemreferenzdokument 5.2.1 („SRD 5.2.1“) von Wizards of the Coast LLC, verfügbar unter https://www.dndbeyond.com/srd. Das SRD 5.2.1 ist lizenziert gemäß Creative Commons Namensnennung 4.0 International Public License (verfügbar unter https://creativecommons.org/licenses/by/4.0/legalcode.de).'
TIPS={
 'barbar':'Plane, wie du deine Verbündeten erreichst und schützt. Ein Rücksichtsloser Angriff erleichtert Treffer, öffnet aber auch deine Verteidigung.',
 'barde':'Sprich vor schwierigen Szenen mit der Gruppe ab, wer welche Aufgabe übernimmt. Halte Inspiration und deine ausgewählten Zauber griffbereit.',
 'druide':'Lege passende Tierformen und Zauber vor der Session bereit. Wähle Formen nicht nur nach Kampfstärke, sondern auch für Erkundung und Reisen.',
 'hexenmeister':'Behalte deine begrenzten Ressourcen und Rastmöglichkeiten im Blick. Gib deinem Pakt ein persönliches Thema, das Abenteuer für die ganze Gruppe eröffnet.',
 'kaempfer':'Notiere die Eigenschaften deiner bevorzugten Waffen. Positionierung und eine passende Waffenauswahl können ebenso wichtig sein wie Schaden.',
 'kleriker':'Bereite neben Heilung auch Unterstützung und Lösungen für Hindernisse vor. Kläre, welche Rolle du im Kampf übernehmen möchtest.',
 'magier':'Sortiere dein Zauberbuch nach Aufgaben: Schutz, Kontrolle, Erkundung und Schaden. Prüfe vor dem Zug Reichweite und Konzentration.',
 'moench':'Nutze Bewegung für ein konkretes Ziel. Plane den Rückweg, bevor du allein zwischen Gegnern landest.',
 'paladin':'Formuliere deinen Schwur als Hilfe bei Entscheidungen. Verbinde ihn mit der Gruppe, statt ihn anderen Figuren aufzuzwingen.',
 'schurke':'Bereite Erkundung so vor, dass alle von deinen Informationen profitieren. Kläre vor Angriffen, ob die Voraussetzungen deiner Merkmale erfüllt sind.',
 'waldlaeufer':'Nutze deine Erkundungsfertigkeiten aktiv: Frage nach Spuren, Gelände und sicheren Wegen. Behalte Konzentration bei deiner Zauberauswahl im Blick.',
 'zauberer':'Wähle Zauber, die unterschiedliche Aufgaben erfüllen. Lege dir kurze Notizen zu deinen Metamagie-Optionen an.',
}
LEVELS=[
 ('Kampfrausch, Ungerüstete Verteidigung, Waffenbeherrschung',2,2,2),
 ('Gefahrengespür, Rücksichtsloser Angriff',2,2,2),('Unterklasse, Urwissen',3,2,2),
 ('Attributswerterhöhung',3,2,3),('Zusätzlicher Angriff, Schnelle Bewegung',3,2,3),
 ('Unterklassenmerkmal',4,2,3),('Instinktiver Sprung, Wilder Instinkt',4,2,3),
 ('Attributswerterhöhung',4,2,3),('Brutaler Hieb',4,3,3),('Unterklassenmerkmal',4,3,4),
 ('Unerbittlicher Kampfrausch',4,3,4),('Attributswerterhöhung',5,3,4),
 ('Verbesserter Brutaler Hieb',5,3,4),('Unterklassenmerkmal',5,3,4),
 ('Anhaltender Kampfrausch',5,3,4),('Attributswerterhöhung',5,4,4),
 ('Verbesserter Brutaler Hieb',6,4,4),('Unbändige Stärke',6,4,4),('Epische Gabe',6,4,4),('Meister der Wildnis',6,4,4)]

SPECIES={
 'drachenbluetiger':('Drachenblütiger',94,'Mittelgroß','9 m (30 ft)','18 m (60 ft)',[
 'Wähle eine drakonische Abstammung. Sie bestimmt die Schadensart deiner Odemwaffe und deiner Resistenz: Blitz, Feuer, Gift, Kälte oder Säure.',
 'Odemwaffe: Ersetzt einen Angriff deiner Angriffsaktion. Wahlweise Kegel 4,5 m (15 ft) oder Linie 9 m (30 ft) lang und 1,5 m (5 ft) breit. Geschicklichkeitsrettungswurf gegen SG 8 + Konstitutionsmodifikator + Übungsbonus; bei Erfolg halber Schaden.',
 'Odemschaden: 1W10; ab Charakterstufe 5: 2W10, ab 11: 3W10, ab 17: 4W10. Anwendungen entsprechend dem Übungsbonus, erneuert nach langer Rast.',
 'Ab Stufe 5: Als Bonusaktion zehn Minuten geisterhafte Flügel; Flugbewegungsrate entspricht der Bewegungsrate. Einmal pro langer Rast, endet auch bei Kampfunfähigkeit oder freiwilligem Verwerfen.']),
 'elf':('Elf',94,'Mittelgroß','9 m (30 ft)','18 m (60 ft); Drow 36 m (120 ft)',[
 'Feenblut gewährt Vorteil auf Rettungswürfe gegen Bezaubert. Wähle Übung in Motiv erkennen, Überlebenskunst oder Wahrnehmung.',
 'Trance: Kein Schlaf nötig, magischer Schlaf wirkt nicht. Vier Stunden bewusste Trance können eine lange Rast ersetzen.',
 'Wähle Drow, Hochelf oder Waldelf als Abstammung. Die jeweiligen Zauber und die Entwicklung auf Charakterstufe 3 und 5 stehen in der Quellentabelle auf Seite 95.']),
 'gnom':('Gnom',95,'Klein','9 m (30 ft)','18 m (60 ft)',[
 'Gnomische Gerissenheit gewährt Vorteil bei Intelligenz-, Weisheits- und Charismarettungswürfen.',
 'Felsengnom: Ausbessern und Taschenspielerei; mit letzterem können kleine Uhrwerkgeräte entstehen. Waldgnom: Einfache Illusion und Mit Tieren sprechen.',
 'Wähle Intelligenz, Weisheit oder Charisma als Zauberattribut deiner Abstammung. Die genauen Geräte- und Anwendungsregeln stehen auf Seite 95.']),
 'goliath':('Goliath',95,'Mittelgroß','10,5 m (35 ft)','Keine durch diese Spezies',[
 'Riesische Abstammung: Wähle eine Gabe von Frost-, Stein-, Feuer-, Hügel-, Sturm- oder Wolkenriesen. Anwendungen entsprechen dem Übungsbonus und erneuern sich nach langer Rast.',
 'Große Gestalt ab Stufe 5: Als Bonusaktion für zehn Minuten Groß werden, sofern Platz vorhanden ist. Vorteil auf Stärkewürfe und +3 m (10 ft) Bewegung; einmal pro langer Rast.',
 'Kräftiger Körperbau: Vorteil auf Attributswürfe zum Beenden von Gepackt; für die Traglast zählt die nächsthöhere Größenkategorie. Die sechs Gaben sind auf Seite 96 beschrieben.']),
 'halbling':('Halbling',96,'Klein','9 m (30 ft)','Keine durch diese Spezies',[
 'Halblingsglück: Eine 1 bei einer W20-Prüfung darf neu gewürfelt werden; das neue Ergebnis gilt.',
 'Tapferkeit: Vorteil auf Rettungswürfe gegen Verängstigt.',
 'Halblingsgewandtheit erlaubt Bewegung durch den Bereich größerer Kreaturen, aber kein Anhalten darin. Angeborene Verstohlenheit erlaubt Verstecken auch hinter einer Kreatur, die mindestens eine Größenkategorie größer ist.']),
 'mensch':('Mensch',96,'Klein oder mittelgroß','9 m (30 ft)','Keine durch diese Spezies',[
 'Einfallsreich: Nach jeder langen Rast erhältst du Heldische Inspiration.',
 'Geschickt: Wähle eine Fertigkeit, in der du geübt bist.',
 'Vielseitig: Wähle ein zusätzliches Herkunftstalent. Die verfügbaren SRD-Talente beginnen auf Seite 98.']),
 'tiefling':('Tiefling',96,'Klein oder mittelgroß','9 m (30 ft)','18 m (60 ft)',[
 'Außerweltliche Präsenz verleiht Thaumaturgie.',
 'Unholdisches Erbe: Abyssisch gewährt Giftresistenz, Chthonisch Resistenz gegen nekrotischen Schaden, Infernalisch Feuerresistenz. Jedes Erbe bringt einen weiteren Zaubertrick und Zauber auf Charakterstufe 3 und 5.',
 'Wähle Intelligenz, Weisheit oder Charisma als Zauberattribut. Die Erbe-Zauber sind stets vorbereitet und können jeweils einmal pro langer Rast ohne Zauberplatz gewirkt werden; passende Zauberplätze sind ebenfalls nutzbar. Die vollständige Erbetabelle steht auf Seite 97.']),
 'zwerg':('Zwerg',97,'Mittelgroß','9 m (30 ft)','36 m (120 ft)',[
 'Zwergische Unverwüstlichkeit: Resistenz gegen Giftschaden und Vorteil auf Rettungswürfe gegen Vergiftet.',
 'Zwergische Zähigkeit erhöht das Trefferpunktemaximum um 1 auf Stufe 1 und um einen weiteren Punkt bei jedem Stufenaufstieg.',
 'Steingespür: Als Bonusaktion zehn Minuten Erschütterungssinn 18 m (60 ft), nutzbar bei Kontakt mit natürlichem oder bearbeitetem Stein. Anwendungen entsprechend dem Übungsbonus, erneuert nach langer Rast.']),
}

def attribution(page):
    return f'<p><a href="{SOURCE}#page={page}">Deutsches SRD 5.2.1 · ab Seite {page}</a> · <a href="https://creativecommons.org/licenses/by/4.0/legalcode.de">CC BY 4.0</a></p><p><small>{escape(ATTRIBUTION)} Bearbeitung: Tormentor, gekürzt und neu gegliedert; feet-Angaben ergänzt.</small></p>'

def barbar():
    rows=''.join(f'<tr><td>{i}</td><td>+{2+(i-1)//4}</td><td>{escape(name)}</td><td>{uses}</td><td>+{damage}</td><td>{weapons}</td></tr>' for i,(name,uses,damage,weapons) in enumerate(LEVELS,1))
    return ('<h2>Barbar: Stufe 1 bis 20</h2><div style="overflow-x:auto"><table><thead><tr><th>Stufe</th><th>Übungsbonus</th><th>Neue Merkmale</th><th>Kampfrausch-Anzahl</th><th>Kampfrausch-Schaden</th><th>Waffenarten mit Meisterschaft</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
    '<h2>Die wichtigsten Regeln</h2><p><b>Kampfrausch:</b> Beginnt als Bonusaktion ohne schwere Rüstung. Resistenz gegen Hieb-, Stich- und Wuchtschaden, Vorteil bei Stärkewürfen und -rettungswürfen sowie Zusatzschaden bei stärkebasierten Waffen- und waffenlosen Angriffen. Zauber und Konzentration sind währenddessen nicht möglich.</p>'
    '<p>Er hält zunächst bis zum Ende des nächsten Zugs. Verlängern durch einen Angriffswurf gegen einen Gegner, einen erzwungenen Rettungswurf eines Gegners oder eine Bonusaktion; maximal zehn Minuten. Schwere Rüstung und Kampfunfähigkeit beenden ihn vorzeitig. Eine kurze Rast gibt eine Anwendung zurück, eine lange Rast alle.</p>'
    '<p><b>Ungerüstete Verteidigung:</b> RK = 10 + Geschicklichkeitsmodifikator + Konstitutionsmodifikator, sofern du keine Rüstung trägst; ein Schild ist erlaubt.</p>'
    '<p><b>Rücksichtsloser Angriff:</b> Beim ersten Angriffswurf deines Zugs entscheiden. Deine stärkebasierten Angriffe haben bis zum Beginn deines nächsten Zugs Vorteil; Angriffe gegen dich ebenfalls.</p>'
    '<p><b>Ab Stufe 5:</b> Zwei Angriffe je Angriffsaktion in deinem Zug; ohne schwere Rüstung +3 m (10 ft) Bewegung.</p>'
    '<p><b>Brutaler Hieb ab Stufe 9:</b> Beim Rücksichtslosen Angriff für einen nicht benachteiligten stärkebasierten Angriff in deinem Zug auf den Vorteil verzichten. Bei Treffer +1W10 Schaden und ein Zusatzeffekt: etwa 4,5 m (15 ft) Wegstoßen oder die gegnerische Bewegung um 4,5 m (15 ft) senken. Die Einzelheiten und Verbesserungen stehen auf Seite 35.</p>'
    '<p><b>Stufe 20:</b> Stärke und Konstitution steigen um je 4, jeweils bis höchstens 25.</p>'
    '<p><b>Unterklasse im SRD:</b> Pfad des Berserkers. Die vollständigen Unterklassenmerkmale stehen auf Seite 35–36. Diese Seite ist eine Regelübersicht; Einzelregeln zu sämtlichen Tabellenmerkmalen sind in der Quelle nachlesbar.</p>')

def level_tables(key):
    data=CLASS_LEVELS[key]
    def table(headers, rows, caption):
        return '<div class="level-table" tabindex="0" role="region" aria-label="'+escape(caption)+'"><table><caption>'+escape(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    body='<h2>Stufe 1 bis 20</h2><p>Die Stufen beziehen sich auf diese Klasse. Zahlen bei Ressourcen geben den jeweiligen Gesamtwert an. Ein Strich bedeutet: kein neuer Eintrag beziehungsweise keine Anwendungen oder Plätze.</p>'
    body+=table(['Stufe','Übungsbonus','Klassenmerkmale']+data['headers'], [[r['level'],r['bonus'],r['features']]+r['values'] for r in data['rows']],CLASSES[key]['name']+' · Stufenentwicklung')
    if data['slot_grades']:
        body+='<h2>Zauberplätze nach Zaubergrad</h2>'+table(['Stufe']+['Grad '+str(i) for i in range(1,data['slot_grades']+1)], [[r['level']]+r['slots'] for r in data['rows']], 'Zauberplätze · Stufe 1 bis 20')
    if key=='hexenmeister':
        body+='<p>Paktmagie-Plätze erneuern sich nach kurzer oder langer Rast. Mystische Arkana sind eigene Anwendungen und zählen nicht zu diesen Plätzen.</p>'
    return body+f'<p>Quelle der Tabelle: <a href="{SOURCE}#page={data["page"]}">Deutsches SRD 5.2.1, Seite {data["page"]}</a>. Zusätzliche Zauber und Merkmale deiner Unterklasse sowie Klassenkombinationen können weitere Regeln mitbringen. Die Beschreibungen der einzelnen Merkmale stehen im verlinkten Klassenkapitel.</p>'

def class_page(key, subclasses_html=''):
    d=CLASSES[key]
    rows=''.join(f'<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>' for k,v in d['stats'].items())
    return (codex_profiles.illustration('srd-'+key,d['name'])+f'<article class="book"><p>Klasse · 2024 · SRD 5.2.1</p><h2>{d["name"]}</h2><h2>Start auf Stufe 1</h2><table>{rows}</table><p>Diese Angaben gelten für den Einstieg mit dieser Klasse. Klassenkombinationen haben eigene Erwerbsregeln.</p>'
            +subclasses_html+codex_spell_help.render(d['name'])+(barbar() if key=='barbar' else level_tables(key))
            +f'<h2>Spieltipp</h2><p>{escape(TIPS[key])}</p><small>Eigener Tormentor-Spieltipp.</small>'+attribution(d['page'])+'<p><a href="/codex/2024">← Inhaltsverzeichnis</a></p></article>')

def species_page(key):
    name,page,size,speed,vision,traits=SPECIES[key]
    return codex_profiles.illustration('species-'+key,name) + species_rules(key)

def species_rules(key):
    name,page,size,speed,vision,traits=SPECIES[key]
    return (f'<article class="book"><p>Spezies · 2024 · SRD 5.2.1</p><h2>{name}</h2><table><tr><th>Kreaturentyp</th><td>Humanoide</td></tr><tr><th>Größenkategorie</th><td>{size}</td></tr><tr><th>Bewegung</th><td>{speed}</td></tr><tr><th>Dunkelsicht</th><td>{vision}</td></tr></table><h2>Merkmale im Überblick</h2><ul>'
            +''.join(f'<li>{escape(t)}</li>' for t in traits)+'</ul><h2>Deine Herkunft</h2><p>Gesinnung und Persönlichkeit bestimmst du für deine Figur. Klasse und Hintergrund liefern Startausrüstung; die Spezies allein legt keinen Beruf oder Kampfstil fest.</p>'+attribution(page)+'<p><a href="/codex/2024">← Inhaltsverzeichnis</a></p></article>')
