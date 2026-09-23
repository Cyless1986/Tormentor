import hashlib
import http.client
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode, quote

import lore
import lore_workflow
import portal


class LoreTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.env = patch.dict(os.environ, {"TORMENTOR_LORE_DIR": str(self.root / "private")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()


class LoreWorkflowTest(LoreTestCase):
    def test_complete_long_transcript_is_analyzed_and_raw_fields_stay_private(self):
        item = lore.new_session("Session 4")
        item["transcript"] = "Der Wald ist dunkel. " * 2000 + "Arin erreicht am Ende Stufe 3."
        lore.save(item)
        submitted = []
        def response(request, timeout):
            data = json.loads(request.data)
            text = data["messages"][-1]["content"]
            submitted.append(text)
            result = {"summary": "Geprüfter Abschnitt", "npcs": ["Arin"], "places": ["Wald"], "quests": [], "transcript": "DARF NICHT EXPORTIERT WERDEN"}
            if "Stufe 3" in text:
                result["level_ups"] = [{"player": "Arin", "level": 3}]
            return io.BytesIO(json.dumps({"message": {"content": json.dumps(result)}}).encode())
        with patch("urllib.request.urlopen", side_effect=response):
            draft = lore.analyze(item)
        self.assertGreater(len(submitted), 1)
        self.assertEqual("".join(submitted), item["transcript"])
        self.assertEqual(draft["level_ups"], [{"player": "Arin", "level": 3}])
        self.assertEqual(draft["npcs"], ["Arin"])
        self.assertNotIn("transcript", draft)
        public = self.root / "published"
        lore.approve(item, {**draft, "raw_audio": "SECRET"}, True, public)
        exported = json.loads((public / item["id"] / "session.json").read_text(encoding="utf-8"))
        self.assertEqual(set(exported), {"id", "title", "created_at", "approved", "published"})
        self.assertNotIn("raw_audio", exported["approved"])
        lore.approve(item, draft, False, public)
        self.assertFalse((public / item["id"] / "session.json").exists())
        self.assertEqual(lore.load(item["id"])["transcript"], item["transcript"])

    def test_review_rejects_invalid_fields_and_paths(self):
        for item in ({"npcs": "name"}, {"summary": []}, {"level_ups": [{"player": "Arin", "level": True}]}, {"level_ups": [{"player": "Arin", "level": 21}]}):
            with self.assertRaises(ValueError):
                lore.validate_review(item)
        with self.assertRaises(ValueError):
            lore.load("../secrets")
        with self.assertRaises(ValueError):
            lore.review_from_fields({"level_ups": "Arin drei"})
        self.assertEqual(lore.review_from_fields({"level_ups": "Arin | 3"})["level_ups"][0]["level"], 3)

    def test_audio_transfer_retries_preserve_session_and_incomplete_uploads_are_removed(self):
        audio = b"sample audio" * 10000
        checksum = hashlib.sha256(audio).hexdigest()
        item, created = lore_workflow.receive_audio(io.BytesIO(audio), len(audio), checksum, ".wav", "Session 4")
        self.assertTrue(created)
        self.assertEqual(item["title"], "Session 4")
        self.assertEqual((lore.session_dir(item["id"]) / item["audio"]).read_bytes(), audio)
        item["transcript"] = "Bereits korrigiert"
        lore.save(item)
        again, created = lore_workflow.receive_audio(io.BytesIO(audio), len(audio), checksum, ".wav", "Anderer Titel")
        self.assertFalse(created)
        self.assertEqual(again["transcript"], "Bereits korrigiert")
        self.assertEqual(again["title"], "Session 4")
        with self.assertRaises(ValueError):
            lore_workflow.receive_audio(io.BytesIO(b"partial"), 100, checksum, ".wav", "Session 5")
        with self.assertRaises(ValueError):
            lore_workflow.receive_audio(io.BytesIO(audio), len(audio), "0" * 64, ".wav", "Session 5")
        self.assertEqual(len(lore.list_sessions()), 1)
        self.assertFalse(list(lore.data_dir().glob("*.upload")))

    def test_processing_locks_session_and_preserves_reviewed_content(self):
        item = lore.new_session("Session 4")
        item["transcript"] = "Transkript"
        item["approved"] = lore.validate_review({"summary": "Letzte Freigabe"})
        lore.save(item)
        started, release = threading.Event(), threading.Event()
        def analyze(session, **kwargs):
            started.set()
            release.wait(5)
            session["draft"] = lore.validate_review({"summary": "Neuer Entwurf"})
            lore.save(session)
        with patch.object(lore, "analyze", side_effect=analyze):
            worker = lore_workflow.start_processing(item["id"], False)
            try:
                self.assertTrue(started.wait(3))
                self.assertTrue(lore_workflow.is_busy(item["id"]))
                with self.assertRaises(lore_workflow.SessionBusy):
                    lore_workflow.start_processing(item["id"], False)
            finally:
                release.set()
                worker.join(5)
        current = lore.load(item["id"])
        self.assertEqual(current["processing"]["state"], "ready")
        self.assertEqual(current["approved"]["summary"], "Letzte Freigabe")
        self.assertEqual(current["draft"]["summary"], "Neuer Entwurf")
        self.assertFalse(lore_workflow.is_busy(item["id"]))


class LorePortalTest(LoreTestCase):
    def request(self, method, path, data=None, role="dm"):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if role:
            headers["Cookie"] = "tormentor_session=" + role
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, urlencode(data or {}), headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read().decode("utf-8")
        connection.close()
        return result

    def test_dm_review_keeps_drafts_private_and_publishes_only_explicit_fields(self):
        with patch.object(portal, "DB", self.root / "portal.sqlite3"), patch.object(portal, "LORE", self.root / "public"):
            with portal.database() as db:
                for role in ("dm", "player"):
                    cursor = db.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (role, "unused", role))
                    db.execute("INSERT INTO sessions VALUES(?,?,?)", (portal.digest(role), cursor.lastrowid, 9999999999))
            self.server = portal.ThreadingHTTPServer(("127.0.0.1", 0), portal.Handler)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            try:
                status, headers, _ = self.request("POST", "/dm/lore", {"title": "Session 4"})
                self.assertEqual(status, 303)
                location = headers["Location"]
                session_id = location.rsplit("/", 1)[-1]
                item = lore.load(session_id)
                item["transcript"] = "DM SECRET: Der Wirt ist der Bösewicht."
                item["draft"] = lore.validate_review({"summary": "PRIVATE DRAFT"})
                lore.save(item)
                for role in (None, "player"):
                    self.assertEqual(self.request("GET", location, role=role)[0], 403)
                    self.assertEqual(self.request("POST", location + "/review", role=role)[0], 403)
                self.assertIn("DM SECRET", self.request("GET", location)[2])
                review = {"revision": portal.lore_revision(item), "title": "Session 4 – Im Wald", "summary": "Die Gruppe erreicht den Wald.", "npcs": "Arin", "places": "Wald", "quests": "Finde die Karte", "level_ups": "Arin | 3", "published": "1"}
                self.assertEqual(self.request("POST", location + "/review", review)[0], 303)
                visible = self.request("GET", "/lore/sitzungen", role="player")[2]
                self.assertIn("Session 4 – Im Wald", visible)
                self.assertIn("Die Gruppe erreicht den Wald.", visible)
                self.assertNotIn("DM SECRET", visible)
                self.assertNotIn("PRIVATE DRAFT", visible)
                self.assertEqual(self.request("POST", location + "/review", review)[0], 409)
                current = lore.load(session_id)
                self.assertEqual(self.request("POST", location + "/unpublish", {"revision": portal.lore_revision(current)})[0], 303)
                self.assertNotIn("Session 4 – Im Wald", self.request("GET", "/lore/sitzungen", role="player")[2])
                self.assertIn("DM SECRET", lore.load(session_id)["transcript"])
            finally:
                self.server.shutdown()
                self.server.server_close()

    def test_wlan_upload_requires_pairing_token_and_preserves_title(self):
        spec = importlib.util.spec_from_file_location("tormentor_bridge_test", Path(__file__).parent / "Tormentor_Android/local_ai/server.py")
        bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge)
        bridge.Handler.config = {"token": "a" * 32}
        self.server = bridge.ThreadingHTTPServer(("127.0.0.1", 0), bridge.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        audio = b"audio"
        try:
            def upload(token):
                connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
                connection.request("POST", "/lore/audio", audio, {"X-Tormentor-Token": token, "X-Tormentor-Title": quote("Session 4 – Rückkehr"), "X-Tormentor-Audio-Extension": ".wav", "X-Tormentor-SHA256": hashlib.sha256(audio).hexdigest()})
                response = connection.getresponse()
                result = response.status, json.loads(response.read())
                connection.close()
                return result
            self.assertEqual(upload("wrong")[0], 401)
            self.assertEqual(len(lore.list_sessions()), 0)
            status, data = upload("a" * 32)
            self.assertEqual(status, 201)
            self.assertEqual(data["title"], "Session 4 – Rückkehr")
            self.assertNotIn("transcript", data)
            self.assertFalse(lore.load(data["id"])["published"])
            self.assertEqual(upload("a" * 32)[0], 200)
        finally:
            self.server.shutdown()
            self.server.server_close()


if __name__ == "__main__":
    unittest.main()
