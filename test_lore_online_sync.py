import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import lore
import lore_online_sync as sync

class SyncTests(unittest.TestCase):
    def sample(self):
        return dict(id='a'*32,title='Session',created_at='2026-09-27',upload_sha256='a'*64,
                    transcript='Private conversation',draft=lore.validate_review({}),
                    audio='android.wav',published=True,approved={'summary':'old'},
                    processing={'state':'ready'})

    def test_transfer_is_always_private_and_has_no_audio(self):
        item=sync.payload(self.sample())
        self.assertFalse(item['published'])
        self.assertIsNone(item['audio'])
        self.assertEqual(item['approved']['summary'],'')
        self.assertEqual(item['transcript'],'Private conversation')

    def test_remote_update_preserves_reviewed_session(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            current=lore.new_session('Reviewed','a'*32)
            current.update(upload_sha256='a'*64,reviewed_at='today',transcript='',synced_transcript='')
            lore.save(current)
            import io
            script=sync.REMOTE.replace("os.environ['TORMENTOR_LORE_DIR']='/srv/tormentor/private_lore'","")
            with patch('sys.stdin',io.StringIO(json.dumps(sync.payload(self.sample())))):
                with self.assertRaisesRegex(RuntimeError,'bereits geprüft'):
                    exec(script,{})
            self.assertEqual(lore.load('a'*32)['title'],'Reviewed')

    def test_remote_rejects_transcript_edits(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            current=lore.new_session('Edited','a'*32)
            current.update(upload_sha256='a'*64,transcript='DM correction',synced_transcript='')
            lore.save(current)
            import io
            script=sync.REMOTE.replace("os.environ['TORMENTOR_LORE_DIR']='/srv/tormentor/private_lore'","")
            with patch('sys.stdin',io.StringIO(json.dumps(sync.payload(self.sample())))):
                with self.assertRaisesRegex(RuntimeError,'bearbeitet'):
                    exec(script,{})
            self.assertEqual(lore.load('a'*32)['transcript'],'DM correction')

    def test_remote_creation_and_retry(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            import io
            script=sync.REMOTE.replace("os.environ['TORMENTOR_LORE_DIR']='/srv/tormentor/private_lore'","")
            for _ in range(2):
                with patch('sys.stdin',io.StringIO(json.dumps(sync.payload(self.sample())))), patch('sys.stdout',io.StringIO()):
                    exec(script,{})
            self.assertFalse(lore.load('a'*32)['published'])
            self.assertEqual(lore.load('a'*32)['synced_transcript'],'Private conversation')

    def test_external_processing_is_not_reported_as_interrupted(self):
        item=self.sample()
        item['processing']={'state':'running'}
        self.assertEqual(sync.payload(item)['processing']['state'],'external')


class CheckpointTests(unittest.TestCase):
    def test_retry_reuses_completed_sections(self):
        import io
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            session=lore.new_session('Checkpoint')
            session['transcript']='Wald und Abenteuer. ' * 900
            def response(summary):
                payload={'summary':summary,'npcs':[],'places':[],'quests':[],'level_ups':[]}
                return io.BytesIO(json.dumps({'message':{'content':json.dumps(payload)}}).encode())
            with patch('urllib.request.urlopen',side_effect=[response('Erster Abschnitt'),TimeoutError('test')]):
                with self.assertRaises(TimeoutError): lore.analyze(session)
            reloaded=lore.load(session['id'])
            self.assertEqual(len(reloaded['analysis_checkpoint']['parts']),1)
            with patch('urllib.request.urlopen',return_value=response('Zweiter Abschnitt')) as call:
                result=lore.analyze(reloaded)
                self.assertEqual(call.call_count,1)
            self.assertEqual(result['summary'],'Erster Abschnitt\n\nZweiter Abschnitt')

    def test_incomplete_model_output_is_not_silently_empty(self):
        import io
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            session=lore.new_session('Schema')
            session['transcript']='Die Gruppe betritt den Wald.'
            response=io.BytesIO(json.dumps({'message':{'content':'{"response":"wrong fields"}'}}).encode())
            with patch('urllib.request.urlopen',return_value=response):
                with self.assertRaisesRegex(ValueError,'unvollständig'): lore.analyze(session)


class CharacterContextTests(unittest.TestCase):
    def test_confirmed_attendance_invalidates_old_checkpoint(self):
        import io
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'TORMENTOR_LORE_DIR':folder}):
            session=lore.new_session('Roster')
            session['transcript']='Die Gruppe beginnt ihre Sitzung.'
            def response(request,timeout):
                request_body=json.loads(request.data)
                confirmed='Zephyra' in request_body['messages'][0]['content']
                result={'summary':'Bestätigte Besetzung' if confirmed else 'Alter Entwurf','npcs':[],'places':[],'quests':[],'level_ups':[]}
                return io.BytesIO(json.dumps({'message':{'content':json.dumps(result)}}).encode())
            with patch('urllib.request.urlopen',side_effect=response) as call:
                self.assertEqual(lore.analyze(session)['summary'],'Alter Entwurf')
                (lore.session_dir(session['id'])/'context.json').write_text(json.dumps({'participants':['Zephyra']}))
                self.assertEqual(lore.analyze(session)['summary'],'Bestätigte Besetzung')
                self.assertEqual(call.call_count,2)

if __name__=='__main__': unittest.main()
