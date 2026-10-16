"""Slot inventory and coin purse for the character sheet."""
import json
from html import escape

COINS = [('iron', 'Eisen', '#899098'), ('copper', 'Kupfer', '#c88050'), ('silver', 'Silber', '#cbd5df'), ('electrum', 'Elektrum', '#c6bc85'), ('gold', 'Gold', '#efc653'), ('platinum', 'Platin', '#e2eced')]
KINDS = {'potion': ('Trank', .25), 'sword': ('Einhandschwert', 1), 'armor': ('Rüstung', 2), 'heavy': ('Schwere Rüstung', 3), 'food': ('Essen', 0), 'drink': ('Trinken', 0), 'money': ('Geld', 0), 'scroll': ('Schriftrollen', None), 'book': ('Bücher', None), 'ingredient': ('Zutaten', None), 'tool': ('Werkzeuge', None), 'quest': ('Questobjekte', None), 'other': ('Sonstiges', None)}

def parse(raw):
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(items, list) or len(items) > 200:
            raise ValueError()
        clean = []
        for item in items:
            name = item['name'].strip()
            kind = item['kind']
            quantity = int(item['quantity'])
            slots = float(item['slots']) if KINDS[kind][1] is None else KINDS[kind][1]
            if not name or len(name) > 120 or not 1 <= quantity <= 9999 or quantity != float(item['quantity']) or not 0 <= slots <= 999 or slots * 4 != int(slots * 4) or type(item['equipped']) is not bool:
                raise ValueError()
            clean.append(dict(name=name, kind=kind, quantity=quantity, slots=slots, equipped=item['equipped']))
        return clean
    except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
        raise ValueError('Bitte Inventar prüfen: maximal 200 Gegenstände, ganze Mengen und Slotkosten in Viertelschritten.') from None

def load_slots(items):
    return sum(item['quantity'] * item['slots'] for item in items if not item['equipped'])

def save(data, stored):
    items = parse(data.get('inventory', stored.get('inventory', [])))
    coins = {}
    for key, _, _ in COINS:
        try:
            amount = int(data.get('coin_' + key, stored.get('coin_' + key, 0)))
            if not 0 <= amount <= 999999999:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('Münzguthaben muss eine nicht negative ganze Zahl sein.') from None
        coins['coin_' + key] = amount
    return dict(inventory=items, **coins)

def render(values):
    raw = values.get('inventory', [])
    raw = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    body = '<section class="card"><h3>Inventar und Tragfähigkeit</h3><p>Stärke = verfügbare Slots. Ausgerüstetes, Geld, Essen und Trinken zählen nicht zur Traglast. Für Schriftrollen, Bücher, Zutaten, Werkzeuge und Questobjekte kannst du die Slots je Stück selbst festlegen.</p><p id="inventory-load" role="status"></p><progress id="inventory-progress" aria-label="Belegte Inventarslots" max="10" value="0"></progress>'
    body += '<input type="hidden" name="inventory" value="' + escape(raw, quote=True) + '"><div id="inventory-rows"></div><button type="button" id="inventory-add">+ Gegenstand</button><noscript>Zum Bearbeiten des Inventars bitte JavaScript aktivieren.</noscript></section>'
    body += '<section class="card"><h3>Münzguthaben</h3><div class="grid">'
    for key, label, color in COINS:
        body += f'<label class="coin-field" style="--coin-color:{color}"><span class="coin-heading"><span class="coin" aria-hidden="true">{label[:2].upper()}</span> {label}</span><input type="number" name="coin_{key}" min="0" max="999999999" step="1" required value="{escape(str(values.get("coin_" + key, 0)), quote=True)}"></label>'
    return body + '</div></section>'
