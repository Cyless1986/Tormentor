"""Player-friendly spellcasting explanations without reproducing rule text."""
from html import escape

CLASS_NOTES = {
    'Barde': ('Charisma', 'Du kennst eine begrenzte Auswahl und erweiterst sie über deine Klassenstufen.', 'Unterstützung, Kontrolle und soziale Wirkung'),
    'Druide': ('Weisheit', 'Du bereitest nach einer langen Rast eine Auswahl aus deiner Druidenzauberliste vor.', 'Natur, Heilung, Verwandlung und Gelände'),
    'Hexenmeister': ('Charisma', 'Deine wenigen Paktplätze haben denselben Grad und kehren meist nach kurzer oder langer Rast zurück.', 'starke Einzelzauber und Paktmagie'),
    'Kleriker': ('Weisheit', 'Du bereitest nach einer langen Rast eine Auswahl vor; Domänenzauber kommen zusätzlich dazu.', 'Schutz, Heilung, Schaden und Unterstützung'),
    'Magier': ('Intelligenz', 'Du sammelst Zauber im Zauberbuch und bereitest daraus täglich eine Auswahl vor.', 'Planung, Rituale, Kontrolle und vielseitige Lösungen'),
    'Paladin': ('Charisma', 'Du erhältst vorbereitete Zauber abhängig von deiner Paladinstufe; dein Eid kann weitere ergänzen.', 'Schutz, Heilung, Verstärkung und Nahkampf'),
    'Waldläufer': ('Weisheit', 'Du lernst oder bereitest Zauber abhängig von Regelfassung und Stufe vor.', 'Erkundung, Jagd, Bewegung und Natur'),
    'Zauberer': ('Charisma', 'Du kennst eine begrenzte Auswahl und kannst sie mit Metamagie verändern.', 'flexible Zauber und spontane Anpassung'),
}

def render(class_name, edition='2024'):
    note = CLASS_NOTES.get(class_name)
    if not note:
        return '<section class="card spell-help"><h2>Zauberhilfe</h2><p>Diese Klasse hat keine eigene Zaubertabelle. Eine Unterklasse kann trotzdem magische Merkmale verleihen.</p></section>'
    ability, preparation, focus = note
    return (f'<section class="card spell-help"><h2>Zauberhilfe · {escape(class_name)}</h2>'
            f'<p><b>Zauberattribut:</b> {escape(ability)}. Es beeinflusst Zauberangriff und Rettungswurf-SG.</p>'
            f'<p><b>Stufentabelle:</b> {escape(preparation)} Zauberplätze sind Energie für Zauber eines Grades; sie sind keine automatisch bekannten Zauber.</p>'
            f'<p><b>Typische Rolle:</b> {escape(focus)}.</p><h3>Was wird benötigt?</h3><ul>'
            '<li><b>Wirkzeit:</b> Aktion, Bonusaktion, Reaktion oder längere Zeit prüfen.</li>'
            '<li><b>Reichweite und Ziel:</b> Ziel muss die Reichweite und Bedingungen erfüllen.</li>'
            '<li><b>Komponenten:</b> V = Formel, S = Handbewegung, M = Material. Ein Fokus ersetzt Materialien ohne angegebenen Preis.</li>'
            '<li><b>Konzentration:</b> Nur ein Konzentrationszauber gleichzeitig; Schaden kann sie stören.</li>'
            '<li><b>Dauer und Effekt:</b> Rettungswurf oder Angriff, Dauer und Verstärkung durch höhere Grade prüfen.</li></ul>'
            '<p><small>Die vollständigen Zauberwerte stehen in der verlinkten offiziellen Regelfassung.</small></p></section>')
