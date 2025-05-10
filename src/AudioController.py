# audio_controller.py
import sounddevice as sd
import numpy as np
from typing import Optional

class AudioController:
    def __init__(self, audio: Optional[np.ndarray] = None,
                 samplerate: Optional[float] = None):
        self.audio = audio
        self.samplerate = samplerate
        self.stream = None
        self.current_frame = 0
        self.blocksize = 1024
        self.playing = False

    def set_params(self, audio: np.ndarray, samplerate: float):
        self.audio = audio
        self.samplerate = samplerate
        self.current_frame = 0
        self.playing = False
        if self.stream:
            self.stream.close()
            self.stream = None

    def callback(self, outdata: np.ndarray, frames: int, time, status):
        if not self.playing or self.audio is None:
            outdata[:] = np.zeros((frames, 1))
            raise sd.CallbackStop

        chunk = self.audio[self.current_frame:self.current_frame + frames]
        if len(chunk) < frames:
            chunk = np.pad(chunk, (0, frames - len(chunk)))

        outdata[:] = chunk.reshape(-1, 1)
        self.current_frame += frames

        if self.current_frame >= len(self.audio):
            self.playing = False
            raise sd.CallbackStop

    def reset(self):
        self.playing = False
        self.current_frame = 0
        self.stream.stop()

    def pause(self):
        if self.stream and self.playing:
            self.stream.stop()
            self.playing = False

    def resume(self):
        if self.audio is None or self.samplerate is None:
            raise ValueError("Audio and Sample Rate must be set before playback")

        if self.stream is None:
            self.stream = sd.OutputStream(samplerate=self.samplerate,
                                          channels=1,
                                          callback=self.callback,
                                          blocksize=self.blocksize)
        if not self.playing:
            self.playing = True
            self.stream.start()
