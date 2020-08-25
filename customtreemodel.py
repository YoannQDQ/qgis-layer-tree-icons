# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import (
    QObject,
    QEvent,
    QSettings,
    QSize,
    Qt,
    QPointF,
)
from PyQt5.QtWidgets import QAction, QDialog, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFontMetricsF

from qgis.core import (
    QgsProject,
    QgsLayerTreeModel,
    QgsLayerTree,
    QgsVectorLayer,
    QgsApplication,
    QgsWkbTypes,
    QgsMapLayer,
    QgsSymbolLegendNode,
    QgsSymbolLayerUtils,
    QgsTextRenderer,
    QgsRenderContext,
    qgsDoubleNear,
    QgsMapToPixel,
)
from qgis.utils import iface, QgsMessageLog

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


def createTemporaryRenderContext():

    layerModel = iface.layerTreeView().model()
    mupp, dpi, scale = layerModel.legendMapViewData()

    if qgsDoubleNear(mupp, 0.0) or dpi == 0 or qgsDoubleNear(scale, 0.0):
        return None

    render_context = QgsRenderContext()
    render_context.setScaleFactor(dpi / 25.4)
    render_context.setRendererScale(scale)
    render_context.setMapToPixel(QgsMapToPixel(mupp))
    return render_context


def pixmapForLegendNode(legend_node):

    # handles only symbol nodes
    if not isinstance(legend_node, QgsSymbolLegendNode):
        return

    # If size is default, use default implementation
    size = iface.layerTreeView().iconSize()
    if size.width() in (-1, 16):
        size = QSize(18, 18)

    symbol = legend_node.symbol()
    if not symbol:
        return

    # Compute minimum width
    model = iface.layerTreeView().model()
    if not legend_node.layerNode():
        return

    text = legend_node.textOnSymbolLabel()

    minimum_width = max(
        max(
            l_node.minimumIconSize().width() + (8 if text else 0)
            for l_node in model.layerLegendNodes(legend_node.layerNode())
            if isinstance(l_node, QgsSymbolLegendNode)
        ),
        size.width(),
    )

    symbol_size = QSize(minimum_width, size.height())
    context = QgsRenderContext.fromMapSettings(iface.mapCanvas().mapSettings())
    pixmap = QgsSymbolLayerUtils.symbolPreviewPixmap(symbol, symbol_size, 0, context)

    if text:
        painter = QPainter(pixmap)
        text_format = legend_node.textOnSymbolTextFormat()

        try:
            text_context = createTemporaryRenderContext()
            if text_context:
                painter.setRenderHint(QPainter.Antialiasing)
                text_context.setPainter(painter)

                font_metrics = QFontMetricsF(text_format.scaledFont(context))
                y_baseline_v_center = (
                    symbol_size.height()
                    + font_metrics.ascent()
                    - font_metrics.descent()
                ) / 2

                QgsTextRenderer.drawText(
                    QPointF(symbol_size.width() / 2, y_baseline_v_center),
                    0,
                    QgsTextRenderer.AlignCenter,
                    [text],
                    text_context,
                    text_format,
                )
                text_context.setPainter(None)

        except Exception as e:
            QgsMessageLog.logMessage(str(e))

    return pixmap


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
        legend_node = self.index2legendNode(index)

        if legend_node and role == Qt.DecorationRole:
            pixmap = pixmapForLegendNode(legend_node)
            if pixmap:
                return pixmap

        if not node:
            return super().data(index, role)

        # Override data for DecorationRole (Icon)
        if role == Qt.DecorationRole and index.column() == 0:
            icon = None
            pixmap = None

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
                        size = iface.layerTreeView().iconSize()

                        legend_node = self.legendNodeEmbeddedInParent(node)
                        pixmap = pixmapForLegendNode(legend_node)

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

            # Special case: In-edition vector layer. Draw an editing icon over
            # the custom icon. Adapted from QGIS source code (qgslayertreemodel.cpp)
            if (pixmap or icon) and QgsLayerTree.isLayer(node):
                layer = node.layer()
                if layer and isinstance(layer, QgsVectorLayer) and layer.isEditable():
                    icon_size = iface.layerTreeView().iconSize().width()
                    if icon_size == -1:
                        icon_size = 16
                    if not pixmap and icon:
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

            if pixmap:
                return pixmap
            if icon:
                return icon

        # call QgsLayerTreeModel implementation
        return super().data(index, role)
