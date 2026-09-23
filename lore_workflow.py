"""Shared private audio transfer and processing for desktop, WLAN bridge and portal."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

import lore

MAX_AUDIO_BYTES = 1024 * 1024 * 1024


class SessionBusy(RuntimeError):
    pass


@contextmanager
def session_lock(session_id):
    """OS lock releases on process exit, including crashes; works across app processes."""
    folder = lore.session_dir(session_id)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".session.lock").open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise SessionBusy("Diese Sitzung wird gerade aufgenommen oder ausgewertet. Bitte kurz warten.") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def is_busy(session_id):
    try:
        with session_lock(session_id):
            return False
    except SessionBusy:
        return True


def receive_audio(source, size, expected_sha256, extension, title):
    """Stream to disk and verify before committing; retries reuse the same session."""
    if type(size) is not int or not 0 < size <= MAX_AUDIO_BYTES:
        raise ValueError("Die Aufnahme muss zwischen 1 Byte und 1 GB groß sein.")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256 or ""):
        raise ValueError("Die Prüfsumme der Aufnahme fehlt.")
    if extension not in lore.AUDIO_EXTENSIONS:
        raise ValueError("Dieses Audioformat wird nicht unterstützt.")
    title = title.strip()[:200] or "Android-Sitzung"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=lore.data_dir(), suffix=".upload", delete=False) as output:
            temporary = Path(output.name)
            checksum = hashlib.sha256()
            remaining = size
            while remaining:
                block = source.read(min(65536, remaining))
                if not block:
                    raise ValueError("Übertragung abgebrochen. Bitte erneut senden.")
                output.write(block)
                checksum.update(block)
                remaining -= len(block)
        if checksum.hexdigest() != expected_sha256:
            raise ValueError("Die Aufnahme ist unvollständig angekommen. Bitte erneut senden.")
        session_id = expected_sha256[:32]
        with session_lock(session_id):
            folder = lore.session_dir(session_id)
            if (folder / "session.json").is_file():
                existing = lore.load(session_id)
                if existing.get("upload_sha256") != expected_sha256:
                    raise ValueError("Die Sitzungskennung ist bereits belegt.")
                return existing, False
            audio_name = "android" + extension
            temporary.replace(folder / audio_name)
            temporary = None
            session = lore.new_session(title, session_id)
            session.update(audio=audio_name, origin="android", upload_sha256=expected_sha256)
            lore.save(session)
            return session, True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_pipeline(session, transcribe_audio=True):
    def progress(message):
        session["processing"] = {"state": "running", "message": message}
        lore.save(session)
    try:
        if transcribe_audio:
            progress("Audio wird lokal transkribiert …")
            lore.transcribe(session)
        progress("Transkript wird lokal ausgewertet …")
        lore.analyze(session, progress=progress)
        session["processing"] = {"state": "ready", "message": "Entwurf bereit · bitte als DM prüfen."}
    except Exception as exc:
        message = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Auswertung fehlgeschlagen. Sprachmodell, Audioformat und lokale KI-Verbindung prüfen. Das bisherige Transkript bleibt erhalten."
        session["processing"] = {"state": "error", "message": message}
    finally:
        lore.save(session)


def start_processing(session_id, transcribe_audio=True):
    lock = session_lock(session_id)
    lock.__enter__()
    try:
        session = lore.load(session_id)
        if transcribe_audio and not session.get("audio"):
            raise ValueError("Bitte zuerst eine Aufnahme vom Android-Gerät übertragen oder am Desktop importieren.")
        if not transcribe_audio and not session.get("transcript", "").strip():
            raise ValueError("Bitte zuerst ein Transkript speichern.")
        session["processing"] = {"state": "running", "message": "Auswertung wird gestartet …"}
        lore.save(session)
        def work():
            try:
                run_pipeline(session, transcribe_audio)
            finally:
                lock.__exit__(None, None, None)
        worker = threading.Thread(target=work, name="Tormentor-Lore", daemon=True)
        worker.start()
        return worker
    except BaseException:
        lock.__exit__(None, None, None)
        raise
