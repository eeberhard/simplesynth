import pyaudio
import numpy as np
import time


class Synth:
    def __init__(self, notes=None, volumes=None, update_hz=60):
        self.master_volume = 1

        if notes is not None:
            self.notes = notes
        else:
            self.notes = []

        if volumes is not None and len(volumes) == len(self.notes):
            self.volumes = volumes
        else:
            self.volumes = [0.5 for _ in self.notes]

        self._p = pyaudio.PyAudio()
        self._fs = 44100
        self._frame_size = int(60 * self._fs / update_hz)

        self._stream = None
        self._status = pyaudio.paComplete

        self.frame = np.zeros(self._frame_size).astype(np.float32)
        self.frame_time = np.arange(self._frame_size)/self._fs

        self._xfade_size = int(10 * self._fs / 100)
        self._last_frame_cross = np.zeros(self._xfade_size).astype(np.float32)

    def start(self):
        self._status = pyaudio.paContinue

        self._stream = self._p.open(format=pyaudio.paFloat32,
                                    output=True,
                                    channels=1,
                                    rate=self._fs,
                                    frames_per_buffer=self._frame_size,
                                    stream_callback=self.stream_frame)

        self._stream.start_stream()

    def stop(self):
        self.master_volume = 0.0
        time.sleep(self._frame_size / self._fs)
        self._status = pyaudio.paComplete
        if self._stream.is_active():
            self._stream.stop_stream()
            self._stream.close()
            self._p.terminate()

    def find_transition_point(self, sample):
        diff = np.abs(sample)

        start = 0
        step = int(self._xfade_size / 100)

        while start + step < len(diff):

            x = start + np.argmin(diff[start:start + step])
            if diff[x] < 0.01 and sample[x] < sample[x + 1] and x <= (self._xfade_size / 2):
                return x

            start += step

        return 0

    def gen_tone(self, f, samples, padding=0):
        t = np.arange(-padding, samples + padding) * f / self._fs

        return np.sin(2 * np.pi * t).astype(np.float32)

    def gen_tones(self, samples):
        next_frame = np.zeros(self._xfade_size + samples + self._xfade_size).astype(np.float32)

        for n in range(len(self.notes)):
            next_frame += self.volumes[n] * self.gen_tone(self.notes[n], samples, padding=self._xfade_size)

        if len(self.notes) > 0:
            next_frame = self.master_volume * np.divide(next_frame, len(self.notes))

        cross = self.find_transition_point(self._last_frame_cross)

        if cross > 0:
            fader = np.arange(2*cross)/(2*cross).astype(np.float32)
            start = np.multiply(self._last_frame_cross[0:2*cross], (1 - fader))
            start += np.multiply(next_frame[self._xfade_size-cross:self._xfade_size+cross], fader)

            self.frame = np.concatenate(
                [start, next_frame[self._xfade_size+cross:self._xfade_size+samples-cross]]).astype(np.float32)
            self._last_frame_cross = next_frame[self._xfade_size+samples-cross:-cross].copy()
        else:
            self.frame = next_frame[self._xfade_size:self._xfade_size+samples].copy()
            self._last_frame_cross = next_frame[-self._xfade_size:].copy()

        # start = next_frame[0:self._cross_fade_size].copy()
        #
        # start = np.multiply(start, self._cross_fade)
        # start += np.multiply(self._last_frame_cross, 1 - self._cross_fade)
        #
        # frame[0:self._cross_fade_size] = start
        #
        # self.frame = frame[0:-self._cross_fade_size]
        # self._last_frame_cross = frame[-self._cross_fade_size:]

        return self.frame

    def stream_frame(self, in_data, frame_count, time_info, status_flags):
        frame = self.gen_tones(frame_count)

        return frame.tobytes(), self._status


if __name__ == "__main__":

    synth = Synth([440.0])
    synth.start()

    input()

    synth.stop()
