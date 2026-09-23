import http.client
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
import portal
import session_schedule as schedule

class ScheduleTest(unittest.TestCase):
    def test_roles_and_optional_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=portal.DB
            portal.DB=Path(tmp)/'portal.sqlite3'
            server=portal.ThreadingHTTPServer(('127.0.0.1',0),portal.Handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with portal.database() as db:
                    for i,role in enumerate(('dm','player'),1):
                        db.execute('INSERT INTO users(id,username,password,role) VALUES(?,?,?,?)',(i,role,'unused',role))
                        db.execute('INSERT INTO sessions VALUES(?,?,?)',(portal.digest(role),i,int(time.time())+3600))
                def request(method,path,role='',data=None):
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
                    conn.request(method,path,urlencode(data or {}),{'Cookie':'tormentor_session='+role,'Content-Type':'application/x-www-form-urlencoded'})
                    response=conn.getresponse(); result=(response.status,response.read().decode());conn.close();return result
                data=dict(title='Session 4',day='2026-09-26',clock='',offset='+02:00')
                self.assertEqual(request('POST','/dm/session','player',data)[0],403)
                self.assertEqual(request('POST','/dm/session','dm',data)[0],303)
                with portal.database() as db:
                    self.assertIn('Uhrzeit noch offen',schedule.render(db))
                    schedule.save(db,{**data,'clock':'18:00'})
                    self.assertIn('2026-09-26T16:00:00+00:00',schedule.render(db))
                self.assertEqual(request('GET','/dashboard')[0],303)
                self.assertEqual(request('POST','/dm/session','dm',{**data,'day':'2026-02-31'})[0],400)
                self.assertEqual(request('POST','/dm/session/clear','player')[0],403)
                self.assertEqual(request('POST','/dm/session/clear','dm')[0],303)
                with portal.database() as db:
                    self.assertIn('Noch kein Termin',schedule.render(db))
            finally:
                server.shutdown();server.server_close();portal.DB=old
