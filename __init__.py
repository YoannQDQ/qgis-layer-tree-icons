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
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LayerTreeIcons class from file layertreeicons.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .layertreeicons import LayerTreeIcons

    return LayerTreeIcons(iface)
