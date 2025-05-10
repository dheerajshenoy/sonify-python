from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent

class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom_factor = 1.25  # Zoom in/out scaling factor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self._zoom_factor, self._zoom_factor)  # Zoom in
        else:
            self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)  # Zoom out

