"""Invitation input and actionable registration errors."""
import re
import unicodedata
from html import escape


def normalize_code(value):
    # Copying from messengers often inserts spaces, line breaks or zero-width marks.
    value = unicodedata.normalize('NFKC', value)
    return ''.join(c for c in value if not c.isspace() and c not in '-\u2010\u2011\u2012\u2013\u2014\u200b\ufeff').upper()


def validate(code, username, password):
    if not re.fullmatch(r'[A-F0-9]{16}', code):
        raise ValueError('Bitte den vollständigen Einladungscode mit 16 Zeichen eingeben. Leerzeichen und Trennstriche sind erlaubt.')
    if not (3 <= len(username) <= 32 and username.replace('_', '').isalnum()):
        raise ValueError('Der Benutzername braucht 3 bis 32 Zeichen: Buchstaben, Zahlen oder Unterstriche.')
    if len(password) < 12:
        raise ValueError('Das Passwort braucht mindestens 12 Zeichen. Dein Einladungscode bleibt unbenutzt; du brauchst keinen neuen Code.')


def form(data=None, error=''):
    data = data or {}
    value = lambda key: escape(data.get(key, ''), quote=True)
    return ('<div class="card">' + ('<p class="error" role="alert">' + escape(error) + '</p>' if error else '') +
            '<p>Dein DM gibt dir einen Einladungscode. Er wird erst verbraucht, wenn dein Konto erfolgreich erstellt wurde.</p>'
            '<form method="post" action="/register"><label>Einladungscode'
            '<input name="code" value="' + value('code') + '" required autocomplete="off" autocapitalize="characters" spellcheck="false"></label>'
            '<label>Benutzername<input name="username" value="' + value('username') + '" required minlength="3" maxlength="32" autocomplete="username" autocapitalize="none" spellcheck="false"></label>'
            '<label>Passwort (mindestens 12 Zeichen)<input name="password" type="password" required minlength="12" autocomplete="new-password"></label>'
            '<button>Konto erstellen</button></form><p>Schon registriert? <a href="/login">Zum Login</a></p></div>')
