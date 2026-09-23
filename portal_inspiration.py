"""DM-managed inspiration balances displayed on player profiles."""
from html import escape

KINDS = {'inspiration': 'Inspiration', 'heroic': 'Heldenhafte Inspiration'}

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS player_inspiration (user_id INTEGER PRIMARY KEY, inspiration INTEGER NOT NULL DEFAULT 0 CHECK(inspiration>=0), heroic INTEGER NOT NULL DEFAULT 0 CHECK(heroic>=0), revision INTEGER NOT NULL DEFAULT 0)')

def render(db, player, editable=False):
    row = db.execute('SELECT * FROM player_inspiration WHERE user_id=?', (player['id'],)).fetchone()
    body = '<section class="card"><h2>Inspirationspunkte</h2><div class="grid">'
    for kind, title in KINDS.items():
        balance = row[kind] if row else 0
        body += f'<div><h3>{title}</h3><p><strong style="font-size:2rem;color:#e5be72">{balance}</strong> Punkte</p>'
        if editable:
            body += f'<form method="post" action="/dm/players/{player["id"]}/inspiration"><input type="hidden" name="kind" value="{kind}"><input type="hidden" name="revision" value="{row["revision"] if row else 0}"><button name="delta" value="-1"' + (' disabled' if balance == 0 else '') + f' aria-label="{title}: einen Punkt abziehen">− 1</button> <button name="delta" value="1" aria-label="{title}: einen Punkt vergeben">+ 1</button></form>'
        body += '</div>'
    return body + '</div><p>Die Punkte werden vom DM vergeben und abgezogen.</p></section>'

def change(db, player_id, data):
    kind = data.get('kind')
    if kind not in KINDS or data.get('delta') not in ('-1', '1'):
        raise ValueError('Bitte eine gültige Punkteänderung wählen.')
    try:
        revision = int(data.get('revision', '-1'))
    except (TypeError, ValueError):
        raise ValueError('Bitte das Profil neu laden.') from None
    delta = int(data['delta'])
    db.execute('INSERT OR IGNORE INTO player_inspiration(user_id) VALUES(?)', (player_id,))
    updated = db.execute(f'UPDATE player_inspiration SET {kind}={kind}+?, revision=revision+1 WHERE user_id=? AND revision=? AND {kind}+? BETWEEN 0 AND 9999', (delta, player_id, revision, delta))
    if not updated.rowcount:
        raise ValueError('Der Punktestand hat sich geändert oder die Grenze ist erreicht. Bitte den aktuellen Stand prüfen und erneut wählen.')
