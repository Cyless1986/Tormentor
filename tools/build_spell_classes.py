"""Extract exact German SRD spell-list membership (printed pages 114–122)."""
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
reader = PdfReader(ROOT / 'assets/srd/SRD_CC_v5.1_DE.pdf')
classes = dict(zip(('Barden','Druiden','Hexenmeisters','Klerikers','Magiers','Paladins','Waldläufers','Zauberers'), ('Barde','Druide','Hexenmeister','Kleriker','Magier','Paladin','Waldläufer','Zauberer')))
membership = {}
current = None
for page in reader.pages[113:122]:
    for line in page.extract_text().splitlines():
        line = ' '.join(line.split())
        if line.startswith('Zauber des '):
            current = classes[line.removeprefix('Zauber des ')]
        elif current and line and not re.search(r'Privatgebrauch|Systemreferenzdokument|Grad|Zauberlisten', line):
            membership.setdefault(line, []).append(current)
spells = json.loads((ROOT / 'assets/srd/spells-2014-de.json').read_text(encoding='utf-8-sig'))
missing = [s['name'] for s in spells if s['name'] not in membership]
print('Unmatched:', missing)
print('Class counts:', {c:sum(c in v for v in membership.values()) for c in classes.values()})
(ROOT / 'assets/srd/spell-classes-de.json').write_text(json.dumps(membership, ensure_ascii=False, indent=2), encoding='utf-8')
