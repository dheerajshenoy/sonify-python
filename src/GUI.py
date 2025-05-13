from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel,
    QPushButton, QVBoxLayout, QMessageBox,
    QHBoxLayout, QApplication, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsLineItem, QMenuBar,
    QGraphicsEllipseItem, QMenu, QFileDialog, QToolBar,
    QComboBox, QLineEdit, QColorDialog)
from GraphicsView import GraphicsView
from PyQt6.QtGui import QPixmap, QPen, QKeySequence, QShortcut, QImage, QColor, QAction
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThreadPool
import sys
import numpy as np
import cv2
import time
import soundfile as sf
import os
from pedalboard import (Pedalboard, Compressor, Reverb, Phaser, PitchShift,
    Delay, Distortion, Chorus, Limiter, LadderFilter, Mix, Convolution)
from typing import Dict

from visound.core.TraversalMode import TraversalMode
from visound.core.sonify import Sonify

from DimensionBox import DimensionDialog
from AudioController import AudioController
from EffectsDialog import *
from ScreenRecordDialog import ScreenRecordDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._width = 0
        self._height = 0
        self._playable = False
        self._playing = False
        self._paused = False
        self._start_time = 0
        self._traversal_mode = None
        self._pixmap: QPixmap = None
        self._pixmap_item: QGraphicsPixmapItem = None
        self._dpc: float = None
        self._bar_x = 0
        self._bar_y = 0
        self._FPS = 60
        self._audio = None
        self._audio_controller = AudioController()
        self._pedalboard = Pedalboard()
        self._active_effects = {}
        self._capture_dir = None
        self._capture_index = 0
        self.sonify_obj = None

        self._layout = QVBoxLayout()
        self._graphics_view = GraphicsView()
        self._graphics_scene = QGraphicsScene(self._graphics_view)
        self._layout.addWidget(self._graphics_view)
        widget = QWidget()
        widget.setLayout(self._layout)
        self.setCentralWidget(widget)

        self._bar_color: str = "#00FF00"
        self._bar = QGraphicsLineItem()
        self._bar_pen = QPen(QColor(self._bar_color), 2)
        self._bar.setPen(self._bar_pen)

        self._circle = QGraphicsEllipseItem()
        self._circle.setPen(self._bar_pen)

        self._timer = QTimer()
        self._timer.setInterval(int(1 / self._FPS * 1000))
        self._timer.timeout.connect(self._advance_bar)

        self._init_toolbar()
        self._init_menubar()
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
            self._audio_controller.resume()
        else:
            self._audio_controller.pause()
            self._timer.stop()

    def _reset_requested(self):
        self._playing = False
        self._audio_controller.reset()
        self.bar_reset()
        self._timer.stop()

    def loadImage(self, img_cv: np.ndarray) -> None:
        """
        Load the image to the GUI
        """
        self._graphics_scene.removeItem(self._pixmap_item)
        bytes_per_line = 3 * self._width
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, self._width, self._height,
                      bytes_per_line, QImage.Format.Format_RGB888)

        self._pixmap = QPixmap.fromImage(qimg)
        self._pixmap_item = QGraphicsPixmapItem(self._pixmap)
        self._graphics_scene.addItem(self._pixmap_item)
        self._graphics_view.setScene(self._graphics_scene)
        self._bar.setZValue(1)

    def init_bar_position(self):
        """
        Initialize the position of the bar depending on the
        mode of traversal
        """
        match self._traversal_mode:

            case TraversalMode.LeftToRight:
                self._bar_x = 0
                self._bar.setLine(self._bar_x, 0, self._bar_x, self._height)
                self._graphics_scene.removeItem(self._circle)
                self._graphics_scene.addItem(self._bar)

            case TraversalMode.RightToLeft:
                self._bar_x = self.width
                self._bar.setLine(self._bar_x, 0, self._bar_x, self.height)
                self._graphics_scene.removeItem(self._circle)
                self._graphics_scene.addItem(self._bar)

            case TraversalMode.TopToBottom:
                self._bar_y = 0
                self._bar.setLine(0, self._bar_y, self._width, self._bar_y)
                self._graphics_scene.removeItem(self._circle)
                self._graphics_scene.addItem(self._bar)

            case TraversalMode.BottomToTop:
                self._bar_y = self._height
                self._bar.setLine(0, self._bar_y, self._width, self._bar_y)
                self._graphics_scene.removeItem(self._circle)
                self._graphics_scene.addItem(self._bar)

            case TraversalMode.CircleInward:
                self._center = (self._width // 2, self._height // 2)
                self._max_radius = int(np.hypot(self._center[0], self._center[1]))
                self._circle.setRect(
                    self._center[1] - self._max_radius,
                    self._center[0] - self._max_radius,
                    2 * self._max_radius,
                    2 * self._max_radius)
                self._graphics_scene.removeItem(self._bar)
                self._graphics_scene.addItem(self._circle)

            case TraversalMode.CircleOutward:
                self._center = (self._width // 2, self._height // 2)
                self._max_radius = int(np.hypot(self._center[0], self._center[1]))
                self._graphics_scene.removeItem(self._bar)
                self._graphics_scene.addItem(self._circle)

    def _advance_bar(self):
        """
        Advance the bar every frame in sync with the audio
        """
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

            case TraversalMode.TopToBottom:
                if self._bar_y < self._height:
                    self._bar_y = int(elapsed / self._dpc)
                    self._bar.setLine(0, self._bar_y, self._width, self._bar_y)
                else:
                    self._playing = False
                    self._timer.stop()

            case TraversalMode.BottomToTop:
                if self._bar_y >= 0:
                    self._bar_y = self._height - int(elapsed / self._dpc)
                    self._bar.setLine(0, self._bar_y, self._width, self._bar_y)
                else:
                    self._playing = False
                    self._timer.stop()

            case TraversalMode.CircleInward:
                self._radius = self._max_radius - int(elapsed / self._dpc)

                if self._radius > 0:
                    self._circle.setRect(
                        self._center[1] - self._radius,
                        self._center[0] - self._radius,
                        2 * self._radius,
                        2 * self._radius)
                else:
                    self._playing = False
                    self._timer.stop()

            case TraversalMode.CircleOutward:
                self._radius = int(elapsed / self._dpc)

                if self._radius < self._max_radius:
                    self._circle.setRect(
                        self._center[1] - self._radius,
                        self._center[0] - self._radius,
                        2 * self._radius,
                        2 * self._radius)
                else:
                    self._playing = False
                    self._timer.stop()

    def _gui_open_image(self) -> bool:
        """
        Open file dialog to get the path of the image and
        load it as a np.ndarray through opencv
        """
        self._filename, _ = QFileDialog.getOpenFileName(self,
                                                        filter="Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)")
        if self._filename != "":
            db = DimensionDialog()
            if db.exec():
                self._width, self._height = db.get_dimensions()
                self._dimension = (self._height, self._width)
            img = cv2.imread(self._filename, cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (self._width, self._height))
            self.loadImage(img_cv=img)
            return True

        return False

    def _init_menubar(self) -> None:
        """
        Initialize the menubar
        """
        self.menubar = self.menuBar()

        # File Menu
        self.menu__file = QMenu("File")

        self.menu__file__open = QAction("Open Image")
        self.menu__file.addAction(self.menu__file__open)
        self.menu__file__open.triggered.connect(self._gui_open_image)

        self.menu__file__save_audio = QAction("Save Audio")
        self.menu__file.addAction(self.menu__file__save_audio)
        self.menu__file__save_audio.triggered.connect(self._save_audio)

        self.menu__file__exit = QAction("Exit")
        self.menu__file.addAction(self.menu__file__exit)
        self.menu__file__exit.triggered.connect(lambda: QApplication.exit())

        self.menu__edit = QMenu("Edit")

        self.menu__edit__effects = QMenu("Effects")

        self.effects__compressor = QAction("Compressor")
        self.effects__compressor.setCheckable(True)

        self.effects__reverb = QAction("Reverb")
        self.effects__reverb.setCheckable(True)

        self.effects__phaser = QAction("Phaser")  # Corrected from "Phaseshift" to "Phaser"
        self.effects__phaser.setCheckable(True)

        self.effects__chorus = QAction("Chorus")
        self.effects__chorus.setCheckable(True)

        self.effects__delay = QAction("Delay")
        self.effects__delay.setCheckable(True)

        self.effects__distortion = QAction("Distortion")
        self.effects__distortion.setCheckable(True)

        self.effects__gain = QAction("Gain")
        self.effects__gain.setCheckable(True)

        self.effects__highpass = QAction("Highpass Filter")
        self.effects__highpass.setCheckable(True)

        self.effects__lowpass = QAction("Lowpass Filter")
        self.effects__lowpass.setCheckable(True)

        self.effects__ladder = QAction("Ladder Filter")
        self.effects__ladder.setCheckable(True)

        self.effects__limiter = QAction("Limiter")
        self.effects__limiter.setCheckable(True)

        self.effects__pitchshift = QAction("Pitch Shift")
        self.effects__pitchshift.setCheckable(True)

        self.effects__convolution = QAction("Convolution")
        self.effects__convolution.setCheckable(True)

        self.effects__mix = QAction("Mix")
        self.effects__mix.setCheckable(True)

        self.menu__edit__effects.addAction(self.effects__compressor)
        self.menu__edit__effects.addAction(self.effects__reverb)
        self.menu__edit__effects.addAction(self.effects__phaser)
        self.menu__edit__effects.addAction(self.effects__chorus)
        self.menu__edit__effects.addAction(self.effects__delay)
        self.menu__edit__effects.addAction(self.effects__distortion)
        self.menu__edit__effects.addAction(self.effects__gain)
        self.menu__edit__effects.addAction(self.effects__highpass)
        self.menu__edit__effects.addAction(self.effects__lowpass)
        self.menu__edit__effects.addAction(self.effects__ladder)
        self.menu__edit__effects.addAction(self.effects__limiter)
        self.menu__edit__effects.addAction(self.effects__pitchshift)
        self.menu__edit__effects.addAction(self.effects__convolution)
        self.menu__edit__effects.addAction(self.effects__mix)

        self._setup_effect_actions()

        self.menu__edit.addMenu(self.menu__edit__effects)

        self.menu__view = QMenu("View")

        self.menu__view__toolbar = QAction("Toolbar")
        self.menu__view__toolbar.setCheckable(True)
        self.menu__view__toolbar.setChecked(self._toolbar.isVisible())
        self.menu__view__toolbar.triggered.connect(lambda b: self._toolbar.setVisible(b))

        self.menu__view.addAction(self.menu__view__toolbar)

        self.menu__tools = QMenu("Tools")

        self.action__screenrecord = QAction("Screen Record")
        self.menu__tools.addAction(self.action__screenrecord)
        self.action__screenrecord.triggered.connect(self._screen_record)


        self.menubar.addMenu(self.menu__file)
        self.menubar.addMenu(self.menu__edit)
        self.menubar.addMenu(self.menu__view)
        self.menubar.addMenu(self.menu__tools)

        self.setMenuBar(self.menubar)

    def _setup_effect_actions(self):
        # Wire actions to effect methods
        self.effects__compressor.triggered.connect(self._add_compressor)
        self.effects__reverb.triggered.connect(self._add_reverb)
        self.effects__gain.triggered.connect(self._add_gain)
        self.effects__pitchshift.triggered.connect(self._add_pitchshift)
        self.effects__delay.triggered.connect(self._add_delay)
        self.effects__distortion.triggered.connect(self._add_distortion)
        self.effects__chorus.triggered.connect(self._add_chorus)
        self.effects__limiter.triggered.connect(self._add_limiter)
        self.effects__ladder.triggered.connect(self._add_ladder_filter)
        self.effects__convolution.triggered.connect(self._add_convolution)
        self.effects__mix.triggered.connect(self._add_mix)

    def _add_compressor(self, is_active: bool):
        dialog = CompressorOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Compressor(**params)
            self._pedalboard.append(effect)
            print("Added Compressor with:", params)

    def _add_reverb(self):
        dialog = ReverbOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Reverb(**params)
            self._pedalboard.append(effect)
            print("Added Reverb with:", params)

    def _add_gain(self):
        dialog = GainOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Gain(**params)
            self._pedalboard.append(effect)
            print("Added Gain with:", params)

    def _add_pitchshift(self):
        dialog = PitchShiftOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = PitchShift(**params)
            self._pedalboard.append(effect)
            print("Added Pitch Shift with:", params)

    def _add_delay(self):
        dialog = DelayOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Delay(**params)
            self._pedalboard.append(effect)
            print("Added Delay with:", params)

    def _add_distortion(self):
        dialog = DistortionOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Distortion(**params)
            self._pedalboard.append(effect)
            print("Added Distortion with:", params)

    def _add_chorus(self):
        dialog = ChorusOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Chorus(**params)
            self._pedalboard.append(effect)
            print("Added Chorus with:", params)

    def _add_phaser(self):
        dialog = PhaserOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Phaser(**params)
            self._pedalboard.append(effect)
            print("Added Phaser with:", params)

    def _add_limiter(self):
        dialog = LimiterOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Limiter(**params)
            self._pedalboard.append(effect)
            print("Added Limiter with:", params)

    def _add_ladder_filter(self):
        dialog = LadderFilterOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = LadderFilter(**params)
            self._pedalboard.append(effect)
            print("Added Ladder Filter with:", params)

    def _add_convolution(self):
        dialog = ConvolutionOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Convolution(**params)
            self._pedalboard.append(effect)
            print("Added Convolution with:", params)

    def _add_mix(self):
        dialog = MixOptionsDialog(self)
        if dialog.exec():
            params = dialog.get_parameters()
            effect = Mix(**params)
            self._pedalboard.append(effect)
            print("Added Mix with:", params)

    def bar_reset(self) -> None:
        """
        Reset the position of the bar
        """
        self.init_bar_position()

    def _init_toolbar(self) -> None:
        """
        Initialize the toolbar
        """
        self._toolbar = QToolBar()
        #self._toolbar.setStyleSheet("QToolBar { padding: 10px; }")
        self._toolbar.setStyleSheet("""
            QToolBar { spacing: 5px; padding: 5px; }
        """)

        self.action__traversal = QComboBox()

        self.action__traversal.addItems([
            "Left to Right",
            "Right to Left",
            "Top to Bottom",
            "Bottom to Top",
            "Circle Inward",
            "Circle Outward",
        ])

        self._toolbar.addWidget(QLabel("Traversal"))
        self._toolbar.addWidget(self.action__traversal)

        self._toolbar.addWidget(QLabel("DPC"))
        self.action__dpc = QLineEdit("0.01")
        self._toolbar.addWidget(self.action__dpc)

        self._toolbar.addWidget(QLabel("Sample Rate (Hz)"))
        self.action__samplerate = QLineEdit("44100")
        self._toolbar.addWidget(self.action__samplerate)

        self._color_button = QPushButton("Color")
        self._color_button.setStyleSheet(f'background-color: {self._bar_color}')
        self._color_button.clicked.connect(self._bar_color_change)

        self._toolbar.addWidget(self._color_button)

        self.action__sonify = QAction("Sonify")
        self._toolbar.addAction(self.action__sonify)

        self.action__sonify.triggered.connect(self._sonify)

        self.action__play = QAction("Play")
        self._toolbar.addAction(self.action__play)
        self.action__play.setEnabled(self._playable)

        self.action__play.triggered.connect(self._play)

        self.addToolBar(self._toolbar)

    def _helper_sonify(self) -> None:
        self._sample_rate = int(self.action__samplerate.text())
        self._dpc = float(self.action__dpc.text())
        self.sonify_obj = Sonify(file_path = self._filename,
                                 dimension = self._dimension,
                                 duration_per_column = self._dpc,
                                 sample_rate = self._sample_rate)

        match self.action__traversal.currentIndex():
            case 0:
                self.sonify_obj.LeftToRight()
                self._traversal_mode = TraversalMode.LeftToRight
            case 1:
                self.sonify_obj.RightToLeft()
                self._traversal_mode = TraversalMode.RightToLeft
            case 2:
                self.sonify_obj.TopToBottom()
                self._traversal_mode = TraversalMode.TopToBottom
            case 3:
                self.sonify_obj.BottomToTop()
                self._traversal_mode = TraversalMode.BottomToTop
            case 4:
                self.sonify_obj.CircleInward()
                self._traversal_mode = TraversalMode.CircleInward
            case 5:
                self.sonify_obj.CircleOutward()
                self._traversal_mode = TraversalMode.CircleOutward

        self._playable = True
        self.action__play.setEnabled(self._playable)
        self.init_bar_position()

        self._audio = self.sonify_obj.audio * 0.5

        # Apply Effects
        if len(self._active_effects) > 0:
            self._audio = self._pedalboard(self._audio,
                                           self._sample_rate)

        if self._audio is not None:
            self._audio_controller.set_params(self._audio,
                                              self._sample_rate)

    def _sonify(self) -> None:
        """
        Sonify loaded image
        """

        if self._pixmap is None:
            if self._gui_open_image():
                self._helper_sonify()
        else:
            self._helper_sonify()

    def _bar_color_change(self) -> None:
        """
        Changes the color of the bar
        """
        c = QColorDialog.getColor()
        if c.isValid():
            self._color_button.setStyleSheet(f'background-color: {c.name()}')
            self.bar_color = c.name()

    def _play(self) -> None:
        """
        Plays the audio if image has been sonified
        """
        self._pause_resume_requested()

    def _save_audio(self) -> None:
        """
        Saves the audio
        """

        if self._audio is None or self._sample_rate is None:
            QMessageBox.warning(self, "No audio or sample rate defined",
                                "Looks like you have not yet sonified any images!")
            return
        filename, _ = QFileDialog.getSaveFileName(self)
        if filename != "":
            sf.write(filename, self._audio, self._sample_rate)

    def _screen_recording(self, record: bool) -> None:
        """
        Function that actually screen records.
        """
        if record:
            self.screen_record_timer = QTimer()
            self.screen_record_timer.setInterval(int(1 / 60 * 1000))  # 60 FPS
            self.screen_record_timer.timeout.connect(self._capture_graphicsview)
            self.screen_record_timer.start()
        else:
            self.screen_record_timer.stop()
            self.screen_record_timer = None
            self._capture_index = 0

    def _capture_graphicsview(self):
        """
        Timer callback for capturing image of the graphics view
        """
        pixmap = self._graphics_view.grab()
        pic_path = os.path.join(self._capture_dir, str(self._capture_index) + ".png")
        self._capture_index += 1
        pixmap.save(pic_path)
        print("Saving")

    def _screen_record(self) -> None:
        """
        Record the QGraphicsView.
        """

        self._capture_dir = QFileDialog.getExistingDirectory(self)

        d = ScreenRecordDialog()
        d.start_recording_signal.connect(self._screen_recording)
