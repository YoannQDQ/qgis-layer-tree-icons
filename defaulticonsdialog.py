# -*- coding: utf-8 -*-

import os
from functools import partial

from PyQt5.QtCore import QResource, Qt, QSettings, QSize, QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QToolButton,
    QAction,
    QLabel,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QFileDialog,
    QGroupBox,
)

from qgis.core import Qgis
from qgis.utils import iface

from .resourcebrowserimpl import ResourceBrowser


class DefaultIconsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings()
        self.settings.beginGroup("plugins/layertreeicons")

        self.setWindowTitle(self.tr("Default layer tree icons"))
        self.setMinimumSize(QSize(200, 0))
        layout = QVBoxLayout(self)

        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel(self.tr("Icon Size")))
        self.icon_size_combo = QComboBox(self)
        self.icon_size_combo.addItem(self.tr("default"), -1)
        for val in (16, 24, 32, 48, 64):
            self.icon_size_combo.addItem(f"{val} px", val)

        idx = self.icon_size_combo.findData(self.settings.value("iconsize", -1, int))
        self.icon_size_combo.setCurrentIndex(idx)
        self.icon_size_combo.currentIndexChanged.connect(self.on_icon_size_changed)

        hlayout.addWidget(self.icon_size_combo)
        layout.addLayout(hlayout)
        group_box = QGroupBox(self)
        group_box.setTitle("Default Icons")
        self.form_layout = QFormLayout(group_box)
        layout.addWidget(group_box)
        self.reset_button = QPushButton(self.tr("Reset default icons"))
        layout.addWidget(self.reset_button)

        self.reset_button.clicked.connect(self.reset_all)

        self.resource_browser = ResourceBrowser(parent)

        self.source_data = {
            "group": (self.tr("Group"), ":/images/themes/default/mActionFolder.svg",),
            "raster": (self.tr("Raster"), ":/images/themes/default/mIconRaster.svg",),
            "point": (self.tr("Point"), ":/images/themes/default/mIconPointLayer.svg",),
            "line": (self.tr("Line"), ":/images/themes/default/mIconLineLayer.svg",),
            "polygon": (
                self.tr("Polygon"),
                ":/images/themes/default/mIconPolygonLayer.svg",
            ),
            "nogeometry": (
                self.tr("No Geometry"),
                ":/images/themes/default/mIconTableLayer.svg",
            ),
        }

        if Qgis.QGIS_VERSION_INT > 30200:

            self.source_data["mesh"] = (
                self.tr("Mesh Layer"),
                ":/images/themes/default/mIconMeshLayer.svg",
            )

        for settings_key, (text, default_icon) in self.source_data.items():

            button = QToolButton(self)
            button.setObjectName(settings_key)
            button.setPopupMode(QToolButton.MenuButtonPopup)
            button.setIconSize(QSize(24, 24))
            button.setIcon(QIcon(default_icon))
            label = QLabel(text, self)
            label.setMinimumSize(QSize(label.minimumSize().width(), 38))
            self.form_layout.addRow(label, button)

            action_from_qgis = QAction("Set from QGIS ressources", button)
            action_from_qgis.triggered.connect(
                partial(self.set_icon_from_ressources, settings_key)
            )
            button.addAction(action_from_qgis)
            button.clicked.connect(action_from_qgis.trigger)

            action_from_file = QAction("Set from file", button)
            action_from_file.triggered.connect(
                partial(self.set_icon_from_file, settings_key)
            )
            button.addAction(action_from_file)

            action_reset = QAction("Reset", button)
            action_reset.triggered.connect(partial(self.reset, settings_key))
            button.addAction(action_reset)

    def set_icon_from_ressources(self, settings_key):
        res = self.resource_browser.exec()
        if res == QDialog.Accepted:
            button = self.findChild(QToolButton, settings_key)
            button.setIcon(QIcon(self.resource_browser.icon))
            self.settings.setValue(
                f"defaulticons/{settings_key}", self.resource_browser.icon
            )
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def set_icon_from_file(self, settings_key):

        iconpath = self.settings.value("iconpath", "")
        icon, _ = QFileDialog.getOpenFileName(
            caption=self.tr("Select Icon"),
            filter=self.tr("Image Files (*.svg *.png *.gif);;All files (*)"),
            directory=iconpath,
        )
        if not icon:
            return

        button = self.findChild(QToolButton, settings_key)
        button.setIcon(QIcon(icon))
        self.settings.setValue(f"defaulticons/{settings_key}", icon)
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def reset(self, settings_key):
        button = self.findChild(QToolButton, settings_key)
        button.setIcon(QIcon(self.source_data[settings_key][1]))
        self.settings.setValue(f"defaulticons/{settings_key}", "")
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())

    def reset_all(self):
        for settings_key, (_, default_icon) in self.source_data.items():
            button = self.findChild(QToolButton, settings_key)
            button.setIcon(QIcon(default_icon))
            self.settings.setValue(f"defaulticons/{settings_key}", "")
        iface.layerTreeView().model().dataChanged.emit(QModelIndex(), QModelIndex())
        self.icon_size_combo.setCurrentIndex(0)

    def on_icon_size_changed(self):
        val = self.icon_size_combo.currentData()
        iface.layerTreeView().setIconSize(QSize(val, val))
        self.settings.setValue("iconsize", val)
