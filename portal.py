"""Local Tormentor player portal. Run behind HTTPS before internet exposure."""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import sys
import time
from contextlib import contextmanager
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import lore
import lore_workflow
import news
import session_schedule
import portal_maps
import codex_homebrew
import portal_security
import codex_core
import codex_2014
import codex_expansions
import codex_spells
import portal_reset
import portal_handouts
import portal_chat
import portal_character
import portal_inspiration
import portal_registration

ROOT = Path(__file__).resolve().parent
INTRO_MUSIC = ROOT / 'assets/music/rising-moon.mp3'
FOREST_MUSIC = INTRO_MUSIC
DB = ROOT / "portal.sqlite3"
LORE = Path(os.environ.get("TORMENTOR_PORTAL_LORE_DIR", str(ROOT / "portal_lore")))
SESSION_AGE = 14 * 86400


@contextmanager
def database():
    db = sqlite3.connect(DB, timeout=15)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL, role TEXT NOT NULL,
          player_name TEXT NOT NULL DEFAULT '', race TEXT NOT NULL DEFAULT '',
          class_name TEXT NOT NULL DEFAULT '', subclass TEXT NOT NULL DEFAULT '',
          group_name TEXT NOT NULL DEFAULT '', level INTEGER NOT NULL DEFAULT 1,
          companion TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS invites (
          code_hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL,
          uses_left INTEGER NOT NULL, created_by INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
          expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS codex_entries (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
          edition TEXT NOT NULL, source TEXT NOT NULL DEFAULT '',
          body TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 0,
          deleted INTEGER NOT NULL DEFAULT 0, created_by INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS level_suggestions (
          id INTEGER PRIMARY KEY, player_id INTEGER NOT NULL,
          proposed_level INTEGER NOT NULL, session_id TEXT NOT NULL,
          evidence TEXT NOT NULL, created_by INTEGER NOT NULL,
          applied INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS handouts (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
          published INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0,
          created_by INTEGER NOT NULL, updated_at INTEGER NOT NULL
        );
        """)
        session_schedule.initialize(db)
        portal_maps.initialize(db)
        portal_reset.initialize(db)
        portal_handouts.initialize(db)
        portal_chat.initialize(db)
        portal_character.initialize(db)
        portal_inspiration.initialize(db)
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def password_hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return salt.hex() + ":" + digest.hex()


def password_ok(password, stored):
    try:
        salt, _ = stored.split(":", 1)
        return hmac.compare_digest(password_hash(password, bytes.fromhex(salt)), stored)
    except (ValueError, TypeError):
        return False


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def escape(value):
    return html.escape(str(value), quote=True)


def page(title, body, user=None):
    # Migration bundles intentionally omit local music files.
    if not INTRO_MUSIC.is_file():
        body = re.sub(r'<p><audio id="intro-music".*?</script>', '', body, flags=re.S)
    if not FOREST_MUSIC.is_file():
        body = re.sub(r'<section class="card"><h2>Spielmusik</h2>.*?</section>', '', body, flags=re.S)
    if 'id="intro-music"' in body or 'id="dashboard-music"' in body:
        body += '<p><small>Musik: <a href="https://opengameart.org/content/fantasy-rising-moon">Rising Moon — RandomMind</a> · <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>.</small></p>'
    login_video = '<video id="login-background" autoplay muted loop playsinline preload="none" aria-hidden="true" poster="/media/login-tavern.png"></video><script src="/media/login-background.js" defer></script>' if title in ('Login', 'Willkommen') else ''
    login_style = '<style>body{background:#10191b url("/media/login-tavern.png") center center/cover fixed no-repeat;min-height:100vh}#login-background{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;pointer-events:none;z-index:-1}body{isolation:isolate}header{background:#100e10d9}@media(prefers-reduced-motion:reduce){#login-background{display:none}}main{max-width:960px}main>h1{text-shadow:0 2px 12px #000}main>.grid>.card{background:#17120fed;backdrop-filter:blur(8px)}main>p{background:#100e10db;padding:.7rem;border-radius:8px} @media(max-width:600px){body{background-position:30% center}#login-background{object-position:30% center}main{padding-top:1.5rem}}</style>' if title in ('Login', 'Willkommen') else ''
    nav = '<a href="/">Start</a><a href="/codex">Codex</a><a href="/news">D&D-News</a><a href="/links">Links</a>'
    if user:
        nav += '<a href="/maps">Karten</a><a href="/messages" id="chat-link">Nachrichten <span id="chat-unread" class="badge" style="background:#a44336;color:white" hidden aria-live="polite"></span></a><a href="/character">Charakterbogen</a>'
        nav += '<a href="/dashboard">Spielerbereich</a><a href="/profil">Mein Profil</a><a href="/lore">Chronik</a><a href="/handouts">Handouts</a>'
        if user["role"] == "dm": nav += '<a href="/dm">DM</a>'
        nav += '<form method="post" action="/logout"><button>Abmelden</button></form>'
    else:
        nav += '<a href="/login">Login</a><a href="/register">Mit Code registrieren</a>'
    if user:
        body += '<script src="/media/chat-unread.js" defer></script>'
    header_style = '<style>header{background:linear-gradient(90deg,rgba(12,10,9,.78),rgba(12,10,9,.48)),url(\'/media/header-castle.png\') center 48%/cover no-repeat;min-height:100px;box-sizing:border-box;text-shadow:0 2px 5px #000}header nav a{color:#f1dfb6}header nav a:hover,header nav a:focus-visible{color:#fff4d7;text-decoration:underline;text-underline-offset:5px}header strong{color:#f0cf89}@media(max-width:600px){header{min-height:140px;background-position:center,65% center}}</style>' if title == 'Spieler-Dashboard' else '<style>header{background-image:none!important;background-color:transparent!important;text-shadow:0 2px 5px #000}header nav a{color:#f1dfb6}header nav a:hover,header nav a:focus-visible{color:#fff4d7;text-decoration:underline;text-underline-offset:5px}header strong{color:#f0cf89}</style>'
    header_style = '''<style>header{background:linear-gradient(90deg,#0c0a09cc,#0c0a0977),url('/media/header-castle.png') center 48%/cover no-repeat;min-height:140px;text-shadow:0 2px 5px #000}header nav a{color:#f1dfb6}</style>'''
    body += '''<style>*{box-sizing:border-box}main,.book,.card,.grid>*{min-width:0;max-width:100%}.grid{grid-template-columns:repeat(auto-fit,minmax(min(240px,100%),1fr))}.book,.card{overflow-wrap:anywhere}.book .card{color:#f1e3c8}.book .card h2,.spell-help h2,.spell-help h3{color:#e5be72}.book .card small,.spell-help small{color:#d3c2a4}.book .card a{color:#edcb85}.level-table{max-width:100%;overflow-x:auto}.book ul,.book ol{padding-left:1.4rem}dd{margin-left:1rem}button{max-width:100%;white-space:normal}@media(max-width:600px){.book{padding:.8rem;border-width:6px}.card{padding:1rem}.cover:hover{transform:none}.book h2{font-size:1.4rem}header{background-position:65% center}}</style>'''
    return f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Tormentor</title><style>
    :root{{color-scheme:dark}}body{{margin:0;background:#100c0b;color:#f1e3c8;font:17px Georgia,serif;cursor:url('/media/dagger.svg') 3 3,auto}}header{{background:#201510;border-bottom:1px solid #806847;padding:1.2rem 4vw;display:flex;align-items:center;gap:2rem;flex-wrap:wrap}}h1,h2{{font-weight:normal;color:#e5be72}}header strong{{font-size:1.6rem;color:#d3a256}}nav{{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}}a{{color:#dcb46d}}nav a{{text-decoration:none}}main{{max-width:1050px;margin:auto;padding:3rem 5vw}}.card{{background:#211915;border:1px solid #785c3a;border-radius:14px;padding:1.5rem;margin:1rem 0;box-shadow:0 15px 35px #0005}}input,textarea,button{{font:inherit;border-radius:6px;padding:.65rem;background:#130f0d;color:#f5e6c8;border:1px solid #9b7546}}input,textarea{{display:block;width:min(100%,560px);box-sizing:border-box;margin:.4rem 0 1rem;cursor:text}}button{{background:#752d26}}button:hover{{background:#a44336}}a,button{{cursor:url('/media/dagger.svg') 3 3,pointer}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}}small{{color:#baa88f}}label{{display:block;margin:.5rem 0}}.error{{color:#ffaaa3}}.book{{background:#e6d4ad;color:#281b11;border:14px solid #4a271d;border-radius:8px 18px 18px 8px;min-height:320px;padding:2rem;box-shadow:12px 18px 30px #0009}}.book h2{{color:#633a22}}.book small{{color:#71583e}}.book a{{color:#713d26}}@media print{{header,button{{display:none}}body{{background:white;color:black}}.book{{box-shadow:none;break-after:page}}}}
    .intro{{width:100%;max-height:420px;object-fit:cover;border:1px solid #785c3a;border-radius:12px;background:#000}}audio{{width:min(100%,560px)}}.cover{{text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:transform .5s}}.cover:hover{{transform:perspective(900px) rotateY(-8deg)}}.cover img{{width:120px;height:120px;object-fit:contain}}.book{{animation:turn .45s ease-out;transform-origin:left center}}@keyframes turn{{from{{opacity:.3;transform:perspective(900px) rotateY(-18deg)}}to{{opacity:1;transform:perspective(900px) rotateY(0)}}}}
    .codex-illustration{{display:block;width:100%;height:auto;max-height:none;object-fit:contain;border-radius:4px}}select{{font:inherit;padding:.6rem;background:#130f0d;color:#f5e6c8;border:1px solid #9b7546;border-radius:6px;max-width:100%}}input[type=checkbox]{{display:inline;width:auto;margin-right:.5rem}}.actions{{display:flex;gap:.8rem;align-items:center;flex-wrap:wrap}}.preserve{{white-space:pre-wrap;overflow-wrap:anywhere}}.review textarea{{width:100%;max-width:none}}.badge{{display:inline-block;border:1px solid #806847;border-radius:20px;padding:.2rem .7rem;font-size:.85rem}}.notice{{border-left:3px solid #d3a256;padding-left:1rem}}@media(prefers-reduced-motion:reduce){{.book,.cover{{animation:none;transition:none}}}}
    .news-feed{{max-width:720px;margin:1.5rem auto}}.feed-card{{overflow:hidden;background:#211915;border:1px solid #785c3a;border-radius:18px;margin:0 0 1.7rem;box-shadow:0 15px 30px #0004}}.feed-copy{{padding:1.3rem 1.6rem}}.feed-copy h2{{line-height:1.25;margin:.5rem 0 1rem;font-size:1.65rem;overflow-wrap:anywhere}}.feed-meta{{font:12px system-ui,sans-serif;letter-spacing:.08em;color:#c1ad8e}}.news-art{{min-height:140px;display:flex;align-items:center;justify-content:center;gap:1rem;background:radial-gradient(ellipse at 70% 15%,#9b734e66,transparent 70%),linear-gradient(130deg,#301716,#594331);color:#e8c98c;letter-spacing:.2em;font:700 20px Georgia,serif}}.news-art span{{font-size:64px}}.video-preview{{aspect-ratio:16/9;background:#080606}}.video-start{{position:relative;display:block;width:100%;height:100%;padding:0;border:0;border-radius:0;overflow:hidden;background:#080606}}.video-start img{{display:block;width:100%;height:100%;object-fit:contain;opacity:.85}}.video-start:hover img{{opacity:1}}.play-icon{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);display:grid;place-items:center;width:70px;height:70px;border:1px solid #ead7ab;border-radius:50%;background:#752d26ed;font-size:28px}}.video-caption{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);padding:.3rem .8rem;background:#000b;border-radius:20px;font:14px system-ui,sans-serif}}.video-preview iframe{{display:block;width:100%;height:100%;border:0}}.feed-filters{{max-width:720px;margin:auto;gap:.6rem}}.feed-filters a{{padding:.65rem 1.2rem;border:1px solid #785c3a;border-radius:25px;background:#211915}}.feed-filters .selected{{background:#752d26;border-color:#e3b66a;color:#fff0d5}}.feed-status,.feed-end{{max-width:720px;margin:1rem auto}}.feed-more{{display:block;margin:1rem auto}}[hidden]{{display:none!important}}@media(max-width:600px){{main{{padding:1.5rem 4vw}}header{{gap:.6rem;padding:1rem 4vw}}nav{{gap:.65rem;font-size:15px}}.feed-copy{{padding:1rem}}.feed-copy h2{{font-size:1.4rem}}.book{{padding:1rem;border-width:7px}}.news-art{{min-height:110px}}}}
    nav>a{{position:relative;display:inline-block;padding:.5rem .65rem;border-radius:8px;transition:transform .18s ease,color .18s ease,background .18s ease,box-shadow .18s ease}}nav>a::after{{content:"";position:absolute;left:.65rem;right:.65rem;bottom:.15rem;height:2px;background:#e5be72;transform:scaleX(0);transform-origin:center;transition:transform .18s ease}}a:focus-visible,button:focus-visible{{outline:2px solid #f4d690;outline-offset:4px}}nav>a:focus-visible{{background:#d4a34b20;color:#ffdf99}}nav>a:focus-visible::after{{transform:scaleX(1)}}button{{transition:transform .18s ease,background .18s ease,box-shadow .18s ease}}@media(hover:hover) and (pointer:fine){{nav>a:hover{{transform:translateY(-3px);color:#ffe4a9;background:#d4a34b20;box-shadow:0 6px 18px #d89c3026}}nav>a:hover::after{{transform:scaleX(1)}}button:not(:disabled):hover{{transform:translateY(-2px);box-shadow:0 5px 14px #0005}}button:not(:disabled):active{{transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{nav>a,nav>a::after,button{{transition:none}}nav>a:hover,button:not(:disabled):hover{{transform:none}}}}
    .book a[href^="/codex"],.card a[href^="/codex"]{{display:inline-block;padding:.35rem .55rem;border-radius:6px;text-decoration-thickness:1px;text-underline-offset:3px;transition:transform .18s ease,background .18s ease,box-shadow .18s ease}}.book li,.card li:has(a[href^="/codex"]){{margin:.25rem 0}}.book a[href^="/codex"]:focus-visible{{outline-color:#71451e;background:#f8e3a7}}@media(hover:hover) and (pointer:fine){{.book a[href^="/codex"]:hover,.card a[href^="/codex"]:hover{{transform:translateY(-2px);background:#dca94340;box-shadow:0 4px 12px #a46c3238}}}}@media(prefers-reduced-motion:reduce){{.book a[href^="/codex"],.card a[href^="/codex"]{{transition:none}}.book a[href^="/codex"]:hover,.card a[href^="/codex"]:hover,.cover:hover{{transform:none}}}}@media print{{.book a[href^="/codex"],.card a[href^="/codex"]{{padding:0;box-shadow:none;transform:none;background:none}}}}
    .level-table{{overflow-x:auto;margin:1rem 0}}.level-table caption{{text-align:left;font-weight:bold;padding:.6rem 0}}.level-table td:first-child{{font-weight:bold}}@media print{{.level-table{{overflow:visible}}.level-table table{{font-size:9pt}}.level-table th,.level-table td{{padding:3pt}}.level-table tr{{break-inside:avoid}}}}
    .book table{{width:100%;border-collapse:collapse;font-size:.95rem}}.book th,.book td{{padding:.6rem;text-align:left;vertical-align:top;border-bottom:1px solid #927854}}.book th{{color:#59341f}}.book tr:nth-child(even){{background:#b29a7020}}
    .codex-art-page{{margin-bottom:1.5rem}}@media print{{.codex-art-page{{break-inside:avoid}}.codex-art-page .codex-illustration{{width:100%;height:220mm;object-fit:contain}}}}
    </style>{login_style}{header_style}{login_video}<header><strong>☉ TORMENTOR</strong><nav>{nav}</nav></header><main><h1>{escape(title)}</h1>{body}<p><small>Version 2.0 created with ChatGPT/Kodex</small></p></main></html>'''


def form_field(name, label, value="", kind="text", autocomplete=None):
    extra = f' autocomplete="{escape(autocomplete)}"' if autocomplete else ""
    return f'<label>{escape(label)}<input name="{escape(name)}" type="{kind}" value="{escape(value)}"{extra} required></label>'


ENTRY_KINDS = ("Spezies", "Klasse", "Unterklasse", "Hintergrund", "Talent", "Zauber", "Sonstiges")
ENTRY_EDITIONS = ("2024", "2014", "Homebrew")


def entry_form(entry=None):
    value = lambda key, default="": entry[key] if entry else default
    select = lambda name, choices: '<label>' + escape(name.capitalize()) + '<select name="' + name + '">' + ''.join('<option' + (' selected' if value(name) == choice else '') + '>' + escape(choice) + '</option>' for choice in choices) + '</select></label>'
    published = ' checked' if entry and entry["published"] else ''
    return ('<form method="post">' + form_field("title", "Name", value("title")) + select("kind", ENTRY_KINDS) + select("edition", ENTRY_EDITIONS) +
            '<label>Quelle oder Lizenzhinweis<input name="source" value="' + escape(value("source")) + '" placeholder="Bei Homebrew: Eigene Schöpfung"></label>' +
            '<label>Beschreibung und Regeln<textarea name="body" rows="14" required>' + escape(value("body")) + '</textarea></label>' +
            '<label><input type="checkbox" name="published" value="1"' + published + '> Für Spieler freigeben</label><button>Eintrag speichern</button></form>')


def backgrounds_page(db, user):
    body = ('<section class="book"><h2>Herkünfte &amp; Hintergründe</h2>'
            '<p>Welches Leben hat dein Charakter vor seinen Abenteuern geführt? Hier findest du die Hintergründe '
            'für deine Figur, getrennt nach Regelfassung und Homebrew.</p></section>')
    rows = db.execute("SELECT id,title,edition,source,published FROM codex_entries WHERE kind='Hintergrund' AND deleted=0 ORDER BY title").fetchall()
    visible = [row for row in rows if row['published'] or user and user['role'] == 'dm']
    if not visible:
        standard = [
            ('Akolyth', 'Regelfassung 2014', 'Du hast als Diener einer Gottheit oder eines Heiligtums gelebt.'),
            ('Scharlatan', 'Regelfassung 2014', 'Du hast dich mit Täuschungen, Fälschungen und Tricks über Wasser gehalten.'),
            ('Krimineller', 'Regelfassung 2014', 'Du kennst die Unterwelt und hast Erfahrung mit Diebstahl und Gaunerei.'),
            ('Unterhalter', 'Regelfassung 2014', 'Du hast dein Publikum mit Musik, Schauspiel oder Geschichten begeistert.'),
            ('Volksheld', 'Regelfassung 2014', 'Du hast deine Gemeinschaft beschützt und bist durch Taten bekannt geworden.'),
            ('Gildenhandwerker', 'Regelfassung 2014', 'Du bist in einem Handwerk ausgebildet und Mitglied einer Handwerksgilde.'),
            ('Einsiedler', 'Regelfassung 2014', 'Du hast abgeschieden gelebt und dabei eine wichtige Erkenntnis gewonnen.'),
            ('Adliger', 'Regelfassung 2014', 'Du entstammst einer wohlhabenden oder einflussreichen Familie.'),
            ('Weiser', 'Regelfassung 2014', 'Du hast dein Leben dem Lernen, Forschen und Sammeln von Wissen gewidmet.'),
            ('Seemann', 'Regelfassung 2014', 'Du hast auf Schiffen gearbeitet und kennst das Leben auf See.'),
            ('Soldat', 'Regelfassung 2014', 'Du hast in einer Armee gedient und militärische Erfahrung gesammelt.'),
            ('Straßenkind', 'Regelfassung 2014', 'Du bist in den Straßen aufgewachsen und hast gelernt, allein zurechtzukommen.'),
            ('Fremder', 'Regelfassung 2014', 'Du stammst aus der Wildnis und bist mit Überleben und Natur vertraut.'),
        ]
        body += '<section class="card"><h2>Regelfassung 2014</h2><ul>' + ''.join('<li><b>'+escape(n)+'</b> · '+escape(d)+'</li>' for n,_,d in standard) + '</ul></section>'
    for edition in ENTRY_EDITIONS:
        label = 'Homebrew' if edition == 'Homebrew' else 'Regelfassung ' + edition
        body += '<section class="card"><h2>' + label + '</h2>'
        entries = [row for row in visible if row['edition'] == edition]
        if entries:
            body += '<ul>' + ''.join(
                f'<li><a href="/codex/eintrag/{row["id"]}">{escape(row["title"])}</a>'
                + (f' · {escape(row["source"])}' if row['source'] else '')
                + (' · Privat (nur DM)' if not row['published'] else '') + '</li>' for row in entries) + '</ul>'
        else:
            body += '<p>Noch keine Herkünfte eingetragen oder freigegeben.</p>'
        body += '</section>'
    if user and user['role'] == 'dm':
        body += '<p><a href="/dm/codex">Herkunft anlegen</a> · Wähle beim neuen Eintrag die Art „Hintergrund“.</p>'
    return body + '<p><a href="/codex">Zurück zum Codex</a></p>'


def entry_links(db, edition, user):
    rows = db.execute("SELECT id,title,kind,published FROM codex_entries WHERE edition=? AND deleted=0 ORDER BY kind,title", (edition,)).fetchall()
    visible = [row for row in rows if row["published"] or user and user["role"] == "dm"]
    if not visible: return ""
    return '<div class="card"><h2>DM-Ergänzungen</h2>' + ''.join(f'<p><a href="/codex/eintrag/{row["id"]}">{escape(row["kind"])} · {escape(row["title"])}</a>{" · Privat" if not row["published"] else ""}</p>' for row in visible) + '</div>'


CODEX = {
    "2024": {
        "title": "Codex 2024 · SRD 5.2.1",
        "source": "https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.1.pdf",
        "species": ["Drachenblütige", "Zwerge", "Elfen", "Gnome", "Goliaths", "Halblinge", "Menschen", "Orks", "Tieflinge"],
        "classes": ["Barbar", "Barde", "Kleriker", "Druide", "Kämpfer", "Mönch", "Paladin", "Waldläufer", "Schurke", "Zauberer (Sorcerer)", "Hexenmeister", "Magier"],
    },
    "2014": {
        "title": "Codex 2014 · SRD 5.1",
        "source": "https://media.dndbeyond.com/compendium-images/srd/5.1/SRD_CC_v5.1.pdf",
        "species": ["Drachenblütige", "Zwerge", "Elfen", "Gnome", "Halbelfen", "Halborks", "Halblinge", "Menschen", "Tieflinge"],
        "classes": ["Barbar", "Barde", "Kleriker", "Druide", "Kämpfer", "Mönch", "Paladin", "Waldläufer", "Schurke", "Zauberer (Sorcerer)", "Hexenmeister", "Magier"],
    },
}

EXTRA_SPECIES = {
    "Mordenkainen: Monsters of the Multiverse": ["Aarakocra", "Aasimar", "Luft-Genasi", "Bugbear", "Zentaur", "Changeling", "Tiefengnom", "Duergar", "Erd-Genasi", "Eladrin", "Fee", "Firbolg", "Feuer-Genasi", "Githyanki", "Githzerai", "Goblin", "Goliath", "Harengon", "Hobgoblin", "Kenku", "Kobold", "Echsenvolk", "Minotaurus", "Ork", "Satyr", "Meereself", "Shadar-kai", "Shifter", "Tabaxi", "Tortle", "Triton", "Wasser-Genasi", "Yuan-ti"],
    "Spelljammer: Adventures in Space": ["Astralelf", "Autognom", "Giff", "Hadozee", "Plasmoid", "Thri-kreen"],
    "Van Richten’s Guide to Ravenloft": ["Dhampir", "Hexblood", "Reborn"],
    "Eberron: Rising from the Last War": ["Changeling", "Kalashtar", "Shifter", "Warforged"],
}


def expansion_index():
    return codex_expansions.index(codex_expansions.catalogue(EXTRA_SPECIES))


def homebrew_book():
    return codex_homebrew.render()


def published_lore():
    entries = []
    if LORE.exists():
        for file in LORE.glob("*/session.json"):
            try:
                item = json.loads(file.read_text(encoding="utf-8"))
                if item.get("published") and isinstance(item.get("approved"), dict): entries.append(item)
            except (OSError, ValueError): pass
    return sorted(entries, key=lambda item: item.get("created_at", ""), reverse=True)


def lore_page(path):
    entries = published_lore()
    menu = '<div class="grid"><div class="card"><a href="/lore/sitzungen">Sitzungen</a></div><div class="card"><a href="/lore/npcs">Bekannte NPCs</a></div><div class="card"><a href="/lore/orte">Bekannte Orte</a></div><div class="card"><a href="/lore/quests">Quests</a></div></div>'
    if path == "/lore": return menu
    if path == "/lore/sitzungen":
        content = ''.join(f'<article class="card"><h2>{escape(s.get("title", "Sitzung"))}</h2><p>{escape(s["approved"].get("summary", ""))}</p></article>' for s in entries)
    else:
        key = {"/lore/npcs": "npcs", "/lore/orte": "places", "/lore/quests": "quests"}[path]
        content = ''.join(f'<article class="card"><h2>{escape(s.get("title", "Sitzung"))}</h2><ul>' + ''.join(f'<li>{escape(value)}</li>' for value in s["approved"].get(key, []) if isinstance(value, str)) + '</ul></article>' for s in entries if s["approved"].get(key))
    return menu + (content or '<p>Noch keine freigegebenen Einträge.</p>')


def lore_revision(item):
    return digest(json.dumps(item, sort_keys=True, ensure_ascii=False))


def dm_lore_page(session_id=None, show_draft=False):
    if session_id is None:
        cards = []
        for item in lore.list_sessions():
            state = item.get("processing", {}).get("message", "Aufnahme oder Transkript bereit")
            cards.append(f'<article class="card"><span class="badge">{"Für Spieler freigegeben" if item.get("published") else "Nur DM"}</span><h2><a href="/dm/lore/{item["id"]}">{escape(item["title"])}</a></h2><p>{escape(state)}</p></article>')
        return ('<p>Aufnahmen vom Android-Gerät und aus Tormentor Desktop erscheinen hier. Prüfe die Ergebnisse vor der Spielerfreigabe.</p>'
                '<div class="card"><h2>Neue Sitzung</h2><form method="post">' + form_field("title", "Sitzungstitel, zum Beispiel Session 4") + '<button>Sitzung anlegen</button></form></div>' + ''.join(cards))
    item = lore.load(session_id)
    revision = f'<input type="hidden" name="revision" value="{lore_revision(item)}">'
    base = f"/dm/lore/{session_id}"
    busy = lore_workflow.is_busy(session_id)
    status = item.get("processing", {}).get("message", "Noch nicht ausgewertet.")
    if not busy and item.get("processing", {}).get("state") == "running":
        status = "Die Auswertung wurde unterbrochen. Du kannst sie erneut starten."
    body = f'<p><a href="/dm/lore">← Alle Sitzungen</a></p><h2>{escape(item["title"])}</h2><p class="notice">{escape(status)}</p>'
    if busy:
        return body + f'<div class="card"><p>Die Sitzung wird gerade bearbeitet. Die letzte Spielerfreigabe bleibt bis zu deiner nächsten Prüfung bestehen.</p><a href="{base}">Status aktualisieren</a></div>'
    body += '<div class="card"><h2>Auswertung</h2><div class="actions">'
    if item.get("audio"):
        body += f'<form method="post" action="{base}/process"><button>Aufnahme transkribieren und auswerten</button></form>'
    if item.get("transcript", "").strip():
        body += f'<form method="post" action="{base}/analyze"><button>Gespeichertes Transkript auswerten</button></form>'
    body += '</div><details><summary>Privates Transkript ansehen oder korrigieren</summary>'
    body += f'<form method="post" action="{base}/transcript">{revision}<label>Transkript · nur für den DM<textarea name="transcript" rows="12">{escape(item.get("transcript", ""))}</textarea></label><button>Transkript speichern</button></form></details></div>'
    edited = item.get("draft", {}) if show_draft or not (item.get("reviewed_at") or item.get("published")) else item.get("approved", {})
    fields = lore.review_fields(edited)
    body += f'<div class="card review"><h2>DM-Prüfung</h2><p>Bearbeite die Texte so, wie deine Spieler sie sehen dürfen. NPCs, Orte und Quests: ein Eintrag pro Zeile.</p><p><a href="{base}?draft=1">KI-Entwurf in die Prüfansicht laden</a> · <a href="{base}">Letzten Prüfstand laden</a></p><form method="post" action="{base}/review">{revision}'
    body += form_field("title", "Sitzungstitel", item["title"])
    for key, label, rows in (("summary", "Session-Zusammenfassung", 7), ("npcs", "Bekannte NPCs", 4), ("places", "Bekannte Orte", 4), ("quests", "Quests", 4), ("level_ups", "Levelvorschläge · pro Zeile Name | Stufe, etwa Arin | 3", 3)):
        body += f'<label>{label}<textarea name="{key}" rows="{rows}">{escape(fields[key])}</textarea></label>'
    body += '<label><input type="checkbox" name="published" value="1"' + (' checked' if item.get("published") else '') + '> Diese geprüften Inhalte für Spieler freigeben</label><button>Prüfung speichern</button></form></div>'
    if item.get("published"):
        body += f'<form method="post" action="{base}/unpublish">{revision}<button>Spielerfreigabe zurücknehmen</button></form>'
    return body


def expansion_classes():
    ravenloft = [("Artificer", "Reanimator"), ("Barde", "College of Spirits"), ("Kleriker", "Grave Domain"), ("Waldläufer", "Hollow Warden"), ("Schurke", "Phantom"), ("Zauberer (Sorcerer)", "Shadow Sorcery"), ("Hexenmeister", "Undead Patron")]
    rows = ''.join(f'<li><b>{escape(codex_expansions.german(kind))}:</b> {escape(codex_expansions.german(subclass))}</li>' for kind, subclass in ravenloft)
    return ('<div class="card"><h2>Magieschmied · zusätzliche Klasse</h2><p>Für 2014 und 2024 gibt es getrennte Fassungen des Magieschmieds (Artificer). Die neuere Fassung steht in „Eberron: Forge of the Artificer“. Sie ist nicht Teil der SRDs und wird deshalb nicht als frei lizenzierter Regeltext wiedergegeben.</p><p><a href="https://www.dndbeyond.com/sources/dnd/efota">Offizielle Quelle: Eberron: Forge of the Artificer</a></p></div>'
            '<div class="card"><h2>Ravenloft: The Horrors Within · 2024</h2><p>Das 2026 erschienene Buch führt sieben Horror-Unterklassen auf:</p><ol>' + rows + '</ol><p><a href="https://www.dndbeyond.com/sources/dnd/rthw">Offizielles Inhaltsverzeichnis</a> · <a href="https://www.dndbeyond.com/posts/2191-become-the-monster-in-the-shadows-with-7">Offizielle Vorstellung der sieben Unterklassen</a></p><p><small>Quellenindex; keine Übernahme der geschützten Unterklassenregeln.</small></p></div>')


def codex_book(edition, term=""):
    data = CODEX[edition]
    entries = [("Spezies", name) for name in data["species"]] + [("Klasse", name) for name in data["classes"]]
    if term: entries = [(kind, name) for kind, name in entries if term.casefold() in name.casefold()]
    toc = ''.join(f'<li><a href="/codex/2024/ork">{escape(kind)} · {escape(name)}</a></li>' if edition == "2024" and name == "Orks" else f'<li>{escape(kind)} · {escape(name)}</li>' for kind, name in entries)
    if edition=='2024':
        destinations={d['name']:'/codex/2024/klasse/'+key for key,d in codex_core.CLASSES.items()}
        destinations['Zauberer (Sorcerer)']=destinations['Zauberer']
        species_keys={'Drachenblütige':'drachenbluetiger','Zwerge':'zwerg','Elfen':'elf','Gnome':'gnom','Goliaths':'goliath','Halblinge':'halbling','Menschen':'mensch','Tieflinge':'tiefling'}
        destinations.update({name:'/codex/2024/spezies/'+key for name,key in species_keys.items()})
        destinations['Orks']='/codex/2024/ork'
        toc=''.join(f'<li><a href="{destinations[name]}">{escape(kind)} · {escape(name)}</a></li>' for kind,name in entries)
    elif edition == '2014':
        destinations = {d[0]: '/codex/2014/klasse/' + key for key, d in codex_2014.CLASSES.items()}
        destinations['Zauberer (Sorcerer)'] = destinations['Zauberer']
        species_keys = {'Drachenblütige':'drachenbluetiger','Zwerge':'zwerg','Elfen':'elf','Gnome':'gnom','Halbelfen':'halbelf','Halborks':'halbork','Halblinge':'halbling','Menschen':'mensch','Tieflinge':'tiefling'}
        destinations.update({name:'/codex/2014/spezies/'+key for name,key in species_keys.items()})
        toc = ''.join(f'<li><a href="{destinations[name]}">{escape(kind)} · {escape(name)}</a></li>' for kind,name in entries)
    attribution = ("This work includes material from the System Reference Document 5.2.1 (\"SRD 5.2.1\") by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode." if edition == "2024" else "This work includes material taken from the System Reference Document 5.1 (\"SRD 5.1\") by Wizards of the Coast LLC and available at https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License available at https://creativecommons.org/licenses/by/4.0/legalcode.")
    return (f'<div class="book"><h2>TC · Tormentors Rassen und Klassen</h2><p>{escape(data["title"])}</p>'
            f'<form method="get"><label>Inhaltsverzeichnis durchsuchen<input name="q" value="{escape(term)}" placeholder="Rasse oder Klasse"></label><button>Suchen</button></form>'
            f'<ol>{toc}</ol><h2>Ergänzungsbücher · Quellen-Steckbriefe</h2>{codex_expansions.links(codex_expansions.catalogue(EXTRA_SPECIES), edition, term)}<p><small>Diese Ausgabe verwendet ausschließlich die genannte Regelversion. Entfernungen werden in Metern und feet (ft) angegeben. Ausführliche Einträge und Originalillustrationen werden ergänzt.</small></p>'
            f'<p>Regelquelle: <a href="{data["source"]}">Wizards of the Coast, SRD {"5.2.1" if edition == "2024" else "5.1"}, CC BY 4.0</a>. Eigene deutsche Inhaltsübersicht.</p><p><small>{escape(attribution)}</small></p>'
            '<p><a href="/codex">Buch schließen ↩</a></p></div>')


def orc_page():
    return '''<div class="book"><h2>Ork · Spezies 2024</h2><img class="codex-illustration" src="/media/orc.png" alt="Originalillustration eines Ork-Kartografen mit Reisekarte"><p><small>Originalillustration für Tormentor, erstellt mit ChatGPT/Kodex.</small></p></div>
    <div class="book"><h2>Ork im Spiel</h2><p>Orks sind in dieser Regelfassung Humanoide mittlerer Größe, ungefähr 1,83 bis 2,13 m (6 bis 7 ft) groß. Ihre Bewegungsrate beträgt 9 m (30 ft).</p>
    <p><b>Merkmale:</b> Adrenalinschub erlaubt die Spurt-Aktion als Bonusaktion und gewährt dabei temporäre Trefferpunkte in Höhe des Übungsbonus. Die Anwendung ist auf den Übungsbonus pro kurzer oder langer Rast begrenzt. Dunkelsicht reicht 36 m (120 ft) weit. Unbeugsame Ausdauer lässt dich einmal pro langer Rast bei 0 statt dessen auf 1 Trefferpunkt fallen, sofern du nicht sofort getötet wurdest.</p>
    <p><b>Gesinnung:</b> frei wählbar; die Spezies gibt keine feste Gesinnung vor. <b>Herkunft:</b> Erzählung und Hintergrund bestimmst du für deinen Charakter. <b>Startausrüstung:</b> kommt von Klasse und Hintergrund, nicht von der Spezies. <b>Zauber:</b> keine durch diese Spezies.</p>
    <p><b>Spieltipp:</b> Setze Adrenalinschub ein, wenn du eine gefährliche Position schnell erreichen musst. Bewahre Unbeugsame Ausdauer für einen Kampf auf, in dem ein zusätzlicher Zug entscheidend sein kann.</p>
    <p><small>Eigene Zusammenfassung nach Wizards of the Coast, System Reference Document 5.2.1, „Character Origins: Orc“, S. 86, CC BY 4.0. Keine Wiedergabe von D&D-Beyond-Buchillustrationen.</small></p><p><a href="/codex/2024">← Inhaltsverzeichnis</a></p></div>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def current_user(self, db):
        jar = cookies.SimpleCookie()
        try: jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError: return None
        token = jar.get("tormentor_session")
        if not token: return None
        row = db.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?", (digest(token.value), int(time.time()))).fetchone()
        return row

    def send(self, status, content, cookie=None):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; connect-src 'self'; script-src 'self'; style-src 'unsafe-inline'; media-src 'self'; img-src 'self' https://i.ytimg.com; frame-src https://www.youtube-nocookie.com; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        if cookie: self.send_header("Set-Cookie", portal_security.cookie(cookie))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, path, cookie=None):
        self.send_response(303)
        self.send_header("Location", path)
        if cookie: self.send_header("Set-Cookie", portal_security.cookie(cookie))
        self.end_headers()

    def post_data(self):
        size = int(self.headers.get("Content-Length", 0))
        limit = 2 * 1024 * 1024 if self.path.startswith("/dm/lore/") else (1000000 if self.path.split("?", 1)[0] == "/character" else 64000)
        if not 0 <= size <= limit: raise ValueError("Formular zu groß")
        raw = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True)
        return {key: values[0].strip() for key, values in raw.items()}

    def do_GET(self):
        if self.path.split('?', 1)[0] == '/reset-password':
            return self.send(200, page('Passwort zurücksetzen', portal_reset.FORM))
        handout_match = re.fullmatch(r'/handouts/(\d+)/file', self.path.split('?', 1)[0])
        if handout_match:
            with database() as db:
                user = self.current_user(db)
                if not user: return self.redirect('/login')
                row = db.execute('SELECT h.* FROM handouts h WHERE h.id=? AND h.deleted=0', (int(handout_match.group(1)),)).fetchone()
                visible = row and (user['role'] == 'dm' or (row['published'] and (portal_handouts.audience(db, row['id']) == 'all' or db.execute('SELECT 1 FROM handout_recipients WHERE handout_id=? AND user_id=?', (row['id'], user['id'])).fetchone())))
                file = portal_handouts.attachment(db, int(handout_match.group(1))) if visible else None
                if not file or not (portal_handouts.ROOT / file['filename']).is_file():
                    return self.send(404, page('Nicht gefunden', '<p>Anhang nicht verfügbar.</p>', user))
                data = (portal_handouts.ROOT / file['filename']).read_bytes()
                self.send_response(200); self.send_header('Content-Type', file['mime']); self.send_header('Content-Length', str(len(data))); self.send_header('Content-Disposition', 'inline; filename="' + file['original_name'].replace('"', '') + '"'); self.send_header('Cache-Control', 'private, no-store'); self.end_headers(); self.wfile.write(data); return
        if self.path in ("/media/character.css", "/media/chat-unread.js", "/media/chat.js", "/media/character.js", "/media/feed.js", "/media/login-background.js", "/media/session-countdown.js", "/media/dashboard-music.js", "/media/intro-music.js", "/media/portal-music.js", "/media/reset-password.js"):
            content = (ROOT / "assets" / self.path.rsplit("/", 1)[-1]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8" if self.path.endswith(".css") else "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)
            return
        media = {"/media/intro.mp4": ROOT / "assets" / "Intro.mp4", "/media/intro.mp3": ROOT / "sound" / "Dungeon2.mp3", "/media/orc.png": ROOT / "assets" / "codex" / "orc-cartographer.png", "/media/tc.png": ROOT / "Tormentor_Android" / "app" / "src" / "main" / "res" / "mipmap-xxxhdpi" / "ic_tormentor.png", "/media/dagger.svg": ROOT / "assets" / "portal-dagger.svg"}
        media["/media/login-tavern-loop.mp4"] = ROOT / "assets" / "login-tavern-loop.mp4"
        media["/media/login-tavern.png"] = ROOT / "assets" / "login-tavern.png"
        media["/media/intro.mp3"] = INTRO_MUSIC
        media["/media/header-castle.png"] = ROOT / "assets" / "header-castle.png"
        media["/media/character-dragons.png"] = ROOT / "assets" / "character-dragons.png"
        media["/media/wald2.mp3"] = FOREST_MUSIC
        media['/media/SRD-5.1-DE.pdf'] = ROOT / 'assets/srd/SRD_CC_v5.1_DE.pdf'
        for filename in ("Tormentor-Codex-2024.pdf", "Tormentor-Codex-2014-Quellen.pdf", "Tormentor-Codex-Homebrew.pdf"):
            media["/media/"+filename] = ROOT / "print" / filename
        for key in codex_expansions.codex_profiles.ILLUSTRATIONS:
            media[f"/media/codex/{key}.png"] = ROOT / "assets" / "codex" / f"{key}.png"
        if self.path in media:
            codex_download = self.path.startswith('/media/Tormentor-Codex-') and self.path.endswith('.pdf')
            if codex_download:
                with database() as db:
                    user = self.current_user(db)
                    if not user or user['role'] != 'dm':
                        return self.send(403, page('Kein Zugriff', '<p>Codex-Downloads sind nur für den DM.</p>', user))
            file = media[self.path]
            if not file.is_file(): return self.send(404, "Medien nicht gefunden")
            size = file.stat().st_size
            byte_range = self.headers.get("Range", "")
            start, end = 0, size - 1
            if byte_range.startswith("bytes="):
                try:
                    first, last = byte_range[6:].split("-", 1)
                    start = int(first) if first else 0
                    end = int(last) if last else end
                    if start < 0 or end < start or start >= size: raise ValueError()
                    end = min(end, size - 1)
                except ValueError:
                    self.send_response(416); self.send_header("Content-Range", f"bytes */{size}"); self.end_headers(); return
            self.send_response(206 if byte_range else 200)
            self.send_header("Content-Type", mimetypes.guess_type(file)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            if codex_download: self.send_header('Cache-Control', 'private, no-store')
            if byte_range: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with file.open("rb") as source:
                source.seek(start)
                remaining = end - start + 1
                while remaining:
                    chunk = source.read(min(65536, remaining))
                    if not chunk: break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            return
        with database() as db:
            user = self.current_user(db)
            path = self.path.split("?", 1)[0]
            if path == '/maps':
                if not user: return self.redirect('/login')
                return self.send(200,page('Kartenbibliothek',portal_maps.library(db,user),user))
            if re.fullmatch(r'/maps/[0-9a-f]{32}/image',path):
                if not portal_maps.serve_image(self,db,user,path): return self.send(404,page('Nicht gefunden','<p>Karte nicht verfügbar.</p>',user))
                return
            if path in ('/messages', '/messages/feed', '/messages/unread', '/character'):
                if not user:
                    if path in ('/messages/feed', '/messages/unread'): return self.send(401, '')
                    return self.redirect('/login')
                if user['role'] not in ('dm', 'player'): return self.send(403, page('Kein Zugriff', '<p>Nur für Spielerkonten.</p>', user))
                if path == '/messages/unread': return self.send(200, str(portal_chat.unread(db, user)))
                if path == '/messages/feed': return self.send(200, portal_chat.feed(db, user))
                if path == '/messages': return self.send(200, page('Nachrichten', portal_chat.render(db, user), user))
                return self.send(200, page('Charakterbogen', portal_character.render(db, user, saved=self.path.endswith('?saved=1')), user))
            if path == "/":
                body = '<div class="card"><h2>Willkommen, Abenteurer!</h2><p>Die Chronik deiner Kampagne, dein Heldenprofil und Tormentors Codex erwarten dich.</p></div><div class="grid"><div class="card"><h2>Für Spieler</h2><p>Melde dich mit deinem persönlichen Zugang an.</p><a href="/register">Einladungscode einlösen</a></div><div class="card"><h2>Gästelogin</h2><p>Entdecke den Codex und nützliche Links. Kampagnendaten bleiben verborgen.</p><a href="/login">Gästelogin</a></div></div>'
                body = '<p><audio id="intro-music" src="/media/intro.mp3" controls loop preload="none" aria-label="Tormentor Titelmusik"></audio><br><small>Titelmusik mit Play/Pause steuern.</small></p><script src="/media/portal-music.js" defer></script>' + body
                body += '<p><a href="/dashboard">Zum Spieler-Dashboard →</a></p>' if user else '<p><a href="/login">Zum Login →</a></p>'
            elif path == "/register":
                body = portal_registration.form()
            elif path == "/login":
                if user: return self.redirect("/dashboard")
                body = '<p><audio id="intro-music" src="/media/intro.mp3" controls loop preload="none" aria-label="Tormentor Intro Musik"></audio><br><small>Ton im Browser mit Play einschalten.</small></p><script src="/media/portal-music.js" defer></script><div class="grid"><div class="card"><h2>Spieler-Login</h2><form method="post">' + form_field("username", "Benutzername", autocomplete="username") + form_field("password", "Passwort", kind="password", autocomplete="current-password") + '<button>Anmelden</button></form><p><a href="/forgot-password">Passwort vergessen?</a></p><p><a href="/register">Mit Einladungscode registrieren</a></p></div><div class="card"><h2>Gästelogin</h2><p>Codex, D&D-News und Videos ohne eigenes Konto anschauen.</p><form method="post" action="/guest"><button>Gästelogin</button></form><p><small>Kampagnen und Spielerprofile sind nur nach Spieler-Login zugänglich.</small></p></div></div>'
            elif path == "/gast":
                body = '<div class="card"><h2>Willkommen, Gast!</h2><p>Stöbere durch Tormentors Bücher, entdecke D&D-News und finde neue Kanäle für dein nächstes Abenteuer.</p></div><div class="grid"><div class="card"><h2>Tormentor Codex</h2><a href="/codex">Bücher öffnen →</a></div><div class="card"><h2>D&D-News und Videos</h2><a href="/news">Zum Newsfeed →</a></div><div class="card"><h2>Kanäle und Werkzeuge</h2><a href="/links">Links entdecken →</a></div></div><p><a href="/login">Zum Spieler-Login</a></p>'
                return self.send(200, page("Gastzugang", body, user))
            elif path in ("/dashboard", "/profil"):
                if not user: return self.redirect("/login")
                fields = [("player_name", "Spielername"), ("race", "Rasse/Spezies"), ("class_name", "Klasse"), ("subclass", "Unterklasse"), ("group_name", "Gruppenname"), ("level", "Level"), ("companion", "Begleiter")]
                body = '<div class="card"><h2>Mein Held</h2><form method="post">' + ''.join(form_field(k, label, user[k], "number" if k == "level" else "text") for k, label in fields) + '<button>Profil speichern</button></form><p><a href="/codex">Klassen und ihre Unterklassen im Codex ansehen →</a></p></div>'
                if path == "/dashboard":
                    body = f'<div class="card"><span class="badge">Dein Spielerbereich</span><h2>Willkommen, {escape(user["player_name"] or user["username"])}!</h2><p>{escape(user["race"])} · {escape(user["class_name"])} · Stufe {user["level"]}</p><p><b>Unterklasse:</b> {escape(user["subclass"] or "Noch nicht gewählt")}</p><div class="actions"><a href="/profil">Mein Profil bearbeiten</a><a href="/lore">Kampagnenchronik</a><a href="/handouts">Handouts</a></div></div>'
                body += portal_inspiration.render(db, user)
                if user["role"] == "dm": body += '<p><a href="/dm">Spielerprofile und Inspirationspunkte verwalten →</a></p>'
                suggestions = db.execute("SELECT * FROM level_suggestions WHERE player_id=? AND applied=0 ORDER BY created_at DESC", (user["id"],)).fetchall()
                if suggestions:
                    body += '<div class="card"><h2>Levelaufstieg aus der Chronik</h2><p>Vom DM geprüft. Du entscheidest, ob du den Vorschlag übernimmst.</p>' + ''.join(f'<form method="post" action="/dashboard/level/{s["id"]}"><p>Stufe {s["proposed_level"]} · {escape(s["evidence"])} <button>Stufe übernehmen</button></p></form>' for s in suggestions) + '</div>'
                if path == "/dashboard":
                    query = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
                    body += '<section class="card"><h2>Spielmusik</h2><p><audio id="dashboard-music" src="/media/intro.mp3" controls loop preload="none" aria-label="Spielmusik ein- und ausschalten"></audio></p><p id="music-status" role="status">Ruhige Fantasy-Musik · Rising Moon. Mit Play einschalten; Videos pausieren die Musik.</p><script src="/media/portal-music.js" defer></script></section>'
                    body += session_schedule.render(db, user['role']=='dm')
                    kind = query.get("type", ["all"])[0]
                    body += '<h2>D&D-News und Videos</h2>' + news.render_feed(kind if kind in {"all", "news", "video"} else "all", "/dashboard")
            elif path == "/forgot-password":
                body = portal_reset.HELP_FORM
            elif path == "/dm/password-resets":
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                body = portal_reset.requests_page(db)
            elif re.fullmatch(r'/dm/players/\d+', path):
                if not user or user['role'] != 'dm': return self.send(403, page('Kein Zugriff', '<p>Nur für den DM.</p>', user))
                player = db.execute("SELECT * FROM users WHERE id=? AND role='player'", (int(path.rsplit('/', 1)[-1]),)).fetchone()
                if not player: return self.send(404, page('Nicht gefunden', '<p>Spieler nicht gefunden.</p>', user))
                body = '<p><a href="/dm">← Zur Spielerübersicht</a></p><section class="card"><h2>' + escape(player['player_name'] or player['username']) + '</h2>'
                for key, label in [('username', 'Konto'), ('race', 'Spezies'), ('class_name', 'Klasse'), ('subclass', 'Unterklasse'), ('level', 'Stufe'), ('group_name', 'Gruppe'), ('companion', 'Begleiter')]:
                    body += '<p><b>' + label + ':</b> ' + escape(str(player[key])) + '</p>'
                return self.send(200, page('Spielerprofil', body + '</section>' + portal_inspiration.render(db, player, True), user))
            elif path == "/dm":
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                body = '<div class="card"><h2>Spieler einladen</h2><p>Ein Code ist einmalig und 7 Tage gültig.</p><form method="post"><button>Einladungscode erzeugen</button></form></div><div class="card"><h2>Codex verwalten</h2><a href="/dm/codex">Einträge hinzufügen, bearbeiten oder entfernen →</a></div>'
                body += '<div class="card"><h2>Spieler</h2>' + ''.join(f'<p>{escape(row["username"])} · {escape(row["player_name"])} · Stufe {row["level"]} · <a href="/dm/players/{row["id"]}">Profil und Inspiration →</a></p>' for row in db.execute("SELECT * FROM users WHERE role='player' ORDER BY username")) + '</div>'
                body += session_schedule.editor(db)
                pending_resets = db.execute('SELECT count(*) FROM password_help_requests').fetchone()[0]
                body += f'<section class="card"><h2>Passwort-Hilfe</h2><p>{pending_resets} offene Anfragen</p><a href="/dm/password-resets">Anfragen prüfen und Rücksetzlink erstellen →</a></section>'
                players = db.execute("SELECT id,username,player_name FROM users WHERE role='player' ORDER BY username").fetchall()
                options = ''.join(f'<option value="{row["id"]}">{escape(row["player_name"] or row["username"])}</option>' for row in players)
                proposals = []
                if LORE.exists():
                    for file in LORE.glob("*/session.json"):
                        try:
                            lore_item = json.loads(file.read_text(encoding="utf-8"))
                            if not lore_item.get("published"): continue
                            for suggestion in lore_item.get("approved", {}).get("level_ups", []):
                                if not isinstance(suggestion, dict): continue
                                level = int(suggestion.get("level", 0))
                                if 1 <= level <= 20:
                                    proposals.append(f'<form method="post" action="/dm/level"><input type="hidden" name="session_id" value="{escape(lore_item["id"])}"><input type="hidden" name="level" value="{level}"><input type="hidden" name="evidence" value="{escape(str(suggestion.get("player", ""))[:120])}"><p>{escape(lore_item.get("title", "Sitzung"))}: {escape(suggestion.get("player", ""))} → Stufe {level} <select name="player_id">{options}</select><button>Spieler vorschlagen</button></p></form>')
                        except (OSError, ValueError, TypeError): pass
                if proposals: body += '<div class="card"><h2>Erkannte Levelaufstiege prüfen</h2><p>Wähle das richtige Spielerkonto. Der Spieler bestätigt die Übernahme selbst.</p>' + ''.join(proposals) + '</div>'
                body += '<div class="card"><h2>Spieler-Handouts</h2><a href="/dm/handouts">Handouts anlegen und verwalten →</a></div>'
                body += '<div class="card"><h2>Tormentor Lore</h2><a href="/dm/lore">Aufnahmen und Transkripte prüfen →</a></div>'
            elif path == "/dm/lore" or path.startswith("/dm/lore/"):
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                session_id = None if path == "/dm/lore" else path.removeprefix("/dm/lore/")
                try:
                    body = dm_lore_page(session_id, "draft=1" in self.path.split("?", 1)[-1])
                except (ValueError, OSError):
                    return self.send(404, page("Nicht gefunden", "<p>Sitzung nicht gefunden oder nicht lesbar.</p>", user))
                return self.send(200, page("Tormentor Lore · DM-Prüfung", body, user))
            elif path == "/dm/handouts":
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                body = '<div class="card"><h2>Neues Handout</h2>' + portal_handouts.form(db) + '</div>'
                rows = db.execute("SELECT * FROM handouts WHERE deleted=0 ORDER BY updated_at DESC,id DESC").fetchall()
                body += '<div class="card"><h2>Handouts</h2>' + ''.join(f'<p>{escape(row["title"])} · {"Freigegeben" if row["published"] else "Privat"} · {escape(portal_handouts.recipient_label(db, row["id"]))} · <a href="/dm/handouts/edit/{row["id"]}">Bearbeiten</a></p>' for row in rows) + '</div>'
            elif path.startswith("/dm/handouts/edit/"):
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                try: handout_id = int(path.rsplit("/", 1)[-1])
                except ValueError: return self.send(404, page("Nicht gefunden", "<p>Handout nicht gefunden.</p>", user))
                row = db.execute("SELECT * FROM handouts WHERE id=? AND deleted=0", (handout_id,)).fetchone()
                if not row: return self.send(404, page("Nicht gefunden", "<p>Handout nicht gefunden.</p>", user))
                body = '<div class="card"><h2>Handout bearbeiten</h2>' + portal_handouts.form(db, row) + '</div><div class="card"><form method="post" action="/dm/handouts/delete/' + str(handout_id) + '"><button>Handout entfernen</button></form></div>'
            elif path == "/dm/codex":
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                body = '<div class="card"><h2>Neuen Eintrag anlegen</h2><p>Neue Einträge bleiben privat, bis du sie freigibst.</p>' + entry_form() + '</div>'
                rows = db.execute("SELECT * FROM codex_entries WHERE deleted=0 ORDER BY updated_at DESC,id DESC").fetchall()
                body += '<div class="card"><h2>Eigene Einträge</h2>' + ''.join(f'<p>{escape(row["edition"])} · {escape(row["kind"])} · {escape(row["title"])} · {"Freigegeben" if row["published"] else "Privat"} · <a href="/dm/codex/edit/{row["id"]}">Bearbeiten</a></p>' for row in rows) + '</div>'
            elif path.startswith("/dm/codex/edit/"):
                if not user or user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                try: entry_id = int(path.rsplit("/", 1)[-1])
                except ValueError: return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                row = db.execute("SELECT * FROM codex_entries WHERE id=? AND deleted=0", (entry_id,)).fetchone()
                if not row: return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                body = '<div class="card"><h2>Eintrag bearbeiten</h2>' + entry_form(row) + '</div><div class="card"><form method="post" action="/dm/codex/delete/' + str(entry_id) + '"><button>Eintrag entfernen</button></form><small>Der Eintrag wird ausgeblendet und bleibt in der Datenbank wiederherstellbar.</small></div>'
            elif path == "/lore":
                if not user: return self.redirect("/login")
                body = lore_page(path)
            elif path in ("/lore/sitzungen", "/lore/npcs", "/lore/orte", "/lore/quests"):
                if not user: return self.redirect("/login")
                body = lore_page(path)
            elif path == "/handouts":
                if not user: return self.redirect("/login")
                rows = portal_handouts.visible(db, user)
                def handout_card(row):
                    file = portal_handouts.attachment(db, row['id'])
                    link = f'<p><a href="/handouts/{row["id"]}/file">Anhang öffnen: {escape(file["original_name"])}</a></p>' if file else ''
                    return f'<article class="card"><h2>{escape(row["title"])}</h2><p style="white-space:pre-wrap">{escape(row["body"])}</p>{link}{"<small>Nur DM</small>" if not row["published"] else ""}</article>'
                body = ''.join(handout_card(row) for row in rows) or '<p>Noch keine freigegebenen Handouts.</p>'
            elif path == "/codex":
                body = '<div class="grid"><div class="book cover"><img src="/media/tc.png" alt="Tormentor TC Logo"><h2>Tormentors Rassen und Klassen</h2><p>Ausgabe 2024 · SRD 5.2.1</p><a href="/codex/2024">Buch öffnen →</a></div><div class="book cover"><img src="/media/tc.png" alt="Tormentor TC Logo"><h2>Tormentors Rassen und Klassen</h2><p>Ausgabe 2014 · SRD 5.1</p><a href="/codex/2014">Buch öffnen →</a></div></div><p><a href="/codex/zauber">Zauberlexikon →</a> · <a href="/codex/weitere">Weitere offizielle Spezies →</a> · <a href="/codex/klassen">Weitere offizielle Klassen →</a> · <a href="/codex/herkuenfte">Herkünfte →</a> · <a href="/codex/homebrew">Separates Homebrew-Buch →</a></p>'
                if user and user["role"] == "dm":
                    body += '<section class="card"><h2>Codex als PDF</h2><p>Druckfassung des aktuellen Stands · A4 · getrennte Bände</p><p><a href="/media/Tormentor-Codex-2024.pdf">2024 herunterladen</a> · <a href="/media/Tormentor-Codex-2014-Quellen.pdf">2014-Quellen herunterladen</a> · <a href="/media/Tormentor-Codex-Homebrew.pdf">Homebrew herunterladen</a></p></section>'
            elif path == "/codex/weitere":
                query = parse_qs(self.path.partition('?')[2]).get('q', [''])[0][:80]
                body = codex_expansions.index(codex_expansions.catalogue(EXTRA_SPECIES), query)
            elif path == "/codex/herkuenfte":
                body = backgrounds_page(db, user)
            elif path == "/codex/zauber":
                query = parse_qs(self.path.partition('?')[2])
                body = codex_spells.index(query.get('q', [''])[0][:80], query.get('level', [''])[0], query.get('school', [''])[0], query.get('class', [''])[0])
            elif path == "/codex/unterklassen":
                query = parse_qs(self.path.partition('?')[2]).get('q', [''])[0][:80]
                body = codex_expansions.subclass_index(codex_expansions.catalogue(EXTRA_SPECIES), query)
            elif path == "/codex/klassen":
                body = expansion_classes() + '<div class="book"><h2>Unterklassen nachschlagen</h2><p>Die Unterklassen stehen direkt auf der jeweiligen Klassenseite. Öffne zum Beispiel die Barbarenseite, um alle Barbar-Unterklassen zu sehen.</p><p><a href="/codex/2024/klasse/barbar">Barbar öffnen →</a> · <a href="/codex/2014/klasse/barbar">Barbar 2014 öffnen →</a></p></div>'
            elif path.startswith('/codex/quelle/'):
                entries = codex_expansions.catalogue(EXTRA_SPECIES)
                entry = next((e for e in entries if e['key'] == path.rsplit('/', 1)[-1]), None)
                if entry is None: return self.send(404, page('Nicht gefunden', '<p>Eintrag nicht gefunden.</p>', user))
                body = codex_expansions.detail(entry, entries)
            elif path == "/codex/homebrew":
                body = homebrew_book() + entry_links(db, "Homebrew", user)
            elif path in ("/codex/2024", "/codex/2014"):
                edition = path.rsplit("/", 1)[-1]
                query = parse_qs(self.path.split("?", 1)[1]).get("q", [""])[0][:80] if "?" in self.path else ""
                body = '<p><a href="/codex/herkuenfte">Herkünfte &amp; Hintergründe →</a></p>' + codex_book(edition, query) + entry_links(db, edition, user)
            elif path == "/codex/2024/ork":
                body = orc_page()
            elif path.startswith('/codex/2014/klasse/'):
                key = path.rsplit('/', 1)[-1]
                if key not in codex_2014.CLASSES: return self.send(404,page('Nicht gefunden','<p>Klasse nicht gefunden.</p>',user))
                body = codex_2014.class_page(key, codex_expansions.class_subclasses(codex_expansions.catalogue(EXTRA_SPECIES), codex_2014.CLASSES[key][0], '2014'))
            elif path.startswith('/codex/2014/spezies/'):
                key = path.rsplit('/', 1)[-1]
                if key not in codex_2014.SPECIES: return self.send(404,page('Nicht gefunden','<p>Volk nicht gefunden.</p>',user))
                body = codex_2014.species_page(key)
            elif path.startswith('/codex/2024/klasse/'):
                key=path.rsplit('/',1)[-1]
                if key not in codex_core.CLASSES: return self.send(404,page('Nicht gefunden','<p>Klasse nicht gefunden.</p>',user))
                body=codex_core.class_page(key, codex_expansions.class_subclasses(codex_expansions.catalogue(EXTRA_SPECIES), codex_core.CLASSES[key]['name'], '2024'))
            elif path.startswith('/codex/2024/spezies/'):
                key=path.rsplit('/',1)[-1]
                if key not in codex_core.SPECIES: return self.send(404,page('Nicht gefunden','<p>Spezies nicht gefunden.</p>',user))
                body=codex_core.species_page(key)
            elif path.startswith("/codex/eintrag/"):
                try: entry_id = int(path.rsplit("/", 1)[-1])
                except ValueError: return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                row = db.execute("SELECT * FROM codex_entries WHERE id=? AND deleted=0", (entry_id,)).fetchone()
                if not row or not row["published"] and (not user or user["role"] != "dm"):
                    return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                body = f'<div class="book"><h2>{escape(row["title"])}</h2><p>{escape(row["kind"])} · {escape(row["edition"])}</p><p style="white-space:pre-wrap">{escape(row["body"])}</p><p><small>Quelle: {escape(row["source"] or "Eigene Schöpfung")}</small></p><a href="/codex">Buch schließen ↩</a></div>'
            elif path == "/links":
                body = news.render_links()
            elif path == "/news":
                query = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
                kind = query.get("type", ["all"])[0]
                body = '<p>Neue Geschichten, Regeln und Inspiration für dein nächstes Abenteuer.</p>' + news.render_feed(kind if kind in {"all", "news", "video"} else "all")
                return self.send(200, page("D&D-News und Videos", body, user))
            else: return self.send(404, page("Nicht gefunden", "<p>Diese Seite gibt es nicht.</p>", user))
            titles = {"/": "Willkommen", "/register": "Registrieren", "/login": "Login", "/dashboard": "Spieler-Dashboard", "/dm": "DM-Zentrale", "/dm/codex": "Codex verwalten", "/dm/handouts": "Handouts verwalten", "/lore": "Chronik", "/lore/sitzungen": "Sitzungen", "/lore/npcs": "Bekannte NPCs", "/lore/orte": "Bekannte Orte", "/lore/quests": "Quests", "/handouts": "Handouts", "/codex": "Tormentor Codex", "/codex/2024": "Codex 2024", "/codex/2014": "Codex 2014", "/codex/2024/ork": "Ork · Codex 2024", "/codex/weitere": "Weitere Spezies", "/codex/klassen": "Weitere Klassen", "/codex/homebrew": "Tormentor Homebrew", "/links": "Entdecken"}
            titles["/profil"] = "Mein Profil"
            titles["/forgot-password"] = "Passwort vergessen"
            titles["/dm/password-resets"] = "Passwort-Anfragen"
            titles["/codex/herkuenfte"] = "Herkünfte · Codex"
            titles["/codex/zauber"] = "Zauberlexikon · Codex"
            titles["/codex/unterklassen"] = "Unterklassen · Codex"
            self.send(200, page(titles.get(path, "Codex-Eintrag"), body, user))

    def do_POST(self):
        if not portal_security.allowed_post(self.headers):
            return self.send(403,page('Anfrage abgelehnt','<p>Bitte das Formular auf dieser Website öffnen und erneut absenden.</p>'))
        if self.path.split('?',1)[0] in ('/login','/register','/reset-password','/forgot-password') and not portal_security.allow_auth(self.client_address[0],self.headers):
            return self.send(429,page('Bitte kurz warten','<p>Zu viele Anmeldeversuche. Bitte in fünf Minuten erneut versuchen.</p>'))
        with database() as db:
            user = self.current_user(db)
            path = self.path.split("?", 1)[0]
            now = int(time.time())
            if path == '/dm/maps/upload':
                if not user or user['role']!='dm': return self.send(403,page('Kein Zugriff','<p>Nur für den DM.</p>',user))
                try: portal_maps.receive(self,db)
                except (ValueError,UnicodeError) as exc: return self.send(400,page('Upload prüfen','<p>'+escape(str(exc))+'</p><a href="/maps">Zurück zu den Karten</a>',user))
                db.commit()
                return self.redirect('/maps')
            if (path == '/dm/handouts' or re.fullmatch(r'/dm/handouts/edit/\d+', path)) and self.headers.get('Content-Type','').startswith('multipart/form-data') and user and user['role'] == 'dm':
                try: data, attachment = portal_handouts.receive(self)
                except (ValueError, UnicodeError) as exc:
                    return self.send(400, page('Upload prüfen', '<p>' + escape(str(exc)) + '</p>', user))
                handout_id = None
                if path != '/dm/handouts':
                    match = re.fullmatch(r'/dm/handouts/edit/(\d+)', path)
                    if not match: return self.send(404, page('Nicht gefunden', '<p>Handout nicht gefunden.</p>', user))
                    handout_id = int(match.group(1))
                try: portal_handouts.save(db, data, user['id'], now, handout_id, attachment)
                except (ValueError, KeyError) as error:
                    db.rollback(); return self.send(400, page('Handout prüfen', '<p>' + escape(str(error)) + '</p>', user))
                db.commit(); return self.redirect('/dm/handouts')
            try: data = self.post_data()
            except (ValueError, UnicodeError): return self.send(400, page("Fehler", "<p>Formular ungültig.</p>", user))
            now = int(time.time())
            if path == '/messages/read':
                if not user or user['role'] not in ('dm', 'player'): return self.send(403, '')
                try: portal_chat.mark_read(db, user, data)
                except ValueError: return self.send(400, '')
                db.commit()
                return self.send(200, '')
            if path == '/messages':
                if not user or user['role'] not in ('dm', 'player'): return self.send(403, page('Kein Zugriff', '<p>Bitte mit einem Spielerkonto anmelden.</p>', user))
                try: portal_chat.send(db, user, data, now)
                except ValueError as exc: return self.send(400, page('Nachrichten', portal_chat.render(db, user, data, str(exc)), user))
                db.commit()
                return self.redirect('/messages')
            if path == '/character':
                if not user or user['role'] not in ('player', 'dm'): return self.send(403, page('Kein Zugriff', '<p>Bitte anmelden.</p>', user))
                try: portal_character.save(db, user, data)
                except ValueError as exc: return self.send(400, page('Charakterbogen', portal_character.render(db, user, data, str(exc)), user))
                db.commit()
                return self.redirect('/character?saved=1')
            if path == '/forgot-password':
                username = data.get('username', '').strip().lower()
                if not (3 <= len(username) <= 32 and username.replace('_', '').isalnum()):
                    return self.send(400, page('Passwort vergessen', '<p>Bitte einen gültigen Benutzernamen eingeben.</p>' + portal_reset.HELP_FORM))
                portal_reset.request_help(db, username)
                db.commit()
                return self.send(200, page('Passwort-Hilfe angefordert', portal_reset.HELP_SENT))
            if path.startswith('/dm/password-resets/'):
                if not user or user['role'] != 'dm': return self.send(403, page('Kein Zugriff', '<p>Nur für den DM.</p>', user))
                match = re.fullmatch(r'/dm/password-resets/(\d+)(/dismiss)?', path)
                if not match: return self.send(404, page('Nicht gefunden', '<p>Anfrage nicht gefunden.</p>', user))
                account_id = int(match.group(1))
                if match.group(2):
                    db.execute('DELETE FROM password_help_requests WHERE user_id=?', (account_id,))
                    db.commit()
                    return self.redirect('/dm/password-resets')
                account = db.execute('SELECT u.username FROM users u JOIN password_help_requests r ON r.user_id=u.id WHERE u.id=?', (account_id,)).fetchone()
                if not account: return self.send(404, page('Nicht gefunden', '<p>Keine offene Anfrage für dieses Konto.</p>', user))
                if data.get('verified') != 'yes':
                    return self.send(400, page('Identität prüfen', '<p>Bitte zuerst die Identität persönlich prüfen und bestätigen.</p><a href="/dm/password-resets">Zurück</a>', user))
                token = portal_reset.issue(db, account['username'])
                db.execute('DELETE FROM password_help_requests WHERE user_id=?', (account_id,))
                db.commit()
                origin = portal_security.PUBLIC_ORIGIN or 'http://127.0.0.1:8787'
                link = origin + '/reset-password#' + token
                body = (f'<p>Rücksetzlink für <b>{escape(account["username"])}</b> · einmalig gültig für 30 Minuten.</p>'
                        '<p>Kopiere diesen Link und gib ihn direkt an den geprüften Spieler weiter. Er wird hier nur einmal angezeigt.</p>'
                        f'<label>Rücksetzlink<input type="text" readonly value="{escape(link)}"></label>'
                        '<p><a href="/dm/password-resets">Zurück zu den Anfragen</a></p>')
                return self.send(200, page('Rücksetzlink erstellt', body, user))
            if path == '/reset-password':
                try:
                    portal_reset.redeem(db, data.get('token', ''), data.get('password', ''), data.get('confirmation', ''))
                except ValueError as error:
                    return self.send(400, page('Passwort zurücksetzen', '<p>' + escape(str(error)) + '</p><p>Bitte den Rücksetzlink erneut öffnen.</p>'))
                return self.send(200, page('Passwort geändert', '<p>Dein Passwort wurde geändert. Alle bisherigen Anmeldungen sind abgemeldet.</p><a href="/login">Jetzt anmelden</a>'), 'tormentor_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
            if path == "/guest":
                jar = cookies.SimpleCookie()
                try: jar.load(self.headers.get("Cookie", ""))
                except cookies.CookieError: pass
                if jar.get("tormentor_session"):
                    db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(jar["tormentor_session"].value),))
                    db.commit()
                return self.redirect("/gast", "tormentor_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")
            if path == "/register":
                code = portal_registration.normalize_code(data.get("code", ""))
                username = data.get("username", "").lower()
                password = data.get("password", "")
                try:
                    portal_registration.validate(code, username, password)
                    db.execute("BEGIN IMMEDIATE")
                    invite = db.execute("SELECT * FROM invites WHERE code_hash=?", (digest(code),)).fetchone()
                    if not invite: raise ValueError("Einladungscode nicht gefunden. Bitte mit dem Code deines DMs vergleichen.")
                    if invite['uses_left'] <= 0: raise ValueError("Dieser Einladungscode wurde bereits eingelöst. Wenn du dein Konto schon erstellt hast, melde dich über den Login an.")
                    if invite['expires_at'] <= now: raise ValueError("Dieser Einladungscode ist abgelaufen. Bitte deinen DM um einen neuen Code bitten.")
                    db.execute("INSERT INTO users(username,password,role) VALUES(?,?,'player')", (username, password_hash(password)))
                    db.execute("UPDATE invites SET uses_left=uses_left-1 WHERE code_hash=?", (digest(code),))
                    db.commit()
                except sqlite3.IntegrityError:
                    db.rollback(); return self.send(409, page("Registrierung", portal_registration.form(data, 'Benutzername bereits vergeben. Wähle einen anderen Namen oder melde dich an. Dieser Code bleibt unbenutzt.')))
                except ValueError as error:
                    db.rollback(); return self.send(400, page("Registrierung", portal_registration.form(data, str(error))))
                return self.redirect("/login")
            if path == "/login":
                account = db.execute("SELECT * FROM users WHERE username=?", (data.get("username", "").lower(),)).fetchone()
                if not account or not password_ok(data.get("password", ""), account["password"]):
                    time.sleep(.4); return self.send(401, page("Login", '<p class="error">Anmeldung fehlgeschlagen.</p>'))
                token = secrets.token_urlsafe(32)
                db.execute("INSERT INTO sessions VALUES(?,?,?)", (digest(token), account["id"], now + SESSION_AGE))
                db.commit()
                return self.redirect("/dashboard", f"tormentor_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_AGE}")
            if path == "/logout":
                jar = cookies.SimpleCookie(); jar.load(self.headers.get("Cookie", ""))
                if jar.get("tormentor_session"): db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(jar["tormentor_session"].value),)); db.commit()
                return self.redirect("/", "tormentor_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")
            if not user: return self.send(403, page("Kein Zugriff", "<p>Bitte anmelden.</p>"))
            if re.fullmatch(r'/dm/players/\d+/inspiration', path):
                if user['role'] != 'dm': return self.send(403, page('Kein Zugriff', '<p>Nur für den DM.</p>', user))
                player_id = int(path.split('/')[3])
                player = db.execute("SELECT * FROM users WHERE id=? AND role='player'", (player_id,)).fetchone()
                if not player: return self.send(404, page('Nicht gefunden', '<p>Spieler nicht gefunden.</p>', user))
                try:
                    portal_inspiration.change(db, player_id, data)
                except ValueError as error:
                    return self.send(409, page('Punktestand prüfen', '<p role="alert">' + escape(str(error)) + '</p>' + portal_inspiration.render(db, player, True), user))
                db.commit()
                return self.redirect(f'/dm/players/{player_id}')
            if path.startswith('/dm/maps/'):
                if user['role']!='dm': return self.send(403,page('Kein Zugriff','<p>Nur für den DM.</p>',user))
                match=re.fullmatch(r'/dm/maps/([0-9a-f]{32})/(visibility|remove)',path)
                if not match: return self.send(404,page('Nicht gefunden','<p>Karte nicht verfügbar.</p>',user))
                key,action=match.groups()
                if action=='remove': db.execute('UPDATE maps SET deleted=1,published=0 WHERE id=?',(key,))
                else: db.execute('UPDATE maps SET published=1-published WHERE id=? AND deleted=0',(key,))
                db.commit()
                return self.redirect('/maps')
            if path in ('/dm/session', '/dm/session/clear'):
                if user['role'] != 'dm': return self.send(403, page('Kein Zugriff','<p>Nur für den DM.</p>',user))
                try:
                    if path.endswith('/clear'): db.execute('DELETE FROM next_session WHERE id=1')
                    else: session_schedule.save(db,data)
                except ValueError: return self.send(400,page('Termin prüfen','<p>Bitte gültiges Datum, Uhrzeit und Zeitzone eingeben.</p>'+session_schedule.editor(db),user))
                db.commit()
                return self.redirect('/dashboard')
            if path == "/dm/lore" or path.startswith("/dm/lore/"):
                if user["role"] != "dm": return self.send(403, page("Kein Zugriff", "<p>Nur für den DM.</p>", user))
                try:
                    if path == "/dm/lore":
                        if not data.get("title"): raise ValueError("Bitte einen Sitzungstitel eingeben.")
                        item = lore.new_session(data["title"])
                        return self.redirect(f'/dm/lore/{item["id"]}')
                    match = re.fullmatch(r"/dm/lore/([0-9a-f]{32})/(review|transcript|process|analyze|unpublish)", path)
                    if not match: return self.send(404, page("Nicht gefunden", "<p>Unbekannte Lore-Funktion.</p>", user))
                    session_id, action = match.groups()
                    if action in ("process", "analyze"):
                        lore_workflow.start_processing(session_id, action == "process")
                    else:
                        with lore_workflow.session_lock(session_id):
                            item = lore.load(session_id)
                            if data.get("revision") != lore_revision(item):
                                return self.send(409, page("Sitzung wurde geändert", f'<p>Bitte den aktuellen Stand laden, bevor du speicherst. Deine Änderung wurde noch nicht übernommen.</p><a href="/dm/lore/{session_id}">Aktuellen Stand öffnen</a>', user))
                            if action == "transcript":
                                item["transcript"] = data.get("transcript", "")
                                lore.save(item)
                            elif action == "unpublish":
                                lore.approve(item, item.get("approved", {}), False, LORE)
                            else:
                                if not data.get("title"): raise ValueError("Bitte einen Sitzungstitel eingeben.")
                                edited = lore.review_from_fields(data)
                                item["title"] = data["title"][:200]
                                lore.approve(item, edited, data.get("published") == "1", LORE)
                    return self.redirect(f"/dm/lore/{session_id}")
                except lore_workflow.SessionBusy as error:
                    return self.send(409, page("Sitzung wird bearbeitet", f'<p>{escape(error)}</p><a href="/dm/lore">Zurück zu Lore</a>', user))
                except ValueError as error:
                    return self.send(400, page("Prüfung nicht gespeichert", f'<p>{escape(error)}</p><p>Mit der Zurück-Taste kannst du deine Eingaben korrigieren.</p>', user))
                except OSError:
                    return self.send(400, page("Lore", '<p>Sitzung nicht lesbar oder nicht speicherbar.</p>', user))
            if path.startswith("/dashboard/level/"):
                try: suggestion_id = int(path.rsplit("/", 1)[-1])
                except ValueError: return self.send(404, page("Nicht gefunden", "<p>Vorschlag nicht gefunden.</p>", user))
                suggestion = db.execute("SELECT * FROM level_suggestions WHERE id=? AND player_id=? AND applied=0", (suggestion_id, user["id"])).fetchone()
                if not suggestion: return self.send(404, page("Nicht gefunden", "<p>Vorschlag nicht gefunden.</p>", user))
                if suggestion["proposed_level"] > user["level"]:
                    db.execute("UPDATE users SET level=? WHERE id=?", (suggestion["proposed_level"], user["id"]))
                db.execute("UPDATE level_suggestions SET applied=1 WHERE id=?", (suggestion_id,))
                db.commit()
                return self.redirect("/dashboard")
            if path in ("/dashboard", "/profil"):
                fields = ["player_name", "race", "class_name", "subclass", "group_name", "companion"]
                values = [data.get(key, "")[:120] for key in fields]
                try: level = int(data.get("level", "1"))
                except ValueError: level = 1
                if not 1 <= level <= 20: return self.send(400, page("Fehler", "<p>Level muss zwischen 1 und 20 liegen.</p>", user))
                db.execute("UPDATE users SET player_name=?,race=?,class_name=?,subclass=?,group_name=?,companion=?,level=? WHERE id=?", (*values, level, user["id"]))
                db.commit(); return self.redirect("/dashboard")
            if path == "/dm" and user["role"] == "dm":
                code = secrets.token_hex(8).upper()
                db.execute("INSERT INTO invites VALUES(?,?,?,?)", (digest(code), now + 7 * 86400, 1, user["id"]))
                db.commit()
                return self.send(200, page("Einladungscode", f'<div class="card"><p>Diesen Code einmalig an einen Spieler weitergeben:</p><h2>{code}</h2><p>7 Tage gültig, einmal verwendbar.</p><a href="/dm">Zurück</a></div>', user))
            if path == "/dm/level" and user["role"] == "dm":
                try: player_id = int(data.get("player_id", "0")); level = int(data.get("level", "0"))
                except ValueError: return self.send(400, page("Fehler", "<p>Ungültige Stufe.</p>", user))
                session_id = data.get("session_id", "")
                if not re.fullmatch(r"[0-9a-f]{32}", session_id) or not 1 <= level <= 20 or not db.execute("SELECT id FROM users WHERE id=? AND role='player'", (player_id,)).fetchone():
                    return self.send(400, page("Fehler", "<p>Spieler oder Stufe ungültig.</p>", user))
                file = LORE / session_id / "session.json"
                try:
                    lore_item = json.loads(file.read_text(encoding="utf-8"))
                    valid = lore_item.get("published") and any(isinstance(item, dict) and item.get("level") == level for item in lore_item.get("approved", {}).get("level_ups", []))
                except (OSError, ValueError, TypeError): valid = False
                if not valid: return self.send(400, page("Fehler", "<p>Kein freigegebener Levelvorschlag aus dieser Sitzung.</p>", user))
                db.execute("INSERT INTO level_suggestions(player_id,proposed_level,session_id,evidence,created_by,created_at) VALUES(?,?,?,?,?,?)", (player_id, level, session_id, data.get("evidence", "")[:120], user["id"], now))
                db.commit()
                return self.redirect("/dm")
            if path.startswith("/dm/handouts") and user["role"] == "dm":
                if path.startswith("/dm/handouts/delete/"):
                    try: handout_id = int(path.rsplit("/", 1)[-1])
                    except ValueError: return self.send(404, page("Nicht gefunden", "<p>Handout nicht gefunden.</p>", user))
                    db.execute("UPDATE handouts SET deleted=1,published=0,updated_at=? WHERE id=?", (now, handout_id))
                    db.commit(); return self.redirect("/dm/handouts")
                handout_id = None
                if path != "/dm/handouts":
                    match = re.fullmatch(r'/dm/handouts/edit/(\d+)', path)
                    if not match: return self.send(404, page("Nicht gefunden", "<p>Aktion nicht gefunden.</p>", user))
                    handout_id = int(match.group(1))
                try:
                    portal_handouts.save(db, data, user["id"], now, handout_id)
                except ValueError as error:
                    db.rollback()
                    return self.send(400, page("Handout prüfen", '<p>' + escape(str(error)) + '</p><p>Gehe im Browser zurück, um deine Eingaben zu korrigieren.</p>', user))
                db.commit(); return self.redirect("/dm/handouts")
            if path.startswith("/dm/codex") and user["role"] == "dm":
                if path.startswith("/dm/codex/delete/"):
                    try: entry_id = int(path.rsplit("/", 1)[-1])
                    except ValueError: return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                    db.execute("UPDATE codex_entries SET deleted=1,published=0,updated_at=? WHERE id=?", (now, entry_id))
                    db.commit()
                    return self.redirect("/dm/codex")
                title = data.get("title", "")[:120]
                kind = data.get("kind", "")
                edition = data.get("edition", "")
                source = data.get("source", "")[:500]
                body = data.get("body", "")[:12000]
                published = int(data.get("published") == "1")
                if not title or kind not in ENTRY_KINDS or edition not in ENTRY_EDITIONS or not body or edition != "Homebrew" and not source:
                    return self.send(400, page("Codex", '<p class="error">Name, Kategorie, Regelversion, Text und bei offiziellen Einträgen eine Quelle sind nötig.</p>', user))
                if path == "/dm/codex":
                    db.execute("INSERT INTO codex_entries(title,kind,edition,source,body,published,created_by,updated_at) VALUES(?,?,?,?,?,?,?,?)", (title, kind, edition, source, body, published, user["id"], now))
                elif path.startswith("/dm/codex/edit/"):
                    try: entry_id = int(path.rsplit("/", 1)[-1])
                    except ValueError: return self.send(404, page("Nicht gefunden", "<p>Eintrag nicht gefunden.</p>", user))
                    db.execute("UPDATE codex_entries SET title=?,kind=?,edition=?,source=?,body=?,published=?,updated_at=? WHERE id=? AND deleted=0", (title, kind, edition, source, body, published, now, entry_id))
                else: return self.send(404, page("Nicht gefunden", "<p>Aktion nicht gefunden.</p>", user))
                db.commit()
                return self.redirect("/dm/codex")
            self.send(403, page("Kein Zugriff", "<p>Aktion nicht erlaubt.</p>", user))


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "init-dm":
        import getpass
        username = input("DM-Benutzername: ").strip().lower()
        password = getpass.getpass("DM-Passwort (mindestens 12 Zeichen): ")
        if len(username) < 3 or len(password) < 12: raise SystemExit("Name oder Passwort zu kurz")
        with database() as db:
            if db.execute("SELECT id FROM users WHERE role='dm'").fetchone(): raise SystemExit("DM-Konto existiert bereits")
            db.execute("INSERT INTO users(username,password,role) VALUES(?,?,'dm')", (username, password_hash(password)))
            db.commit()
        print("DM-Konto angelegt")
    else:
        print("Tormentor Portal: http://127.0.0.1:8787")
        ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()


if __name__ == "__main__": main()
