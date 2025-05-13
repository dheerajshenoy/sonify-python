from PyQt6.QtWidgets import (QWidget, QPushButton, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal

class ScreenRecordDialog(QWidget):
    start_recording_signal = pyqtSignal(bool)

    def __init__(self, parent = None):
        super().__init__(parent)

        self._is_recording = False
        self._init_gui()
        self.show()

    def _init_gui(self) -> None:
        self.layout = QHBoxLayout()

        self.record_btn = QPushButton("Record")
        self.record_btn.clicked.connect(self._start_recording)
        self.layout.addWidget(self.record_btn)
        self.setLayout(self.layout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def _start_recording(self) -> None:
        self._is_recording = not self._is_recording

        if self._is_recording:
            self.record_btn.setText("Stop Recording")
        else:
            self.record_btn.setText("Record")

        self.start_recording_signal.emit(self._is_recording)
