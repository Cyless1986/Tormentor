"""Import the four supplied Loreify PDF notes as private DM review drafts."""
from pathlib import Path
import hashlib
import re
import shutil
from pypdf import PdfReader
import lore

ROOT = Path(__file__).resolve().parent
CONFIG = {
 1: ('Dungeon von Gorna · Session ohne Nummer', ['Alte Wilma','Verletzte Abenteurer','Huppler Hustle Standbesitzer'], ['Jahrmarkt von Gorna','Dungeon von Gorna (Ebene 1)','Great Hall']),
 2: ('Session 1 · Flucht aus Hochoch', ['Der Statthalter von Hochoch','Monti'], ['Taverne zum Schlitzohr','Kerker von Hochoch','Hochoch']),
 3: ('Session 2 · Der Druidentempel', ['Zweiköpfiger Hund','Dschinn','Ogre-Boss','Unknown'], ['Düsterwald','Holzfällercamp','See am Wasserfall','Druidentempel / Druidenhain']),
 4: ('Session 3 · Ankunft in Gorna', ['Boromir Krimskrams','Brutus','Alessandria','Valentine','Die Bardin'], ['Gorna','Kirche der aufgehenden Sonne','Der Güldene Ochse','Friedrichs Schmiede Eisenhard','Herberge zur alten Lady Wilma']),
}

def section(text, start, end):
    return text.split('\n'+start+'\n',1)[1].split('\n'+end+'\n',1)[0].strip()

def entries(text, names):
    lines=text.splitlines()
    indices=[lines.index(name) for name in names]+[len(lines)]
    return [lines[a]+' — '+' '.join(lines[a+1:b]) for a,b in zip(indices,indices[1:])]

def main():
    for number,(title,npcs,places) in CONFIG.items():
        path=ROOT/'loreify'/f'session_{number}_session_notes.pdf'
        checksum=hashlib.sha256(path.read_bytes()).hexdigest()
        ident=hashlib.sha256(('loreify:'+checksum).encode()).hexdigest()[:32]
        if (lore.session_dir(ident)/'session.json').exists():
            print('Bereits importiert:',title)
            continue
        text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
        text=re.sub(r'^Page \d+\s*$', '', text, flags=re.M)
        text=re.sub(r'\n{3,}','\n\n',text)
        quest_text=section(text,'Quests','Characters & NPCs')
        quest_lines=[line for line in quest_text.splitlines() if line.strip()]
        quest_names=[line for line in quest_lines if '[' in line and not line.startswith('[')]
        if number==4:quest_names.append('Die Goblin-Notiz übersetzen')
        item=lore.new_session(title,ident)
        item['transcript']=text
        item['draft']=lore.validate_review({
            'summary':section(text,'Session Summary','Timeline of Events'),
            'npcs':entries(section(text,'Characters & NPCs','Locations'),npcs),
            'places':entries(section(text,'Locations','Loot & Items'),places),
            'quests':entries('\n'.join(quest_lines),quest_names),
            'level_ups':[],
        })
        item['source_document']={'filename':path.name,'sha256':checksum,'type':'Loreify PDF session notes'}
        item['processing']={'state':'completed','message':f'Loreify-PDF importiert: {path.name}. Zusammenfassung, NPCs, Orte und Quests zur DM-Prüfung bereit. Dokumentnummerierung übernommen; PDF-Datum nicht als Spieltermin interpretiert.'}
        shutil.copy2(path,lore.session_dir(ident)/'source-notes.pdf')
        lore.save(item)
        assert not lore.load(ident)['published']
        print('Importiert:',title,ident)

if __name__=='__main__':main()
