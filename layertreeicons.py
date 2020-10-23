# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Layer Tree Icons
 A QGIS plugin which provides layer tree icons customization

                              -------------------
        begin                : 2020-05-09
        git sha              : $Format:%H$
        copyright            : (C) 2020 Yoann Quenach de Quivillic
        email                : yoann.quenach@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import configparser

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QMessageBox,
    QWidget,
    QToolBar,
    QDockWidget,
)


# Initialize Qt resources from file resources.py
from .resources import *

from .defaulticonsdialog import DefaultIconsDialog
from .customtreemodel import CustomTreeModel

from .layertreecontextmenumanager import LayerTreeContextMenuManager
from .menuprovider import LayerTreeMenuProvider


class LayerTreeIcons:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "LayerTreeIcons_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Save original layer tree model
        self.original_layer_tree_model = self.iface.layerTreeView().model()
        self.original_layer_tree_model.blockSignals(True)

        # Init settings
        self.settings = QSettings()
        self.settings.beginGroup("plugins/layertreeicons")

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("LayerTreeIcons", message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.manage_default_action = QAction(
            QIcon(":/plugins/layertreeicons/icon.svg"),
            self.tr("Manage Default Tree Properties"),
            parent=self.iface.mainWindow(),
        )
        self.about_action = QAction(
            QIcon(":/plugins/layertreeicons/about.svg"),
            self.tr("About Layer Tree Icons"),
            parent=self.iface.mainWindow(),
        )
        self.about_action.triggered.connect(self.show_about)

        self.plugin_menu = self.iface.pluginMenu().addMenu(
            QIcon(":/plugins/layertreeicons/icon.svg"), "LayerTreeIcons"
        )
        self.plugin_menu.addAction(self.manage_default_action)
        self.plugin_menu.addAction(self.about_action)

        # Replace the default QgsLayerTreeModel with our custom model
        self.custom_model = CustomTreeModel()
        self.contextMenuManager = LayerTreeContextMenuManager()
        self.contextMenuManager.addProvider(LayerTreeMenuProvider())
        self.iface.layerTreeView().setModel(self.custom_model)

        icon_size = self.settings.value("iconsize", -1, int)
        self.iface.layerTreeView().setIconSize(QSize(icon_size, icon_size))

        # Add the action to the QGIS Layer Panel toolbar
        self.layer_tree_toolbar = (
            self.iface.mainWindow().findChild(QDockWidget, "Layers").findChild(QToolBar)
        )
        if self.layer_tree_toolbar:
            self.separator = self.layer_tree_toolbar.addSeparator()
            self.layer_tree_toolbar.addAction(self.manage_default_action)

        self.default_icons_dialog = DefaultIconsDialog(self.iface.mainWindow())
        self.manage_default_action.triggered.connect(self.default_icons_dialog.show)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.pluginMenu().removeAction(self.plugin_menu.menuAction())
        self.iface.layerTreeView().setModel(self.original_layer_tree_model)
        self.original_layer_tree_model.blockSignals(False)
        self.default_icons_dialog.deleteLater()
        self.iface.layerTreeView().setIconSize(QSize(-1, -1))

        if self.layer_tree_toolbar:
            self.layer_tree_toolbar.removeAction(self.manage_default_action)
            self.layer_tree_toolbar.removeAction(self.separator)

    def show_about(self):

        # Used to display plugin icon in the about message box
        bogus = QWidget(self.iface.mainWindow())
        bogus.setWindowIcon(QIcon(":/plugins/layertreeicons/icon.svg"))

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
        version = cfg.get("general", "version")

        QMessageBox.about(
            bogus,
            self.tr("About Layer Tree Icons"),
            "<b>Version</b> {0}<br><br>"
            "<b>{1}</b> : <a href=https://github.com/YoannQDQ/layer-tree-icons>GitHub</a><br>"
            "<b>{2}</b> : <a href=https://github.com/YoannQDQ/layer-tree-icons/issues>GitHub</a><br>"
            "<b>{3}</b> : <a href=https://github.com/YoannQDQ/layer-tree-icons#layer-tree-icons-qgis-plugin>GitHub</a>".format(
                version,
                self.tr("Source code"),
                self.tr("Report issues"),
                self.tr("Documentation"),
            ),
        )
        bogus.deleteLater()
