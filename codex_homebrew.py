"""Original Tormentor house rules, deliberately separate from official books."""
import codex_profiles

TITLE = 'Myzelgeborene · Pilzwesen'
TRAITS = [
 ('Kreaturentyp und Größe', 'Humanoid. Wähle bei der Erschaffung Klein oder Mittelgroß. Dein Pilzkörper verändert keine allgemeinen Heilungs-, Atem- oder Nahrungsregeln.'),
 ('Bewegungsrate', '9 m (30 ft).'),
 ('Dunkelsicht', '18 m (60 ft). Im dämmrigen Licht siehst du wie bei hellem Licht, in Dunkelheit wie bei dämmrigem Licht; dort erkennst du nur Grautöne.'),
 ('Pilzkunde', 'Du bist in Naturkunde geübt. Falls du darin bereits geübt bist, wähle stattdessen Überlebenskunst.'),
 ('Sporengespräch', 'Als Bonusaktion wählst du eine willige Kreatur, die du innerhalb von 9 m (30 ft) siehst. Eine Minute lang könnt ihr euch gedanklich einfache Worte senden, solange ihr höchstens 9 m (30 ft) voneinander entfernt seid und mindestens eine Sprache gemeinsam sprecht. Dies liest keine Gedanken und übermittelt keine Bilder. Du kannst das Merkmal so oft wie deinen Übungsbonus verwenden; alle Anwendungen kehren nach einer langen Rast zurück.'),
 ('Myzelruhe', 'Während einer kurzen Rast kannst du dich auf festem Boden verwurzeln. Am Ende der Rast erhältst du temporäre Trefferpunkte in Höhe deines Übungsbonus, sofern du mindestens einen Trefferpunktewürfel ausgegeben hast. Danach ist dieses Merkmal erst nach einer langen Rast wieder verfügbar. Temporäre Trefferpunkte werden nicht addiert.'),
]

def render():
    return (codex_profiles.illustration('homebrew-myzelgeborene', TITLE)
      + '<article class="book"><h2>'+TITLE+'</h2><p><b>Tormentor Homebrew · Spieltestfassung 0.1 · für die Regelausgabe 2024</b></p>'
      + '<p>Eigene spielbare Pilzwesen, keine offizielle D&amp;D-Spezies und keine Übertragung eines Mykoniden-Monsterwerteblocks. Nur mit Zustimmung des DMs verwenden.</p>'
      + '<h2>Zwischen Wurzeln und Wanderwegen</h2><p>Myzelgeborene erzählen Geschichten mit Duft, Stimme und langsam wechselnden Farben ihrer Pilzhüte. Manche bewahren die Erinnerung eines Hains, andere ziehen mit einem winzigen Garten im Rucksack durch die Welt. Ihr Aussehen, ihre Herkunft und ihre Gesinnung bestimmst du selbst.</p>'
      + '<h2>Speziesmerkmale</h2><dl>'+''.join('<dt><b>'+name+'</b></dt><dd>'+text+'</dd>' for name,text in TRAITS)+'</dl>'
      + '<h2>Klasse, Hintergrund und Entwicklung</h2><p>Attributsboni und Herkunftstalent kommen aus deinem gewählten Hintergrund. Trefferpunkte, Rettungswürfe, Startausrüstung, Zauber und die Entwicklung bis Stufe 20 kommen aus deiner Klasse. Die Spezies verleiht keine zusätzlichen Zauberplätze oder Stufenmerkmale. Übungsbonus und damit die beiden Ressourcen steigen mit der gesamten Charakterstufe.</p>'
      + '<h2>Beispiel: Mooslicht, wandernde Druidin</h2><p>Mooslicht sucht den Ursprung einer Krankheit im Heimatwald. In ihrem Gepäck wachsen drei Setzlinge, denen sie jeden Abend von der Reise erzählt. Verwende die normale Druidentabelle der Ausgabe 2024; das Pilzaussehen gewährt keine zusätzlichen Druidenkräfte.</p>'
      + '<h2>Am Spieltisch erproben</h2><p>Notiert nach drei Sessions, wie oft Sporengespräch eine Situation verändert und wie nützlich Myzelruhe ist. Die Fassung ist noch nicht durch Spieltests ausbalanciert. Vereinbart Änderungen gemeinsam, statt während einer Szene neue Vorteile anzunehmen.</p>'
      + '<p><small>Text und Spieloption: eigene Tormentor-Schöpfung, erstellt mit ChatGPT/Kodex. Begriffe und Grundsystem nach SRD 5.2.1; die SRD-Lizenz gilt nicht automatisch für diesen eigenen Entwurf.</small></p><p><a href="/codex">Buch schließen ↩</a></p></article>')
