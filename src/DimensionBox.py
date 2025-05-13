from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
)
import sys

class DimensionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Image Dimensions")

        self.layout = QVBoxLayout()

        self.width_input = QLineEdit()
        self.height_input = QLineEdit()

        self.width_input.setText("256")
        self.height_input.setText("256")

        self.layout.addWidget(QLabel("Width:"))
        self.layout.addWidget(self.width_input)
        self.layout.addWidget(QLabel("Height:"))
        self.layout.addWidget(self.height_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.adjustSize()
        self.setFixedSize(self.size())

    def get_dimensions(self):
        return int(self.width_input.text()), int(self.height_input.text())
