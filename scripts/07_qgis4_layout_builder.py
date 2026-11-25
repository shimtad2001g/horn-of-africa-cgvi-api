# 07_qgis4_layout_builder.py
# Standalone PyQGIS script (supports QGIS 3.32 / QGIS 4.x via python-qgis.bat or QGIS Python Console)
import os
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsSingleBandPseudoColorRenderer,
    QgsColorRampShader,
    QgsRasterShader,
    QgsLayoutItemMap,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemScaleBar,
    QgsLayoutItemPage,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsPrintLayout,
)
from qgis.PyQt.QtGui import QColor, QFont

qgs_app = QgsApplication.instance()
owns_app = False
if qgs_app is None:
    qgs_app = QgsApplication([], False)
    qgs_app.initQgis()
    owns_app = True

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
qgis_dir = r"C:\GeoProjects\HornVulnerability\qgis_project"
os.makedirs(qgis_dir, exist_ok=True)

project = QgsProject.instance()
project.clear()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

def make_pseudocolor_renderer(provider, stops):
    shader = QgsRasterShader()
    ramp_shader = QgsColorRampShader()
    ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)
    items = [QgsColorRampShader.ColorRampItem(val, QColor(hex_c), lbl) for val, hex_c, lbl in stops]
    ramp_shader.setColorRampItemList(items)
    shader.setRasterShaderFunction(ramp_shader)
    return QgsSingleBandPseudoColorRenderer(provider, 1, shader)

# 1. Continuous CGVI layer
cont_path = os.path.join(proc_dir, "horn_cgvi_continuous.tif")
cont_layer = QgsRasterLayer(cont_path, "horn_cgvi_continuous", "gdal")
if cont_layer.isValid():
    stops = [
        (0.20, "#ffffb2", "0.20 (Low)"),
        (0.30, "#fecc5c", "0.30"),
        (0.40, "#fd8d3c", "0.40 (Moderate)"),
        (0.51, "#bd0026", "0.51 (Peak Observed)"),
    ]
    cont_layer.setRenderer(make_pseudocolor_renderer(cont_layer.dataProvider(), stops))
    cont_layer.triggerRepaint()
    project.addMapLayer(cont_layer)
else:
    print("Warning: Invalid continuous layer:", cont_path)

# 2. Classified CGVI layer
cls_path = os.path.join(proc_dir, "horn_cgvi_classified.tif")
cls_layer = QgsRasterLayer(cls_path, "horn_cgvi_classified", "gdal")
if cls_layer.isValid():
    cls_stops = [
        (1, "#2b83ba", "1 - Very Low (0.00-0.20)"),
        (2, "#abdda4", "2 - Low (0.20-0.40)"),
        (3, "#fdae61", "3 - Moderate (0.40-0.60)"),
        (4, "#f46d43", "4 - High (0.60-0.80)"),
        (5, "#d7191c", "5 - Very High (0.80-1.00)"),
    ]
    cls_layer.setRenderer(make_pseudocolor_renderer(cls_layer.dataProvider(), cls_stops))
    cls_layer.triggerRepaint()
    project.addMapLayer(cls_layer)
else:
    print("Warning: Invalid classified layer:", cls_path)

# 3. Harmonized component rasters
for name, fname in [
    ("drought_hazard_1km", "drought_hazard_1km.tif"),
    ("female_exposure_1km", "female_exposure_1km.tif"),
    ("slope_sensitivity_1km", "slope_sensitivity_1km.tif"),
]:
    p = os.path.join(proc_dir, fname)
    rl = QgsRasterLayer(p, name, "gdal")
    if rl.isValid():
        project.addMapLayer(rl, False)
        project.layerTreeRoot().addLayer(rl)

# 4. Print Layout (A3 Landscape)
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName("Horn_CGVI_Layout")
page = layout.pageCollection().page(0)
page.setPageSize("A3", QgsLayoutItemPage.Landscape)

map_item = QgsLayoutItemMap(layout)
map_item.attemptMove(QgsLayoutPoint(12, 22, QgsUnitTypes.LayoutMillimeters))
map_item.attemptResize(QgsLayoutSize(280, 245, QgsUnitTypes.LayoutMillimeters))
if cont_layer.isValid():
    map_item.setExtent(cont_layer.extent())
map_item.setFrameEnabled(True)
layout.addLayoutItem(map_item)

title_item = QgsLayoutItemLabel(layout)
title_item.setText("Horn of Africa Climate & Gender Vulnerability (CGVI, ~1 km)")
title_item.setFont(QFont("Arial", 14, QFont.Bold))
title_item.adjustSizeToText()
title_item.attemptMove(QgsLayoutPoint(12, 8, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(title_item)

legend_item = QgsLayoutItemLegend(layout)
legend_item.setLinkedMap(map_item)
legend_item.attemptMove(QgsLayoutPoint(298, 22, QgsUnitTypes.LayoutMillimeters))
legend_item.attemptResize(QgsLayoutSize(108, 130, QgsUnitTypes.LayoutMillimeters))
legend_item.setFrameEnabled(True)
layout.addLayoutItem(legend_item)

scalebar_item = QgsLayoutItemScaleBar(layout)
scalebar_item.setLinkedMap(map_item)
scalebar_item.setStyle("Single Box")
scalebar_item.setUnits(QgsUnitTypes.DistanceKilometers)
scalebar_item.setNumberOfSegments(4)
scalebar_item.setUnitsPerSegment(250)
scalebar_item.attemptMove(QgsLayoutPoint(18, 242, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(scalebar_item)

footer_item = QgsLayoutItemLabel(layout)
footer_item.setText(
    "Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM (GEE: ee-shimtad2001g) | Author: Shimeles Tadesse Zelelew"
)
footer_item.setFont(QFont("Arial", 8))
footer_item.adjustSizeToText()
footer_item.attemptMove(QgsLayoutPoint(12, 272, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(footer_item)

project.layoutManager().addLayout(layout)

qgz_path = os.path.join(qgis_dir, "horn_vulnerability_styled.qgz")
saved_ok = project.write(qgz_path)
print("Saved styled QGIS project:", qgz_path, "| Success:", saved_ok)

if owns_app:
    qgs_app.exitQgis()
