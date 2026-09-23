import http.client
import tempfile
import threading
import time
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image
import portal
import portal_maps

class MapsTest(unittest.TestCase):
    def test_upload_and_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_db,old_root=portal.DB,portal_maps.ROOT
            portal.DB=Path(tmp)/'test.sqlite3';portal_maps.ROOT=Path(tmp)/'maps'
            server=portal.ThreadingHTTPServer(('127.0.0.1',0),portal.Handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with portal.database() as db:
                    for i,role in enumerate(('dm','player'),1):
                        db.execute('INSERT INTO users(id,username,password,role) VALUES(?,?,?,?)',(i,role,'unused',role))
                        db.execute('INSERT INTO sessions VALUES(?,?,?)',(portal.digest(role),i,int(time.time())+600))
                def req(method,path,role='',body=b'',kind='application/x-www-form-urlencoded',extra=None):
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
                    conn.request(method,path,body,{'Cookie':'tormentor_session='+role,'Content-Type':kind,**(extra or {})})
                    response=conn.getresponse();result=(response.status,response.read());conn.close();return result
                image=BytesIO();Image.new('RGB',(32,32),'green').save(image,format='PNG')
                prefix=b'--test-boundary\r\nContent-Disposition: form-data; name="title"\r\n\r\nKellerkarte\r\n--test-boundary\r\nContent-Disposition: form-data; name="map"; filename="map.png"\r\nContent-Type: image/png\r\n\r\n'
                body=prefix+image.getvalue()+b'\r\n--test-boundary--\r\n';kind='multipart/form-data; boundary=test-boundary'
                self.assertEqual(req('POST','/dm/maps/upload','player',body,kind)[0],403)
                self.assertEqual(req('POST','/dm/maps/upload','dm',body,kind)[0],303)
                with portal.database() as db: key=db.execute('SELECT id FROM maps').fetchone()[0]
                path=f'/maps/{key}/image'
                self.assertEqual(req('GET',path,'dm')[0],200)
                self.assertEqual(req('GET',path,'player')[0],404)
                movie=(Path(__file__).parent/'assets/login-tavern-loop.mp4').read_bytes()
                self.assertTrue(portal_maps.mp4_video(movie))
                self.assertFalse(portal_maps.mp4_video(movie[:64]))
                self.assertEqual(req('POST','/dm/maps/upload','dm',prefix+movie+b'\r\n--test-boundary--\r\n',kind)[0],303)
                with portal.database() as db:
                    video=db.execute("SELECT * FROM maps WHERE mime='video/mp4'").fetchone()
                    self.assertIn('<video',portal_maps.library(db,{'role':'dm'}))
                video_path=f'/maps/{video["id"]}/image'
                self.assertEqual(req('GET',video_path,'player',extra={'Range':'bytes=0-31'})[0],404)
                status,content=req('GET',video_path,'dm',extra={'Range':'bytes=0-31'})
                self.assertEqual((status,content),(206,movie[:32]))
                self.assertEqual(req('GET',video_path,'dm',extra={'Range':'bytes=-16'}),(206,movie[-16:]))
                self.assertEqual(req('GET',video_path,'dm',extra={'Range':'bytes=999999999-'})[0],416)
                self.assertEqual(req('POST',f'/dm/maps/{video["id"]}/visibility','dm')[0],303)
                self.assertEqual(req('GET',video_path,'player',extra={'Range':'bytes=0-31'})[0],206)
                self.assertEqual(req('GET',video_path,extra={'Range':'bytes=0-31'})[0],404)
                self.assertEqual(req('GET',path)[0],404)
                self.assertEqual(req('POST',f'/dm/maps/{key}/visibility','dm')[0],303)
                self.assertEqual(req('GET',path,'player')[0],200)
                self.assertEqual(req('GET',path)[0],404)
                self.assertEqual(req('POST','/dm/maps/upload','dm',prefix+b'not an image\r\n--test-boundary--\r\n',kind)[0],400)
                self.assertEqual(req('POST',f'/dm/maps/{key}/remove','dm')[0],303)
                self.assertEqual(req('GET',path,'player')[0],404)
            finally:
                server.shutdown();server.server_close();portal.DB=old_db;portal_maps.ROOT=old_root
