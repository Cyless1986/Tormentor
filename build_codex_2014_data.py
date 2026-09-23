"""Extract the CC BY 4.0 SRD 5.1 class tables; no network at runtime."""
import json
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SPECS = [
    ('barbar', 'Barbar', 8, 2, 0), ('barde', 'Barde', 11, 2, 9),
    ('druide', 'Druide', 15, 1, 9), ('hexenmeister', 'Hexenmeister', 20, 5, 0),
    ('kaempfer', 'Kämpfer', 27, 0, 0), ('kleriker', 'Kleriker', 30, 1, 9),
    ('magier', 'Magier', 34, 1, 9), ('moench', 'Mönch', 38, 0, 0),
    ('paladin', 'Paladin', 42, 0, 5), ('schurke', 'Schurke', 47, 0, 0),
    ('waldlaeufer', 'Waldläufer', 50, 1, 5), ('zauberer', 'Zauberer', 54, 2, 9),
]
HEADERS = {
    'barbar': ['Kampfrausch-Anzahl', 'Kampfrausch-Schaden'],
    'barde': ['Zaubertricks', 'Bekannte Zauber'],
    'druide': ['Zaubertricks'],
    'hexenmeister': ['Zaubertricks', 'Bekannte Zauber', 'Paktplätze', 'Platzgrad', 'Anrufungen'],
    'kaempfer': [], 'kleriker': ['Zaubertricks'], 'magier': ['Zaubertricks'],
    'moench': ['Kampfkünste', 'Ki', 'Zusätzliche Bewegung'], 'paladin': [],
    'schurke': ['Hinterhältiger Angriff'], 'waldlaeufer': ['Bekannte Zauber'],
    'zauberer': ['Zaubereipunkte', 'Zaubertricks', 'Bekannte Zauber'],
}


def build():
    reader = PdfReader(ROOT / 'assets/srd/SRD_CC_v5.1_DE.pdf')
    result = {}
    for key, name, page, resources, grades in SPECS:
        text = unicodedata.normalize('NFC', reader.pages[page - 1].extract_text())
        text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', text)
        first = re.search(r'(?m)^1\.\s+\+2\s+', text)
        chunks = re.split(r'(?m)^(\d{1,2})\.\s+(\+\d)\s+', text[first.start():])
        rows = []
        for i in range(1, len(chunks), 3):
            level, bonus, body = int(chunks[i]), chunks[i+1], chunks[i+2]
            # The last table row is followed by a new paragraph on some pages.
            if level == 20:
                body = body.split('\n \n', 1)[0]
            body = body.split('\nStufe', 1)[0]
            body = re.sub(r'\s+', ' ', body).strip()
            values = []
            if key == 'moench':
                m = re.match(r'(1W\d+) (\d+|−) (−|\+[\d,]+ (?:Meter|m)) (.*)', body)
                if not m: raise ValueError((key, level, body))
                dice, ki, movement, body = m.groups()
                if movement != '−':
                    metres = float(movement.split()[0].replace(',', '.'))
                    movement += f' ({metres / .3:g} ft)'
                values = [dice, ki, movement]
            elif key == 'schurke':
                dice, body = body.split(' ', 1)
                values = [dice]
            elif key == 'zauberer':
                points, body = body.split(' ', 1)
                values = [points]
            count = resources + grades
            slots = []
            if count:
                parts = body.rsplit(' ', count)
                if len(parts) != count + 1: raise ValueError((key, level, body))
                body, numbers = parts[0], parts[1:]
                values += numbers[:resources]
                slots = numbers[resources:]
            body = body.replace('Attributswerterhöhung', 'Attributswerterhöhung').replace('Attributswerhöhung', 'Attributswerterhöhung')
            rows.append(dict(level=level, bonus=bonus, features=body, values=values, slots=slots))
        assert [r['level'] for r in rows] == list(range(1,21)), key
        for row in rows:
            assert len(row['values']) == len(HEADERS[key]), (key, row)
            assert all(re.fullmatch(r'[+]?\d+[.]?|−|Unbegrenzt', v) for v in row['slots']), (key,row)
        result[key] = dict(name=name, page=page, headers=HEADERS[key], slot_grades=grades, rows=rows)
    (ROOT / 'assets/srd/levels-2014.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('12 Klassen, 240 Stufen aus SRD 5.1 extrahiert.')


if __name__ == '__main__':
    build()
