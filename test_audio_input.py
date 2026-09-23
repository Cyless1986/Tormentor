import ast
import json
import os
import re
import sys
import tempfile
import threading
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import audio_input
import lore


class AudioSharingTest(unittest.TestCase):
    def test_recording_and_voice_share_one_microphone_and_unsubscribe_independently(self):
        opened = []
        class Stream:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]
                self.closed = False
                opened.append(self)
            def start(self): pass
            def stop(self): pass
            def close(self): self.closed = True
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"TORMENTOR_LORE_DIR": directory}), patch.dict(sys.modules, {"sounddevice": types.SimpleNamespace(RawInputStream=Stream)}), patch.object(audio_input, "microphone", audio_input.SharedInput()):
            heard = []
            unsubscribe = audio_input.microphone.subscribe(lambda audio, status: heard.append(audio))
            item = lore.new_session("Session 4")
            recorder = lore.Recorder(item)
            self.assertEqual(len(opened), 1)
            opened[0].callback(b"\x01\x00" * 1600, 1600, None, False)
            unsubscribe()
            self.assertFalse(opened[0].closed)
            opened[0].callback(b"\x02\x00" * 1600, 1600, None, False)
            recorder.stop()
            self.assertTrue(opened[0].closed)
            self.assertEqual(len(heard), 1)
            with wave.open(str(lore.session_dir(item["id"]) / item["audio"])) as audio:
                self.assertEqual(audio.getnframes(), 3200)
                self.assertEqual(audio.readframes(3200), b"\x01\x00" * 1600 + b"\x02\x00" * 1600)

    def test_desktop_accepts_direct_and_two_stage_recording_commands(self):
        # Isolate the real dispatcher without initializing GUI, API clients or audio hardware.
        tree = ast.parse((Path(__file__).parent / "main.py").read_text(encoding="utf-8-sig"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_cortana")
        for phrases in (["cortana starte aufnahme", "cortana beende aufnahme"], ["cortana", "starte aufnahme", "kortana", "beende die aufnahme"]):
            stop = threading.Event()
            pending = iter(phrases)
            actions = []
            count = [0]
            class Recognizer:
                def listen(self, source, **kwargs): return next(pending)
                def recognize_google(self, audio, **kwargs):
                    count[0] += 1
                    if count[0] == len(phrases): stop.set()
                    return audio
            class Source:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            namespace = {"sr": types.SimpleNamespace(Recognizer=Recognizer), "re": re, "os": os,
                         "resource_path": lambda path: path, "play_voice_file": lambda *args, **kwargs: None}
            exec(compile(ast.Module(body=[function], type_ignores=[]), "main.py", "exec"), namespace)
            with patch.object(audio_input, "speech_source", Source), patch("os.path.isfile", return_value=True):
                namespace["run_cortana"](stop, lambda text: None, actions.append)
            self.assertEqual(actions, ["start", "stop"])


if __name__ == "__main__":
    unittest.main()
