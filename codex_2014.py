"""German, edition-specific SRD 5.1 summaries and source-derived level tables."""
import json
from html import escape
from pathlib import Path
import codex_profiles
import codex_spell_help

SOURCE = 'https://media.wizards.com/2023/downloads/dnd/SRD_CC_v5.1_DE.pdf'
ATTRIBUTION = 'Dieses Werk enthält Material aus dem Systemreferenzdokument 5.1 („SRD 5.1”) von Wizards of the Coast LLC, das unter https://dnd.wizards.com/de/resources/systems-reference-document verfügbar ist. Das SRD 5.1 ist lizenziert gemäß der Lizenz Creative Commons Namensnennung 4.0 International, die unter https://creativecommons.org/licenses/by/4.0/legalcode.de verfügbar ist.'
LEVELS = json.loads((Path(__file__).parent / 'assets/srd/levels-2014.json').read_text(encoding='utf-8'))

# name, hit die, saving throws, armor, subclass, key rules, play example
CLASSES = {
 'barbar': ('Barbar', 12, 'Stärke, Konstitution', 'Leicht, mittelschwer, Schilde', 'Pfad des Berserkers (ab Stufe 3)', [
  ('Kampfrausch', 'Als Bonusaktion beginnen; eine Minute lang. Ohne schwere Rüstung: Vorteil auf Stärkewürfe und -rettungswürfe, Zusatzschaden bei stärkebasierten Nahkampfwaffenangriffen sowie Resistenz gegen Hieb-, Stich- und Wuchtschaden. Kein Zauberwirken und keine Konzentration. Endet bei Bewusstlosigkeit oder wenn dein Zug endet und du seit deinem letzten Zug weder einen Gegner angegriffen noch Schaden erlitten hast; freiwilliges Beenden als Bonusaktion. Anwendungen erneuern sich nach langer Rast.'),
  ('Verteidigung und Angriff', 'Ohne Rüstung beträgt die RK 10 + Geschicklichkeitsmodifikator + Konstitutionsmodifikator; ein Schild ist erlaubt. Ab Stufe 2 kannst du beim ersten Angriff deines Zugs Rücksichtslosen Angriff wählen: Vorteil für stärkebasierte Nahkampfwaffenangriffe in diesem Zug, aber Vorteil für Angriffe gegen dich bis zu deinem nächsten Zug.'),
  ('Entwicklung', 'Ab Stufe 5 zwei Angriffe je Angriffsaktion und ohne schwere Rüstung +3 m (10 ft) Bewegung. Brutale kritische Treffer erhalten zusätzliche Waffenwürfel ab Stufe 9, 13 und 17. Auf Stufe 20 steigen Stärke und Konstitution um je 4, bis maximal 24.'),
  ('Berserker', 'Ab Stufe 3 erlaubt Raserei während des Kampfrauschs ab den folgenden Zügen je einen Nahkampfwaffenangriff als Bonusaktion. Danach erhältst du eine Erschöpfungsstufe. Weitere Merkmale schützen vor Bezaubert und Verängstigt im Kampfrausch und ermöglichen Einschüchterung sowie Vergeltung.')],
  'Mit Stärke 16 und einer Zweihandaxt verursacht ein normaler Treffer im Kampfrausch auf Stufe 1 insgesamt 1W12 + 3 + 2 Schaden.'),
 'barde': ('Barde', 8, 'Geschicklichkeit, Charisma', 'Leichte Rüstung', 'Schule des Wissens (ab Stufe 3)', [
  ('Zauberwirken', 'Charisma ist dein Zauberattribut. Du lernst eine begrenzte Zahl von Zaubern; die Stufentabelle nennt Zaubertricks, bekannte Zauber und Plätze. Plätze erneuern sich nach langer Rast. Bekannte Bardenzauber mit Ritualkennzeichen kannst du als Ritual wirken.'),
  ('Bardische Inspiration', 'Als Bonusaktion erhält eine andere Kreatur, die dich innerhalb von 18 m (60 ft) hören kann, einen Inspirationswürfel für zehn Minuten. Sie kann ihn zu einem Attributs-, Angriffs- oder Rettungswurf addieren: nach dem W20-Wurf, bevor Erfolg oder Misserfolg feststeht. Anwendungen gleich Charismamodifikator, mindestens eine. Zunächst lange Rast; ab Stufe 5 auch kurze Rast. Würfel: W6, ab Stufe 5 W8, ab 10 W10, ab 15 W12.'),
  ('Fertigkeiten und fremde Magie', 'Ab Stufe 2 addierst du den halben, abgerundeten Übungsbonus auf Attributswürfe, die nicht bereits deinen Übungsbonus erhalten. Expertise verdoppelt ihn für je zwei gewählte geübte Fertigkeiten auf Stufe 3 und 10. Magische Geheimnisse auf Stufe 10, 14 und 18 eröffnen je zwei Zauber beliebiger Klassen.'),
  ('Schule des Wissens', 'Auf Stufe 3 drei weitere Fertigkeiten und Schneidende Worte: Mit Reaktion und Inspiration einen gegnerischen Angriffs-, Attributs- oder Schadenswurf innerhalb von 18 m (60 ft) senken, wenn das Ziel dich hören kann und nicht gegen Bezaubert immun ist. Weitere Magische Geheimnisse auf Stufe 6; auf Stufe 14 Inspiration für eigene Attributswürfe.')],
  'Bei Charisma 16 stehen dir drei Inspirationen zur Verfügung. Auf Bardenstufe 5 sind es W8; nach einer kurzen Rast erhältst du verbrauchte Anwendungen zurück.'),
 'druide': ('Druide', 8, 'Intelligenz, Weisheit', 'Leicht, mittelschwer, Schilde; laut Klassenregel kein Metall', 'Zirkel des Landes (ab Stufe 2)', [
  ('Zauberwirken', 'Weisheit ist dein Zauberattribut. Nach langer Rast bereitest du Weisheitsmodifikator + Druidenstufe Zauber vor, mindestens einen; nur Grade, für die du Plätze hast. Vorbereitete Ritualzauber kannst du als Ritual wirken. Plätze erneuern sich nach langer Rast. Du kennst außerdem die Geheimsprache Druidisch.'),
  ('Tiergestalt', 'Ab Stufe 2 als Aktion in ein bereits gesehenes Tier verwandeln, zweimal pro kurzer oder langer Rast. Deine Trefferpunkte werden durch die Trefferpunkte des Tiers ersetzt; auch die Trefferwürfel des Tiers übernimmst du. Schaden am Tier wird zuerst dort abgezogen. Verwandelst du dich freiwillig zurück, erhältst du die Trefferpunkte zurück, die du vor der Verwandlung hattest. Sinkst du in Tiergestalt auf 0 Trefferpunkte, verwandelst du dich automatisch zurück und nur überschüssiger Schaden wird auf deine normale Gestalt übertragen (Beispiel: 1 TP im Tier, 10 Schaden = 9 Schaden auf deine normale Gestalt). Du wirst dadurch nicht bewusstlos, solange deine normalen Trefferpunkte nicht auf 0 sinken. Dauer: halbe Druidenstufe, abgerundet, in Stunden. Höchstens HG 1/4 ohne Schwimm- oder Flugbewegung; ab Stufe 4 HG 1/2 ohne Flugbewegung; ab Stufe 8 HG 1 einschließlich Flugbewegung.'),
  ('In Tierform', 'Stärke, Geschicklichkeit, Konstitution und Trefferpunkte stammen grundsätzlich aus der Tierform; geistige Attribute und Persönlichkeit bleiben. Beim Rückverwandeln kehren die vorherigen Trefferpunkte zurück. Überschüssiger Schaden beim Fallen auf 0 TP wird übertragen. Normalerweise kannst du nicht zaubern, aber bereits bestehende Konzentration bleibt möglich. Die Quelle beschreibt Ausrüstung, Übung und Sonderfälle.'),
  ('Zirkel des Landes', 'Ein zusätzlicher Druidenzaubertrick und Natürliche Erholung ab Stufe 2. Einmal pro Tag bei kurzer Rast Plätze mit insgesamt höchstens halber Druidenstufe, aufgerundet, zurückgewinnen; keine Plätze ab Grad 6. Landschaftsabhängige Zirkelzauber sind stets vorbereitet. Auf Stufe 20 ist Tiergestalt unbegrenzt nutzbar.')],
  'Ein Druide auf Stufe 4 mit Weisheit 16 bereitet sieben Zauber vor. Seine Tiergestalt darf bis HG 1/2 reichen und schwimmen, aber noch nicht fliegen.'),
 'hexenmeister': ('Hexenmeister', 8, 'Weisheit, Charisma', 'Leichte Rüstung', 'Der Unhold (ab Stufe 1)', [
  ('Paktmagie', 'Charisma ist dein Zauberattribut. Deine wenigen Paktplätze haben alle denselben Grad und erneuern sich nach kurzer oder langer Rast. Bekannte Zauber und Platzgrad stehen in der Tabelle. Ab Stufe 11 gewähren Mystische Arkana je einen eigenen Zauber des Grades 6, später 7, 8 und 9; jeder davon einmal pro langer Rast ohne Paktplatz.'),
  ('Anrufungen und Pakt', 'Ab Stufe 2 wählst du Schauerliche Anrufungen; Voraussetzungen und einzelne Effekte stehen auf Seite 23–25. Auf Stufe 3 wählst du den Pakt der Kette, der Klinge oder des Buches. Diese Wahl ist vom Schutzherrn getrennt und bringt einen besonderen Vertrauten, eine Paktwaffe oder zusätzliche Zaubertricks.'),
  ('Der Unhold', 'Wenn du eine feindliche Kreatur auf 0 TP bringst, erhältst du temporäre TP gleich Charismamodifikator + Hexenmeisterstufe, mindestens 1. Ab Stufe 6 kannst du einmal pro kurzer oder langer Rast 1W10 zu einem Attributs- oder Rettungswurf addieren, bevor das Ergebnis feststeht. Höhere Merkmale verleihen anpassbare Schadensresistenz und Höllenqual.'),
  ('Zauberauswahl', 'Die erweiterte Zauberliste des Schutzherrn erweitert die Auswahl beim Lernen; sie macht diese Zauber nicht automatisch bekannt. Mystischer Meister auf Stufe 20 stellt nach einer Minute Anrufung alle Paktplätze wieder her, einmal pro langer Rast.')],
  'Auf Stufe 5 hast du zwei Paktplätze des 3. Grades. Beide kehren nach einer kurzen Rast zurück; dies sind keine gewöhnlichen Zauberplätze mit mehreren Graden.'),
 'kaempfer': ('Kämpfer', 10, 'Stärke, Konstitution', 'Alle Rüstungen, Schilde', 'Champion (ab Stufe 3)', [
  ('Kampfstil', 'Wähle Bogenschießen, Duellieren, Kampf mit großen Waffen, Leibwache, Verteidigung oder Zwei-Waffen-Kampf. Beispielsweise gibt Bogenschießen +2 auf Angriffswürfe mit Fernkampfwaffen; Verteidigung gibt beim Tragen einer Rüstung +1 RK.'),
  ('Durchschnaufen und Tatendrang', 'Durchschnaufen heilt als Bonusaktion 1W10 + Kämpferstufe TP, einmal pro kurzer oder langer Rast. Tatendrang gibt ab Stufe 2 eine zusätzliche Aktion im eigenen Zug, einmal pro kurzer oder langer Rast; ab Stufe 17 zweimal, aber höchstens einmal im selben Zug.'),
  ('Angriffe und Rettungswürfe', 'Je Angriffsaktion zwei Angriffe ab Stufe 5, drei ab Stufe 11, vier ab Stufe 20. Unbeugsamkeit erlaubt ab Stufe 9 einen misslungenen Rettungswurf zu wiederholen; das neue Ergebnis gilt. Eine Anwendung pro langer Rast, ab Stufe 13 zwei, ab Stufe 17 drei.'),
  ('Champion', 'Ab Stufe 3 erzielen Waffenangriffe bei 19 oder 20 kritische Treffer; ab Stufe 15 bei 18–20. Hinzu kommen Bemerkenswerter Athlet auf Stufe 7, ein weiterer Kampfstil auf Stufe 10 und Überlebenskünstler auf Stufe 18.')],
  'Auf Kämpferstufe 5 ergeben Angriffsaktion und Tatendrang zusammen vier Angriffe. Tatendrang gewährt keine zweite Bonusaktion.'),
 'kleriker': ('Kleriker', 8, 'Weisheit, Charisma', 'Leicht, mittelschwer, Schilde; weitere durch Domäne', 'Domäne des Lebens (ab Stufe 1)', [
  ('Zauberwirken', 'Weisheit ist dein Zauberattribut. Du bereitest Weisheitsmodifikator + Klerikerstufe Zauber vor, mindestens einen. Domänenzauber sind stets vorbereitet und zählen nicht gegen diese Zahl. Vorbereitete Ritualzauber sind als Ritual nutzbar; Plätze erneuern sich nach langer Rast.'),
  ('Göttliche Macht fokussieren', 'Ab Stufe 2 einmal pro kurzer oder langer Rast, ab Stufe 6 zweimal, ab Stufe 18 dreimal. Wähle bei jeder Anwendung einen verfügbaren Effekt. Untote vertreiben verwendet eine Aktion: Untote innerhalb von 9 m (30 ft), die dich sehen oder hören, machen einen Weisheitsrettungswurf; bei Misserfolg bis zu einer Minute oder bis zu Schaden vertrieben.'),
  ('Untote und Intervention', 'Ab Stufe 5 werden beim misslungenen Vertreibungsrettungswurf Untote bis HG 1/2 zerstört; höhere Grenzen stehen in der Tabelle. Göttliche Intervention ab Stufe 10: Als Aktion um Hilfe bitten, W100 höchstens gleich Klerikerstufe. Bei Erfolg erst nach sieben Tagen erneut; sonst nach langer Rast. Auf Stufe 20 gelingt die Bitte ohne Wurf.'),
  ('Domäne des Lebens', 'Übung mit schwerer Rüstung. Jünger des Lebens verbessert Heilzauber ab Grad 1 um 2 + Zaubergrad TP. Leben erhalten verteilt ab Stufe 2 über Göttliche Macht fokussieren einen Heilvorrat von fünfmal Klerikerstufe innerhalb von 9 m (30 ft), aber höchstens bis zur Hälfte des jeweiligen TP-Maximums und nicht auf Untote oder Konstrukte.')],
  'Mit Weisheit 16 und Klerikerstufe 3 bereitest du sechs Zauber vor, zusätzlich zu den Domänenzaubern. Deine Domäne wird bereits auf Stufe 1 gewählt.'),
 'magier': ('Magier', 6, 'Intelligenz, Weisheit', 'Keine', 'Schule der Hervorrufung (ab Stufe 2)', [
  ('Zauberbuch', 'Intelligenz ist dein Zauberattribut. Dein Buch beginnt mit sechs Magierzaubern des 1. Grades; pro Magierstufe kommen zwei passende Zauber hinzu. Weitere gefundene Zauber können nach den Kopierregeln ins Buch gelangen. Vorbereitet: Intelligenzmodifikator + Magierstufe, mindestens einer. Ritualzauber im Buch müssen für das Ritual nicht vorbereitet sein.'),
  ('Arkane Erholung', 'Einmal pro Tag bei kurzer Rast verbrauchte Plätze zurückgewinnen: Summe der Grade höchstens halbe Magierstufe, aufgerundet; kein Platz des 6. Grades oder höher. Eine lange Rast erneuert alle Plätze.'),
  ('Schule der Hervorrufung', 'Zeit und Gold zum Kopieren von Hervorrufungszaubern sind halbiert. Zauber formen schützt ab Stufe 2 ausgewählte sichtbare Kreaturen vor eigenen Hervorrufungszaubern mit Rettungswurf: bis zu 1 + Zaubergrad Kreaturen bestehen automatisch und nehmen keinen Schaden, wenn der erfolgreiche Wurf sonst halbiert. Weitere Merkmale verbessern Zaubertricks, Schaden und Überladen.'),
  ('Hohe Stufen', 'Zaubermeisterschaft auf Stufe 18 erlaubt einen gewählten Zauber des 1. und einen des 2. Grades aus dem Buch auf ihrem niedrigsten Grad ohne Platz, sofern vorbereitet. Lieblingszauber auf Stufe 20 betrifft zwei Zauber des 3. Grades: stets vorbereitet und jeweils einmal pro kurzer oder langer Rast ohne Platz.')],
  'Ein Magier auf Stufe 5 mit Intelligenz 18 bereitet neun Zauber vor. Arkane Erholung kann beispielsweise einen Platz des 3. Grades oder einen des 2. und einen des 1. Grades erneuern.'),
 'moench': ('Mönch', 8, 'Stärke, Geschicklichkeit', 'Keine', 'Weg der Offenen Hand (ab Stufe 3)', [
  ('Kampfkünste', 'Ohne Rüstung und Schild, unbewaffnet oder nur mit Mönchwaffen: Geschicklichkeit statt Stärke für entsprechende Angriffe und Schaden; Kampfkünste-Würfel statt normalem Schaden. Nach einer Angriffsaktion mit Mönchwaffe oder unbewaffnetem Angriff ist ein unbewaffneter Angriff als Bonusaktion möglich. Mönchwaffen sind Kurzschwerter und einfache Nahkampfwaffen ohne schwer oder zweihändig.'),
  ('Ki', 'Ab Stufe 2 Ki-Punkte gleich Mönchstufe; Erholung nach kurzer oder langer Rast mit mindestens 30 Minuten Meditation. Für 1 Ki erlaubt Schlaghagel direkt nach der Angriffsaktion zwei unbewaffnete Angriffe als Bonusaktion. Alternativ mit 1 Ki Ausweichen als Bonusaktion oder Spurt/Rückzug als Bonusaktion mit verdoppelter Sprungweite für den Zug.'),
  ('Verteidigung und Betäubung', 'Ohne Rüstung und Schild RK 10 + Geschicklichkeitsmodifikator + Weisheitsmodifikator. Ab Stufe 5 zwei Angriffe pro Angriffsaktion. Nach einem Treffer mit Nahkampfwaffenangriff kannst du 1 Ki für Betäubenden Schlag ausgeben: Konstitutionsrettungswurf gegen 8 + Übungsbonus + Weisheitsmodifikator, sonst bis Ende deines nächsten Zugs betäubt.'),
  ('Weg der Offenen Hand', 'Schlaghagel-Treffer können ab Stufe 3 zu Boden werfen (Geschicklichkeitsrettungswurf), bis 4,5 m (15 ft) wegstoßen (Stärkerettungswurf) oder Reaktionen bis Ende deines nächsten Zugs verhindern. Weitere Merkmale: Selbstheilung auf Stufe 6, Schutz auf Stufe 11 und Vibrierende Handfläche auf Stufe 17.')],
  'Auf Stufe 5 sind mit Angriffsaktion und Schlaghagel vier Angriffe möglich. Das kostet 1 Ki und deine Bonusaktion; Betäubender Schlag kostet gegebenenfalls zusätzlich Ki.'),
 'paladin': ('Paladin', 10, 'Weisheit, Charisma', 'Alle Rüstungen, Schilde', 'Schwur der Hingabe (ab Stufe 3)', [
  ('Handauflegen', 'Heilvorrat von fünfmal Paladinstufe pro langer Rast. Mit einer Aktion eine Kreatur berühren und beliebig viele verbleibende Punkte heilen; fünf Punkte können stattdessen eine Krankheit oder ein Gift neutralisieren. Keine Wirkung auf Untote oder Konstrukte.'),
  ('Zauber und Niederstrecken', 'Ab Stufe 2 Charisma als Zauberattribut; vorbereitet werden Charismamodifikator + halbe Paladinstufe, abgerundet, mindestens ein Zauber. Bei Treffer mit Nahkampfwaffenangriff darfst du einen Zauberplatz für Göttliches Niederstrecken ausgeben: 2W8 gleißend für Grad 1, +1W8 je weiterem Grad bis 5W8. Gegen Untote oder Unholde nochmals +1W8, bis 6W8. Dies ist 2014 ein Klassenmerkmal ohne Bonusaktion.'),
  ('Schützende Auren', 'Ab Stufe 6 erhalten du und befreundete Kreaturen innerhalb von 3 m (10 ft) einen Bonus auf Rettungswürfe in Höhe deines Charismamodifikators, mindestens +1, solange du bei Bewusstsein bist. Ab Stufe 10 schützt Aura der Tapferkeit dort vor Verängstigt. Reichweiten steigen auf Stufe 18 auf 9 m (30 ft).'),
  ('Schwur der Hingabe', 'Schwurzauber sind stets vorbereitet. Göttliche Macht fokussieren ab Stufe 3: Heilige Waffe oder Unheilige vertreiben, einmal pro kurzer oder langer Rast. Höhere Merkmale schützen vor Bezaubert, gewähren Schutz vor Gut und Böse und auf Stufe 20 eine Heilige Aura.')],
  'Ein Treffer mit Langschwert, Stärke 16 und Niederstrecken über einen Platz des 1. Grades verursacht 1W8 + 3 Hiebschaden und 2W8 gleißenden Schaden; gegen einen Untoten 3W8 gleißend.'),
 'schurke': ('Schurke', 8, 'Geschicklichkeit, Intelligenz', 'Leichte Rüstung', 'Dieb (ab Stufe 3)', [
  ('Expertise und Hinterhältiger Angriff', 'Expertise verdoppelt deinen Übungsbonus für zwei passende Auswahlen auf Stufe 1 und zwei weitere auf Stufe 6. Hinterhältiger Angriff einmal pro Zug mit Finesse- oder Fernkampfwaffe, wenn du Vorteil hast. Ohne Vorteil genügt ein anderer, nicht kampfunfähiger Gegner des Ziels innerhalb von 1,5 m (5 ft), sofern dein Angriff keinen Nachteil hat. Zusatzschaden steht in der Tabelle.'),
  ('Raffinierte Aktion', 'Ab Stufe 2 kannst du in deinem Zug Spurt, Rückzug oder Verstecken als Bonusaktion nutzen. Verstecken verlangt weiterhin eine geeignete Situation und den nötigen Wurf; die Aktion macht nicht automatisch unsichtbar.'),
  ('Überleben', 'Unglaubliches Ausweichen ab Stufe 5 halbiert mit Reaktion den Schaden eines Angriffs eines sichtbaren Angreifers. Entrinnen ab Stufe 7: Bei Geschicklichkeitsrettungswürfen für halben Schaden nimmst du bei Erfolg keinen, bei Misserfolg halben Schaden. Verlässliches Talent ab Stufe 11 behandelt bei Attributswürfen mit deinem Übungsbonus W20-Ergebnisse unter 10 als 10.'),
  ('Dieb', 'Ab Stufe 3 Schnelle Hände für Fingerfertigkeit, Diebeswerkzeug und Gegenstand verwenden über Raffinierte Aktion; dazu Klettern ohne zusätzliche Bewegungskosten und verbesserte Anlaufsprünge. Höhere Merkmale verbessern Heimlichkeit, erlauben den Umgang mit magischen Gegenständen und geben einen zweiten Zug in der ersten Kampfrunde.')],
  'Auf Schurkenstufe 5 verursacht ein passender Rapier-Treffer mit Geschicklichkeit 18 insgesamt 1W8 + 4 + 3W6 Schaden. Einmal pro Zug kann auch einen fremden Zug mit Gelegenheitsangriff betreffen.'),
 'waldlaeufer': ('Waldläufer', 10, 'Stärke, Geschicklichkeit', 'Leicht, mittelschwer, Schilde', 'Jäger (ab Stufe 3)', [
  ('Erzfeind und Gelände', 'Auf Stufe 1 wählst du einen Erzfeindtyp oder zwei humanoide Völker und ein bevorzugtes Gelände. Erzfeind erleichtert Spurenlesen und Wissen über diese Gegner und kann eine Sprache vermitteln. Bevorzugtes Gelände verbessert passende Intelligenz- und Weisheitswürfe mit Übung sowie Reisen von mindestens einer Stunde im betreffenden Gelände. Weitere Auswahlen auf höheren Stufen stehen in der Tabelle.'),
  ('Kampfstil und Magie', 'Ab Stufe 2 Kampfstil: Bogenschießen, Duellieren, Verteidigung oder Zwei-Waffen-Kampf. Weisheit ist dein Zauberattribut. Du lernst eine feste Zahl an Zaubern und bereitest keine tägliche Liste vor. Zauberplätze erneuern sich nach langer Rast. Ab Stufe 5 zwei Angriffe je Angriffsaktion.'),
  ('Jäger', 'Auf Stufe 3 Wahl zwischen Kolossjäger, Riesentöter und Hordenbrecher. Kolossjäger gibt beispielsweise einmal pro Zug +1W8 mit einem Waffenangriff gegen ein Ziel unter seinem TP-Maximum. Auf Stufe 7 eine defensive Taktik; auf Stufe 11 Salve oder Wirbelwindangriff; auf Stufe 15 eine überlegene Verteidigung.'),
  ('2014-Fassung', 'Dies sind die ursprünglichen SRD-Merkmale. Optionale Ersatzmerkmale aus Tasha und die 2024-Klasse werden nicht automatisch eingemischt. Mal des Jägers erfordert in dieser Fassung einen bekannten Zauber, einen Platz und Konzentration nach der Zauberbeschreibung.')],
  'Ein Waldläufer auf Stufe 5 kennt vier Zauber und hat vier Plätze des 1. sowie zwei des 2. Grades. Das bedeutet nicht, dass alle vier bekannten Zauber vom 2. Grad sein dürfen.'),
 'zauberer': ('Zauberer', 6, 'Konstitution, Charisma', 'Keine', 'Drakonische Blutlinie (ab Stufe 1)', [
  ('Angeborene Magie', 'Charisma ist dein Zauberattribut. Du kennst eine begrenzte Zauberauswahl; bekannte Zauber, Zaubertricks und Plätze stehen in der Tabelle. Plätze erneuern sich nach langer Rast. Zauberer und Magier sind getrennte Klassen; der Zauberer benötigt kein Zauberbuch.'),
  ('Quelle der Magie', 'Ab Stufe 2 Zaubereipunkte gleich Zaubererstufe, erneuert nach langer Rast. Als Bonusaktion kannst du Plätze in Punkte in Höhe des Platzgrades umwandeln oder Punkte für neue Plätze ausgeben. Kosten für Grade 1–5: 2, 3, 5, 6, 7 Punkte. Erschaffene Plätze verschwinden nach langer Rast; der Punktevorrat kann sein Maximum nicht überschreiten.'),
  ('Metamagie', 'Auf Stufe 3 wählst du zwei Optionen, auf Stufe 10 und 17 je eine weitere. Sie ändern einzelne Zauber gegen Zaubereipunkte. Normalerweise nur eine Option je Zauber, sofern eine Option nichts anderes erlaubt. Beschleunigter Zauber kostet 2 Punkte und macht einen Zauber mit Wirkzeit eine Aktion zur Bonusaktion; die allgemeine Regel für Bonusaktionszauber gilt weiterhin.'),
  ('Drakonische Blutlinie', 'Wähle einen Drachenvorfahren mit zugehöriger Schadensart. Auf Stufe 1 +1 TP und nochmals +1 pro weiterer Zaubererstufe; ohne Rüstung RK 13 + Geschicklichkeitsmodifikator. Auf Stufe 6 verbessert Elementare Affinität passende Schadenszauber. Auf Stufe 14 entstehen Drachenflügel, auf Stufe 18 wirkt Drakonische Präsenz.')],
  'Auf Stufe 3 besitzt du drei Zaubereipunkte. Ein neuer Platz des 2. Grades kostet alle drei. Ein beschleunigter Zauber lässt in demselben Zug normalerweise nur einen weiteren Zaubertrick mit Wirkzeit eine Aktion zu.'),
}

# name, page, size, speed, ability increases, traits
SPECIES = {
 'elf': ('Elf / Hochelf', 2, 'Mittelgroß', '9 m (30 ft)', 'Geschicklichkeit +2; Hochelf zusätzlich Intelligenz +1', [
  'Dunkelsicht 18 m (60 ft); Wahrnehmung geübt. Feenblut: Vorteil auf Rettungswürfe gegen Bezaubert und Immunität gegen magischen Schlaf.',
  'Trance: vier Stunden halbbewusste Meditation statt Schlaf; siehe Rastregeln der verwendeten Fassung. Sprachen: Gemeinsprache und Elfisch.',
  'Hochelf im SRD: Übung mit Kurz- und Langschwert sowie Kurz- und Langbogen; ein Magierzaubertrick mit Intelligenz als Zauberattribut; eine zusätzliche Sprache. Andere Elfenunterarten sind nicht Teil dieses SRD-Eintrags.']),
 'halbling': ('Halbling / Leichtfuß', 3, 'Klein', '7,5 m (25 ft)', 'Geschicklichkeit +2; Leichtfuß zusätzlich Charisma +1', [
  'Halblingsglück: Bei einer natürlichen 1 auf einem Angriffs-, Attributs- oder Rettungswurf darfst du neu würfeln; das neue Ergebnis gilt.',
  'Tapferkeit: Vorteil gegen Verängstigt. Halblingsgewandtheit: Du kannst dich durch den Bereich größerer Kreaturen bewegen; dies erlaubt nicht, dort deinen Zug zu beenden.',
  'Leichtfuß: Du darfst versuchen, dich hinter einer mindestens eine Größenkategorie größeren Kreatur zu verstecken. Sprachen: Gemeinsprache und Halblingisch.']),
 'mensch': ('Mensch', 4, 'Mittelgroß', '9 m (30 ft)', 'Alle sechs Attribute +1', [
  'Die SRD-Standardfassung gibt keine weiteren Volksmerkmale. Sprachen: Gemeinsprache und eine weitere Sprache deiner Wahl.',
  'Der Variantenmensch mit Talent ist eine andere Regeloption und gehört nicht zu dieser SRD-Fassung. Herkunftstalente und Heldische Inspiration der 2024-Menschen werden hier nicht hinzugefügt.']),
 'zwerg': ('Zwerg / Hügelzwerg', 4, 'Mittelgroß', '7,5 m (25 ft)', 'Konstitution +2; Hügelzwerg zusätzlich Weisheit +1', [
  'Schwere Rüstung senkt deine Bewegungsrate nicht. Dunkelsicht 18 m (60 ft); Vorteil auf Rettungswürfe gegen Gift und Resistenz gegen Giftschaden.',
  'Übung mit Beil, Streitaxt, leichtem Hammer und Kriegshammer; eines aus Schmiede-, Brau- oder Steinmetzwerkzeug. Steingespür: Bei Geschichte zur Herkunft von Steinarbeiten giltst du als geübt und addierst den doppelten Übungsbonus.',
  'Hügelzwerg: +1 TP-Maximum ab Stufe 1 und bei jedem weiteren Stufenaufstieg. Sprachen: Gemeinsprache und Zwergisch.']),
 'drachenbluetiger': ('Drachenblütiger', 5, 'Mittelgroß', '9 m (30 ft)', 'Stärke +2, Charisma +1', [
  'Wähle eine Drachenabstammung; sie legt Odemform, Rettungswurf und Schadensart fest. Du erhältst Resistenz gegen diese Schadensart. Sprachen: Gemeinsprache und Drakonisch.',
  'Odem als ganze Aktion, einmal pro kurzer oder langer Rast. SG = 8 + Konstitutionsmodifikator + Übungsbonus. Schaden 2W6, ab Charakterstufe 6: 3W6, ab 11: 4W6, ab 16: 5W6; erfolgreicher Rettungswurf halbiert.',
  'Linie 1,5 × 9 m (5 × 30 ft), Geschicklichkeitsrettungswurf: Blau/Bronze Blitz, Kupfer/Schwarz Säure, Messing Feuer. Kegel 4,5 m (15 ft): Gold/Rot Feuer mit Geschicklichkeit; Grün Gift sowie Silber/Weiß Kälte mit Konstitution. Keine eingebauten Flügel in dieser Fassung.']),
 'gnom': ('Gnom / Felsengnom', 5, 'Klein', '7,5 m (25 ft)', 'Intelligenz +2; Felsengnom zusätzlich Konstitution +1', [
  'Dunkelsicht 18 m (60 ft). Gnomische Gerissenheit gibt Vorteil auf Intelligenz-, Weisheits- und Charismarettungswürfe gegen Magie. Die deutsche SRD-Übersetzung lässt die Einschränkung aus; hier ist sie nach dem englischen SRD 5.1, Seite 6, ergänzt.',
  'Felsengnom: Artefaktkunde verdoppelt bei Geschichtswürfen zu magischen Gegenständen, Alchemie und Technik den sonst anwendbaren Übungsbonus. Übung mit Tüftlerwerkzeug.',
  'Mit einer Stunde Arbeit und 10 GM Material baust du ein winziges Uhrwerkgerät, RK 5 und 1 TP; höchstens drei gleichzeitig. Nach 24 Stunden endet die Funktion ohne eine Stunde Wartung. Optionen: Anzünder, Spieluhr oder bewegliches Spielzeug. Sprachen: Gemeinsprache und Gnomisch.']),
 'halbelf': ('Halbelf', 6, 'Mittelgroß', '9 m (30 ft)', 'Charisma +2, zwei andere Attribute deiner Wahl jeweils +1', [
  'Dunkelsicht 18 m (60 ft). Feenblut: Vorteil gegen Bezaubert; magischer Schlaf wirkt nicht.',
  'Vielseitigkeit: zwei beliebige Fertigkeiten geübt. Sprachen: Gemeinsprache, Elfisch und eine weitere Sprache deiner Wahl.',
  'Du erhältst keine elfische Trance und keinen Hochelfen-Zaubertrick allein durch deine Abstammung. Halbelf ist hier eine eigene 2014-Spieloption.']),
 'halbork': ('Halbork', 7, 'Mittelgroß', '9 m (30 ft)', 'Stärke +2, Konstitution +1', [
  'Dunkelsicht 18 m (60 ft) und Übung in Einschüchtern. Sprachen: Gemeinsprache und Orkisch.',
  'Unermüdliches Durchhaltevermögen: Wenn du auf 0 TP fällst, aber nicht sofort stirbst, bleibst du stattdessen bei 1 TP. Einmal pro langer Rast.',
  'Wilde Angriffe: Bei einem kritischen Nahkampfwaffentreffer einen Schadenswürfel der Waffe zusätzlich würfeln. Beispiel: Eine Zweihandaxt verursacht beim kritischen Treffer 3W12 statt 2W12 zuzüglich normalem Attributsmodifikator.']),
 'tiefling': ('Tiefling', 7, 'Mittelgroß', '9 m (30 ft)', 'Charisma +2, Intelligenz +1', [
  'Dunkelsicht 18 m (60 ft), Feuerresistenz. Sprachen: Gemeinsprache und Infernalisch.',
  'Infernalisches Erbe mit Charisma: Thaumaturgie ab Stufe 1; ab Charakterstufe 3 Höllischer Tadel als Zauber des 2. Grades einmal pro langer Rast; ab Stufe 5 Dunkelheit einmal pro langer Rast.',
  'Die beiden Zauber haben getrennte Anwendungen. Die mehreren Erbe-Varianten und frei wählbaren Zauberattribute aus 2024 gelten hier nicht.']),
}


def attribution(page):
    return (f'<p>Quelle: <a href="{SOURCE}#page={page}">Deutsches SRD 5.1, ab Seite {page}</a> · '
            f'<a href="/media/SRD-5.1-DE.pdf#page={page}">Lokale Originalquelle</a>.</p>'
            '<p>Deutsche Zusammenfassung und neu gegliederte Stufentabellen. Regeln der Ausgabe 2014; '
            'die verlinkte Quelle enthält auch die vollständigen Einzelmerkmale, Ausrüstungsoptionen und Zauberregeln.</p>'
            f'<p><small>{escape(ATTRIBUTION)}</small></p>')


def table(headers, rows):
    return '<div class="level-table" tabindex="0"><table><thead><tr>' + ''.join('<th scope="col">'+escape(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows) + '</tbody></table></div>'


def class_page(key, subclasses_html=''):
    name, die, saves, armor, subclass, rules, example = CLASSES[key]
    data = LEVELS[key]
    body = f'<article class="book"><h2>{name} · Klasse 2014</h2>'
    body += table(['Grundwert', 'Regel'], [
        ('Trefferwürfel', f'1W{die} pro Klassenstufe'),
        ('TP bei Start in dieser Klasse', f'{die} + Konstitutionsmodifikator'),
        ('TP pro weiterer Klassenstufe', f'1W{die} (oder {die//2+1}) + Konstitutionsmodifikator; mindestens 1'),
        ('Geübte Rettungswürfe', saves), ('Rüstungsübung', armor), ('SRD-Unterklasse', subclass)])
    body += subclasses_html + codex_spell_help.render(name, '2014') + '<h2>So funktioniert die Klasse</h2>'
    body += ''.join(f'<h3>{escape(title)}</h3><p>{escape(text)}</p>' for title, text in rules)
    body += f'<h2>Beispiel am Spieltisch</h2><p>{escape(example)}</p>'
    body += '<h2>Stufen 1 bis 20</h2><p>Klassenstufen, keine Gesamtstufen bei Klassenkombinationen. Ressourcen sind Gesamtwerte. Attributswerterhöhung: ein Attribut +2 oder zwei Attribute +1, jeweils höchstens 20. Ein Strich bezeichnet keinen neuen Eintrag.</p>'
    body += table(['Stufe', 'Übungsbonus', 'Merkmale'] + data['headers'], [[r['level'],r['bonus'],r['features']] + r['values'] for r in data['rows']])
    if data['slot_grades']:
        body += '<h2>Zauberplätze</h2>' + table(['Stufe'] + [f'Grad {n}' for n in range(1,data['slot_grades']+1)], [[r['level']] + r['slots'] for r in data['rows']])
    body += '<p>Für Zauber: Angriffsbonus = Übungsbonus + Zauberattributsmodifikator; Rettungswurf-SG = 8 + Übungsbonus + Zauberattributsmodifikator, sofern die Klasse Zauberwirken gewährt. Klassenkombinationen können andere Zauberplatztabellen benötigen.</p>'
    return body + attribution(data['page']) + '<p><a href="/codex/2014">Inhaltsverzeichnis</a></p></article>'


def species_page(key):
    name, page, size, speed, abilities, traits = SPECIES[key]
    body = codex_profiles.illustration('species-'+key,name) + f'<article class="book"><h2>{escape(name)} · Volk 2014</h2>'
    body += table(['Grundwert', 'Regel'], [('Größe',size), ('Bewegung',speed), ('Attributswerte',abilities)])
    body += '<h2>Volksmerkmale</h2>' + ''.join('<p>'+escape(t)+'</p>' for t in traits)
    body += '<h2>Deine Figur</h2><p>Persönlichkeit, Werte und Verbundenheit zur Gruppe bestimmst du selbst. Die Attributserhöhungen hier gehören zur ursprünglichen 2014-Fassung; alternative Herkunftsregeln vorab mit dem DM vereinbaren.</p>'
    if key == 'gnom':
        body += '<p><a href="https://media.wizards.com/2023/downloads/dnd/SRD_CC_v5.1.pdf#page=6">Englische Originalregel: Gnome Cunning, Seite 6</a>.</p>'
    return body + attribution(page) + '<p><a href="/codex/2014">Inhaltsverzeichnis</a></p></article>'
