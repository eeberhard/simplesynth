from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from synth import Synth, square_wave, triangle_wave, sawtooth_wave
import sys


class WavePlot(pg.PlotWidget):
    def __init__(self, parent=None):
        super(WavePlot, self).__init__(parent=parent)

        pg.setConfigOptions(antialias=True)

        self.setMinimumSize(400, 400)

        self.fs = 44100

        self.wave = self.plot(x=np.arange(self.fs) / self.fs, y=np.zeros(self.fs), pen='r')
        self.enableAutoRange('xy', False)
        self.setXRange(0, 0.05)
        self.setYRange(-1, 1)

    def draw_frequencies(self, frequencies, amplitudes):
        t = np.arange(self.fs) / self.fs
        y = np.zeros(self.fs)
        for n in range(len(frequencies)):
            y += amplitudes[n] * np.sin(2 * np.pi * t * frequencies[n])

        if len(frequencies) > 0:
            y /= len(frequencies)

        self.wave.setData(x=t, y=y)


class Frequencies(QWidget):
    def __init__(self, parent=None, frequencies=None, amplitudes=None):
        super(Frequencies, self).__init__(parent=parent)

        if frequencies is None:
            self.frequencies = []
        else:
            self.frequencies = frequencies
        if amplitudes is None:
            self.amplitudes = []
        else:
            self.amplitudes = amplitudes

        self.freq_layout = QVBoxLayout()
        self.btn_add_freq = QPushButton('+')
        self.btn_add_freq.clicked.connect(self.add_frequency)
        self.freq_layout.addWidget(self.btn_add_freq)
        self.stretch = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.freq_layout.addItem(self.stretch)
        self.setLayout(self.freq_layout)
        self.setMinimumWidth(400)

        for note in range(len(self.frequencies)):
            self.add_frequency(self.frequencies[note], self.amplitudes[note])

    def add_frequency(self, freq=None, amp=None):
        if self.freq_layout.count() < 10:
            self.freq_layout.removeItem(self.stretch)
            self.freq_layout.addWidget(FrequencyPicker(self, freq=freq, amp=amp))
            self.freq_layout.addItem(self.stretch)

    def get_frequencies(self):
        frequencies = []
        amplitudes = []
        for child in self.children():
            if isinstance(child, FrequencyPicker):
                if child.freq is not None:
                    frequencies.append(child.freq)
                if child.amp is not None:
                    amplitudes.append(child.amp)

        self.frequencies = frequencies
        self.amplitudes = amplitudes

        return frequencies, amplitudes


class FrequencyPicker(QWidget):
    def __init__(self, parent=None, freq=None, amp=None):
        super(FrequencyPicker, self).__init__(parent=parent)

        self.parent = parent

        self.layout = QHBoxLayout()

        if freq is None:
            self.freq = 0
        else:
            self.freq = freq

        if amp is None:
            self.amp = 0.5
        else:
            self.amp = amp

        self.text_box = QLineEdit()
        self.text_box.setMaximumHeight(50)
        self.text_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout.addWidget(self.text_box)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(100)
        self.slider.setMaximum(10000)
        self.slider.setMaximumHeight(50)
        self.slider.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.layout.addWidget(self.slider)

        self.dial = QDial()
        self.dial.setMinimum(0)
        self.dial.setMaximum(100)
        self.dial.setValue(self.amp * 100)
        self.dial.setMaximumHeight(50)
        self.dial.setMaximumWidth(50)
        self.dial.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.layout.addWidget(self.dial)

        self.btn_remove = QPushButton('-')
        self.dial.setMaximumHeight(50)
        self.dial.setMaximumWidth(50)
        self.btn_remove.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.layout.addWidget(self.btn_remove)

        self.setLayout(self.layout)

        self.text_box.setText(f'{self.freq}')
        self.update_slider()

        self.text_box.editingFinished.connect(self.update_slider)
        self.slider.valueChanged.connect(self.update_text)
        self.dial.valueChanged.connect(self.update_dial)
        self.btn_remove.clicked.connect(self.deleteLater)

    def update_text(self, val):
        self.freq = val / 10
        self.text_box.setText(f'{val / 10:4.1f}')

    def update_slider(self):
        try:
            self.freq = float(self.text_box.text())
            self.slider.setValue(int(10 * self.freq))
        except ValueError:
            pass

    def update_dial(self):
        self.amp = self.dial.value() / 100


class MainWindow(QWidget):
    def __init__(self, parent=None, notes=None, volumes=None):
        super(MainWindow, self).__init__(parent=parent)

        self.resize(800, 600)

        self.layout = QHBoxLayout()

        self.plot = WavePlot(self)
        self.layout.addWidget(self.plot)

        self.freq = Frequencies(self, frequencies=notes, amplitudes=volumes)
        self.layout.addWidget(self.freq)

        self.setLayout(self.layout)

        self.synth = Synth([], update_hz=1000)
        self.synth.start()

    def update(self):
        notes, volumes = self.freq.get_frequencies()
        self.synth.notes = notes
        self.synth.volumes = volumes
        self.plot.draw_frequencies(notes, volumes)


if __name__ == "__main__":
    app = QApplication([])

    if len(sys.argv) > 1:
        f = 100.0
        if len(sys.argv) > 2:
            try:
                f = float(sys.argv[2])
            except ValueError:
                pass

        if sys.argv[1] == 'full':
            window = MainWindow(notes=[f * h for h in range(1, 9)],
                                volumes=np.zeros(8))
        elif sys.argv[1] == 'odd':
            window = MainWindow(notes=[f * h for h in range(1, 16, 2)],
                                volumes=np.zeros(8))
        elif sys.argv[1] == 'even':
            window = MainWindow(notes=[f * h for h in range(2, 17, 2)],
                                volumes=np.zeros(8))
        elif sys.argv[1] == 'square':
            notes, volumes = square_wave(f=f, order=8)
            window = MainWindow(notes=notes, volumes=volumes)
        elif sys.argv[1] == 'triangle':
            notes, volumes = triangle_wave(f=f, order=8)
            window = MainWindow(notes=notes, volumes=volumes)
        elif sys.argv[1] == 'sawtooth':
            notes, volumes = sawtooth_wave(f=f, order=8)
            window = MainWindow(notes=notes, volumes=volumes)
        else:
            raise Exception(f'Unrecognised input argument {sys.argv[1]}')
    else:
        window = MainWindow()

    window.show()

    timer = pg.Qt.QtCore.QTimer()
    timer.timeout.connect(window.update)
    timer.start(50)

    app.exec_()
