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
                    '<h1>Tormentor 2.5.6 – Update</h1><p>Direkt würfeln, Ergebnis in der Logbox und englische Cortana-Ansage. Stimmfilter für kurze Befehle angepasst.</p>'
                    '<p><a href="Tormentor-Android.apk?v=2.5.6">App herunterladen (Version 2.5.6)</a></p>'
                    '<p>Die APK in Eigene Dateien öffnen und als Update installieren. Die vorhandene App nicht deinstallieren.</p>'
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    host = parser.parse_args().host
    server = ThreadingHTTPServer((host, 8766), Handler)
    (ROOT / 'local_ai/tablet-download-url.txt').write_text(f'http://{host}:8766/{KEY}/', encoding='utf-8')
    timer = threading.Timer(7200, server.shutdown)
    timer.daemon = True
    timer.start()
    server.serve_forever()
    server.server_close()





