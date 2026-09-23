import sqlite3
import unittest
import http.client
import re
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch
import portal
import portal_reset as reset

class RecoveryTest(unittest.TestCase):
    def test_player_request_dm_link_and_existing_account_over_http(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(portal, 'DB', Path(temporary) / 'portal.sqlite3'), patch.object(portal.portal_security, '_requests', {}):
            with portal.database() as db:
                db.execute("INSERT INTO users(username,password,role) VALUES(?,?,'dm')", ('meister', portal.password_hash('dm-password-123')))
                player_id = db.execute("INSERT INTO users(username,password,role,player_name,subclass,group_name) VALUES(?,?,'player','Arin','Champion','Nachtwache')", ('spieler', portal.password_hash('old-password-123'))).lastrowid
            server = portal.ThreadingHTTPServer(('127.0.0.1', 0), portal.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def request(method, path, data=None, cookie=None, origin=None):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                if cookie: headers['Cookie'] = cookie
                if origin: headers['Origin'] = origin
                try:
                    conn.request(method, path, urlencode(data or {}), headers)
                    response = conn.getresponse()
                    return response.status, dict(response.getheaders()), response.read().decode()
                finally:
                    conn.close()

            try:
                self.assertIn('/forgot-password', request('GET', '/login')[2])
                self.assertEqual(request('GET', '/forgot-password')[0], 200)
                self.assertEqual(request('POST', '/forgot-password', {'username': 'spieler'}, origin='https://evil.example')[0], 403)
                known = request('POST', '/forgot-password', {'username': 'Spieler'})
                unknown = request('POST', '/forgot-password', {'username': 'unknown'})
                self.assertEqual(known, unknown)
                request('POST', '/forgot-password', {'username': 'spieler'})
                with portal.database() as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM password_help_requests').fetchone()[0], 1)
                    self.assertEqual(db.execute('SELECT count(*) FROM password_resets').fetchone()[0], 0)
                self.assertEqual(request('GET', '/dm/password-resets')[0], 403)
                _, headers, _ = request('POST', '/login', {'username': 'spieler', 'password': 'old-password-123'})
                player_cookie = headers['Set-Cookie'].split(';')[0]
                endpoint = '/dm/password-resets/' + str(player_id)
                self.assertEqual(request('POST', endpoint, {'verified': 'yes'}, player_cookie)[0], 403)
                _, headers, _ = request('POST', '/login', {'username': 'meister', 'password': 'dm-password-123'})
                dm_cookie = headers['Set-Cookie'].split(';')[0]
                self.assertIn('spieler', request('GET', '/dm/password-resets', cookie=dm_cookie)[2])
                self.assertEqual(request('POST', endpoint, cookie=dm_cookie)[0], 400)
                status, _, body = request('POST', endpoint, {'verified': 'yes'}, dm_cookie)
                self.assertEqual(status, 200)
                token = re.search(r'/reset-password#([A-Za-z0-9_-]+)', body).group(1)
                with portal.database() as db:
                    self.assertNotEqual(db.execute('SELECT token_hash FROM password_resets').fetchone()[0], token)
                self.assertEqual(request('POST', '/reset-password', {'token': token, 'password': 'new-password-123', 'confirmation': 'different'})[0], 400)
                data = {'token': token, 'password': 'new-password-123', 'confirmation': 'new-password-123'}
                self.assertEqual(request('POST', '/reset-password', data)[0], 200)
                self.assertEqual(request('POST', '/reset-password', data)[0], 400)
                self.assertEqual(request('GET', '/dashboard', cookie=player_cookie)[0], 303)
                self.assertEqual(request('POST', '/login', {'username': 'spieler', 'password': 'old-password-123'})[0], 401)
                status, headers, _ = request('POST', '/login', {'username': 'spieler', 'password': 'new-password-123'})
                self.assertEqual(status, 303)
                body = request('GET', '/profil', cookie=headers['Set-Cookie'].split(';')[0])[2]
                self.assertIn('Champion', body)
                self.assertIn('Nachtwache', body)
                with portal.database() as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0], 2)
                    self.assertEqual(db.execute('SELECT count(*) FROM password_help_requests').fetchone()[0], 0)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_expiry_reissue_one_use_and_session_revocation(self):
        db = sqlite3.connect(':memory:')
        db.executescript('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password TEXT); CREATE TABLE sessions(token_hash TEXT,user_id INTEGER,expires_at INTEGER);')
        db.execute('INSERT INTO users VALUES(1,?,?)', ('dm', portal.password_hash('old-password-123')))
        db.execute('INSERT INTO sessions VALUES(?,1,9999999999)', ('session',))
        db.commit()
        old = reset.issue(db, 'dm')
        token = reset.issue(db, 'dm')
        with self.assertRaises(ValueError): reset.redeem(db, old, 'new-password-123', 'new-password-123')
        with self.assertRaises(ValueError): reset.redeem(db, token, 'new-password-123', 'different')
        reset.redeem(db, token, 'new-password-123', 'new-password-123')
        self.assertTrue(portal.password_ok('new-password-123', db.execute('SELECT password FROM users').fetchone()[0]))
        self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
        with self.assertRaises(ValueError): reset.redeem(db, token, 'another-password', 'another-password')
        expired = reset.issue(db, 'dm')
        db.execute('UPDATE password_resets SET expires_at=0'); db.commit()
        with self.assertRaises(ValueError): reset.redeem(db, expired, 'new-password-123', 'new-password-123')
        db.close()
