import os

from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtWidgets import QAction, QDialog, QFileDialog
from PyQt5.QtGui import QIcon, QColor

from qgis.utils import iface
from qgis.core import QgsLayerTree, Qgis

from .resourcebrowserimpl import ResourceBrowser
from .colorfontdialog import ColorFontDialog


class LayerTreeMenuProvider(QObject):
    def __call__(self, menu):
        return self.customize(menu)

    def customize(self, menu):
        """ Add custom actions at the end of the default context menu """

        view = iface.layerTreeView()

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

        action_set_custom_font = QAction(
            QIcon(":/plugins/layertreeicons/font.svg"),
            self.tr("Set custom font"),
            menu,
        )
        action_set_custom_font.triggered.connect(self.set_custom_font)
        menu.addAction(action_set_custom_font)

        custom_icon = any(
            node.customProperty("plugins/customTreeIcon/icon") for node in self.nodes
        )
        custom_font = (
            any(
                node.customProperty("plugins/customTreeIcon/font")
                for node in self.nodes
            )
            or any(
                node.customProperty("plugins/customTreeIcon/textColor")
                for node in self.nodes
            )
            or any(
                node.customProperty("plugins/customTreeIcon/backgroundColor")
                for node in self.nodes
            )
        )
        if custom_icon or custom_font:
            if custom_icon and custom_font:
                action_txt = self.tr("Reset icon && font")
            elif custom_icon:
                action_txt = self.tr("Reset icon")
            else:
                action_txt = self.tr("Reset font")

            self.action_reset_icon = QAction(action_txt)
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

    def set_custom_font(self):
        """ Set a custom icon as a custom property on the selected nodes """
        dialog = ColorFontDialog(iface.mainWindow())

        if Qgis.QGIS_VERSION_INT >= 31800:
            layer_tree_model = iface.layerTreeView().layerTreeModel()
        else:
            layer_tree_model = iface.layerTreeView().model()

        f = layer_tree_model.layerTreeNodeFont(QgsLayerTree.NodeLayer)

        for node in self.nodes:
            if node.customProperty("plugins/customTreeIcon/font"):
                f.fromString(node.customProperty("plugins/customTreeIcon/font"))
                text_color = node.customProperty(
                    "plugins/customTreeIcon/textColor", "black"
                )
                background_color = node.customProperty(
                    "plugins/customTreeIcon/backgroundColor", "white"
                )
                dialog.setTextColor(QColor(text_color))
                dialog.setBackgroundColor(QColor(background_color))

                break
        dialog.setCurrentFont(f)
        res = dialog.exec()
        if res == QDialog.Accepted:
            for node in self.nodes:
                node.setCustomProperty(
                    "plugins/customTreeIcon/font", dialog.currentFont().toString()
                )
                node.setCustomProperty(
                    "plugins/customTreeIcon/textColor", dialog.textColor().name()
                )
                node.setCustomProperty(
                    "plugins/customTreeIcon/backgroundColor",
                    dialog.backgroundColor().name(),
                )

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
            node.removeCustomProperty("plugins/customTreeIcon/font")
            node.removeCustomProperty("plugins/customTreeIcon/textColor")
            node.removeCustomProperty("plugins/customTreeIcon/backgroundColor")
