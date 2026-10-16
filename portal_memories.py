"""DM uploads and authenticated-player access to session photos and videos."""
from datetime import date, datetime
from html import escape
from pathlib import Path
from urllib.parse import unquote, parse_qs
import json, re, secrets, shutil
ROOT=Path(__file__).resolve().parent/'portal_memories'
TYPES={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif','video/mp4':'.mp4','video/webm':'.webm'}
IMAGE_LIMIT=25*1024*1024
VIDEO_LIMIT=250*1024*1024
TOTAL_LIMIT=2*1024*1024*1024

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS memories (
      id TEXT PRIMARY KEY,title TEXT NOT NULL,caption TEXT NOT NULL DEFAULT '',
      session_date TEXT NOT NULL DEFAULT '',filename TEXT NOT NULL UNIQUE,
      mime TEXT NOT NULL,size INTEGER NOT NULL,created_by INTEGER NOT NULL,
      created_at INTEGER NOT NULL,deleted INTEGER NOT NULL DEFAULT 0)""")

def allowed(user):
    return user is not None and user['role'] in ('dm','player')

def json_reply(handler,status,value):
    body=json.dumps(value,ensure_ascii=False).encode()
    handler.send_response(status)
    for name,value in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','private, no-store'),('X-Content-Type-Options','nosniff')]:
        handler.send_header(name,value)
    handler.end_headers()
    handler.wfile.write(body)

def field(handler,name,limit):
    value=handler.headers.get('X-Memory-'+name,'')
    if len(value)>limit*12: raise ValueError('Textfeld zu lang.')
    value=unquote(value,encoding='utf-8',errors='strict').strip()
    if len(value)>limit: raise ValueError('Textfeld zu lang.')
    return value

def validate_media(path,mime):
    if mime.startswith('image/'):
        from PIL import Image
        try:
            with Image.open(path) as img:
                if img.width*img.height>40_000_000: raise ValueError('Bild zu groß: maximal 40 Megapixel.')
                if img.format!={'image/jpeg':'JPEG','image/png':'PNG','image/webp':'WEBP','image/gif':'GIF'}[mime]:
                    raise ValueError('Bildformat stimmt nicht mit der Datei überein.')
                img.verify()
        except (OSError,SyntaxError,Image.DecompressionBombError) as exc:
            raise ValueError('Die Bilddatei ist beschädigt oder wird nicht unterstützt.') from exc
    else:
        with path.open('rb') as file: head=file.read(4096)
        if mime=='video/mp4':
            brands=(b'isom',b'iso2',b'iso4',b'iso5',b'iso6',b'mp41',b'mp42',b'avc1',b'M4V ',b'dash')
            if len(head)<16 or head[4:8]!=b'ftyp' or not any(b in head[8:min(int.from_bytes(head[:4],'big'),128)] for b in brands):
                raise ValueError('Bitte ein MP4-Video hochladen.')
        elif not head.startswith(b'\x1a\x45\xdf\xa3') or b'webm' not in head:
            raise ValueError('Bitte ein WebM-Video hochladen.')

def receive(handler,db,user,now):
    if handler.headers.get('Transfer-Encoding'): raise ValueError('Bitte eine Datei mit fester Größe hochladen.')
    size=int(handler.headers.get('Content-Length','0'))
    mime=handler.headers.get('Content-Type','').split(';',1)[0].lower()
    if mime not in TYPES: raise ValueError('Erlaubt sind JPG, PNG, WebP, GIF, MP4 und WebM.')
    if not 0<size<=(IMAGE_LIMIT if mime.startswith('image/') else VIDEO_LIMIT):
        raise ValueError('Bilder dürfen bis 25 MB, Videos bis 250 MB groß sein.')
    title,caption,session_date=field(handler,'Title',120),field(handler,'Caption',2000),field(handler,'Date',10)
    if not title: raise ValueError('Bitte einen Titel eingeben.')
    if session_date:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',session_date): raise ValueError('Bitte ein gültiges Sessiondatum eingeben.')
        date.fromisoformat(session_date)
    ROOT.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(ROOT).free<size+256*1024*1024: raise ValueError('Auf dem Server ist nicht genug Speicher frei.')
    key=secrets.token_hex(16)
    temporary,target=ROOT/(key+'.upload'),ROOT/(key+TYPES[mime])
    old_timeout=handler.connection.gettimeout()
    try:
        handler.connection.settimeout(120)
        remaining=size
        with temporary.open('xb') as output:
            while remaining:
                block=handler.rfile.read(min(65536,remaining))
                if not block: raise ValueError('Übertragung abgebrochen. Bitte erneut versuchen.')
                output.write(block)
                remaining-=len(block)
        validate_media(temporary,mime)
        db.execute('BEGIN IMMEDIATE')
        used=db.execute('SELECT COALESCE(SUM(size),0) FROM memories WHERE deleted=0').fetchone()[0]
        if used+size>TOTAL_LIMIT: raise ValueError('Der Memories-Speicher ist voll. Bitte zuerst ältere Einträge entfernen.')
        temporary.replace(target)
        db.execute('INSERT INTO memories(id,title,caption,session_date,filename,mime,size,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
          (key,title,caption,session_date,target.name,mime,size,user['id'],now))
        db.commit()
        return key
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
        handler.connection.settimeout(old_timeout)

def remove(db,key):
    row=db.execute('SELECT filename FROM memories WHERE id=? AND deleted=0',(key,)).fetchone()
    if not row: return
    db.execute('UPDATE memories SET deleted=1 WHERE id=?',(key,))
    db.commit()
    (ROOT/row['filename']).unlink(missing_ok=True)

def byte_range(value,size):
    if not value: return 0,size-1
    match=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
    if not match or not any(match.groups()): raise ValueError()
    first,last=match.groups()
    if not first:
        count=int(last)
        if count<=0: raise ValueError()
        return max(0,size-count),size-1
    start=int(first)
    end=min(int(last),size-1) if last else size-1
    if start>=size or end<start: raise ValueError()
    return start,end

def serve(handler,db,user,key):
    if not allowed(user): return handler.send(403,'Bitte anmelden.')
    row=db.execute('SELECT * FROM memories WHERE id=? AND deleted=0',(key,)).fetchone()
    if not row or not (ROOT/row['filename']).is_file(): return handler.send(404,'Memory nicht gefunden.')
    file=ROOT/row['filename']
    size=file.stat().st_size
    try: start,end=byte_range(handler.headers.get('Range',''),size)
    except ValueError:
        handler.send_response(416)
        handler.send_header('Content-Range',f'bytes */{size}')
        handler.send_header('Content-Length','0')
        handler.send_header('Cache-Control','private, no-store')
        handler.end_headers()
        return
    partial=bool(handler.headers.get('Range'))
    handler.send_response(206 if partial else 200)
    for name,value in [('Content-Type',row['mime']),('Content-Length',str(end-start+1)),('Accept-Ranges','bytes'),('Cache-Control','private, no-store'),('Vary','Cookie'),('X-Content-Type-Options','nosniff'),('Content-Disposition','inline; filename="'+row['filename']+'"')]:
        handler.send_header(name,value)
    if partial: handler.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    handler.end_headers()
    try:
        with file.open('rb') as source:
            source.seek(start)
            remaining=end-start+1
            while remaining:
                chunk=source.read(min(65536,remaining))
                if not chunk: break
                handler.wfile.write(chunk)
                remaining-=len(chunk)
    except (BrokenPipeError,ConnectionResetError): pass

STYLE="""<style>
.memories-hero{padding:32px;border:1px solid #84653e;border-radius:16px;background:#21170f url("/media/memories-journal-hero.png") center/cover no-repeat;margin-bottom:24px;position:relative;isolation:isolate;overflow:hidden;min-height:280px}
.memories-hero:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#100c09ed 0%,#100c09b8 43%,#100c0922 100%);z-index:-1}
.memories-candlelight{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:-2}
.memories-candlelight .glow{animation:memories-flicker 3.7s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.memories-candlelight .glow-second{animation-duration:2.9s;animation-delay:-1.3s}
@keyframes memories-flicker{0%,100%{opacity:.42;transform:scale(.96)}19%{opacity:.67;transform:scale(1.04)}37%{opacity:.48;transform:scale(.98)}61%{opacity:.8;transform:scale(1.06)}82%{opacity:.58;transform:scale(1)}}
.memories-hero h2,.memories-hero p,.memories-eyebrow{text-shadow:0 2px 8px #000}
@media(prefers-reduced-motion:reduce){.memories-candlelight .glow{animation:none;opacity:.5}}
.memories-hero p{max-width:640px;line-height:1.6;color:#d7c6aa}.memories-hero h2{font-size:clamp(28px,4vw,42px);margin:12px 0}
.memories-eyebrow{font:12px system-ui,sans-serif;letter-spacing:.18em;color:#dcbf88}
.memories-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:22px}
.memory-card{overflow:hidden;border:1px solid #695136;border-radius:14px;background:#201a16;min-width:0}
.memory-media{display:block;width:100%;height:240px;object-fit:contain;background:#100e0b}
.memory-text{padding:22px}.memory-text h2{font-size:23px;margin:10px 0;overflow-wrap:anywhere}.memory-caption{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.6;color:#d6c7b0}
.memory-meta{font:12px system-ui,sans-serif;letter-spacing:.04em;color:#c3a77a}.memory-text form{margin:16px 0 0}.memory-text button{font-size:13px;background:#34261f}
.memories-upload{margin:0 0 28px;padding:22px;border:1px solid #84653e;border-radius:14px;background:#241d16}
.memories-upload summary{cursor:pointer;font-size:21px;color:#e7c991}.memories-upload[open] summary{margin-bottom:22px}
.memories-upload input,.memories-upload textarea{box-sizing:border-box;max-width:100%}.memories-fields{display:grid;grid-template-columns:2fr 1fr;gap:18px}
.memories-upload progress{width:100%;accent-color:#d9ae58}.memories-empty{padding:48px 24px;text-align:center;border:1px dashed #78603f;border-radius:14px;color:#d6c7b0}
.memories-pages{display:flex;justify-content:space-between;margin:24px 0}.memories-status{min-height:24px;line-height:1.5}
@media(max-width:600px){.memories-hero{padding:24px}.memories-fields{grid-template-columns:1fr;gap:0}.memory-media{height:210px}}
</style>"""

def render(db,user,query=''):
    try: number=max(1,int(parse_qs(query).get('page',['1'])[0]))
    except ValueError: number=1
    total=db.execute('SELECT COUNT(*) FROM memories WHERE deleted=0').fetchone()[0]
    number=min(number,max(1,(total+23)//24))
    rows=db.execute("SELECT * FROM memories WHERE deleted=0 ORDER BY COALESCE(NULLIF(session_date,''),date(created_at,'unixepoch')) DESC,created_at DESC,id DESC LIMIT 24 OFFSET ?",((number-1)*24,)).fetchall()
    body=STYLE+'<section class="memories-hero"><svg class="memories-candlelight" viewBox="0 0 2172 724" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><defs><radialGradient id="memories-flame"><stop offset="0" stop-color="#fff8cc" stop-opacity=".95"/><stop offset=".18" stop-color="#ffc65d" stop-opacity=".75"/><stop offset="1" stop-color="#ff8b26" stop-opacity="0"/></radialGradient></defs><ellipse class="glow" cx="1240" cy="42" rx="105" ry="135" fill="url(#memories-flame)"/><ellipse class="glow glow-second" cx="1348" cy="120" rx="90" ry="115" fill="url(#memories-flame)"/></svg><span class="memories-eyebrow">UNSERE GEMEINSAMEN ABENTEUER</span><h2>Momente, die bleiben.</h2><p>Bilder und Videos aus unseren Sessions. Nur für unsere angemeldete Runde sichtbar.</p><span class="badge">'+str(total)+' Erinnerungen</span></section>'
    if user['role']=='dm':
        body+='''<details class="memories-upload"><summary>＋ Erinnerung hochladen</summary>
<form id="memory-upload" action="/dm/memories/upload" method="post">
<div class="memories-fields"><label>Titel<input name="title" maxlength="120" required placeholder="Zum Beispiel: Unser Abend in Gorna"></label><label>Sessiondatum · optional<input type="date" name="session_date"></label></div>
<label>Beschreibung · optional<textarea name="caption" maxlength="2000" rows="3" placeholder="Was möchtet ihr von diesem Moment festhalten?"></textarea></label>
<label>Bild oder Video<input type="file" name="memory" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,.jpg,.jpeg,.png,.webp,.gif,.mp4,.webm" required></label>
<p><small>JPG, PNG, WebP oder GIF bis 25 MB · MP4 oder WebM bis 250 MB. Nach dem Upload für alle angemeldeten Spieler sichtbar.</small></p>
<button type="submit">Für Spieler hochladen</button><progress id="memory-progress" max="100" value="0" hidden aria-label="Upload-Fortschritt"></progress><p id="memory-status" class="memories-status" role="status" aria-live="polite"></p>
<noscript>Bitte JavaScript aktivieren, um Dateien hochzuladen.</noscript></form></details>'''
    body+='<div class="memories-grid">'
    for row in rows:
        url='/memories/'+row['id']+'/file'
        title=escape(row['title'],quote=True)
        media=(f'<a href="{url}" target="_blank" rel="noopener"><img class="memory-media" src="{url}" alt="{title}" loading="lazy"></a>' if row['mime'].startswith('image/') else f'<video class="memory-media" controls playsinline preload="none" aria-label="{title}"><source src="{url}" type="{row["mime"]}">Dein Browser kann dieses Video nicht abspielen. <a href="{url}">Video öffnen</a></video>')
        when=date.fromisoformat(row['session_date']).strftime('%d.%m.%Y') if row['session_date'] else datetime.fromtimestamp(row['created_at']).strftime('%d.%m.%Y')
        label='BILD' if row['mime'].startswith('image/') else 'VIDEO'
        body+=f'<article class="memory-card">{media}<div class="memory-text"><span class="memory-meta">{label} · {when}</span><h2>{title}</h2>'
        if row['caption']: body+='<p class="memory-caption">'+escape(row['caption'])+'</p>'
        if row['mime'].startswith('video/'): body+=f'<p><small>Falls die Wiedergabe nicht klappt: <a href="{url}" download>Video herunterladen</a>.</small></p>'
        if user['role']=='dm': body+=f'<form method="post" action="/dm/memories/{row["id"]}/remove" class="memory-remove"><button>Erinnerung entfernen</button></form>'
        body+='</div></article>'
    body+='</div>'
    if not rows: body+='<div class="memories-empty"><h2>Das nächste Abenteuer wartet.</h2><p>Hier sammeln wir die Bilder und Videos unserer Runde.</p></div>'
    body+='<nav class="memories-pages">'
    if number>1: body+=f'<a href="/memories?page={number-1}">← Neuere Erinnerungen</a>'
    if number*24<total: body+=f'<a href="/memories?page={number+1}">Ältere Erinnerungen →</a>'
    return body+'</nav><script src="/media/memories.js" defer></script>'
