"""DM-controlled experience; independent of player-editable character data."""

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS player_experience (user_id INTEGER PRIMARY KEY, current INTEGER NOT NULL DEFAULT 0, target INTEGER NOT NULL DEFAULT 300, revision INTEGER NOT NULL DEFAULT 0)')

def render(db, player, editable=False):
    row = db.execute('SELECT * FROM player_experience WHERE user_id=?', (player['id'],)).fetchone()
    current, target, revision = (row['current'], row['target'], row['revision']) if row else (0, 300, 0)
    body = f'<section class="experience"><h3>Stufe {player["level"]} · Erfahrung</h3><progress style="width:100%;accent-color:#d9ae58" max="{target}" value="{min(current, target)}" aria-label="Erfahrungspunkte"></progress><p>{current} / {target} EP' + (' · Aufstiegsziel erreicht' if current >= target else '') + '</p>'
    if editable:
        body += f'<form method="post" action="/dm/players/{player["id"]}/experience"><input type="hidden" name="revision" value="{revision}"><label>Aktuelle EP<input name="current" type="number" min="0" max="999999999" value="{current}" required></label><label>EP-Ziel für den nächsten Aufstieg<input name="target" type="number" min="1" max="999999999" value="{target}" required></label><button>EP speichern</button></form>'
    return body + '<p>Vom Spielleiter verwaltet. Ein erreichtes EP-Ziel ändert die Stufe nicht automatisch.</p></section>'

def change(db, uid, data):
    try:
        current, target, revision = (int(data.get(key, '-1')) for key in ('current', 'target', 'revision'))
        if not 0 <= current <= 999999999 or not 1 <= target <= 999999999:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('Bitte gültige EP und ein positives EP-Ziel eingeben.') from None
    db.execute('INSERT OR IGNORE INTO player_experience(user_id) VALUES(?)', (uid,))
    updated = db.execute('UPDATE player_experience SET current=?,target=?,revision=revision+1 WHERE user_id=? AND revision=?', (current, target, uid, revision))
    if not updated.rowcount:
        raise ValueError('Der EP-Stand wurde inzwischen geändert. Bitte neu laden.')
