from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from synth import Synth


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
    def __init__(self, parent=None):
        super(Frequencies, self).__init__(parent=parent)

        self.frequencies = []
        self.amplitudes = []

        # self.group = QGroupBox()

        self.freq_layout = QVBoxLayout()
        self.btn_add_freq = QPushButton('+')
        self.btn_add_freq.clicked.connect(self.add_frequency)
        self.freq_layout.addWidget(self.btn_add_freq)
        self.stretch = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.freq_layout.addItem(self.stretch)
        self.setLayout(self.freq_layout)
        self.setMinimumWidth(400)

        # self.group.setLayout(self.freq_layout)
        # self.scroll = QScrollArea()
        # self.scroll.setWidget(self.group)
        # self.scroll.setWidgetResizable(True)
        # self.scroll.setFixedHeight(400)
        # self.scroll.setMinimumWidth(400)
        # self.top_layout = QVBoxLayout(self)
        # self.top_layout.addWidget(self.scroll)

    def add_frequency(self):
        if self.freq_layout.count() < 8:
            self.freq_layout.removeItem(self.stretch)
            self.freq_layout.addWidget(FrequencyPicker(self))
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
    def __init__(self, parent=None):
        super(FrequencyPicker, self).__init__(parent=parent)

        self.parent = parent

        self.layout = QHBoxLayout()

        self.freq = 0
        self.amp = 0.5

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
        self.dial.setValue(50)
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
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)

        self.resize(600, 600)

        self.layout = QHBoxLayout()

        self.plot = WavePlot(self)
        self.layout.addWidget(self.plot)

        self.freq = Frequencies(self)
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

    window = MainWindow()
    window.show()

    timer = pg.Qt.QtCore.QTimer()
    timer.timeout.connect(window.update)
    timer.start(50)

    app.exec_()
