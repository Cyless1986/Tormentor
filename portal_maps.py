"""DM-managed private map library for the portal's player group."""
from pathlib import Path
from html import escape
from email.parser import BytesParser
from email.policy import default
from io import BytesIO
import secrets
import warnings
import re
from PIL import Image

ROOT=Path(__file__).resolve().parent/'portal_maps'
IMAGE_LIMIT=25*1024*1024
LIMIT=100*1024*1024

def mp4_video(data):
    """Check the ISO media container structure and presence of a video track."""
    offset=0; boxes=set(); video=False
    while offset+8<=len(data):
        size=int.from_bytes(data[offset:offset+4],'big'); kind=data[offset+4:offset+8]; header=8
        if size==1:
            if offset+16>len(data): return False
            size=int.from_bytes(data[offset+8:offset+16],'big'); header=16
        elif size==0: size=len(data)-offset
        if size<header or offset+size>len(data): return False
        boxes.add(kind)
        if kind==b'moov': video=b'vide' in data[offset+header:offset+size]
        offset+=size
    return offset==len(data) and {b'ftyp',b'moov',b'mdat'}<=boxes and video

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS maps (id TEXT PRIMARY KEY, title TEXT NOT NULL, session_title TEXT NOT NULL, filename TEXT NOT NULL, mime TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0)')

def can_view(row,user):
    return bool(row and user and not row['deleted'] and (user['role']=='dm' or row['published']))

def library(db,user):
    dm=user['role']=='dm'
    body='<p>Karten eurer gespielten Sessions aus Dungeon Alchemist.</p><p class="notice">Diese Sammlung enthält auch Karten aus der Dungeon-Alchemist-Community. Vielen Dank an die jeweiligen Kartenerstellerinnen und Kartenersteller!</p>'
    if dm:
        body+=('<section class="card"><h2>Karte hochladen</h2><p>PNG, JPG oder WebP bis 25 MB · animierte MP4-Karten bis 100 MB. Für die Wiedergabe im Browser eignet sich MP4 mit H.264.</p>'
               '<form method="post" action="/dm/maps/upload" enctype="multipart/form-data"><label>Titel<input name="title" required maxlength="120"></label>'
               '<label>Session oder Gruppe<input name="session_title" maxlength="120" placeholder="Zum Beispiel Session 4 · Die Nebelwanderer"></label>'
               '<label>Kartenbild oder MP4<input type="file" name="map" accept="image/png,image/jpeg,image/webp,video/mp4,.mp4" required></label>'
               '<label><input type="checkbox" name="published" value="1"> Für angemeldete Spieler freigeben</label><button>Karte hochladen</button></form></section>')
    rows=db.execute('SELECT * FROM maps WHERE deleted=0 ORDER BY rowid DESC').fetchall()
    cards=[]
    for row in rows:
        if not can_view(row,user): continue
        key=row['id']
        url=f'/maps/{key}/image'
        visual=(f'<video src="{url}" controls loop muted playsinline preload="metadata" aria-label="{escape(row["title"])}" style="display:block;width:100%;max-height:620px;object-fit:contain"></video>' if row['mime']=='video/mp4' else f'<a href="{url}" target="_blank" rel="noopener"><img src="{url}" alt="{escape(row["title"])}" loading="lazy" style="display:block;width:100%;max-height:420px;object-fit:contain"></a>')
        card=f'<article class="card"><h2>{escape(row["title"])}</h2><p>{escape(row["session_title"])}</p>{visual}<p><a href="{url}" target="_blank" rel="noopener">In Originalgröße öffnen</a> · <a href="{url}" download="karte-{key}{Path(row["filename"]).suffix}">Herunterladen</a></p>'
        if dm:
            card+=f'<p>{"Für Spieler sichtbar" if row["published"] else "Nur für den DM sichtbar"}</p><form method="post" action="/dm/maps/{key}/visibility"><button>{"Freigabe zurücknehmen" if row["published"] else "Für Spieler freigeben"}</button></form><form method="post" action="/dm/maps/{key}/remove"><button>Aus Bibliothek entfernen</button></form>'
        cards.append(card+'</article>')
    return body+(''.join(cards) or '<p>Noch keine Karten verfügbar.</p>')

def receive(handler,db):
    size=int(handler.headers.get('Content-Length','0'))
    if not 0<size<=LIMIT+65536: raise ValueError('Die Datei darf maximal 100 MB groß sein.')
    content_type=handler.headers.get('Content-Type','')
    if not content_type.startswith('multipart/form-data;'): raise ValueError('Bitte das Uploadformular verwenden.')
    raw=handler.rfile.read(size)
    if len(raw)!=size: raise ValueError('Upload unvollständig.')
    message=BytesParser(policy=default).parsebytes(('Content-Type: '+content_type+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+raw)
    if not message.is_multipart(): raise ValueError('Upload ungültig.')
    fields={}; images=[]
    for part in message.iter_parts():
        name=part.get_param('name',header='content-disposition')
        data=part.get_payload(decode=True) or b''
        if name=='map': images.append(data)
        elif name in ('title','session_title','published'):
            if len(data)>1024: raise ValueError('Formularfeld zu lang.')
            fields[name]=data.decode('utf-8').strip()
    if len(images)!=1 or not 0<len(images[0])<=LIMIT: raise ValueError('Bitte genau eine Kartendatei bis 100 MB wählen.')
    title=fields.get('title',''); session=fields.get('session_title','')
    if not title or max(len(title),len(session))>120: raise ValueError('Bitte einen Titel mit höchstens 120 Zeichen angeben.')
    if mp4_video(images[0]):
        suffix,mime='mp4','video/mp4'
    else:
        suffix,mime=validate_image(images[0])
    key=secrets.token_hex(16); filename=f'{key}.{suffix}'
    ROOT.mkdir(exist_ok=True)
    file=ROOT/filename
    file.write_bytes(images[0])
    try:
        db.execute('INSERT INTO maps VALUES(?,?,?,?,?,?,0)',(key,title,session,filename,mime,int(fields.get('published')=='1')))
    except Exception:
        file.unlink(missing_ok=True)
        raise

def validate_image(data):
    if len(data)>IMAGE_LIMIT: raise ValueError('Kartenbilder dürfen maximal 25 MB groß sein; MP4-Videos maximal 100 MB.')
    with warnings.catch_warnings():
        warnings.simplefilter('error',Image.DecompressionBombWarning)
        try:
            with Image.open(BytesIO(data)) as picture:
                kind=picture.format
                if kind not in ('PNG','JPEG','WEBP') or picture.width*picture.height>40_000_000:
                    raise ValueError('Bitte PNG, JPG oder WebP mit höchstens 40 Megapixeln verwenden.')
                picture.verify()
        except (OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
            raise ValueError('Bitte ein gültiges PNG-, JPG-, WebP-Bild oder MP4-Video wählen.') from exc
    return {'PNG':('png','image/png'),'JPEG':('jpg','image/jpeg'),'WEBP':('webp','image/webp')}[kind]

def serve_image(handler,db,user,path):
    key=path.split('/')[2]
    row=db.execute('SELECT * FROM maps WHERE id=?',(key,)).fetchone()
    if not can_view(row,user): return False
    file=ROOT/row['filename']
    if not file.is_file(): return False
    size=file.stat().st_size; start,end=0,size-1
    byte_range=handler.headers.get('Range')
    if byte_range:
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',byte_range)
        try:
            if not match or not any(match.groups()): raise ValueError()
            first,last=match.groups()
            if first:
                start=int(first);end=min(int(last),size-1) if last else size-1
            else:
                if int(last)<=0: raise ValueError()
                start=max(0,size-int(last))
            if start>=size or end<start: raise ValueError()
        except ValueError:
            handler.send_response(416);handler.send_header('Content-Range',f'bytes */{size}');handler.send_header('Content-Length','0');handler.end_headers();return True
    handler.send_response(206 if byte_range else 200)
    handler.send_header('Content-Type',row['mime'])
    handler.send_header('Content-Length',str(end-start+1))
    handler.send_header('Accept-Ranges','bytes')
    if byte_range: handler.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    handler.send_header('Cache-Control','private, no-store')
    handler.send_header('X-Content-Type-Options','nosniff')
    handler.end_headers()
    with file.open('rb') as source:
        source.seek(start);remaining=end-start+1
        try:
            while remaining:
                chunk=source.read(min(65536,remaining))
                if not chunk: break
                handler.wfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
    return True
