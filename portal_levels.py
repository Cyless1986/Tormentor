"""DM-only player level management."""
from html import escape


def render(db, player):
    level = player['level']
    body = f'<section class="card"><h2>Level verwalten</h2><form method="post" action="/dm/players/{player["id"]}/level"><input type="hidden" name="previous_level" value="{level}"><label>Level (1 bis 20)<input type="number" name="level" min="1" max="20" step="1" value="{level}" required></label><button>Level speichern</button></form><p>Nur der Spielleiter kann die Stufe ändern. EP bleiben unverändert.</p>'
    suggestions = db.execute('SELECT proposed_level,evidence FROM level_suggestions WHERE player_id=? AND applied=0 ORDER BY created_at DESC', (player['id'],)).fetchall()
    if suggestions:
        body += '<h3>Offene Vorschläge aus der Chronik</h3>' + ''.join(f'<p>Stufe {row["proposed_level"]} · {escape(row["evidence"])}</p>' for row in suggestions)
    return body + '</section>'


def change(db, player, data):
    try:
        level = int(data.get('level', ''))
        previous = int(data.get('previous_level', ''))
        if not 1 <= level <= 20 or not 1 <= previous <= 20:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Bitte eine ganze Stufe zwischen 1 und 20 eingeben und das aktuelle Profil verwenden.') from None
    changed = db.execute("UPDATE users SET level=? WHERE id=? AND role='player' AND level=?", (level, player['id'], previous))
    if not changed.rowcount:
        raise ValueError('Die Stufe wurde inzwischen geändert. Bitte das Spielerprofil neu laden.')
    db.execute('UPDATE level_suggestions SET applied=1 WHERE player_id=? AND applied=0 AND proposed_level<=?', (player['id'], level))
