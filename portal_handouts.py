"""DM-authored handouts with server-enforced recipient selection."""
from html import escape
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent / 'portal_handouts'
MAX_FILE = 25 * 1024 * 1024


def initialize(db):
    # Absence of a policy preserves the existing all-player visibility.
    db.execute("CREATE TABLE IF NOT EXISTS handout_audiences (handout_id INTEGER PRIMARY KEY, audience TEXT NOT NULL CHECK(audience IN ('all','selected')))")
    db.execute('CREATE TABLE IF NOT EXISTS handout_recipients (handout_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY(handout_id,user_id))')
    db.execute('CREATE TABLE IF NOT EXISTS handout_files (handout_id INTEGER PRIMARY KEY, filename TEXT NOT NULL, original_name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL)')


def audience(db, handout_id):
    row = db.execute('SELECT audience FROM handout_audiences WHERE handout_id=?', (handout_id,)).fetchone()
    return row[0] if row else 'all'


def form(db, entry=None):
    selected = set()
    mode = 'selected'
    if entry is not None:
        mode = audience(db, entry['id'])
        selected = {row[0] for row in db.execute('SELECT user_id FROM handout_recipients WHERE handout_id=?', (entry['id'],))}
    players = db.execute("SELECT id,username,player_name FROM users WHERE role='player' ORDER BY username").fetchall()
    value = lambda key: entry[key] if entry is not None else ''
    options = ''.join(f'<option value="{key}"' + (' selected' if mode == key else '') + f'>{label}</option>'
                      for key, label in (('selected', 'Nur ausgewählte Spieler'), ('all', 'Alle Spieler')))
    boxes = ''.join(f'<label><input type="checkbox" name="recipient_{row["id"]}" value="1"'
                    + (' checked' if row['id'] in selected else '') + '>'
                    + escape(row['username'] + (' · ' + row['player_name'] if row['player_name'] else '')) + '</label>' for row in players)
    attachment = ''
    if entry is not None:
        file = db.execute('SELECT original_name,size FROM handout_files WHERE handout_id=?', (entry['id'],)).fetchone()
        if file:
            attachment = f'<p>Anhang: {escape(file["original_name"])} ({file["size"] // 1024} KB). Eine neue Datei ersetzt den bisherigen Anhang.</p>'
    return ('<form method="post" enctype="multipart/form-data"><label>Titel<input name="title" maxlength="120" value="' + escape(value('title'), quote=True) + '" required></label>'
            '<label>Inhalt<textarea name="body" rows="10" maxlength="12000" required>' + escape(value('body')) + '</textarea></label>'
            '<label>PDF oder Bild<input type="file" name="attachment" accept="application/pdf,image/png,image/jpeg,image/webp"></label>' + attachment +
            '<label>Sichtbar für<select name="audience">' + options + '</select></label>' +
            '<fieldset><legend>Spielerauswahl</legend><p>Gilt bei „Nur ausgewählte Spieler“. Du kannst mehrere Personen auswählen.</p>'
            + (boxes or '<p>Noch keine Spielerkonten vorhanden.</p>') + '</fieldset>'
            '<p role="status">Aktueller Status: ' + ('Freigegeben' if value('published') else 'Privater Entwurf') + '</p>'
            '<p>Die Spielerauswahl legt die Empfänger fest. Erst „Speichern und freigeben“ macht das Handout für sie sichtbar.</p>'
            '<button name="publication" value="draft">Als Entwurf speichern</button> '
            '<button name="publication" value="publish">Speichern und freigeben</button></form>')


def save(db, data, creator_id, now, handout_id=None, attachment=None):
    title, body = data.get('title', '').strip()[:120], data.get('body', '').strip()[:12000]
    mode = data.get('audience')
    action = data.get('publication')
    if action is not None and action not in ('draft', 'publish'):
        raise ValueError('Bitte Entwurf oder Freigabe wählen.')
    published = int(action == 'publish' if action is not None else data.get('published') == '1')
    if not title or not body:
        raise ValueError('Titel und Inhalt fehlen.')
    if mode not in ('all', 'selected'):
        raise ValueError('Bitte die Empfänger auswählen und erneut speichern.')
    recipients = set()
    if mode == 'selected':
        for key, value in data.items():
            if key.startswith('recipient_') and value == '1':
                try:
                    recipients.add(int(key.removeprefix('recipient_')))
                except ValueError:
                    raise ValueError('Die Spielerauswahl ist ungültig.') from None
        valid = {row[0] for row in db.execute("SELECT id FROM users WHERE role='player'")}
        if not recipients <= valid:
            raise ValueError('Mindestens ein ausgewähltes Spielerkonto existiert nicht mehr. Bitte die Auswahl prüfen.')
        if published and not recipients:
            raise ValueError('Wähle mindestens einen Spieler aus oder speichere das Handout ohne Freigabe.')
    if handout_id is None:
        handout_id = db.execute('INSERT INTO handouts(title,body,published,created_by,updated_at) VALUES(?,?,?,?,?)',
                               (title, body, published, creator_id, now)).lastrowid
    else:
        changed = db.execute('UPDATE handouts SET title=?,body=?,published=?,updated_at=? WHERE id=? AND deleted=0',
                             (title, body, published, now, handout_id))
        if not changed.rowcount:
            raise ValueError('Handout nicht gefunden oder bereits entfernt.')
    db.execute('INSERT INTO handout_audiences VALUES(?,?) ON CONFLICT(handout_id) DO UPDATE SET audience=excluded.audience', (handout_id, mode))
    db.execute('DELETE FROM handout_recipients WHERE handout_id=?', (handout_id,))
    db.executemany('INSERT INTO handout_recipients VALUES(?,?)', ((handout_id, player_id) for player_id in sorted(recipients)))
    if attachment:
        data_bytes, original_name, mime = attachment
        suffix = {'application/pdf': '.pdf', 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}[mime]
        ROOT.mkdir(exist_ok=True)
        filename = secrets.token_hex(16) + suffix
        (ROOT / filename).write_bytes(data_bytes)
        old = db.execute('SELECT filename FROM handout_files WHERE handout_id=?', (handout_id,)).fetchone()
        db.execute('INSERT INTO handout_files(handout_id,filename,original_name,mime,size) VALUES(?,?,?,?,?) ON CONFLICT(handout_id) DO UPDATE SET filename=excluded.filename,original_name=excluded.original_name,mime=excluded.mime,size=excluded.size', (handout_id, filename, original_name[:180], mime, len(data_bytes)))
        if old:
            (ROOT / old['filename']).unlink(missing_ok=True)
    return handout_id


def receive(handler):
    size = int(handler.headers.get('Content-Length', '0'))
    if not 0 < size <= MAX_FILE + 256 * 1024:
        raise ValueError('Das Handout darf höchstens 25 MB groß sein.')
    content_type = handler.headers.get('Content-Type', '')
    if not content_type.startswith('multipart/form-data;'):
        raise ValueError('Bitte das Handout-Formular verwenden.')
    raw = handler.rfile.read(size)
    message = BytesParser(policy=default).parsebytes(('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + raw)
    fields = {}; attachment = None
    for part in message.iter_parts():
        name = part.get_param('name', header='content-disposition')
        data = part.get_payload(decode=True) or b''
        if name == 'attachment' and data:
            mime = part.get_content_type()
            if mime not in ('application/pdf','image/png','image/jpeg','image/webp') or len(data) > MAX_FILE:
                raise ValueError('Erlaubt sind PDF, PNG, JPG oder WebP bis 25 MB.')
            attachment = (data, Path(part.get_filename() or 'anhang').name, mime)
        elif name:
            if len(data) > 16000: raise ValueError('Formularfeld zu lang.')
            fields[name] = data.decode('utf-8').strip()
    return fields, attachment


def visible(db, user):
    if user['role'] == 'dm':
        return db.execute('SELECT * FROM handouts WHERE deleted=0 ORDER BY updated_at DESC,id DESC').fetchall()
    if user['role'] != 'player':
        return []
    return db.execute("""SELECT h.* FROM handouts h
        LEFT JOIN handout_audiences a ON a.handout_id=h.id
        WHERE h.deleted=0 AND h.published=1 AND
        (COALESCE(a.audience,'all')='all' OR EXISTS
         (SELECT 1 FROM handout_recipients r WHERE r.handout_id=h.id AND r.user_id=?))
         ORDER BY h.updated_at DESC,h.id DESC""", (user['id'],)).fetchall()


def attachment(db, handout_id):
    return db.execute('SELECT * FROM handout_files WHERE handout_id=?', (handout_id,)).fetchone()


def recipient_label(db, handout_id):
    if audience(db, handout_id) == 'all':
        return 'Alle Spieler'
    names = [row[0] for row in db.execute('SELECT u.username FROM handout_recipients r JOIN users u ON u.id=r.user_id WHERE r.handout_id=? ORDER BY u.username', (handout_id,))]
    return 'Ausgewählt: ' + ', '.join(names) if names else 'Noch keine Spieler ausgewählt'
