# 08_export_qgis_layout.py
import os
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsLayoutExporter,
)

qgs_app = QgsApplication.instance()
owns_app = False
if qgs_app is None:
    qgs_app = QgsApplication([], False)
    qgs_app.initQgis()
    owns_app = True

qgz_path = r"C:\GeoProjects\HornVulnerability\qgis_project\horn_vulnerability_styled.qgz"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(out_dir, exist_ok=True)

out_png = os.path.join(out_dir, "horn_qgis_layout_300dpi.png")
out_pdf = os.path.join(out_dir, "horn_qgis_layout_A3.pdf")

project = QgsProject.instance()
project.clear()
loaded = project.read(qgz_path)
print("Loaded project:", qgz_path, "| Success:", loaded)

layout = project.layoutManager().layoutByName("Horn_CGVI_Layout")
if layout is not None:
    exporter = QgsLayoutExporter(layout)

    img_settings = QgsLayoutExporter.ImageExportSettings()
    img_settings.dpi = 300
    png_res = exporter.exportToImage(out_png, img_settings)
    print("Exported PNG:", out_png, "| Status:", png_res)

    pdf_settings = QgsLayoutExporter.PdfExportSettings()
    pdf_settings.dpi = 300
    pdf_res = exporter.exportToPdf(out_pdf, pdf_settings)
    print("Exported PDF:", out_pdf, "| Status:", pdf_res)
else:
    print("Layout 'Horn_CGVI_Layout' not found in project.")

if owns_app:
    qgs_app.exitQgis()
