"""One desktop microphone stream for voice commands and full-session recording."""
import queue
import threading


class SharedInput:
    def __init__(self):
        self.lock = threading.RLock()
        self.sinks = ()
        self.stream = None

    def subscribe(self, sink):
        with self.lock:
            self.sinks = (*self.sinks, sink)
            if self.stream is None:
                import sounddevice as sd
                def callback(indata, frames, time_info, status):
                    audio = bytes(indata)
                    for subscriber in self.sinks:
                        subscriber(audio, status)
                try:
                    self.stream = sd.RawInputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1600, callback=callback)
                    self.stream.start()
                except Exception:
                    self.sinks = tuple(value for value in self.sinks if value is not sink)
                    if self.stream is not None:
                        self.stream.close()
                    self.stream = None
                    raise
        def unsubscribe():
            with self.lock:
                self.sinks = tuple(value for value in self.sinks if value is not sink)
                if not self.sinks and self.stream is not None:
                    try:
                        self.stream.stop()
                    finally:
                        self.stream.close()
                        self.stream = None
        return unsubscribe


microphone = SharedInput()


def speech_source():
    import speech_recognition as sr
    class Source(sr.AudioSource):
        def __init__(self):
            self.SAMPLE_RATE, self.SAMPLE_WIDTH, self.CHUNK = 16000, 2, 1600
            self.stream = None
            self.pending = bytearray()
            self.blocks = queue.Queue(maxsize=40)

        def __enter__(self):
            def receive(audio, status):
                try:
                    self.blocks.put_nowait(audio)
                except queue.Full:
                    try:
                        self.blocks.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self.blocks.put_nowait(audio)
                    except queue.Full:
                        pass
            self.unsubscribe = microphone.subscribe(receive)
            self.stream = self
            return self

        def read(self, size):
            required = size * self.SAMPLE_WIDTH
            while len(self.pending) < required:
                try:
                    self.pending.extend(self.blocks.get(timeout=3))
                except queue.Empty:
                    raise OSError("Das Mikrofon liefert keine Audiodaten.")
            data = bytes(self.pending[:required])
            del self.pending[:required]
            return data

        def __exit__(self, *args):
            self.unsubscribe()
            self.stream = None
    return Source()
