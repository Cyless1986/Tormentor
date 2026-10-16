import http.client, io, json, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote
from PIL import Image
import portal, portal_memories as memories

class MemoriesTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.patches=[patch.object(portal,'DB',root/'db.sqlite3'),patch.object(memories,'ROOT',root/'files'),patch.object(portal.portal_security,'PUBLIC_ORIGIN','')]
        for p in self.patches: p.start()
        with portal.database() as db:
            for role in ('dm','player'):
                uid=db.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)',(role,'unused',role)).lastrowid
                db.execute('INSERT INTO sessions VALUES(?,?,?)',(portal.digest(role),uid,9999999999))
        self.server=portal.ThreadingHTTPServer(('127.0.0.1',0),portal.Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        output=io.BytesIO()
        Image.new('RGB',(4,3),(127,70,20)).save(output,format='PNG')
        self.png=output.getvalue()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        for p in reversed(self.patches): p.stop()
        self.temp.cleanup()

    def request(self,method,path,role=None,body=b'',headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        h=dict(headers or {})
        if role: h['Cookie']='tormentor_session='+role
        conn.request(method,path,body,h)
        response=conn.getresponse()
        result=response.status,dict(response.getheaders()),response.read()
        conn.close()
        return result

    def upload(self,body=None,mime='image/png',role='dm',extra=None):
        h={'Content-Type':mime,'X-Memory-Title':quote('Gorna <script>'),'X-Memory-Caption':quote('Gemeinsamer Abend'),'X-Memory-Date':'2026-09-26'}
        h.update(extra or {})
        return self.request('POST','/dm/memories/upload',role,self.png if body is None else body,h)

    def test_upload_visibility_and_direct_file_access(self):
        self.assertEqual(self.request('GET','/memories')[0],303)
        for role in (None,'player','invalid'):
            self.assertEqual(self.upload(role=role)[0],403)
        status,_,body=self.upload()
        self.assertEqual(status,201,body)
        key=json.loads(body)['id']
        url='/memories/'+key+'/file'
        for role in (None,'invalid'):
            self.assertEqual(self.request('GET',url,role)[0],403)
        status,headers,body=self.request('GET',url,'player')
        self.assertEqual((status,body),(200,self.png))
        self.assertEqual(headers['Cache-Control'],'private, no-store')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        player=self.request('GET','/memories','player')[2].decode()
        self.assertIn('Gorna &lt;script&gt;',player)
        self.assertNotIn('memory-upload',player)
        self.assertNotIn('class="memory-remove"',player)
        self.assertIn('memory-upload',self.request('GET','/memories','dm')[2].decode())
        self.assertEqual(self.request('GET','/memories/../portal.sqlite3','player')[0],404)

    def test_range_requests_and_video(self):
        mp4=b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'+b'video test'*10
        status,_,body=self.upload(mp4,'video/mp4')
        self.assertEqual(status,201,body)
        url='/memories/'+json.loads(body)['id']+'/file'
        for header,expected in [('bytes=0-7',mp4[:8]),('bytes=-8',mp4[-8:]),('bytes=8-',mp4[8:])]:
            status,h,data=self.request('GET',url,'player',headers={'Range':header})
            self.assertEqual((status,data),(206,expected))
            self.assertEqual(h['Content-Length'],str(len(expected)))
        for header in ('bytes=99999-','bytes=8-1','bytes=-0','bytes=1-2,4-5'):
            self.assertEqual(self.request('GET',url,'player',headers={'Range':header})[0],416)
        self.assertEqual(self.request('GET',url,None,headers={'Range':'bytes=0-7'})[0],403)

    def test_bad_formats_limits_and_cleanup(self):
        for data,mime in [(b'<svg/>','image/svg+xml'),(b'<html>bad','image/png'),(b'fake','video/mp4'),(b'fake','video/webm')]:
            self.assertEqual(self.upload(data,mime)[0],400)
        self.assertEqual(self.upload(extra={'X-Memory-Date':'2026-02-31'})[0],400)
        with patch.object(memories,'IMAGE_LIMIT',1):
            self.assertEqual(self.upload()[0],400)
        with patch.object(memories,'TOTAL_LIMIT',1):
            self.assertEqual(self.upload()[0],400)
        with portal.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM memories').fetchone()[0],0)
        self.assertEqual(list(memories.ROOT.glob('*')),[])

    def test_csrf_and_deletion(self):
        self.assertEqual(self.upload(extra={'Origin':'https://foreign.example'})[0],403)
        key=json.loads(self.upload()[2])['id']
        remove='/dm/memories/'+key+'/remove'
        for role in (None,'player'):
            self.assertEqual(self.request('POST',remove,role)[0],403)
        self.assertEqual(self.request('POST',remove,'dm')[0],303)
        self.assertEqual(self.request('GET','/memories/'+key+'/file','player')[0],404)
        self.assertEqual(list(memories.ROOT.glob('*')),[])

if __name__=='__main__': unittest.main()
