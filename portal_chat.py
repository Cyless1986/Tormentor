"""Session messages with recipient checks enforced before rendering."""
from html import escape
from datetime import datetime, timezone
import secrets


def initialize(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS chat_messages (
      id INTEGER PRIMARY KEY, sender_id INTEGER NOT NULL, body TEXT NOT NULL,
      audience TEXT NOT NULL, created_at INTEGER NOT NULL, nonce TEXT NOT NULL UNIQUE);
    CREATE TABLE IF NOT EXISTS chat_recipients (
      message_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY(message_id,user_id));
    CREATE INDEX IF NOT EXISTS chat_recipient_user ON chat_recipients(user_id,message_id);
    CREATE TABLE IF NOT EXISTS chat_read_state (
      user_id INTEGER PRIMARY KEY, last_read INTEGER NOT NULL DEFAULT 0);
    ''')


def unread(db, user):
    return db.execute('''SELECT COUNT(*) FROM chat_recipients r JOIN chat_messages m ON m.id=r.message_id
      WHERE r.user_id=? AND m.sender_id<>? AND m.id>COALESCE(
      (SELECT last_read FROM chat_read_state WHERE user_id=?),0)''', (user['id'], user['id'], user['id'])).fetchone()[0]


def mark_read(db, user, data):
    try:
        through = int(data.get('through', ''))
    except ValueError:
        raise ValueError('Ungültiger Lesestand.') from None
    if through < 0 or through > 9223372036854775807:
        raise ValueError('Ungültiger Lesestand.')
    # Bound the marker to an actual visible message, so future messages stay unread.
    last = db.execute('''SELECT COALESCE(MAX(m.id),0) FROM chat_messages m WHERE m.id<=?
      AND (m.sender_id=? OR EXISTS (SELECT 1 FROM chat_recipients r WHERE r.message_id=m.id AND r.user_id=?))''',
      (through, user['id'], user['id'])).fetchone()[0]
    db.execute('''INSERT INTO chat_read_state VALUES(?,?) ON CONFLICT(user_id)
      DO UPDATE SET last_read=MAX(last_read,excluded.last_read)''', (user['id'], last))


def send(db, user, data, now):
    if user['role'] not in ('dm', 'player'):
        raise ValueError('Bitte mit einem Spielerkonto anmelden.')
    body = data.get('body', '').strip()
    mode = data.get('audience', '')
    nonce = data.get('nonce', '')
    if not body or len(body) > 4000:
        raise ValueError('Bitte eine Nachricht mit 1 bis 4000 Zeichen eingeben.')
    modes = ('all', 'selected') if user['role'] == 'dm' else ('dm',)
    if mode not in modes or len(nonce) != 32 or any(c not in '0123456789abcdef' for c in nonce):
        raise ValueError('Bitte die Empfänger prüfen und erneut senden.')
    role = 'player' if user['role'] == 'dm' else 'dm'
    valid = {r[0] for r in db.execute('SELECT id FROM users WHERE role=?', (role,))}
    try:
        recipients = {int(data.get('dm_id', ''))} if mode == 'dm' else (valid if mode == 'all' else {int(k[10:]) for k, v in data.items() if k.startswith('recipient_') and v == '1'})
    except ValueError:
        raise ValueError('Spielerauswahl ungültig.') from None
    if not recipients or not recipients <= valid:
        raise ValueError('Bitte einen gültigen Empfänger auswählen.')
    existing = db.execute('SELECT sender_id FROM chat_messages WHERE nonce=?', (nonce,)).fetchone()
    if existing:
        if existing[0] != user['id']:
            raise ValueError('Bitte das Nachrichtenformular neu öffnen.')
        return
    mid = db.execute('INSERT INTO chat_messages(sender_id,body,audience,created_at,nonce) VALUES(?,?,?,?,?)',
                     (user['id'], body, mode, now, nonce)).lastrowid
    db.executemany('INSERT INTO chat_recipients VALUES(?,?)', ((mid, uid) for uid in recipients))


def feed(db, user):
    rows = db.execute('''SELECT m.*,u.username FROM chat_messages m JOIN users u ON u.id=m.sender_id
      WHERE m.sender_id=? OR EXISTS
      (SELECT 1 FROM chat_recipients r WHERE r.message_id=m.id AND r.user_id=?)
      ORDER BY m.id DESC LIMIT 100''', (user['id'], user['id'])).fetchall()
    result = ''
    for row in rows:
        label = 'Nachricht vom DM'
        if row['audience'] == 'dm':
            label = 'Deine private Nachricht an den DM' if row['sender_id'] == user['id'] else 'Private Nachricht von: ' + row['username']
        elif user['role'] == 'dm':
            names = [r[0] for r in db.execute('SELECT u.username FROM chat_recipients r JOIN users u ON u.id=r.user_id WHERE r.message_id=? ORDER BY u.username', (row['id'],))]
            label = ('Alle Spieler: ' if row['audience'] == 'all' else 'Privat an: ') + ', '.join(names)
        timestamp = datetime.fromtimestamp(row['created_at'], timezone.utc).isoformat()
        result += f'<article class="card" data-message-id="{row["id"]}"><small>{escape(label)} · <time datetime="{timestamp}">{timestamp}</time></small><p class="preserve">{escape(row["body"])}</p></article>'
    return result or '<p>Noch keine Nachrichten.</p>'


def render(db, user, data=None, error=''):
    data = data or {}
    body = '<p>Nachrichten während der Session · die letzten 100 Nachrichten, neueste zuerst.</p>'
    if error:
        body += '<p class="error" role="alert">' + escape(error) + '</p>'
    if user['role'] == 'dm':
        boxes = ''.join(f'<label><input type="checkbox" name="recipient_{r["id"]}" value="1"' + (' checked' if data.get(f'recipient_{r["id"]}') == '1' else '') + '>' + escape(r['username'] + (' · ' + r['player_name'] if r['player_name'] else '')) + '</label>' for r in db.execute("SELECT id,username,player_name FROM users WHERE role='player' ORDER BY username"))
        body += ('<form class="card" method="post" action="/messages"><input type="hidden" name="nonce" value="' + secrets.token_hex(16) + '">'
                 '<label>Empfänger<select name="audience"><option value="selected">Ausgewählte Spieler</option><option value="all"' + (' selected' if data.get('audience') == 'all' else '') + '>Alle Spieler</option></select></label>'
                 '<fieldset><legend>Spielerauswahl (bei „Ausgewählte Spieler“)</legend>' + (boxes or '<p>Noch keine Spieler registriert.</p>') + '</fieldset>'
                 '<label>Nachricht<textarea name="body" rows="4" maxlength="4000" required>' + escape(data.get('body', '')) + '</textarea></label><button>Senden</button></form>')
    elif user['role'] == 'player':
        options = ''.join(f'<option value="{r["id"]}"' + (' selected' if str(r['id']) == data.get('dm_id') else '') + '>' + escape(r['username']) + '</option>' for r in db.execute("SELECT id,username FROM users WHERE role='dm' ORDER BY username"))
        body += ('<form class="card" method="post" action="/messages"><h2>Privat an den DM antworten</h2><p>Nur du und der ausgewählte DM sehen deine Nachricht.</p>'
                 '<input type="hidden" name="audience" value="dm"><input type="hidden" name="nonce" value="' + secrets.token_hex(16) + '">'
                 '<label>Dungeonmaster<select name="dm_id" required>' + options + '</select></label>'
                 '<label>Deine Antwort<textarea name="body" rows="4" maxlength="4000" required>' + escape(data.get('body', '')) + '</textarea></label><button>Privat senden</button></form>')
    return body + '<p id="chat-status" role="status">Wird automatisch alle 3 Sekunden aktualisiert.</p><section id="chat-feed" aria-label="Nachrichten">' + feed(db, user) + '</section><script src="/media/chat.js" defer></script>'
