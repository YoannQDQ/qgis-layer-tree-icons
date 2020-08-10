Layer Tree Icons (QGIS plugin)
===
![Icon](./icon.png)

This plugin add an item in the QGIS layer tree context menu to set a custom icon on any node.
It includes a ressource browser to use QGIS icons. Icons can also be set for a given node type (i.e. group, or polygon layer).

Category Icon
--
It is possible to set new icons for node categories, from the plugin menu, or from a new button, added in the Layer Panel toolbar. It is also possible to change the default icon size in this dialog.

![Default icons dialog](./docs/default_icons.png)

Node Icon
--
Custom icons can be set by right-clicking on a node in the Layer Panel.

![Menu](./docs/menu.png)

 - **Set icon from file**: Browse the computer to set the node icon from an image file
 - **Set icon from QGIS resources**: Open a Resource Browser to use one of the icons embedded in QGIS
 - **Reset custom icon** (visible if a custom icon is set): Revert to the default icon, or, if defined, to the custom icon for the node's category

Resource browser
--
![Resource browser](./docs/resource_browser.png)

The resource browser allow to search through the embedded .qrc files to look for images to use as icon.

PyQGIS Cookbook
--

 - Set custom icon for a specific node:

```python
iface.layerTreeView().currentNode().setCustomProperty(
    "plugins/customTreeIcon/icon",
    "path/to/icon.png"
)
```
 - Set custom icon for an icon type:
```python
# Group
QSettings().setValue("plugins/layertreeicons/defaulticons/group", "path/to/icon.png")
# Raster
QSettings().setValue("plugins/layertreeicons/defaulticons/raster", "path/to/icon.png")
# Point
QSettings().setValue("plugins/layertreeicons/defaulticons/point", "path/to/icon.png")
# Line
QSettings().setValue("plugins/layertreeicons/defaulticons/line", "path/to/icon.png")
# Polygon
QSettings().setValue("plugins/layertreeicons/defaulticons/polygon", "path/to/icon.png")
# No Geometry
QSettings().setValue("plugins/layertreeicons/defaulticons/nogeometry", "path/to/icon.png")
# Mesh
QSettings().setValue("plugins/layertreeicons/defaulticons/mesh", "path/to/icon.png")
```



*Copyright © 2020 Yoann Quenach de Quivillic*

