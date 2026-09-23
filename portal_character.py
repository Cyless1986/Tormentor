"""German D&D 2024 character sheet, stored per authenticated player."""
import json
import portal_inspiration
from html import escape

ABILITIES = [('str', 'Stärke'), ('dex', 'Geschicklichkeit'), ('con', 'Konstitution'), ('int', 'Intelligenz'), ('wis', 'Weisheit'), ('cha', 'Charisma')]
SKILLS = [('acrobatics', 'Akrobatik', 'dex'), ('arcana', 'Arkane Kunde', 'int'), ('athletics', 'Athletik', 'str'), ('performance', 'Auftreten', 'cha'), ('intimidation', 'Einschüchtern', 'cha'), ('sleight', 'Fingerfertigkeit', 'dex'), ('history', 'Geschichte', 'int'), ('medicine', 'Heilkunde', 'wis'), ('stealth', 'Heimlichkeit', 'dex'), ('animal', 'Mit Tieren umgehen', 'wis'), ('insight', 'Motiv erkennen', 'wis'), ('nature', 'Naturkunde', 'int'), ('religion', 'Religion', 'int'), ('investigation', 'Nachforschungen', 'int'), ('deception', 'Täuschen', 'cha'), ('survival', 'Überlebenskunst', 'wis'), ('persuasion', 'Überzeugen', 'cha'), ('perception', 'Wahrnehmung', 'wis')]
NUMBERS = {'hp': ('Aktuelle Trefferpunkte', 0, 9999, 0), 'hp_max': ('Maximale Trefferpunkte', 0, 9999, 0), 'hp_temp': ('Temporäre Trefferpunkte', 0, 9999, 0), 'ac': ('Rüstungsklasse', 0, 99, 10), 'speed': ('Bewegungsrate (Meter)', 0, 999, 9), 'initiative': ('Zusätzlicher Initiativebonus', -30, 30, 0), 'exhaustion': ('Erschöpfungsstufe', 0, 6, 0), 'death_success': ('Erfolgreiche Todesrettungswürfe', 0, 3, 0), 'death_failure': ('Misslungene Todesrettungswürfe', 0, 3, 0)}
TEXTS = [('name', 'Charaktername'), ('background', 'Hintergrund'), ('alignment', 'Gesinnung'), ('hit_dice', 'Trefferwürfel (verfügbar / gesamt)'), ('attacks', 'Angriffe und Waffen (Angriffsbonus, Schaden, Eigenschaften)'), ('features', 'Klassenmerkmale, Talente und Waffenmeisterschaften'), ('spells', 'Zauber (Grad, vorbereitet, Wirkung und Notizen)'), ('equipment', 'Inventar, Ausrüstung und Münzen'), ('languages', 'Sprachen und Werkzeugübungen'), ('conditions', 'Zustände und weitere Effekte'), ('notes', 'Persönlichkeit, Hintergrundgeschichte und Notizen')]


COMPANION_TEXTS = [(f'companion_{i}_{key}', title) for i in range(1, 4) for key, title in (
    ('name', 'Name'), ('kind', 'Art / Wesen'), ('abilities', 'Angriffe und Fähigkeiten'), ('notes', 'Ausrüstung, Bindung und Notizen'))]
COMPANION_NUMBERS = {f'companion_{i}_{key}': (title, low, high, default) for i in range(1, 4) for key, title, low, high, default in (
    ('hp', 'Aktuelle Trefferpunkte', 0, 9999, 0), ('hp_max', 'Maximale Trefferpunkte', 0, 9999, 0), ('ac', 'Rüstungsklasse', 0, 99, 10))}


def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS character_sheets (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1)')


def load(db, uid):
    row = db.execute('SELECT data,revision FROM character_sheets WHERE user_id=?', (uid,)).fetchone()
    return (json.loads(row['data']), row['revision']) if row else ({}, 0)


def save(db, user, data):
    result = {}
    def number(key, low, high, default):
        try:
            value = float(data.get(key, default)) if key == 'speed' else int(data.get(key, default))
        except (ValueError, TypeError):
            raise ValueError('Bitte alle Zahlenfelder gültig ausfüllen.') from None
        if not low <= value <= high:
            raise ValueError('Ein Zahlenwert liegt außerhalb des erlaubten Bereichs.')
        result[key] = value
    for key, _ in ABILITIES:
        number(key, 1, 30, 10)
        number('save_' + key, 0, 1, 0)
    for key, _, _ in SKILLS:
        number(key, 0, 2, 0)
    for key, (_, low, high, default) in (NUMBERS | COMPANION_NUMBERS).items():
        number(key, low, high, default)
    for level in range(1, 10):
        number(f'slots_{level}', 0, 30, 0)
        number(f'used_{level}', 0, 30, 0)
        if result[f'used_{level}'] > result[f'slots_{level}']:
            raise ValueError('Verbrauchte Zauberplätze dürfen die Gesamtzahl nicht überschreiten.')
    for key, _ in TEXTS + COMPANION_TEXTS:
        value = data.get(key, '').strip()
        if len(value) > 6000:
            raise ValueError('Ein Textfeld enthält mehr als 6000 Zeichen.')
        result[key] = value
    result['spell_ability'] = data.get('spell_ability', '')
    if result['spell_ability'] not in ('', 'str', 'dex', 'con', 'int', 'wis', 'cha'):
        raise ValueError('Ungültiges Zauberattribut.')
    try:
        revision = int(data.get('revision', '-1'))
    except ValueError:
        raise ValueError('Bitte den Charakterbogen neu öffnen.') from None
    # The optimistic revision prevents a second browser from overwriting newer edits.
    if revision == 0:
        changed = db.execute('INSERT OR IGNORE INTO character_sheets(user_id,data,revision) VALUES(?,?,1)', (user['id'], json.dumps(result, ensure_ascii=False)))
    else:
        changed = db.execute('UPDATE character_sheets SET data=?,revision=revision+1 WHERE user_id=? AND revision=?', (json.dumps(result, ensure_ascii=False), user['id'], revision))
    if not changed.rowcount:
        raise ValueError('Der Bogen wurde inzwischen in einem anderen Fenster gespeichert. Deine Eingaben stehen unten. Öffne den aktuellen Bogen in einem neuen Tab und übertrage deine Änderungen.')


def render(db, user, data=None, error='', saved=False):
    stored, revision = load(db, user['id'])
    values = stored if data is None else data
    def value(key, default=''):
        return escape(str(values.get(key, default)), quote=True)
    def num(key, title, low, high, default):
        step = ' step="0.5"' if key == 'speed' else ''
        return f'<label>{title}<input type="number" name="{key}" min="{low}" max="{high}"{step} value="{value(key, default)}" required></label>'
    def select(key, title, options, default=0):
        return f'<label>{title}<select name="{key}">' + ''.join(f'<option value="{v}"' + (' selected' if str(values.get(key, default)) == str(v) else '') + f'>{label}</option>' for v, label in options) + '</select></label>'
    def fields(*keys):
        labels = dict(TEXTS)
        return '<div class="card">' + ''.join(f'<label>{labels[key]}<textarea name="{key}" rows="{2 if key in ("name", "background", "alignment", "hit_dice") else 6}" maxlength="6000">{value(key)}</textarea></label>' for key in keys) + '</div>'
    abilities = '<section class="card"><h3>Attribute und Rettungswürfe</h3><p class="sheet-totals">Übungsbonus <output id="proficiency"></output></p><div class="grid">'
    for key, title in ABILITIES:
        abilities += '<div class="sheet-stat">' + num(key, title, 1, 30, 10) + f'<p>Modifikator <output id="mod-{key}"></output> · Rettungswurf <output id="save-{key}"></output></p>' + select('save_' + key, 'Rettungswurf-Übung', [(0, 'Nicht geübt'), (1, 'Geübt')]) + '</div>'
    abilities += '</div></section>'
    combat = '<section class="card"><h3>Kampf und Zustand</h3><div class="grid">'
    for key, (title, low, high, default) in NUMBERS.items():
        combat += num(key, title, low, high, default)
    combat += '</div><div class="sheet-totals"><span>Initiative <output id="initiative-total"></output></span><span>Passive Wahrnehmung <output id="passive"></output></span></div></section>' + portal_inspiration.render(db, user)
    skills = '<section class="card"><h3>Fertigkeiten</h3><div class="grid">'
    for key, title, ability in SKILLS:
        skills += '<div class="sheet-skill">' + select(key, title, [(0, 'Nicht geübt'), (1, 'Geübt'), (2, 'Expertise')]) + f'<output data-skill="{key}" data-ability="{ability}"></output></div>'
    skills += '</div></section>'
    magic = '<section class="card"><h3>Zauberwirken</h3>' + select('spell_ability', 'Zauberattribut', [('', 'Keines')] + ABILITIES, '') + '<div class="sheet-totals"><span>Rettungswurf-SG <output id="spell-dc"></output></span><span>Zauberangriff <output id="spell-attack"></output></span></div><div class="grid">'
    for level in range(1, 10):
        magic += f'<div class="sheet-stat"><h4>Grad {level}</h4>' + num(f'slots_{level}', 'Zauberplätze gesamt', 0, 30, 0) + num(f'used_{level}', 'Davon verbraucht', 0, 30, 0) + '</div>'
    magic += '</div></section>'
    companions = ''
    for i in range(1, 4):
        prefix = f'companion_{i}_'
        companions += '<details class="card sheet-companion"' + (' open' if i == 1 or any(values.get(prefix + key) for key in ('name', 'kind', 'abilities', 'notes')) else '') + f'><summary>Begleiter {i}</summary><div class="grid">'
        for key, title in COMPANION_TEXTS:
            if key in (prefix + 'name', prefix + 'kind'):
                companions += f'<label>{title}<input name="{key}" maxlength="6000" value="{value(key)}"></label>'
        companions += '</div><div class="grid">'
        for key, (title, low, high, default) in COMPANION_NUMBERS.items():
            if key.startswith(prefix):
                companions += num(key, title, low, high, default)
        companions += '</div>'
        for key, title in COMPANION_TEXTS:
            if key in (prefix + 'abilities', prefix + 'notes'):
                companions += f'<label>{title}<textarea name="{key}" rows="4" maxlength="6000">{value(key)}</textarea></label>'
        companions += '</details>'
    pages = [
        ('identity', 'Charakter', 'Name, Herkunft und die Geschichte hinter deinem Abenteuer.', fields('name', 'background', 'alignment', 'notes')),
        ('combat', 'Kampf', 'Alles, was im nächsten Gefecht zählt.', combat + fields('hit_dice', 'attacks', 'conditions')),
        ('skills', 'Fertigkeiten', 'Deine Attribute, Rettungswürfe und besonderen Stärken.', abilities + skills + fields('features')),
        ('magic', 'Magie', 'Deine Zauber und verfügbaren Zauberplätze.', magic + fields('spells')),
        ('companions', 'Begleiter', 'Tiergefährte, Vertrauter oder Reittier – Platz für bis zu drei treue Gefährten. Werte und Fähigkeiten trägst du selbst ein.', companions),
        ('gear', 'Ausrüstung', 'Von der ersten Goldmünze bis zum liebsten Werkzeug.', fields('equipment', 'languages')),
    ]
    tabs = '<nav class="sheet-tabs" aria-label="Seiten des Charakterbogens">' + ''.join(f'<a id="tab-{key}" href="#sheet-{key}"><span>0{i}</span>{title}</a>' for i, (key, title, _, _) in enumerate(pages, 1)) + '</nav>'
    panels = ''.join(f'<section class="sheet-panel" id="sheet-{key}" aria-labelledby="tab-{key}"><h2>{title}</h2><p class="sheet-hint">{intro}</p>{content}</section>' for key, title, intro, content in pages)
    notices = ('<p class="error" role="alert">' + escape(error) + '</p>') if error else ''
    if saved:
        notices += '<p role="status">Charakterbogen gespeichert.</p>'
    body = f'<form method="post" id="character-sheet" data-level="{user["level"]}"><input type="hidden" name="revision" value="{value("revision", revision)}">' + tabs + panels
    body += '<div class="sheet-paging" hidden><button type="button" id="sheet-prev">← Zurück</button><span id="sheet-page-count" aria-live="polite"></span><button type="button" id="sheet-next">Weiter →</button></div><p class="sheet-hint">Berechnete Boni berücksichtigen Attribute, Stufe und Übung. Zusätzliche Klassenmerkmale, Talente, Gegenstände und Zustände bitte selbst berücksichtigen und in den Notizen festhalten.</p><div class="sheet-save"><div><strong>Dein Abenteuer, dein Bogen</strong><span id="sheet-status" role="status">Alle Seiten gemeinsam speichern</span></div><button type="submit">Charakterbogen speichern</button></div></form><script src="/media/character.js" defer></script>'
    hero = '<link rel="stylesheet" href="/media/character.css"><div class="sheet-hero"><p class="sheet-eyebrow">TORMENTOR · D&D 2024</p><h2 id="hero-name">' + (value('name') or 'Deine Legende beginnt') + '</h2><p>' + escape(user['class_name'] or 'Klasse offen') + ' · ' + escape(user['subclass'] or 'Unterklasse offen') + '</p><div class="sheet-badges"><span>Stufe ' + str(user['level']) + '</span><span>' + escape(user['race'] or 'Spezies offen') + '</span></div><a href="/profil">Profildaten bearbeiten ↗</a> · <a href="/codex/zauber">Zauberlexikon ↗</a></div>'
    return hero + notices + body
