"""Subclass names by published book; German labels are editorial translations.

Checked 2026-09-17 against the D&D Beyond book indexes and PHB update article:
https://www.dndbeyond.com/sources/dnd/phb-2014
https://www.dndbeyond.com/sources/dnd/phb-2024
https://www.dndbeyond.com/posts/1810-updates-in-the-players-handbook-2024
https://www.dndbeyond.com/sources/dnd/xgte
This is a source index, not a reproduction of subclass rules.
"""

# Each row: parent class | original name | editorial German name.
PHB_2014 = """
Barbar|Path of the Berserker|Pfad des Berserkers
Barbar|Path of the Totem Warrior|Pfad des Totemkriegers
Barde|College of Lore|Kollegium des Wissens
Barde|College of Valor|Kollegium der Tapferkeit
Kleriker|Knowledge Domain|Domäne des Wissens
Kleriker|Life Domain|Domäne des Lebens
Kleriker|Light Domain|Domäne des Lichts
Kleriker|Nature Domain|Domäne der Natur
Kleriker|Tempest Domain|Domäne des Sturms
Kleriker|Trickery Domain|Domäne der List
Kleriker|War Domain|Domäne des Krieges
Druide|Circle of the Land|Zirkel des Landes
Druide|Circle of the Moon|Zirkel des Mondes
Kämpfer|Battle Master|Kampfmeister
Kämpfer|Champion|Champion
Kämpfer|Eldritch Knight|Mystischer Ritter
Mönch|Way of the Open Hand|Weg der Offenen Hand
Mönch|Way of Shadow|Weg des Schattens
Mönch|Way of the Four Elements|Weg der Vier Elemente
Paladin|Oath of Devotion|Schwur der Hingabe
Paladin|Oath of the Ancients|Schwur der Uralten
Paladin|Oath of Vengeance|Schwur der Vergeltung
Waldläufer|Hunter|Jäger
Waldläufer|Beast Master|Herr der Tiere
Schurke|Thief|Dieb
Schurke|Assassin|Assassine
Schurke|Arcane Trickster|Arkaner Betrüger
Zauberer|Draconic Bloodline|Drachenblutlinie
Zauberer|Wild Magic|Wilde Magie
Hexenmeister|The Archfey|Die Erzfee
Hexenmeister|The Fiend|Der Unhold
Hexenmeister|The Great Old One|Der Große Alte
Magier|School of Abjuration|Schule der Bannmagie
Magier|School of Conjuration|Schule der Beschwörung
Magier|School of Divination|Schule der Erkenntnismagie
Magier|School of Enchantment|Schule der Verzauberung
Magier|School of Evocation|Schule der Hervorrufung
Magier|School of Illusion|Schule der Illusion
Magier|School of Necromancy|Schule der Nekromantie
Magier|School of Transmutation|Schule der Verwandlung
"""

PHB_2024 = """
Barbar|Path of the Berserker|Pfad des Berserkers
Barbar|Path of the Wild Heart|Pfad des Wilden Herzens
Barbar|Path of the World Tree|Pfad des Weltenbaums
Barbar|Path of the Zealot|Pfad des Zeloten
Barde|College of Dance|Kollegium des Tanzes
Barde|College of Glamour|Kollegium des Glamours
Barde|College of Lore|Kollegium des Wissens
Barde|College of Valor|Kollegium der Tapferkeit
Kleriker|Life Domain|Domäne des Lebens
Kleriker|Light Domain|Domäne des Lichts
Kleriker|Trickery Domain|Domäne der List
Kleriker|War Domain|Domäne des Krieges
Druide|Circle of the Land|Zirkel des Landes
Druide|Circle of the Moon|Zirkel des Mondes
Druide|Circle of the Sea|Zirkel des Meeres
Druide|Circle of the Stars|Zirkel der Sterne
Kämpfer|Battle Master|Kampfmeister
Kämpfer|Champion|Champion
Kämpfer|Eldritch Knight|Mystischer Ritter
Kämpfer|Psi Warrior|Psi-Krieger
Mönch|Warrior of Mercy|Krieger der Gnade
Mönch|Warrior of Shadow|Krieger des Schattens
Mönch|Warrior of the Elements|Krieger der Elemente
Mönch|Warrior of the Open Hand|Krieger der Offenen Hand
Paladin|Oath of Devotion|Schwur der Hingabe
Paladin|Oath of Glory|Schwur des Ruhms
Paladin|Oath of the Ancients|Schwur der Uralten
Paladin|Oath of Vengeance|Schwur der Vergeltung
Waldläufer|Beast Master|Herr der Tiere
Waldläufer|Fey Wanderer|Feenwanderer
Waldläufer|Gloom Stalker|Düsternispirscher
Waldläufer|Hunter|Jäger
Schurke|Arcane Trickster|Arkaner Betrüger
Schurke|Assassin|Assassine
Schurke|Soulknife|Seelenklinge
Schurke|Thief|Dieb
Zauberer|Aberrant Sorcery|Aberrante Zauberei
Zauberer|Clockwork Sorcery|Uhrwerkzauberei
Zauberer|Draconic Sorcery|Drachenzauberei
Zauberer|Wild Magic Sorcery|Zauberei der Wilden Magie
Hexenmeister|Archfey Patron|Erzfee als Schutzherr
Hexenmeister|Celestial Patron|Himmlischer Schutzherr
Hexenmeister|Fiend Patron|Unhold als Schutzherr
Hexenmeister|Great Old One Patron|Großer Alter als Schutzherr
Magier|Abjurer|Bannmagier
Magier|Diviner|Erkenntnismagier
Magier|Evoker|Hervorrufungsmagier
Magier|Illusionist|Illusionist
"""

XANATHAR = """
Barbar|Path of the Ancestral Guardian|Pfad des Ahnenwächters
Barbar|Path of the Storm Herald|Pfad des Sturmherolds
Barbar|Path of the Zealot|Pfad des Zeloten
Barde|College of Glamour|Kollegium des Glamours
Barde|College of Swords|Kollegium der Schwerter
Barde|College of Whispers|Kollegium des Flüsterns
Kleriker|Forge Domain|Domäne der Schmiede
Kleriker|Grave Domain|Grabesdomäne
Druide|Circle of Dreams|Zirkel der Träume
Druide|Circle of the Shepherd|Zirkel des Hirten
Kämpfer|Arcane Archer|Arkaner Bogenschütze
Kämpfer|Cavalier|Kavalier
Kämpfer|Samurai|Samurai
Mönch|Way of the Drunken Master|Weg des Betrunkenen Meisters
Mönch|Way of the Kensei|Weg des Kensei
Mönch|Way of the Sun Soul|Weg der Sonnenseele
Paladin|Oath of Conquest|Schwur der Eroberung
Paladin|Oath of Redemption|Schwur der Erlösung
Waldläufer|Gloom Stalker|Düsternispirscher
Waldläufer|Horizon Walker|Horizontwanderer
Waldläufer|Monster Slayer|Monstertöter
Schurke|Inquisitive|Inquisitiver
Schurke|Mastermind|Drahtzieher
Schurke|Scout|Späher
Schurke|Swashbuckler|Säbelrassler
Zauberer|Divine Soul|Göttliche Seele
Zauberer|Shadow Magic|Schattenmagie
Zauberer|Storm Sorcery|Sturmzauberei
Hexenmeister|The Celestial|Der Himmlische
Hexenmeister|The Hexblade|Die Fluchklinge
Magier|War Magic|Kriegsmagie
"""

BOOKS = (
    ('2014', 'phb-2014', 'Spielerhandbuch 2014', PHB_2014),
    ('2024', 'phb-2024', 'Spielerhandbuch 2024', PHB_2024),
    ('2014', 'xgte', 'Xanathars Ratgeber für Alles', XANATHAR),
)


def rows():
    for edition, code, source, data in BOOKS:
        for line in data.strip().splitlines():
            parent, name, german = line.split('|')
            yield edition, code, source, parent, name, german
