"""Administrator-issued single-use recovery tokens, valid for 30 minutes."""
import secrets
import time
from html import escape

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS password_resets (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS password_help_requests (user_id INTEGER PRIMARY KEY, requested_at INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS dm_recovery (user_id INTEGER PRIMARY KEY, code_hash TEXT NOT NULL, expires_at INTEGER NOT NULL)')


def create_recovery(db, user, password):
    import portal
    if not user or user['role'] != 'dm' or not portal.password_ok(password, user['password']):
        raise ValueError('Bitte dein aktuelles DM-Passwort bestätigen.')
    code = secrets.token_hex(24)
    db.execute('INSERT INTO dm_recovery VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET code_hash=excluded.code_hash,expires_at=excluded.expires_at', (user['id'], portal.digest(code), int(time.time()) + 365 * 86400))
    db.commit()
    return '-'.join(code[i:i+8] for i in range(0, len(code), 8))


def recover_dm(db, username, code, password, confirmation):
    import portal
    if not 12 <= len(password) <= 256 or password != confirmation:
        raise ValueError('Passwörter müssen übereinstimmen und 12 bis 256 Zeichen lang sein.')
    normalized = code.strip().replace('-', '').replace(' ', '').lower()
    db.execute('BEGIN IMMEDIATE')
    row = db.execute("SELECT u.id FROM users u JOIN dm_recovery r ON r.user_id=u.id WHERE u.username=? AND u.role='dm' AND r.code_hash=? AND r.expires_at>?", (username.strip().lower(), portal.digest(normalized), int(time.time()))).fetchone()
    if not row:
        db.rollback()
        raise ValueError('Benutzername oder Notfallcode ungültig, bereits verwendet oder abgelaufen.')
    db.execute('UPDATE users SET password=? WHERE id=?', (portal.password_hash(password), row[0]))
    for table in ('sessions', 'password_resets', 'password_help_requests', 'dm_recovery'):
        db.execute(f'DELETE FROM {table} WHERE user_id=?', (row[0],))
    db.commit()


RECOVERY_SETUP = '''<section class="card"><h2>Eigener DM-Zugang · Notfallcode</h2><p>Der Code ersetzt im Notfall dein Passwort. Er wird nur einmal angezeigt, gilt ein Jahr und kann einmal verwendet werden. Bewahre ihn im Passwortmanager oder ausgedruckt sicher auf. Ein neuer Code ersetzt den bisherigen.</p><form method="post" action="/dm/recovery"><label>Aktuelles DM-Passwort<input type="password" name="current_password" autocomplete="current-password" required></label><button>Neuen Notfallcode erzeugen</button></form></section>'''
RECOVERY_FORM = '''<p>Verwende deinen vorher im DM-Bereich erzeugten Notfallcode. Nach dem Zurücksetzen sind alte Anmeldungen und der Code ungültig.</p><form method="post" action="/recover-dm"><label>DM-Benutzername<input name="username" autocomplete="username" required></label><label>Notfallcode<input name="code" type="password" autocomplete="off" required></label><label>Neues Passwort<input name="password" type="password" minlength="12" maxlength="256" autocomplete="new-password" required></label><label>Passwort wiederholen<input name="confirmation" type="password" minlength="12" maxlength="256" autocomplete="new-password" required></label><button>DM-Passwort zurücksetzen</button></form>'''


def request_help(db, username):
    """Queue existing accounts only; callers always return the same public reply."""
    initialize(db)
    account = db.execute('SELECT id FROM users WHERE username=?', (username.strip().lower(),)).fetchone()
    if account:
        db.execute('INSERT OR IGNORE INTO password_help_requests VALUES(?,?)', (account[0], int(time.time())))


def requests_page(db):
    initialize(db)
    rows = db.execute('SELECT u.id,u.username,u.player_name FROM password_help_requests r JOIN users u ON u.id=r.user_id ORDER BY r.requested_at,u.id').fetchall()
    body = '<p>Prüfe persönlich, ob die Anfrage tatsächlich von diesem Spieler stammt. Gib den Rücksetzlink nur direkt an diese Person weiter.</p>'
    for row in rows:
        body += (f'<section class="card"><h2>{escape(row["username"])}</h2><p>{escape(row["player_name"])}</p>'
                 f'<form method="post" action="/dm/password-resets/{row["id"]}">'
                 '<label><input type="checkbox" name="verified" value="yes" required>Identität persönlich bestätigt</label>'
                 '<button>Rücksetzlink erstellen</button></form>'
                 f'<form method="post" action="/dm/password-resets/{row["id"]}/dismiss"><button>Anfrage schließen</button></form></section>')
    if not rows:
        body += '<p>Keine offenen Passwort-Anfragen.</p>'
    return body + '<p><a href="/dm">Zurück zur DM-Zentrale</a></p>'


HELP_FORM = '''<p>Trage deinen Benutzernamen ein. Dein DM kann danach einen einmaligen Rücksetzlink für dich erstellen. Melde dich zusätzlich persönlich bei ihm, damit er deine Identität prüfen kann.</p>
<form method="post" action="/forgot-password"><label>Benutzername<input name="username" minlength="3" maxlength="32" autocomplete="username" required></label><button>Hilfe beim DM anfordern</button></form>
<p><a href="/recover-dm">Eigenen DM-Zugang mit Notfallcode zurücksetzen</a></p><p>Ohne zuvor eingerichteten Notfallcode hilft der Portalbetreiber.</p><p><a href="/login">Zurück zum Login</a></p>'''

HELP_SENT = '<p>Falls zu diesem Benutzernamen ein Konto existiert, ist die Anfrage beim DM hinterlegt. Bitte melde dich zusätzlich persönlich bei deinem DM. Dein bisheriges Passwort bleibt bis zum Zurücksetzen gültig.</p><p><a href="/login">Zurück zum Login</a></p>'

def issue(db, username):
    import portal
    initialize(db)
    db.execute('BEGIN IMMEDIATE')
    account = db.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
    if not account:
        db.rollback()
        raise ValueError('Konto nicht gefunden')
    token = secrets.token_urlsafe(32)
    db.execute('DELETE FROM password_resets WHERE user_id=? OR expires_at<=?', (account[0], int(time.time())))
    db.execute('INSERT INTO password_resets VALUES(?,?,?)', (portal.digest(token), account[0], int(time.time()) + 1800))
    db.commit()
    return token

def redeem(db, token, password, confirmation):
    import portal
    if not 12 <= len(password) <= 256 or password != confirmation:
        raise ValueError('Passwörter müssen übereinstimmen und 12 bis 256 Zeichen lang sein.')
    if not 40 <= len(token) <= 64: raise ValueError('Rücksetzlink ungültig oder abgelaufen.')
    initialize(db)
    db.execute('BEGIN IMMEDIATE')
    row = db.execute('SELECT user_id FROM password_resets WHERE token_hash=? AND expires_at>?', (portal.digest(token), int(time.time()))).fetchone()
    if not row:
        db.rollback()
        raise ValueError('Rücksetzlink ungültig oder abgelaufen.')
    db.execute('UPDATE users SET password=? WHERE id=?', (portal.password_hash(password), row[0]))
    db.execute('DELETE FROM sessions WHERE user_id=?', (row[0],))
    db.execute('DELETE FROM password_resets WHERE user_id=?', (row[0],))
    db.execute('DELETE FROM password_help_requests WHERE user_id=?', (row[0],))
    db.commit()

FORM = '''<p>Dieser Link gilt einmalig für 30 Minuten. Danach bitte neu anmelden.</p>
<form method="post" action="/reset-password"><input type="hidden" name="token" id="reset-token">
<label>Neues Passwort (12–256 Zeichen)<input type="password" name="password" minlength="12" maxlength="256" autocomplete="new-password" required></label>
<label>Passwort wiederholen<input type="password" name="confirmation" minlength="12" maxlength="256" autocomplete="new-password" required></label>
<button>Passwort ändern</button></form>
<script src="/media/reset-password.js" defer></script>'''

if __name__ == '__main__':
    import sys
    import portal
    with portal.database() as db: token = issue(db, sys.argv[1])
    print('https://tormentor-codex.de/reset-password#' + token)
