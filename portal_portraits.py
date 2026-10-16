"""Private character portraits, normalized before storage."""
import io
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

LIMIT = 8 * 1024 * 1024

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS character_portraits (user_id INTEGER NOT NULL, slot TEXT NOT NULL, image BLOB NOT NULL, PRIMARY KEY(user_id,slot))')

def save(db, uid, raw, slot="hero"):
    if slot not in ("hero", "companion-1", "companion-2", "companion-3"):
        raise ValueError("Ungültiges Bildfeld.")
    if not 0 < len(raw) <= LIMIT:
        raise ValueError('Bitte ein Bild bis 8 MB auswählen.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Bitte JPG, PNG oder WebP auswählen.')
                if source.width * source.height > 25_000_000:
                    raise ValueError('Das Bild darf höchstens 25 Megapixel haben.')
                image = ImageOps.exif_transpose(source)
                image.thumbnail((1200, 1600))
                rgba = image.convert('RGBA')
                clean = Image.new('RGB', rgba.size, '#191a1e')
                clean.paste(rgba, mask=rgba.getchannel('A'))
                output = io.BytesIO()
                clean.save(output, format='JPEG', quality=88)
    except (OSError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('Diese Bilddatei ist beschädigt oder zu groß.') from exc
    db.execute('INSERT INTO character_portraits(user_id,slot,image) VALUES(?,?,?) ON CONFLICT(user_id,slot) DO UPDATE SET image=excluded.image', (uid, slot, output.getvalue()))

def render(db, uid, slot="hero"):
    exists = db.execute('SELECT 1 FROM character_portraits WHERE user_id=? AND slot=?', (uid,slot)).fetchone() is not None
    url = '/character/portrait' + ('' if slot == 'hero' else '/' + slot)
    label = 'Deine Figur' if slot == 'hero' else 'Bild des Begleiters'
    image = '<img data-portrait-image src="'+url+'" alt="'+label+'">' if exists else '<img data-portrait-image alt="'+label+'" hidden>'
    return '<aside class="card character-portrait-card" data-portrait-url="'+url+'"><h3>'+label+'</h3><div class="character-portrait-frame">' + image + '<p data-portrait-empty' + (' hidden' if exists else '') + '>Hier ist Platz für ein Bild.</p></div><label>Bild auswählen<input type="file" id="portrait-file-'+slot+'" data-portrait-file accept="image/jpeg,image/png,image/webp"></label><p class="sheet-hint">JPG, PNG oder WebP · bis 8 MB</p><button type="button" data-portrait-upload>'+('Bild ersetzen' if exists else 'Bild hochladen')+'</button><p class="portrait-status" data-portrait-status role="status" aria-live="polite">Das Bild wird separat gespeichert.</p></aside>'

STYLE = '''<style>.character-identity-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(230px,300px);gap:20px;align-items:start}.character-identity-layout>div{min-width:0}.character-portrait-frame{aspect-ratio:3/4;display:grid;place-items:center;background:#101114;border:1px solid #806847;border-radius:10px;overflow:hidden}.character-portrait-frame img{width:100%;height:100%;max-height:400px;object-fit:contain}.character-portrait-frame p{padding:20px;text-align:center;color:#c9b798}.character-portrait-card input[type=file]{width:100%;font-size:13px}.character-portrait-card button{width:100%}.portrait-status{font-size:14px;overflow-wrap:anywhere}@media(max-width:700px){.character-identity-layout{grid-template-columns:1fr}.character-portrait-card{width:100%;max-width:360px;justify-self:center}}@media print{.character-portrait-card label,.character-portrait-card button,.character-portrait-card .sheet-hint,.portrait-status{display:none}}</style>'''

STYLE += """<style>.character-combat-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(180px,260px);gap:20px;align-items:start}.character-combat-layout>div{min-width:0}.character-combat-art{margin:1rem 0;border:1px solid #806847;border-radius:12px;overflow:hidden}.character-combat-art img{display:block;width:100%;height:auto}.sheet-panel textarea[name=features],.sheet-panel textarea[name=spells],.sheet-panel textarea[name=equipment],.sheet-panel textarea[name=languages]{width:100%;max-width:none;min-height:320px;box-sizing:border-box}@media(max-width:700px){.character-combat-layout{grid-template-columns:1fr}.character-combat-art{width:100%;max-width:260px;justify-self:center}}@media print{.character-combat-art{display:none}.character-combat-layout{display:block}}</style>"""

STYLE += """<style>.companion-portrait-placement{display:flex;justify-content:flex-end}.companion-portrait-placement>.character-portrait-card{width:280px;max-width:100%}.magic-heading{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.magic-elements{display:grid;grid-template-columns:repeat(3,minmax(58px,1fr));gap:7px;max-width:270px}.magic-elements span{display:flex;align-items:center;flex-direction:column;padding:7px;border:1px solid #80684766;border-radius:9px;background:#10121bcc;font:12px system-ui;color:#ddcba8}.magic-elements b{font-size:24px;margin-bottom:3px}.magic-elements .fire{color:#ff9a52}.magic-elements .ice{color:#8ddcf5}.magic-elements .air{color:#d9e5ed}.magic-elements .earth{color:#a9c982}.magic-elements .lightning{color:#e9cb74}.magic-elements .shadow{color:#c2a6ed}@media(max-width:500px){.magic-heading{flex-direction:column}.magic-elements{width:100%;max-width:none}.companion-portrait-placement{justify-content:center}}</style>"""
