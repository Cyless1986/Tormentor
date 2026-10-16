"""Transfer local Lore drafts to a configured private portal archive over SSH."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import threading
import lore
import lore_workflow

CONFIG = Path(__file__).parent / "Tormentor_Android/local_ai/lore-online.json"
REMOTE = """
import json, os, sys
sys.path.insert(0, '/srv/tormentor')
os.environ['TORMENTOR_LORE_DIR']='/srv/tormentor/private_lore'
import lore, lore_workflow
incoming=json.load(sys.stdin)
sid=incoming['id']
with lore_workflow.session_lock(sid):
    path=lore.session_dir(sid)/'session.json'
    if path.exists():
        current=lore.load(sid)
        if current.get('upload_sha256') != incoming.get('upload_sha256'):
            raise RuntimeError('Sitzungskonflikt: Online-Eintrag bleibt unverändert.')
        # Never replace DM edits, approvals, publication or corrected transcripts.
        if current.get('reviewed_at') or current.get('published'):
            raise RuntimeError('Online bereits geprüft: automatische Übernahme angehalten.')
        if current.get('transcript','') != current.get('synced_transcript',''):
            raise RuntimeError('Online-Transkript wurde bearbeitet: Übernahme angehalten.')
    incoming['synced_transcript']=incoming.get('transcript','')
    lore.save(incoming)
print(json.dumps({'id':sid,'private':True}))
"""

def payload(session):
    result = {key: session[key] for key in
              ('id','title','created_at','upload_sha256','transcript','draft')}
    result.update(audio=None, origin='android-local', published=False,
                  approved=lore.validate_review({}))
    state = session.get('processing', {})
    if state.get('state') == 'ready':
        result['processing'] = {'state':'ready','message':'Entwurf bereit · bitte als DM prüfen. Die Originalaufnahme bleibt auf dem Laptop.'}
    elif state.get('state') == 'error':
        result['processing'] = {'state':'error','message':state.get('message','Auswertung auf dem Laptop fehlgeschlagen.')}
    else:
        result['processing'] = {'state':'external','message':'Aufnahme auf dem Laptop gespeichert. Lokale Auswertung läuft; der Entwurf wird anschließend hier bereitgestellt. Die Audiodatei bleibt auf dem Laptop.'}
    return result

def sync(session):
    config=json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    encoded=base64.b64encode(REMOTE.encode()).decode()
    remote_command="cd /srv/tormentor && runuser -u tormentor -- .venv/bin/python -c \"import base64;exec(base64.b64decode('"+encoded+"'))\""
    result=subprocess.run(['ssh','-i',config['identity'],'-o','BatchMode=yes',
                           '-o','ConnectTimeout=10',config['destination'],remote_command],
                          input=json.dumps(payload(session),ensure_ascii=False).encode(),
                          capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-1500:])
    print(result.stdout.decode().strip(),flush=True)

def enqueue(session_id):
    # A separate worker survives a WLAN bridge restart.
    log_path=lore.session_dir(session_id) / "online-sync.log"
    with log_path.open("ab") as log:
        worker=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),session_id,'--process'],
                         cwd=str(Path(__file__).parent),stdout=log,stderr=log,
                         creationflags=0x08000000 if sys.platform == 'win32' else 0)
    threading.Thread(target=worker.wait,daemon=True).start()

def run(session_id, process=False):
    with lore_workflow.session_lock(session_id):
        session=lore.load(session_id)
        if process and session.get('processing',{}).get('state') != 'ready':
            session['processing']={'state':'running','message':'Lokale Auswertung läuft.'}
            lore.save(session)
            sync(session)
            lore_workflow.run_pipeline(session, not bool(session.get('transcript','').strip()))
        sync(session)

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('session_id')
    parser.add_argument('--process',action='store_true')
    args=parser.parse_args()
    run(args.session_id,args.process)
