from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QSpinBox, QPushButton

class EffectOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout().addWidget(self.ok_button)

    def get_parameters(self):
        return {}

class CompressorOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compressor Options")
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(-60, 0)
        self.threshold.setValue(-24)
        self.ratio = QDoubleSpinBox()
        self.ratio.setRange(1, 20)
        self.ratio.setValue(2)
        self.layout().insertWidget(0, QLabel("Threshold (dB):"))
        self.layout().insertWidget(1, self.threshold)
        self.layout().insertWidget(2, QLabel("Ratio:"))
        self.layout().insertWidget(3, self.ratio)

    def get_parameters(self):
        return {
            "threshold_db": self.threshold.value(),
            "ratio": self.ratio.value()
        }

class ReverbOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reverb Options")
        self.room_size = QDoubleSpinBox()
        self.room_size.setRange(0.0, 1.0)
        self.room_size.setValue(0.25)
        self.layout().insertWidget(0, QLabel("Room Size:"))
        self.layout().insertWidget(1, self.room_size)

    def get_parameters(self):
        return {"room_size": self.room_size.value()}

class GainOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gain Options")
        self.gain_db = QDoubleSpinBox()
        self.gain_db.setRange(-60, 60)
        self.gain_db.setValue(0)
        self.layout().insertWidget(0, QLabel("Gain (dB):"))
        self.layout().insertWidget(1, self.gain_db)

    def get_parameters(self):
        return {"gain_db": self.gain_db.value()}

class PitchShiftOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pitch Shift Options")
        self.semitones = QDoubleSpinBox()
        self.semitones.setRange(-24, 24)
        self.semitones.setValue(0)
        self.layout().insertWidget(0, QLabel("Semitones:"))
        self.layout().insertWidget(1, self.semitones)

    def get_parameters(self):
        return {"semitones": self.semitones.value()}

class DelayOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delay Options")
        self.delay_seconds = QDoubleSpinBox()
        self.delay_seconds.setRange(0, 5)
        self.delay_seconds.setValue(0.25)
        self.layout().insertWidget(0, QLabel("Delay Time (seconds):"))
        self.layout().insertWidget(1, self.delay_seconds)

    def get_parameters(self):
        return {"delay_seconds": self.delay_seconds.value()}

class DistortionOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distortion Options")
        self.drive = QDoubleSpinBox()
        self.drive.setRange(0.0, 1.0)
        self.drive.setValue(0.5)
        self.layout().insertWidget(0, QLabel("Drive:"))
        self.layout().insertWidget(1, self.drive)

    def get_parameters(self):
        return {"drive": self.drive.value()}

class FilterOptionsDialog(EffectOptionsDialog):
    def __init__(self, filter_type="Lowpass", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{filter_type} Filter Options")
        self.cutoff = QDoubleSpinBox()
        self.cutoff.setRange(20, 20000)
        self.cutoff.setValue(1000)
        self.layout().insertWidget(0, QLabel("Cutoff Frequency (Hz):"))
        self.layout().insertWidget(1, self.cutoff)

    def get_parameters(self):
        return {"cutoff_frequency_hz": self.cutoff.value()}

class ChorusOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chorus Options")
        self.rate = QDoubleSpinBox()
        self.rate.setRange(0.1, 10.0)
        self.rate.setValue(1.5)
        self.depth = QDoubleSpinBox()
        self.depth.setRange(0.0, 1.0)
        self.depth.setValue(0.5)
        self.layout().insertWidget(0, QLabel("Rate (Hz):"))
        self.layout().insertWidget(1, self.rate)
        self.layout().insertWidget(2, QLabel("Depth:"))
        self.layout().insertWidget(3, self.depth)

    def get_parameters(self):
        return {"rate_hz": self.rate.value(), "depth": self.depth.value()}

class PhaserOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Phaser Options")
        self.rate = QDoubleSpinBox()
        self.rate.setRange(0.1, 10.0)
        self.rate.setValue(1.0)
        self.depth = QDoubleSpinBox()
        self.depth.setRange(0.0, 1.0)
        self.depth.setValue(0.5)
        self.layout().insertWidget(0, QLabel("Rate (Hz):"))
        self.layout().insertWidget(1, self.rate)
        self.layout().insertWidget(2, QLabel("Depth:"))
        self.layout().insertWidget(3, self.depth)

    def get_parameters(self):
        return {"rate_hz": self.rate.value(), "depth": self.depth.value()}

class LimiterOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Limiter Options")
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(-60, 0)
        self.threshold.setValue(-1)
        self.layout().insertWidget(0, QLabel("Threshold (dB):"))
        self.layout().insertWidget(1, self.threshold)

    def get_parameters(self):
        return {"threshold_db": self.threshold.value()}

class LadderFilterOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ladder Filter Options")
        self.cutoff = QDoubleSpinBox()
        self.cutoff.setRange(20, 20000)
        self.cutoff.setValue(1000)
        self.resonance = QDoubleSpinBox()
        self.resonance.setRange(0.0, 4.0)
        self.resonance.setValue(0.5)
        self.layout().insertWidget(0, QLabel("Cutoff Frequency (Hz):"))
        self.layout().insertWidget(1, self.cutoff)
        self.layout().insertWidget(2, QLabel("Resonance:"))
        self.layout().insertWidget(3, self.resonance)

    def get_parameters(self):
        return {"cutoff_hz": self.cutoff.value(), "resonance": self.resonance.value()}

class ConvolutionOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Convolution Options")
        # For real use: add a file picker for impulse response file
        self.layout().insertWidget(0, QLabel("No options (impulse loaded externally)."))

    def get_parameters(self):
        return {}

class MixOptionsDialog(EffectOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mix Options")
        self.balance = QDoubleSpinBox()
        self.balance.setRange(0.0, 1.0)
        self.balance.setValue(0.5)
        self.layout().insertWidget(0, QLabel("Balance (0 = dry, 1 = wet):"))
        self.layout().insertWidget(1, self.balance)

    def get_parameters(self):
        return {"wet_level": self.balance.value()}

