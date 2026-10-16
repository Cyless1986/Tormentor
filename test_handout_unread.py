import http.client,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
import portal,portal_handouts as handouts

class HandoutUnreadTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patches=[patch.object(portal,'DB',Path(self.temp.name)/'portal.sqlite3'),patch.object(portal.portal_security,'PUBLIC_ORIGIN','')]
        for p in self.patches:p.start()
        self.users={}
        with portal.database() as db:
            for name,role in [('dm','dm'),('alice','player'),('bob','player')]:
                uid=db.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)',(name,'unused',role)).lastrowid
                db.execute('INSERT INTO sessions VALUES(?,?,?)',(portal.digest(name),uid,9999999999))
                self.users[name]={'id':uid,'role':role}
            self.private=handouts.save(db,{'title':'Nur Alice','body':'Geheim','audience':'selected','recipient_'+str(self.users['alice']['id']):'1','publication':'publish'},self.users['dm']['id'],100)
            self.public=handouts.save(db,{'title':'Für alle','body':'Text','audience':'all','publication':'publish'},self.users['dm']['id'],100)
            handouts.save(db,{'title':'Entwurf','body':'Privat','audience':'all','publication':'draft'},self.users['dm']['id'],100)
        self.server=portal.ThreadingHTTPServer(('127.0.0.1',0),portal.Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close()
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def request(self,method,path,user=None,data=None,headers=None):
        h=dict(headers or {})
        if user:h['Cookie']='tormentor_session='+user
        h['Content-Type']='application/x-www-form-urlencoded'
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        c.request(method,path,urlencode(data or {}),h)
        r=c.getresponse();result=r.status,r.read().decode();c.close();return result
    def count(self,user):
        status,body=self.request('GET','/handouts/unread',user)
        self.assertEqual(status,200);return int(body)
    def test_individual_visibility_and_opening(self):
        self.assertEqual(self.count('alice'),2)
        self.assertEqual(self.count('bob'),1)
        self.assertEqual(self.count('dm'),0)
        self.assertEqual(self.request('GET','/handouts/unread')[0],401)
        body=self.request('GET','/handouts','alice')[1]
        self.assertIn('handouts-unread',body)
        self.assertIn('data-handout-read="0"',body)
        self.assertEqual(self.count('alice'),2)
        data={'id':self.private,'version':2}
        self.assertEqual(self.request('POST','/handouts/read','bob',data)[0],400)
        self.assertEqual(self.request('POST','/handouts/read',None,data)[0],403)
        self.assertEqual(self.request('POST','/handouts/read','alice',data)[0],200)
        self.assertEqual(self.count('alice'),1)
        self.assertEqual(self.count('bob'),1)
        self.assertEqual(self.request('POST','/handouts/read','alice',data)[0],200)
        self.assertEqual(self.count('alice'),1)
    def test_new_revision_and_stale_tab(self):
        data={'id':self.public,'version':2}
        self.assertEqual(self.request('POST','/handouts/read','alice',data)[0],200)
        with portal.database() as db:
            handouts.save(db,{'title':'Für alle','body':'Neuer Text','audience':'all','publication':'publish'},self.users['dm']['id'],100,self.public)
        self.assertEqual(self.count('alice'),2)
        self.assertEqual(self.request('POST','/handouts/read','alice',data)[0],409)
        self.assertEqual(self.count('alice'),2)
        data['version']=3
        self.assertEqual(self.request('POST','/handouts/read','alice',data)[0],200)
        self.assertEqual(self.count('alice'),1)
        self.assertEqual(self.count('bob'),1)
    def test_revocation_deletion_legacy_and_csrf(self):
        data={'id':self.public,'version':2}
        self.assertEqual(self.request('POST','/handouts/read','alice',data,{'Origin':'https://foreign.example'})[0],403)
        with portal.database() as db:
            db.execute('UPDATE handouts SET published=0 WHERE id=?',(self.public,))
            db.execute('UPDATE handouts SET deleted=1 WHERE id=?',(self.private,))
            legacy=db.execute("INSERT INTO handouts(title,body,published,created_by,updated_at) VALUES('Alt','Alt',1,?,0)",(self.users['dm']['id'],)).lastrowid
        self.assertEqual(self.count('alice'),1)
        self.assertEqual(self.count('bob'),1)
        self.assertEqual(self.request('POST','/handouts/read','alice',{'id':legacy,'version':999})[0],409)
        self.assertEqual(self.request('POST','/handouts/read','alice',{'id':legacy,'version':1})[0],200)
        self.assertEqual(self.count('alice'),0)

if __name__=='__main__':unittest.main()
