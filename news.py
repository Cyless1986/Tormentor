"""Public D&D news and video feed. Only titles, dates and source links are cached."""
from __future__ import annotations

import html
import json
import os
import re
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "news-cache.json"
SEED = ROOT / "assets/news-seed.json"
REFRESH_SECONDS = 3600
LOCK = threading.Lock()
last_attempt = 0
CHANNELS = [
    {"name": "Dice Actors", "url": "https://www.youtube.com/c/diceactors", "language": "Deutsch", "about": "D&D-Abenteuer mit deutschen Synchronsprechern."},
    {"name": "Orkenspalter TV", "url": "https://www.youtube.com/@orkenspaltertv", "language": "Deutsch", "about": "Pen-&-Paper-Runden, Interviews und Rollenspielthemen."},
    {"name": "Dungeons & Dragons", "url": "https://www.youtube.com/@DNDWizards", "language": "Englisch", "about": "Der offizielle D&D-Kanal: Neuigkeiten, Einblicke und Spielrunden."},
    {"name": "Dungeon Dudes", "url": "https://www.youtube.com/dungeondudes", "language": "Englisch", "about": "Klassentipps, Regeln und die Abenteuer von Drakkenheim."},
    {"name": "Critical Role", "url": "https://www.youtube.com/criticalrole", "language": "Englisch", "about": "Lange Abenteuer, Charaktergeschichten und Spielrunden."},
]
SOURCES = [
    ("D&D Beyond", "news", "https://www.dndbeyond.com/posts.rss"),
    ("Dungeons & Dragons", "video", "https://www.youtube.com/feeds/videos.xml?channel_id=UCi-PULMg2eD_v5AO0PlW4sg"),
    ("Dungeon Dudes", "video", "https://www.youtube.com/feeds/videos.xml?channel_id=UCQDKouT6G_6P1eBIfkTkC-w"),
]


def public_link(value, kind):
    parsed = urlsplit(value)
    hosts = {"www.dndbeyond.com", "dndbeyond.com"} if kind == "news" else {"www.youtube.com", "youtube.com"}
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("Unbekannte Nachrichtenquelle.")
    return urlunsplit(("https", parsed.hostname, parsed.path, parsed.query, ""))


def parse_feed(raw, source, kind):
    if len(raw) > 2 * 1024 * 1024 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Feed nicht lesbar.")
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    elements = root.findall("./channel/item") if kind == "news" else root.findall("a:entry", ns)
    result = []
    for item in elements[:30]:
        try:
            title = item.findtext("title") if kind == "news" else item.findtext("a:title", namespaces=ns)
            title = html.unescape(title or "").strip()[:240]
            if not title: continue
            if kind == "news":
                link = public_link(item.findtext("link", ""), kind)
                if not re.match(r"/posts/\d+-", urlsplit(link).path): continue
                stamp = parsedate_to_datetime(item.findtext("pubDate", ""))
                video_id = ""
            else:
                video_id = item.findtext("yt:videoId", "", ns)
                if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id): continue
                link = "https://www.youtube.com/watch?v=" + video_id
                stamp = datetime.fromisoformat(item.findtext("a:published", "", ns).replace("Z", "+00:00"))
            if stamp.tzinfo is None: stamp = stamp.replace(tzinfo=timezone.utc)
            result.append({"title": title, "url": link, "source": source, "kind": kind,
                           "published": stamp.astimezone(timezone.utc).isoformat(), "video_id": video_id})
        except (ValueError, TypeError, AttributeError):
            continue
    if not result:
        raise ValueError("Feed enthält keine gültigen Einträge.")
    return result


def read_snapshot(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) and isinstance(value.get("entries"), list) else {}
    except (OSError, ValueError):
        return {}


def snapshot():
    return read_snapshot(CACHE) or read_snapshot(SEED) or {"entries": [], "updated_at": 0, "errors": []}


def refresh():
    global last_attempt
    if not LOCK.acquire(blocking=False): return
    try:
        last_attempt = time.time()
        previous = snapshot()
        entries, errors = [], []
        for source, kind, url in SOURCES:
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Tormentor/2.0 public-feed-reader"})
                with urllib.request.urlopen(request, timeout=12) as response:
                    raw = response.read(2 * 1024 * 1024 + 1)
                entries.extend(parse_feed(raw, source, kind))
            except Exception:
                errors.append(source)
                entries.extend(item for item in previous.get("entries", []) if item.get("source") == source)
        # Keep the last successful snapshot if all sources are temporarily unavailable.
        result = {"entries": entries, "updated_at": time.time() if len(errors) < len(SOURCES) else previous.get("updated_at", 0), "errors": errors}
        temporary = CACHE.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(CACHE)
    finally:
        LOCK.release()


def maybe_refresh():
    if os.environ.get("TORMENTOR_NEWS_OFFLINE") == "1": return
    if time.time() - max(last_attempt, snapshot().get("updated_at", 0)) >= REFRESH_SECONDS:
        threading.Thread(target=refresh, name="Tormentor-News", daemon=True).start()


def mixed_entries(entries, kind="all"):
    newest = sorted(entries, key=lambda item: item.get("published", ""), reverse=True)
    if kind in {"news", "video"}:
        return [item for item in newest if item["kind"] == kind]
    articles = [item for item in newest if item["kind"] == "news"]
    videos = [item for item in newest if item["kind"] == "video"]
    mixed = []
    while articles or videos:
        mixed.extend(articles[:2]); articles = articles[2:]
        if videos: mixed.append(videos.pop(0))
    return mixed


def render_feed(kind="all", path="/news"):
    maybe_refresh()
    data = snapshot()
    escape = html.escape
    filters = '<nav class="feed-filters" aria-label="Newsfeed filtern">' + ''.join(f'<a href="{path}?type={value}" class="{"selected" if kind == value else ""}">{label}</a>' for value, label in (("all", "Für dich"), ("news", "D&D-News"), ("video", "Videos"))) + '</nav>'
    cards = []
    for item in mixed_entries(data["entries"], kind):
        title, source = escape(item["title"]), escape(item["source"])
        try:
            url = escape(public_link(item["url"], item["kind"]), quote=True)
            stamp = datetime.fromisoformat(item["published"]).strftime("%d.%m.%Y")
        except (ValueError, KeyError): continue
        is_video = item["kind"] == "video"
        top = f'<div class="news-art"><span>✦</span><b>D&amp;D NEWS</b></div>'
        if is_video:
            video_id = item.get("video_id", "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id): continue
            top = f'<div class="video-preview"><button class="video-start" type="button" data-video="{video_id}" aria-label="Video laden: {title}"><img src="https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" alt="" loading="lazy"><span class="play-icon">▶</span><span class="video-caption">Video laden</span></button></div>'
        feed_id = escape(item.get("video_id") or item.get("url", ""), quote=True)
        cards.append(f'<article class="feed-card" data-feed-card data-feed-id="{feed_id}">{top}<div class="feed-copy"><p class="feed-meta">{"VIDEO" if is_video else "NACHRICHT"} · {source} · <time>{stamp}</time></p><h2>{title}</h2><p><a data-feed-link href="{url}" target="_blank" rel="noopener noreferrer">{"Auf YouTube ansehen" if is_video else "Artikel bei der Quelle lesen"} ↗</a></p></div></article>')
    status = ""
    if data.get("updated_at"):
        status = "Quellenstand: " + datetime.fromtimestamp(data["updated_at"]).strftime("%d.%m.%Y, %H:%M")
    if data.get("errors"):
        status += " · Einzelne Quellen sind vorübergehend nicht erreichbar; vorhandene Beiträge bleiben sichtbar."
    return filters + f'<p class="feed-status"><small>{escape(status)}</small></p><p class="feed-controls"><button type="button" data-feed-show-seen>Auch gesehene anzeigen</button></p><section class="news-feed" aria-label="D&D Newsfeed">' + (''.join(cards) or '<p>Die ersten Beiträge werden geladen. Bitte die Seite gleich aktualisieren.</p>') + '</section><button class="feed-more" type="button" data-feed-more hidden>Weitere Beiträge laden</button><p class="feed-end" data-feed-end>Du hast alle geladenen Beiträge erreicht.</p><script src="/media/feed.js" defer></script>'


def render_links():
    result = '<div class="card"><h2>D&D-News und Videos</h2><p>Nachrichten lesen und zwischendurch eine Spielrunde oder ein Regelvideo anschauen.</p><a href="/news">Newsfeed öffnen →</a></div><h2>YouTube-Kanäle</h2><div class="grid">'
    for channel in CHANNELS:
        result += f'<article class="card"><span class="badge">{html.escape(channel["language"])}</span><h2>{html.escape(channel["name"])}</h2><p>{html.escape(channel["about"])}</p><a href="{channel["url"]}" target="_blank" rel="noopener noreferrer">Zum YouTube-Kanal ↗</a></article>'
    return result + '</div><h2>Miniaturen und Hobby</h2><div class="grid"><article class="card"><h2>Hero Forge</h2><p>Eigene Charakterminiaturen gestalten.</p><a href="https://www.heroforge.com/" target="_blank" rel="noopener noreferrer">Hero Forge öffnen ↗</a></article><article class="card"><h2>The Army Painter</h2><p>Farben, Pinsel und Anleitungen für deine Miniaturen.</p><a href="https://thearmypainter.com/" target="_blank" rel="noopener noreferrer">The Army Painter öffnen ↗</a></article></div>'


def render_atmosphere(title):
    """Decorative lights aligned with each background's cover crop."""
    scenes = {
        'D&D-News und Videos': (1672, 941, [(448,281,7,18),(1192,526,4,14),(1300,391,4,14),(1131,220,4,12),(510,451,4,12)]),
        'Entdecken': (2172,724,[(1242,30,9,26),(1384,130,7,22),(940,80,22,40)]),
        'Weitere Klassen': (1536,1024,[(251,819,5,22),(1369,670,5,22),(508,272,4,15),(623,36,3,12),(679,22,3,12),(749,22,3,12),(811,36,3,12),(1508,515,20,20),(1047,474,18,25)]),
        'Weitere Spezies': (1536,1024,[(55,188,8,22),(556,291,4,12),(711,465,4,12),(1460,751,9,24)]),
        'Handouts': (1672,941,[(98,163,9,24),(1607,473,5,22),(1562,550,5,20),(1532,637,4,16)]),
        'Charakterbogen': (1672,941,[(82,474,5,20),(1523,819,7,20),(454,328,3,11),(1235,328,3,11),(1090,330,3,10),(785,32,3,10),(953,44,3,10)]),
        'Spieler-Dashboard': (1672,941,[(32,700,7,24),(1177,652,5,20),(1205,669,4,16),(1395,884,10,25),(1073,344,3,10),(25,316,20,45)]),
        'Mein Profil': (1672,941,[(1470,413,5,22),(1498,433,4,18),(1618,400,4,17),(204,339,3,11),(52,322,3,12),(792,8,3,10),(894,8,3,10)]),
        'Chronik': (1672,941,[(17,404,6,24),(32,780,5,20),(1627,519,5,22),(1226,214,4,16),(1263,188,4,16),(286,8,4,15)]),
        'DM-Zentrale': (1672,941,[(83,23,5,19),(125,55,4,15),(153,41,4,15),(1418,453,5,19),(1471,541,4,16),(1523,584,4,16),(1371,388,3,12),(31,310,4,16)]),
        'Memories': (1672,941,[(1579,355,5,20),(1526,389,4,16),(1550,478,4,16),(1655,240,18,35),(1278,34,3,12)]),
        'Kartenbibliothek': (2172,724,[(900,170,4,14),(1020,122,4,14),(1234,79,4,14),(1344,96,4,14),(1120,359,4,14),(1320,329,4,14),(1650,450,4,14),(1790,504,4,14),(1983,135,4,14),(2054,369,4,14)]),
    }
    if title not in scenes:
        return ''
    links = title == 'Entdecken'
    width, height, lights = scenes[title]
    flames = ''
    for index, (x, y, rx, ry) in enumerate(lights):
        flames += (f'<g class="ambient-light" style="--delay:-{index * .73}s;--speed:{2.7 + index * .31}s;transform-origin:{x}px {y}px">'
                   f'<ellipse cx="{x}" cy="{y}" rx="{rx * 9}" ry="{ry * 4}" fill="url(#ambient-glow)"/>'
                   f'<ellipse class="ambient-flame" cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="url(#ambient-fire)"/>'
                   '</g>')
    magic = {'Spieler-Dashboard': (1620,345,35), 'DM-Zentrale': (1610,401,66)}.get(title)
    if magic:
        mx, my, radius = magic
        flames += f'<circle class="ambient-light" style="--delay:-1s;--speed:6s;transform-origin:{mx}px {my}px" cx="{mx}" cy="{my}" r="{radius}" fill="url(#ambient-magic)"/>'
    # Match CSS background-size:cover and the existing horizontal crop exactly.
    ratio = width / height
    wide = f'{ratio * 100:.6f}vh'
    tall = f'{100 / ratio:.6f}vw'
    position = '.65' if links else '.5'
    mist = ('<g class="ambient-mist" fill="url(#ambient-mist)"><ellipse cx="890" cy="670" rx="260" ry="140"/><ellipse cx="1050" cy="500" rx="190" ry="80"/></g>' if title == 'Weitere Spezies' else '')
    header_style = ('header{position:relative;isolation:isolate;background-position:center center!important}header>strong,header>nav{position:relative;z-index:1}.ambient-scene.ambient-header{position:absolute;z-index:0}.ambient-scene.ambient-header svg{inset:0;width:100%;height:100%}' if title == 'Kartenbibliothek' else '')
    scene_class = 'ambient-scene ambient-header' if title == 'Kartenbibliothek' else 'ambient-scene'
    return (f'<style>.ambient-scene{{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:-1}}'
            f'.ambient-scene svg{{position:absolute;width:max(100vw,{wide});height:max(100vh,{tall});'
            f'left:calc((100vw - max(100vw,{wide}))*{position});top:calc((100vh - max(100vh,{tall}))*.5)}}'
            '.ambient-light{opacity:.5;animation:ambient-flicker var(--speed) ease-in-out var(--delay) infinite alternate}'
            '.ambient-flame{mix-blend-mode:screen;filter:blur(1px)}'
            '.ambient-dust{animation:ambient-drift 22s ease-in-out infinite alternate;opacity:.2}'
            '.ambient-mist{animation:ambient-mist 25s ease-in-out infinite alternate;opacity:.12}'
            '@keyframes ambient-mist{from{transform:translate(-12px,10px);opacity:.08}to{transform:translate(12px,-12px);opacity:.18}}'
            '@keyframes ambient-flicker{0%,100%{opacity:.32;transform:scale(.94,1)}23%{opacity:.55;transform:scale(1.04,.96)}'
            '47%{opacity:.42;transform:scale(.97,1.03)}71%{opacity:.65;transform:scale(1.03,1.01)}}'
            '@keyframes ambient-drift{from{transform:translate(0,12px);opacity:.12}to{transform:translate(14px,-20px);opacity:.35}}'
            f'@media(max-width:600px){{.ambient-scene svg{{left:calc((100vw - max(100vw,{wide}))*.65)}}}}'
            + header_style + '@media(prefers-reduced-motion:reduce){.ambient-scene{display:none}}'
            '@media print{.ambient-scene{display:none}}</style>'
            f'<div class="{scene_class}" aria-hidden="true"><svg preserveAspectRatio="xMidYMid slice" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" focusable="false">'
            '<defs><radialGradient id="ambient-magic"><stop stop-color="#b6e7ff" stop-opacity=".45"/><stop offset=".5" stop-color="#398de8" stop-opacity=".2"/><stop offset="1" stop-color="#398de8" stop-opacity="0"/></radialGradient><radialGradient id="ambient-mist"><stop stop-color="#d4e4e1" stop-opacity=".7"/><stop offset="1" stop-color="#d4e4e1" stop-opacity="0"/></radialGradient><radialGradient id="ambient-glow"><stop stop-color="#ffb342" stop-opacity=".5"/>'
            '<stop offset=".4" stop-color="#ed7f24" stop-opacity=".16"/><stop offset="1" stop-color="#ed7f24" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="ambient-fire"><stop stop-color="#fff5ce" stop-opacity=".85"/>'
            '<stop offset=".4" stop-color="#ffcb68" stop-opacity=".55"/><stop offset="1" stop-color="#ffa129" stop-opacity="0"/></radialGradient></defs>'
            + mist + flames + '<g class="ambient-dust" fill="#ffdc9b">'
            + ''.join(f'<circle cx="{width * x}" cy="{height * y}" r="1.1"/>' for x, y in ((.12,.43),(.2,.68),(.32,.23),(.47,.6),(.62,.34),(.82,.72),(.91,.3)))
            + '</g></svg></div>')
