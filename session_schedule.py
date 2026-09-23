"""Single next-session appointment; optional time uses explicit UTC offset."""
from datetime import date, datetime, timezone
from html import escape

def sabers():
    blade = '<path d="M-5 22 L-5 -32 Q-5 -66 15 -88 Q5 -60 5 -30 L5 22Z" fill="#dce4df" stroke="#778b87" stroke-width="2"/><path d="M-2 14 L-2 -31 Q-2 -60 10 -78" fill="none" stroke="#fff6d9" stroke-width="2"/><path d="M-18 24 Q0 12 18 24 L16 30 Q0 22 -16 30Z" fill="#b99654" stroke="#e5c985" stroke-width="2"/><rect x="-4" y="27" width="8" height="26" rx="3" fill="#704337" stroke="#c3a267"/><path d="M-7 54 L7 54" stroke="#e5c985" stroke-width="5"/>'
    return ('<div class="session-sabers"><svg viewBox="0 0 220 180" aria-hidden="true" focusable="false"><g transform="translate(110 108)"><g class="saber-left">'+blade+'</g><g class="saber-right">'+blade+'</g><path class="saber-spark" d="M0 -24 L0 -36 M-7 -22 L-15 -29 M7 -22 L15 -29" stroke="#f7df9c" stroke-width="2"/></g></svg><button type="button" class="saber-toggle" aria-pressed="false">Animation pausieren</button></div>'
            '<style>.session-countdown{position:relative;overflow:hidden;padding-right:210px}.session-sabers{position:absolute;right:12px;top:12px;width:180px;text-align:center}.session-sabers svg{width:100%;height:150px}.saber-left{transform:rotate(-40deg);animation:saber-left 5s ease-in-out infinite}.saber-right{transform:rotate(40deg);animation:saber-right 5s ease-in-out infinite}.saber-spark{opacity:0;animation:saber-spark 5s infinite}.saber-toggle{font:12px Georgia,serif;padding:.35rem .55rem;background:#211915;color:#dbc394}.sabers-paused svg *{animation-play-state:paused!important}@keyframes saber-left{0%,28%,100%{transform:rotate(-40deg)}10%{transform:rotate(-58deg)}16%,22%{transform:rotate(-32deg)}19%,25%{transform:rotate(-38deg)}}@keyframes saber-right{0%,28%,100%{transform:rotate(40deg)}10%{transform:rotate(58deg)}16%,22%{transform:rotate(32deg)}19%,25%{transform:rotate(38deg)}}@keyframes saber-spark{0%,14%,20%,26%,100%{opacity:0}16%,22%{opacity:.9}}@media(max-width:600px){.session-countdown{padding-right:1rem}.session-sabers{position:relative;right:auto;top:auto;float:right;width:105px;margin:0 0 .5rem .5rem}.session-sabers svg{height:100px}.saber-toggle{font-size:10px}}@media(prefers-reduced-motion:reduce){.session-sabers svg *{animation:none!important}.saber-toggle{display:none}}@media print{.session-sabers{display:none}}</style>')

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS next_session (id INTEGER PRIMARY KEY CHECK(id=1), title TEXT NOT NULL, day TEXT NOT NULL, clock TEXT NOT NULL, offset TEXT NOT NULL)')

def save(db, data):
    title=data.get('title','').strip() or 'Nächste Session'
    if len(title)>120: raise ValueError('Der Titel darf höchstens 120 Zeichen haben.')
    day=data.get('day',''); clock=data.get('clock',''); offset=data.get('offset','+02:00')
    date.fromisoformat(day)
    if offset not in ('+01:00','+02:00'): raise ValueError('Bitte Winter- oder Sommerzeit auswählen.')
    if clock:
        datetime.strptime(clock,'%H:%M')
    db.execute('INSERT INTO next_session VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,day=excluded.day,clock=excluded.clock,offset=excluded.offset',(title,day,clock,offset))

def render(db, dm=False):
    row=db.execute('SELECT * FROM next_session WHERE id=1').fetchone()
    if not row:
        return '<section class="card session-countdown">'+sabers()+'<h2>Nächste Session</h2><p>Noch kein Termin festgelegt.</p></section><script src="/media/session-countdown.js" defer></script>'
    day=date.fromisoformat(row['day'])
    label=day.strftime('%d.%m.%Y')
    target=''
    if row['clock']:
        target=datetime.fromisoformat(row['day']+'T'+row['clock']+row['offset']).astimezone(timezone.utc).isoformat()
        label+=' · '+row['clock']+' Uhr (UTC'+row['offset']+')'
    else: label+=' · Uhrzeit noch offen'
    return ('<section class="card session-countdown">'+sabers()+f'<span class="badge">Nächstes Abenteuer</span><h2>{escape(row["title"])}</h2><p>{escape(label)}</p>'
            f'<p class="countdown-value" data-session-target="{escape(target)}" data-session-day="{row["day"]}">Termin: {day.strftime("%d.%m.%Y")}</p>'
            + ('<a href="/dm#session-plan">Termin bearbeiten</a>' if dm else '') + '</section><script src="/media/session-countdown.js" defer></script>')

def editor(db):
    row=db.execute('SELECT * FROM next_session WHERE id=1').fetchone()
    values=dict(row) if row else dict(title='Nächste Session',day='',clock='',offset='+02:00')
    options=''.join(f'<option value="{v}"'+(' selected' if values['offset']==v else '')+f'>{label}</option>' for v,label in (('+02:00','Sommerzeit · Deutschland (UTC+2)'),('+01:00','Winterzeit · Deutschland (UTC+1)')))
    return (f'<section class="card" id="session-plan"><h2>Nächste Session planen</h2><form method="post" action="/dm/session">'
            f'<label>Titel<input name="title" maxlength="120" value="{escape(values["title"])}"></label>'
            f'<label>Datum<input type="date" name="day" required value="{values["day"]}"></label>'
            f'<label>Uhrzeit · optional<input type="time" name="clock" value="{values["clock"]}"></label>'
            f'<label>Zeitzone<select name="offset">{options}</select></label><button>Termin speichern</button></form>'
            '<form method="post" action="/dm/session/clear"><button>Termin zurücknehmen</button></form></section>')
