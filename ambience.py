import pyaudio
import numpy as np
import time
import random


class Scales:
    def __init__(self):
        self.notes = [261.6256, 277.1826, 293.6648, 311.1270, 329.6276, 349.2282, 369.9944,
                      391.9954, 415.3047, 440.0000, 466.1638, 493.8833]

        self.notes_8va = [n*2 for n in self.notes]
        self.notes_8vb = [n/2 for n in self.notes]

        self.notes = self.notes_8vb + self.notes

        self.intervals = {'major': (0, 2, 4, 5, 7, 9, 11, 12),
                          'minor': (0, 2, 3, 5, 7, 8, 10, 12),
                          'seven': (0, 2, 4, 5, 7, 9, 10, 12)}

        self.roots = {'C': 0,
                      'Db': 1,
                      'D': 2,
                      'Eb': 3,
                      'E': 4,
                      'F': 5,
                      'Gb': 6,
                      'G': 7,
                      'Ab': 8,
                      'A': 9,
                      'Bb': 10,
                      'B': 11}

    def gen_scale(self, root='C', interval='major'):
        return [self.notes[i + self.roots[root]] for i in self.intervals[interval]]


class Synth:
    def __init__(self):
        self.volume = 0.5
        self.bpm = 12

        self._p = pyaudio.PyAudio()
        self._fs = 44100
        self._frame_size = int(60 * self._fs / self.bpm)

        self._stream = None
        self._status = pyaudio.paComplete

        self.scales = Scales()
        self.scale = self.scales.gen_scale('C', 'major')

        self.cross_fade_size = int(25 * self._frame_size / 100)
        self.cross_fade = np.arange(self.cross_fade_size) / self.cross_fade_size

        self.last_frame = np.zeros(self._frame_size + self.cross_fade_size)

        self.plot_callback = None

    def start(self):
        self._status = pyaudio.paContinue

        self._stream = self._p.open(format=pyaudio.paFloat32,
                                    output=True,
                                    channels=1,
                                    rate=self._fs,
                                    frames_per_buffer=self._frame_size,
                                    stream_callback=self.callback)

        self._stream.start_stream()

    def stop(self):
        self.volume = 0.0
        time.sleep(self._frame_size / self._fs)
        self._status = pyaudio.paComplete
        if self._stream.is_active():
            self._stream.stop_stream()
            self._stream.close()
            self._p.terminate()

    def set_volume(self, volume):
        if volume >= 1.0:
            self.volume = 1.0
        elif volume <= 0.0:
            self.volume = 0.0
        else:
            self.volume = volume

    def set_scale(self, root, interval):
        self.scale = self.scales.gen_scale(root, interval)

    def set_bpm(self, bpm):
        self.bpm = bpm
        self._frame_size = int(60 * self._fs / self.bpm)

    def gen_tone(self, f, samples):
        t = np.arange(samples + self.cross_fade_size) * f / self._fs

        frame = self.volume * (np.sin(2 * np.pi * t)).astype(np.float32)

        start = frame[0:self.cross_fade_size].copy()

        start = np.multiply(start, self.cross_fade)
        start += np.multiply(self.last_frame[-self.cross_fade_size:], 1 - self.cross_fade)

        frame[0:self.cross_fade_size] = start

        self.last_frame = frame

        return frame

    def gen_tones_2(self, f1, f2, samples):
        last = self.last_frame.copy()
        tone1 = self.gen_tone(f1, samples)
        self.last_frame = last
        tone2 = self.gen_tone(f2, samples)

        frame = (tone1 + tone2) / 2
        self.last_frame = frame

        return frame

    def gen_tones_3(self, f1, f2, f3, samples):
        last = self.last_frame.copy()
        tone1 = self.gen_tone(f1, samples)
        self.last_frame = last
        tone2 = self.gen_tone(f2, samples)
        self.last_frame = last
        tone3 = self.gen_tone(f3, samples)

        frame = (tone1 + tone2 + tone3) / 3
        self.last_frame = frame

        return frame

    def callback(self, in_data, frame_count, time_info, status_flags):
        # frame = self.gen_tone(random.choice(self.scale), frame_count)
        # frame = self.gen_tones_2(self.scale[0], random.choice(self.scale), frame_count)
        frame = self.gen_tones_3(self.scale[0], random.choice(self.scale), random.choice(self.scale), frame_count)

        if self.plot_callback is not None:
            self.plot_callback(frame)

        r = random.randint(0, 100)
        if r < 5:
            self.set_scale(random.choice([r for r in self.scales.roots.keys()]),
                           random.choice([r for r in self.scales.intervals.keys()]))

        return frame.tobytes(), self._status


if __name__ == "__main__":
    synth = Synth()
    synth.start()

    while True:
        k = input('v - volume, s - scale, q - quit: ')

        if k == 'v':
            k = input('volume [0.0 - 1.0]: ')
            try:
                synth.volume = float(k)
            except Exception as e:
                print(e)
                continue
        elif k == 's':
            k = input('scale (e.g. C major): ')
            inp = k.split()
            try:
                synth.set_scale(inp[0], inp[1])
            except Exception as e:
                print(e)
                continue
        elif k == 'q':
            break
        else:
            inp = k.split()
            try:
                synth.set_scale(inp[0], inp[1])
            except Exception as e:
                print(e)
                continue

    synth.stop()
