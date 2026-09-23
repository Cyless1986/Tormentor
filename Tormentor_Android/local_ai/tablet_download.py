"""Temporary, allowlisted WLAN downloads for tablet setup."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import secrets
import shutil
import time
import threading

ROOT = Path(__file__).resolve().parents[1]
URL_FILE = ROOT / 'local_ai/tablet-download-url.txt'
KEY = URL_FILE.read_text(encoding='utf-8').strip().rstrip('/').rsplit('/', 1)[-1] if URL_FILE.exists() else secrets.token_urlsafe(12)
FILES = {
    'Tormentor-Android.apk': ROOT / 'Tormentor-Android.apk',
    'Medienpaket.zip': ROOT / 'Medienpaket.zip',
    'Tablet-Verbindung.json': ROOT / 'local_ai/Tablet-Verbindung.json',
    'Tablet-Videos.zip': ROOT / 'Tablet-Videos.zip',
}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        prefix = '/' + KEY + '/'
        if not self.path.startswith(prefix):
            self.send_error(404)
            return
        name = self.path[len(prefix):]
        if not name:
            body = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                    '<title>Tormentor installieren</title><body style="font:22px sans-serif;padding:24px">'
                    '<h1>Tormentor 1.6 – Update</h1><p>Neues Layout: Steinplatten im Rahmen, Funktionen links. Nur die App aktualisieren.</p>'
                    '<p><a href="Tormentor-Android.apk?v=1.6">1. App aktualisieren (Version 1.6)</a></p>'
                    '<p><a href="Tablet-Videos.zip">Optional: Reparaturpaket für alte Szenenvideos</a></p>'
                    '<p>APK als Update installieren, ohne die App zu deinstallieren. Wenn die Szenenvideos bereits laufen, ist kein erneuter ZIP-Import nötig. Nur bei noch defekten Szenenvideos Tablet-Videos.zip '
                    'unter Medien verwalten → Laptop-Medienpaket importieren auswählen. '
                    'Gleichnamige Videos werden ersetzt; Sounds und Bilder bleiben erhalten.</p>'
                    '<h2>Nur bei neuer Einrichtung</h2>'
                    + ''.join(f'<p><a href="{n}">{n}</a></p>' for n in ('Medienpaket.zip', 'Tablet-Verbindung.json'))
                    + '<p>Danach die APK in Eigene Dateien öffnen. ZIP und Verbindungsdatei in der App importieren.</p>'
                    '<p>Laptop während des Downloads eingeschaltet lassen.</p>').encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif name.split('?')[0] in FILES:
            name = name.split('?')[0]
            path = FILES[name]
            if not path.is_file():
                self.send_error(503, 'Datei wird noch vorbereitet')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{name}"')
            self.send_header('Content-Length', str(path.stat().st_size))
            self.end_headers()
            try:
                with path.open('rb') as source:
                    shutil.copyfileobj(source, self.wfile, 1024 * 1024)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_error(404)

if __name__ == '__main__':
    host = json.loads(FILES['Tablet-Verbindung.json'].read_text(encoding='utf-8'))['host'].split('://')[1].split(':')[0]
    server = ThreadingHTTPServer((host, 8766), Handler)
    (ROOT / 'local_ai/tablet-download-url.txt').write_text(f'http://{host}:8766/{KEY}/', encoding='utf-8')
    timer = threading.Timer(7200, server.shutdown)
    timer.daemon = True
    timer.start()
    server.serve_forever()
    server.server_close()





