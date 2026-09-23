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
