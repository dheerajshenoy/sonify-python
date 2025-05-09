from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QGraphicsView, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsLineItem)
from PyQt6.QtGui import QPixmap, QPen, QKeySequence, QShortcut, QImage, QColor
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThreadPool
import sys
import numpy as np
import cv2
import time
from visound.core.TraversalMode import TraversalMode

class MainWindow(QMainWindow):
    reset_signal = pyqtSignal(bool)
    pause_resume_signal = pyqtSignal(bool)
    def __init__(self):
        super().__init__()

        self._playing = False
        self._paused = False
        self._start_time = 0
        self._traversal_mode = None
        self._pixmap: QPixmap = None
        self._pixmap_item: QGraphicsPixmapItem = None
        self._dpc: float = None
        self._bar_x = 0
        self._FPS = 60

        self._layout = QVBoxLayout()
        self._graphics_view = QGraphicsView()
        self._graphics_scene = QGraphicsScene(self._graphics_view)
        self._layout.addWidget(self._graphics_view)
        widget = QWidget()
        widget.setLayout(self._layout)
        self.setCentralWidget(widget)

        self._bar_color: str = "#00FF00"
        self._bar = QGraphicsLineItem()
        self._bar_pen = QPen(QColor(self._bar_color), 2)
        self._bar.setPen(self._bar_pen)

        self._timer = QTimer()
        self._timer.setInterval(int(1 / self._FPS * 1000))
        self._timer.timeout.connect(self._advance_bar)

        self._handle_keybindings()
        self.show()

    @property
    def dpc(self) -> float:
        return self._dpc

    @dpc.setter
    def dpc(self, d: float) -> None:
        self._dpc = d

    @property
    def bar_color(self) -> str:
        return self._bar_color

    @bar_color.setter
    def bar_color(self, c: str) -> None:
        self._bar_color = c
        self._bar_pen = QPen(QColor(self._bar_color), 2)
        self._bar.setPen(self._bar_pen)

    @property
    def traversal_mode(self) -> TraversalMode:
        return self._traversal_mode

    @traversal_mode.setter
    def traversal_mode(self, mode: TraversalMode) -> None:
        self._traversal_mode = mode

    def _handle_keybindings(self):
        sc_reset = QShortcut(QKeySequence("r"), self)
        sc_reset.activated.connect(self._reset_requested)

        sc_pause_resume = QShortcut(QKeySequence("space"), self)
        sc_pause_resume.activated.connect(self._pause_resume_requested)

    def _pause_resume_requested(self):
        self._playing = not self._playing

        if self._playing:
            self._start_time = time.perf_counter()
            self._timer.start()
        else:
            self._timer.stop()

        self.pause_resume_signal.emit(self._playing)

    def _reset_requested(self):
        self._playing = False
        self._timer.stop()
        self.reset_signal.emit(self._playing)

    def loadImage(self, img_cv: np.ndarray) -> None:
        self._graphics_scene.clear()
        self._height, self._width = img_cv.shape
        bytes_per_line = 3 * self._width
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, self._width, self._height,
                      bytes_per_line, QImage.Format.Format_RGB888)

        self._pixmap = QPixmap.fromImage(qimg)
        self._pixmap_item = QGraphicsPixmapItem(self._pixmap)
        self._graphics_scene.addItem(self._pixmap_item)
        self._graphics_view.setScene(self._graphics_scene)
        self._graphics_scene.addItem(self._bar)

    def init_bar_position(self):

        match self.traversal_mode:

            case TraversalMode.LeftToRight:
                self._bar_x = 0
                self._bar.setLine(self._bar_x, 0, self._bar_x, self._height)

            case TraversalMode.RightToLeft:
                self._bar_x = self.width
                self._bar.setLine(self._bar_x, 0, self._bar_x, self.height)

    def _advance_bar(self):
        elapsed = time.perf_counter() - self._start_time
        match self._traversal_mode:

            case TraversalMode.LeftToRight:
                if self._bar_x < self._pixmap.width():
                    self._bar_x = int(elapsed / self._dpc)
                    self._bar.setLine(self._bar_x, 0, self._bar_x, self._height)
                else:
                    self._playing = False
                    self._timer.stop()

            case TraversalMode.RightToLeft:
                if self._bar_x > 0:
                    self._bar_x = self._width - int(elapsed / self._dpc)
                    self._bar.setLine(self._bar_x, 0, self._bar_x, self._height)
                else:
                    self._playing = False
                    self._timer.stop()
