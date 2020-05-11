# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import QObject, QEvent, Qt, QSettings
from PyQt5.QtWidgets import QAction, QDialog, QMenu, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter

from qgis.core import (
    QgsProject,
    QgsLayerTreeModel,
    QgsLayerTree,
    QgsVectorLayer,
    QgsApplication,
    QgsWkbTypes,
    QgsMapLayer,
)
from qgis.utils import iface

from .resourcebrowserimpl import ResourceBrowser


class LayerTreeViewEventFilter(QObject):
    """ Installed as an event filter on the QGIS layer tree view to customize the
    default MenuProvider
    """

    def eventFilter(self, obj, event):
        """ Qt method to implement to use a QObject as an event filter """
        if event.type() == QEvent.ContextMenu:
            menu = self.createContextMenu()
            menu.exec(iface.layerTreeView().mapToGlobal(event.pos()))
            return True
        return False

    def createContextMenu(self):
        """ Add custom actions at the end of the default context menu """

        view = iface.layerTreeView()

        menu = view.menuProvider().createContextMenu()

        # Work on selected nodes, or current node
        self.nodes = view.selectedNodes()
        if not self.nodes:
            # current node is root node: return menu
            if not view.currentNode() or not view.currentNode().parent():
                return menu
            self.nodes = [view.currentNode()]

        menu.addSeparator()

        action_set_icon_from_file = QAction(
            QIcon(":/plugins/layertreeicons/icon.svg"),
            self.tr("Set icon from file"),
            menu,
        )
        action_set_icon_from_file.triggered.connect(self.set_custom_icon_from_file)
        menu.addAction(action_set_icon_from_file)

        action_set_icon_from_qgis = QAction(
            QIcon(":/plugins/layertreeicons/icon.svg"),
            self.tr("Set icon from QGIS resources"),
            menu,
        )
        action_set_icon_from_qgis.triggered.connect(self.set_custom_icon_from_qgis)
        menu.addAction(action_set_icon_from_qgis)

        if any(
            node.customProperty("plugins/customTreeIcon/icon") for node in self.nodes
        ):
            self.action_reset_icon = QAction(self.tr("Reset icon"))
            self.action_reset_icon.triggered.connect(self.reset_custom_icon)
            menu.addAction(self.action_reset_icon)
        return menu

    def set_custom_icon_from_qgis(self):
        """ Set a custom icon as a custom property on the selected nodes """
        dialog = ResourceBrowser(iface.mainWindow())
        if len(self.nodes) == 1:
            dialog.set_icon(
                self.nodes[0].customProperty("plugins/customTreeIcon/icon", "")
            )
        res = dialog.exec()
        if res == QDialog.Accepted:
            for node in self.nodes:
                node.setCustomProperty("plugins/customTreeIcon/icon", dialog.icon)
        dialog.deleteLater()

    def set_custom_icon_from_file(self):
        """ Set a custom icon as a custom property on the selected nodes """

        settings = QSettings()
        settings.beginGroup("plugins/layertreeicons")

        iconpath = settings.value("iconpath", "")

        filename, _ = QFileDialog.getOpenFileName(
            caption=self.tr("Select Icon"),
            filter=self.tr("Image Files (*.svg *.png *.gif);;All files (*)"),
            directory=iconpath,
        )
        if not filename:
            return

        settings.setValue("iconpath", os.path.dirname(filename))

        for node in self.nodes:
            node.setCustomProperty("plugins/customTreeIcon/icon", filename)

    def reset_custom_icon(self):
        """ Delete the custom property, which will restore the default icon """
        for node in self.nodes:
            node.removeCustomProperty("plugins/customTreeIcon/icon")


class CustomTreeModel(QgsLayerTreeModel):
    """ Custom tree model which handles custom icons on nodes """

    def __init__(self, parent=None):
        super().__init__(QgsProject.instance().layerTreeRoot(), parent)
        self.setFlags(iface.layerTreeView().layerTreeModel().flags())
        self.settings = QSettings()
        self.settings.beginGroup("plugins/layertreeicons/defaulticons")

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        node = self.index2node(index)
        if not node:
            return super().data(index, role)

        # Override data for DecorationRole (Icon)
        if role == Qt.DecorationRole and index.column() == 0:
            icon = None
            # If a custom icon was set for this node
            if node.customProperty("plugins/customTreeIcon/icon"):
                icon = QIcon(node.customProperty("plugins/customTreeIcon/icon"))

            # If an icon was set for the node type
            elif QgsLayerTree.isGroup(node):
                if self.settings.value("group", ""):
                    icon = QIcon(self.settings.value("group"))
            elif QgsLayerTree.isLayer(node):
                layer = node.layer()

                if not layer:
                    return super().data(index, role)

                if layer.type() == QgsMapLayer.RasterLayer:
                    if self.settings.value("raster", ""):
                        icon = QIcon(self.settings.value("raster"))

                if layer.type() == QgsMapLayer.VectorLayer:

                    if self.testFlag(
                        QgsLayerTreeModel.ShowLegend
                    ) and self.legendEmbeddedInParent(node):
                        icon = self.legendIconEmbeddedInParent(node)

                        pixmap = QPixmap(icon.pixmap(64, 64)).scaled(64, 64)
                        icon = QIcon(pixmap)

                    else:
                        if layer.geometryType() == QgsWkbTypes.PointGeometry:
                            if self.settings.value("point", ""):
                                icon = QIcon(self.settings.value("point"))
                        elif layer.geometryType() == QgsWkbTypes.LineGeometry:
                            if self.settings.value("line", ""):
                                icon = QIcon(self.settings.value("line"))
                        elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                            if self.settings.value("polygon", ""):
                                icon = QIcon(self.settings.value("polygon"))
                        elif layer.geometryType() == QgsWkbTypes.NullGeometry:
                            if self.settings.value("nogeometry", ""):
                                icon = QIcon(self.settings.value("nogeometry"))

                try:
                    if layer.type() == QgsMapLayer.MeshLayer:
                        if self.settings.value("mesh", ""):
                            icon = QIcon(self.settings.value("mesh"))
                except AttributeError:
                    pass

            if icon:
                # Special case: In-edition vector layer. Draw an editing icon over
                # the custom icon. Adapted from QGIS source code (qgslayertreemodel.cpp)
                if QgsLayerTree.isLayer(node):
                    layer = node.layer()
                    if (
                        layer
                        and isinstance(layer, QgsVectorLayer)
                        and layer.isEditable()
                    ):
                        icon_size = iface.layerTreeView().iconSize().width()
                        if icon_size == -1:
                            icon_size = 16
                        pixmap = QPixmap(icon.pixmap(icon_size, icon_size))
                        painter = QPainter(pixmap)
                        painter.drawPixmap(
                            0,
                            0,
                            icon_size,
                            icon_size,
                            QgsApplication.getThemeIcon(
                                ("/mIconEditableEdits.svg")
                                if layer.isModified()
                                else ("/mActionToggleEditing.svg")
                            ).pixmap(icon_size, icon_size),
                        )
                        painter.end()
                        del painter
                        icon = QIcon(pixmap)

                return icon

        # call QgsLayerTreeModel implementation
        return super().data(index, role)
