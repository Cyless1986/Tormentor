"""Personal WLAN bridge: local Ollama text plus male Windows speech. No cloud APIs."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import base64
import hmac
import ipaddress
import json
import re
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
import lore_workflow
CONFIG = ROOT / "connection.json"
LOCK = threading.Lock()
OLLAMA = "http://127.0.0.1:11435/api/chat"
SYSTEM_PROMPT = """Du bist Tormentor, ein hilfreicher deutschsprachiger D&D-Assistent am Spieltisch.
Beantworte immer zuerst die konkrete Frage. Bei Regelfragen erkläre sachlich und verständlich den Ablauf,
die benötigten Würfel, die addierten Werte und das Ergebnis. Gib bei Würfelfragen ein kurzes Zahlenbeispiel.
Keine düsteren Metaphern statt einer Erklärung, keine Beleidigungen, keine Rätselantworten.
Nur wenn ausdrücklich eine Szene, Geschichte oder Atmosphäre gewünscht ist, erzähle düster und bildhaft.
Die dunkle Stimme entsteht durch die Sprachausgabe, nicht durch unverständliche Formulierungen.
Gehe ohne andere Angabe von D&D 5e aus und benenne diese Annahme kurz bei Regelfragen.
Wenn eine Regel editionsabhängig oder dir unbekannt ist, sage das und frage gezielt nach; erfinde keine Regel.
Grundlagen für D&D 5e: Ein Angriffswurf ist W20 plus Angriffsbonus. Der Bonus enthält den passenden
Attributsmodifikator sowie den Übungsbonus, falls für den Angriff anwendbar. Das Ergebnis muss die
Rüstungsklasse des Ziels erreichen oder übertreffen. Es wird nicht gegen die Rüstungsklasse gewürfelt,
indem man unter ihr bleibt. Beispiel: 12 auf dem W20 plus 5 Angriffsbonus ergibt 17 und trifft RK 16.
Nach einem Treffer wird der Schaden separat mit den Schadenswürfeln des Angriffs bestimmt.
Bei Angriffswürfen verfehlt eine natürliche 1; eine natürliche 20 trifft kritisch.
Diese Sonderregel nicht pauschal auf Attributsproben übertragen.
Antworte normalerweise in vier bis sechs kurzen Sätzen, ohne Markdown. Verständlichkeit geht vor Stimmung.
"""


def settings():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    data = {"token": secrets.token_hex(16), "port": 8765, "model": "gemma3:4b", "dark_voice": True}
    CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def answer(question, model):
    # Keep these common beginner questions precise; do not route special attacks here.
    basic_question = re.sub(r"[?.!]+$", "", question.strip().lower()).strip()
    if re.fullmatch(r"wie (?:würfle|würfel|würfelt|würfele) (?:ich|man) (?:gegen (?:die )?rüstungsklasse|(?:einen? )?angriff)(?: aus)?", basic_question):
        return ("In D&D 5e würfelst du einmal mit einem zwanzigseitigen Würfel und addierst deinen Angriffsbonus. "
                "Der Angriffsbonus enthält den passenden Attributsmodifikator und, wenn anwendbar, deinen Übungsbonus. "
                "Erreicht oder übertrifft die Summe die Rüstungsklasse des Ziels, triffst du. "
                "Zum Beispiel: Du würfelst eine 12 und addierst 5; das ergibt 17 und trifft Rüstungsklasse 16. "
                "Danach würfelst du den Schaden separat mit den Schadenswürfeln deines Angriffs. "
                "Eine gewürfelte 1 verfehlt bei Angriffswürfen immer; eine gewürfelte 20 trifft kritisch.")
    request = {"model": model, "stream": False, "keep_alive": "30m", "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}], "options": {"num_ctx": 2048, "num_predict": 320, "temperature": 0.25, "num_thread": 2}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(request).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        text = json.load(response).get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError("Die lokale KI hat keine Antwort geliefert.")
    return text


def speech(text):
    try:
        from neural_voice import synthesize
        return base64.b64encode(synthesize(text, dark=Handler.config.get("dark_voice", True))).decode("ascii")
    except Exception as exc:
        raise RuntimeError("Die lokale Thorsten-Stimme ist nicht verfügbar. Piper-Installation und Sprachmodell prüfen.") from exc


class Handler(BaseHTTPRequestHandler):
    config = None

    def log_message(self, fmt, *args):
        pass  # Do not log questions or pairing tokens.

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"ready": True, "lore_upload": True, "version": "2.0"})
        self.reply(404, {"error": "Unbekannte Funktion"})

    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        self.connection.settimeout(15)
        if not ipaddress.ip_address(self.client_address[0]).is_private:
            return self.reply(403, {"error": "Nur im lokalen Netzwerk verfügbar."})
        if not hmac.compare_digest(self.headers.get("X-Tormentor-Token", ""), self.config["token"]):
            return self.reply(401, {"error": "Verbindungscode falsch. Bitte mit connection.json vergleichen."})
        if self.path == "/lore/audio":
            try:
                self.connection.settimeout(60)
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("Bitte die Dateigröße für die Übertragung angeben.")
                title = unquote(self.headers.get("X-Tormentor-Title", "Android-Sitzung"), encoding="utf-8", errors="strict")
                item, created = lore_workflow.receive_audio(
                    self.rfile, int(self.headers.get("Content-Length", "0")),
                    self.headers.get("X-Tormentor-SHA256", ""),
                    self.headers.get("X-Tormentor-Audio-Extension", ""), title)
                return self.reply(201 if created else 200, {"id": item["id"], "title": item["title"], "created": created,
                    "message": "Privat auf dem Laptop gespeichert. Unter DM → Tormentor Lore auswerten und prüfen."})
            except lore_workflow.SessionBusy as exc:
                return self.reply(409, {"error": str(exc)})
            except (ValueError, UnicodeError) as exc:
                return self.reply(400, {"error": str(exc)})
            except OSError:
                return self.reply(400, {"error": "Übertragung unterbrochen oder nicht speicherbar. Bitte erneut senden."})
        if self.path not in ("/ask", "/test"):
            return self.reply(404, {"error": "Unbekannte Funktion"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 20000:
                return self.reply(413, {"error": "Anfrage zu groß oder leer"})
            data = json.loads(self.rfile.read(size))
            question = data.get("question", "").strip()
            if self.path == "/ask" and not 1 <= len(question) <= 4000:
                return self.reply(400, {"error": "Bitte eine Frage mit höchstens 4000 Zeichen stellen."})
        except (ValueError, TypeError, AttributeError, OSError):
            return self.reply(400, {"error": "Anfrage nicht lesbar"})
        if not LOCK.acquire(blocking=False):
            return self.reply(409, {"error": "Tormentor beantwortet gerade eine Frage."})
        try:
            text = "Ich bin Tormentor. Die Verbindung funktioniert, Dungeonmaster." if self.path == "/test" else answer(question, self.config["model"])
            result = {"text": text}
            try:
                result["audio"] = speech(text)
            except RuntimeError as exc:
                result["warning"] = str(exc)
            self.reply(200, result)
        except urllib.error.URLError:
            self.reply(503, {"error": "Lokale KI nicht erreichbar. KI starten und Modell-Download prüfen."})
        except Exception:
            self.reply(500, {"error": "Die lokale Antwort konnte nicht erzeugt werden. Bitte erneut versuchen."})
        finally:
            LOCK.release()


def main():
    Handler.config = settings()
    server = ThreadingHTTPServer(("0.0.0.0", Handler.config["port"]), Handler)
    # Local WLAN only; token auth; no router port forwarding.
    networks = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
    addresses = sorted({a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET) if any(ipaddress.ip_address(a[4][0]) in n for n in networks)})
    (ROOT / "Tablet-Verbindung.txt").write_text("Tormentor: Laptop und Tablet im gleichen privaten WLAN\n\nLaptop-Adressen:\n" + "\n".join(f"http://{address}:{Handler.config['port']}" for address in addresses) + "\n\nVerbindungscode:\n" + Handler.config["token"] + "\n\nIn der App unter „Lokale KI einrichten“ eintragen.\n", encoding="utf-8")
    if addresses:
        (ROOT / "Tablet-Verbindung.json").write_text(json.dumps({"host": f"http://{addresses[0]}:{Handler.config['port']}", "token": Handler.config["token"]}), encoding="utf-8")
    print("Tormentor-KI bereit. Verbindung siehe Tablet-Verbindung.txt", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
