""" Custom QFontDialog that also defines text & background color """

from PyQt5.QtWidgets import (
    QFontDialog,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QLineEdit,
    QSizePolicy,
)
from PyQt5.QtGui import QColor

from qgis.gui import QgsColorButton


class ColorFontDialog(QFontDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.text_color_button = QgsColorButton(self)
        self.background_color_button = QgsColorButton(self)
        self.group_box = QGroupBox("Color", self)
        layout = QHBoxLayout(self.group_box)

        self.background_color_button.setColor(QColor("white"))
        self.text_color_button.setColor(QColor("black"))

        button_box = (
            self.layout().itemAtPosition(self.layout().rowCount() - 1, 0).widget()
        )
        self.layout().addWidget(
            button_box, self.layout().rowCount() + 1, 0, 1, -1,
        )
        self.layout().addWidget(
            self.group_box, self.layout().rowCount() - 3, 0, 1, -1,
        )
        self.layout().addWidget(
            QLabel(" "), self.layout().rowCount() - 2, 0, 1, -1,
        )
        layout.addWidget(QLabel("Text"))
        layout.addWidget(self.text_color_button)
        layout.addStretch()
        layout.addWidget(QLabel("Background"))
        layout.addWidget(self.background_color_button)
        self.text_color_button.setMinimumHeight(20)
        self.text_color_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.text_color_button.colorChanged.connect(self.on_color_changed)
        self.background_color_button.setMinimumHeight(20)
        self.background_color_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.background_color_button.colorChanged.connect(self.on_color_changed)

    def on_color_changed(self):
        sample = self.findChild(QLineEdit, "qt_fontDialog_sampleEdit")
        if sample:
            color1 = self.text_color_button.color().name()
            color2 = self.background_color_button.color().name()
            sample.setStyleSheet(f"color:{color1}; background-color:{color2}")

    def textColor(self):
        return self.text_color_button.color()

    def setTextColor(self, color):
        return self.text_color_button.setColor(color)

    def backgroundColor(self):
        return self.background_color_button.color()

    def setBackgroundColor(self, color):
        return self.background_color_button.setColor(color)
