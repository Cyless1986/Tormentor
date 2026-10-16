"""Illustrated hardcover books for the Codex library."""
BOOKS = [
 ('2024','Rassen & Klassen','Ausgabe 2024','SRD 5.2.1','/codex/2024'),
 ('2014','Rassen & Klassen','Ausgabe 2014','SRD 5.1','/codex/2014'),
 ('spells','Zauberlexikon','Die Kunst der Magie','Zauber nachschlagen','/codex/zauber'),
 ('homebrew','Homebrew','Eigene Welten','Tormentors eigene Inhalte','/codex/homebrew'),
]
STYLE = '''<style>
.codex-shelf{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:60px 48px;padding:20px 22px 50px;max-width:900px;margin:auto}
.codex-volume{position:relative;display:block;aspect-ratio:2/3;text-decoration:none;color:#f3d8a3;isolation:isolate;border-radius:4px 10px 10px 4px;border:1px solid #ab8148;box-shadow:8px 9px 0 #35291d,12px 13px 0 #c3ad83,15px 15px 0 #493023,22px 28px 30px #0009;transform:perspective(1300px) rotateY(-7deg);transition:transform .3s,box-shadow .3s;background:#1b1011;min-width:0}
.codex-volume::before{content:"";position:absolute;inset:0;z-index:2;border-radius:inherit;background:linear-gradient(90deg,#000b,transparent 3%,#fff2 4%,#0008 6%,transparent 10%,transparent 96%,#fff2);pointer-events:none}
.codex-volume::after{content:"";position:absolute;inset:12px 12px 12px 25px;z-index:2;border:1px solid #e2be7477;box-shadow:inset 0 0 0 3px #0002;pointer-events:none}
.codex-volume img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:inherit;z-index:-2}
.codex-cover-shade{position:absolute;inset:0;border-radius:inherit;background:linear-gradient(#050607cc,transparent 45%,transparent 60%,#050607ed);z-index:-1}
.codex-volume-copy{height:100%;display:flex;flex-direction:column;text-align:center;padding:30px 24px 25px 38px;text-shadow:0 2px 4px #000,0 0 18px #000}
.codex-imprint{font:11px system-ui;letter-spacing:.3em;color:#e3c695}
.codex-volume h2{margin:10px 0 3px;font-weight:bold;line-height:1.1;font-size:clamp(25px,3.8vw,43px);color:#f0d49b;letter-spacing:.025em;text-shadow:0 1px #fff4,0 3px 3px #000}
.codex-volume-subtitle{font-size:15px;color:#f5e4c7}.codex-volume-bottom{margin-top:auto;display:grid;gap:9px}.codex-volume-edition{font:11px system-ui;letter-spacing:.13em;text-transform:uppercase;color:#ecd8b5}.codex-volume-open{font-size:15px;color:#ffe1a7}
.codex-library-links{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin:18px 0 30px}.codex-library-links a{padding:10px 16px;border:1px solid #806847;border-radius:8px;background:#211915}
@media(hover:hover) and (pointer:fine){.codex-volume:hover{transform:perspective(1300px) rotateY(-2deg) translateY(-8px);box-shadow:8px 9px 0 #35291d,12px 13px 0 #c3ad83,15px 15px 0 #493023,22px 36px 35px #000a}}
.codex-volume:focus-visible{outline:3px solid #ffe1a7;outline-offset:10px}
@media(max-width:600px){.codex-shelf{grid-template-columns:minmax(0,1fr);max-width:390px;gap:45px;padding:12px 24px 36px 12px}.codex-volume h2{font-size:34px}.codex-volume-copy{padding-top:30px}}
@media(prefers-reduced-motion:reduce){.codex-volume{transition:none}.codex-volume:hover{transform:perspective(1300px) rotateY(-7deg)}}
</style>'''

def render():
    books=''
    for key,title,subtitle,edition,url in BOOKS:
        books += f'<a class="codex-volume" href="{url}" aria-label="{title} · {subtitle} öffnen"><img src="/media/codex-cover-{key}.png" alt="" loading="lazy"><span class="codex-cover-shade"></span><div class="codex-volume-copy"><span class="codex-imprint">TORMENTOR · CODEX</span><h2>{title}</h2><span class="codex-volume-subtitle">{subtitle}</span><span class="codex-volume-bottom"><span class="codex-volume-edition">{edition}</span><span class="codex-volume-open">Buch öffnen →</span></span></div></a>'
    sources = '<section class="card"><h2>Weitere Quellen</h2><h3><a href="/codex/quellen/tasha">Tashas Kessel mit Allem</a></h3><p>Regelfassung 2014 · Magieschmied und Unterklassen</p><p><a href="/codex/quellen/tasha">Quelle öffnen →</a></p></section>'
    return STYLE+'<div class="codex-shelf">'+books+'</div>'+sources+'<nav class="codex-library-links" aria-label="Weitere Codex-Themen"><a href="/codex/weitere">Weitere Spezies</a><a href="/codex/klassen">Weitere Klassen</a><a href="/codex/herkuenfte">Herkünfte</a></nav>'
