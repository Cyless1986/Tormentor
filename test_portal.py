import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

import portal


class PortalRegistrationTest(unittest.TestCase):
    def test_invitation_registration_and_guest_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_db = portal.DB
            old_lore = portal.LORE
            portal.DB = Path(temporary) / "portal.sqlite3"
            portal.LORE = Path(temporary) / "lore"
            server = portal.ThreadingHTTPServer(("127.0.0.1", 0), portal.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with portal.database() as db:
                    db.execute("INSERT INTO users(username,password,role) VALUES(?,?,'dm')", ("meister", portal.password_hash("secure-passphrase")))
                    db.commit()

                def request(method, path, data=None, cookie=None):
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}
                    if cookie: headers["Cookie"] = cookie
                    connection.request(method, path, urlencode(data or {}), headers)
                    response = connection.getresponse()
                    result = response.status, dict(response.getheaders()), response.read().decode("utf-8", errors="replace")
                    connection.close()
                    return result

                status, headers, _ = request("POST", "/login", {"username": "meister", "password": "secure-passphrase"})
                self.assertEqual(status, 303)
                dm_cookie = headers["Set-Cookie"].split(";", 1)[0]
                status, _, body = request("POST", "/dm", cookie=dm_cookie)
                self.assertEqual(status, 200)
                import re
                code = re.search(r"<h2>([A-F0-9]+)</h2>", body).group(1)
                status, _, _ = request("POST", "/register", {"code": code, "username": "spieler", "password": "another-passphrase"})
                self.assertEqual(status, 303)
                status, _, _ = request("POST", "/register", {"code": code, "username": "zweiter", "password": "another-passphrase"})
                self.assertEqual(status, 400)
                status, _, _ = request("GET", "/dashboard")
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/lore")
                self.assertEqual(status, 303)
                status, headers, _ = request("POST", "/login", {"username": "spieler", "password": "another-passphrase"})
                self.assertEqual(status, 303)
                player_cookie = headers["Set-Cookie"].split(";", 1)[0]
                status, _, body = request("GET", "/dm", cookie=player_cookie)
                self.assertEqual(status, 403)
                status, _, _ = request("POST", "/dashboard", {"player_name": "Arin", "race": "Ork", "class_name": "Kämpfer", "subclass": "Champion", "group_name": "Nachtwache", "level": "2", "companion": "Rabe"}, player_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/profil", cookie=player_cookie)
                self.assertIn('value="2"', body)
                self.assertIn('name="subclass"', body)
                self.assertIn('value="Champion"', body)
                self.assertIn('Klassen und ihre Unterklassen', body)
                status, _, body = request("GET", "/dashboard", cookie=player_cookie)
                self.assertIn('<b>Unterklasse:</b> Champion', body)
                self.assertIn('Rising Moon — RandomMind', body)
                self.assertIn('id="dashboard-music" src="/media/intro.mp3"', body)
                status, _, body = request("GET", "/codex/unterklassen")
                self.assertEqual(status, 200)
                self.assertIn('Regelfassung 2014', body)
                self.assertIn('Regelfassung 2024', body)
                self.assertIn('/codex/quelle/tcoe-circle-of-spores', body)
                self.assertIn('/codex/quelle/rthw-phantom', body)
                status, _, body = request("GET", "/codex/unterklassen?q=Druide")
                self.assertEqual(status, 200)
                self.assertIn('/codex/quelle/tcoe-circle-of-spores', body)
                self.assertNotIn('/codex/quelle/rthw-phantom', body)
                import json
                session_id = "a" * 32
                folder = portal.LORE / session_id
                folder.mkdir(parents=True)
                (folder / "session.json").write_text(json.dumps({"id": session_id, "title": "Sitzung 1", "published": True, "approved": {"level_ups": [{"player": "Arin", "level": 3}]}}), encoding="utf-8")
                with portal.database() as db:
                    player_id = db.execute("SELECT id FROM users WHERE username='spieler'").fetchone()["id"]
                status, _, _ = request("POST", "/dm/level", {"player_id": player_id, "level": 3, "session_id": session_id, "evidence": "Arin"}, dm_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/dashboard", cookie=player_cookie)
                self.assertIn("Stufe 3", body)
                with portal.database() as db:
                    suggestion_id = db.execute("SELECT id FROM level_suggestions").fetchone()["id"]
                status, _, _ = request("POST", f"/dashboard/level/{suggestion_id}", cookie=player_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/profil", cookie=player_cookie)
                self.assertIn('value="3"', body)
                handout = {"audience": "all", "title": "Geheime Karte", "body": "Der Turm liegt im Norden."}
                status, _, _ = request("POST", "/dm/handouts", handout, player_cookie)
                self.assertEqual(status, 403)
                status, _, _ = request("POST", "/dm/handouts", handout, dm_cookie)
                self.assertEqual(status, 303)
                with portal.database() as db:
                    handout_id = db.execute("SELECT id FROM handouts WHERE title='Geheime Karte'").fetchone()["id"]
                status, _, body = request("GET", "/handouts", cookie=player_cookie)
                self.assertNotIn("Geheime Karte", body)
                handout["published"] = "1"
                status, _, _ = request("POST", f"/dm/handouts/edit/{handout_id}", handout, dm_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/handouts", cookie=player_cookie)
                self.assertIn("Geheime Karte", body)
                self.assertIn("Der Turm liegt im Norden.", body)
                status, _, _ = request("POST", f"/dm/handouts/delete/{handout_id}", cookie=dm_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", "/handouts", cookie=player_cookie)
                self.assertNotIn("Geheime Karte", body)
                for path in ("/lore/sitzungen", "/lore/npcs", "/lore/orte", "/lore/quests"):
                    status, _, _ = request("GET", path, cookie=player_cookie)
                    self.assertEqual(status, 200)
                entry = {"title": "Sporengeborene", "kind": "Spezies", "edition": "Homebrew", "source": "Eigene Schöpfung", "body": "Eine eigene Pilzspezies."}
                status, _, _ = request("POST", "/dm/codex", entry, player_cookie)
                self.assertEqual(status, 403)
                status, _, _ = request("POST", "/dm/codex", entry, dm_cookie)
                self.assertEqual(status, 303)
                with portal.database() as db:
                    item_id = db.execute("SELECT id FROM codex_entries WHERE title='Sporengeborene'").fetchone()["id"]
                status, _, _ = request("GET", f"/codex/eintrag/{item_id}")
                self.assertEqual(status, 404)
                entry["published"] = "1"
                status, _, _ = request("POST", f"/dm/codex/edit/{item_id}", entry, dm_cookie)
                self.assertEqual(status, 303)
                status, _, body = request("GET", f"/codex/eintrag/{item_id}")
                self.assertEqual(status, 200)
                self.assertIn("Sporengeborene", body)
                status, _, _ = request("POST", f"/dm/codex/delete/{item_id}", cookie=dm_cookie)
                self.assertEqual(status, 303)
                status, _, _ = request("GET", f"/codex/eintrag/{item_id}")
                self.assertEqual(status, 404)
                status, _, body = request("GET", "/login")
                self.assertEqual(status, 200)
                self.assertNotIn('src="/media/intro.mp4"', body)
                self.assertIn('id="login-background"', body)
                self.assertEqual('src="/media/intro.mp3"' in body, portal.INTRO_MUSIC.is_file())
                self.assertIn('action="/guest"', body)
                self.assertIn("Gästelogin", body)
                status, headers, _ = request("POST", "/guest", cookie=player_cookie)
                self.assertEqual(status, 303)
                self.assertEqual(headers["Location"], "/gast")
                self.assertEqual(request("GET", "/dashboard", cookie=player_cookie)[0], 303)
                self.assertEqual(request("GET", "/lore", cookie=player_cookie)[0], 303)
                self.assertEqual(request("GET", "/gast")[0], 200)
                status, headers, _ = request("GET", "/media/intro.mp4")
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Type"], "video/mp4")
            finally:
                server.shutdown()
                server.server_close()
                portal.DB = old_db
                portal.LORE = old_lore


if __name__ == "__main__":
    unittest.main()
