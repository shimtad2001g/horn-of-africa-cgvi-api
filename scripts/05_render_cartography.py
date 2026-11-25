# 05_render_cartography.py
import os
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import rioxarray as rxr
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import FancyArrowPatch

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
qgis_dir = r"C:\GeoProjects\HornVulnerability\qgis_project"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(qgis_dir, exist_ok=True)

print("1. Loading processed CGVI layers...")
cgvi_da = rxr.open_rasterio(os.path.join(proc_dir, "horn_cgvi_continuous.tif"), masked=True).squeeze()
cgvi = cgvi_da.values.astype(np.float32)
cgvi = np.where(np.isfinite(cgvi), cgvi, np.nan)

# Spatial extent from raster bounds [minx, miny, maxx, maxy]
minx, miny, maxx, maxy = cgvi_da.rio.bounds()
extent = [minx, maxx, miny, maxy]

# Compute 5-quintile relative vulnerability classes (1..5) for visual contrast across [0.1976, 0.5079]
valid_mask = np.isfinite(cgvi)
q_edges = np.nanpercentile(cgvi[valid_mask], [0, 20, 40, 60, 80, 100])
quintile_grid = np.full(cgvi.shape, np.nan, dtype=np.float32)
for idx in range(5):
    low, high = q_edges[idx], q_edges[idx + 1]
    if idx < 4:
        m = valid_mask & (cgvi >= low) & (cgvi < high)
    else:
        m = valid_mask & (cgvi >= low) & (cgvi <= high)
    quintile_grid[m] = float(idx + 1)

print("2. Rendering 600 DPI publication map with clean white background...")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 7.2), dpi=600, facecolor="white")
fig.patch.set_facecolor("white")

# Panel A: Continuous CGVI
im1 = ax1.imshow(
    cgvi,
    extent=extent,
    origin="upper",
    cmap="YlOrRd",
    vmin=np.nanpercentile(cgvi[valid_mask], 1),
    vmax=np.nanpercentile(cgvi[valid_mask], 99),
    interpolation="nearest",
)
ax1.set_facecolor("white")
ax1.set_title("A. Composite Climate & Gender Vulnerability (CGVI)", fontsize=11, fontweight="bold", pad=10, color="#111111")
ax1.set_xlabel("Longitude (°E)", fontsize=9.5, color="#222222")
ax1.set_ylabel("Latitude (°N / °S)", fontsize=9.5, color="#222222")
ax1.set_xlim(minx, maxx)
ax1.set_ylim(miny, maxy)
ax1.grid(True, linestyle="--", linewidth=0.4, color="#888888", alpha=0.45)

cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.042, pad=0.03, shrink=0.88)
cbar1.set_label("CGVI Score (0.45 SPI + 0.40 Female + 0.15 Slope)", fontsize=8.5, color="#222222")
cbar1.ax.tick_params(labelsize=8)

# North arrow on Panel A
arrow_x = maxx - 1.5
arrow_y_base = maxy - 3.0
ax1.annotate(
    "N",
    xy=(arrow_x, arrow_y_base + 1.5),
    xytext=(arrow_x, arrow_y_base),
    ha="center",
    va="bottom",
    fontsize=10,
    fontweight="bold",
    color="#111111",
    arrowprops=dict(facecolor="#111111", width=2.2, headwidth=7, headlength=7),
)

# Approximate ~500 km scale bar near bottom-left of Panel A (~4.5 deg at equator)
sb_x0 = minx + 1.0
sb_x1 = sb_x0 + 4.5
sb_y = miny + 1.2
ax1.plot([sb_x0, sb_x1], [sb_y, sb_y], color="#111111", linewidth=2.5)
ax1.text((sb_x0 + sb_x1) / 2, sb_y + 0.35, "~500 km", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#111111")

# Panel B: 5-Quintile Relative Vulnerability Tiers
q_colors = ["#2b83ba", "#abdda4", "#ffffbf", "#fdae61", "#d7191c"]
q_cmap = ListedColormap(q_colors)
q_norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5, 5.5], q_cmap.N)

im2 = ax2.imshow(
    quintile_grid,
    extent=extent,
    origin="upper",
    cmap=q_cmap,
    norm=q_norm,
    interpolation="nearest",
)
ax2.set_facecolor("white")
ax2.set_title("B. Relative Vulnerability Quintiles (Regional Distribution)", fontsize=11, fontweight="bold", pad=10, color="#111111")
ax2.set_xlabel("Longitude (°E)", fontsize=9.5, color="#222222")
ax2.set_ylabel("Latitude (°N / °S)", fontsize=9.5, color="#222222")
ax2.set_xlim(minx, maxx)
ax2.set_ylim(miny, maxy)
ax2.grid(True, linestyle="--", linewidth=0.4, color="#888888", alpha=0.45)

cbar2 = fig.colorbar(im2, ax=ax2, ticks=[1, 2, 3, 4, 5], fraction=0.042, pad=0.03, shrink=0.88)
cbar2.ax.set_yticklabels(["Q1 Very Low", "Q2 Low", "Q3 Moderate", "Q4 High", "Q5 Very High"], fontsize=8)
cbar2.set_label("Relative Quintile Tier", fontsize=8.5, color="#222222")

fig.suptitle(
    "Horn of Africa Climate & Gender Vulnerability Assessment (~1 km Grid, EPSG:4326)",
    fontsize=13,
    fontweight="bold",
    y=0.97,
    color="#111111",
)

footer_text = (
    f"Fixed-Interval Summary: Min={np.nanmin(cgvi):.4f}, Mean={np.nanmean(cgvi):.4f}, Max={np.nanmax(cgvi):.4f} "
    f"(Fixed 0.0-0.2: ~0.00%, 0.2-0.4: 70.51%, 0.4-0.6: 29.49%)  |  "
    "Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM (GEE: ee-shimtad2001g)  |  Author: Shimeles Tadesse Zelelew"
)
fig.text(0.5, 0.015, footer_text, ha="center", va="bottom", fontsize=7.5, color="#333333")

plt.tight_layout(rect=[0.0, 0.04, 1.0, 0.93])

map_png_600 = os.path.join(out_dir, "horn_climate_gender_vulnerability_600dpi.png")
map_png_300 = os.path.join(out_dir, "horn_climate_gender_vulnerability_300dpi.png")
fig.savefig(map_png_600, dpi=600, facecolor="white")
fig.savefig(map_png_300, dpi=300, facecolor="white")
plt.close(fig)

print(f"Saved 600 DPI map: {map_png_600}")
print(f"Saved 300 DPI map: {map_png_300}")

print("3. Generating QGIS project file (horn_vulnerability.qgs)...")
layers = [
    ("horn_cgvi_classified", os.path.join(proc_dir, "horn_cgvi_classified.tif")),
    ("horn_cgvi_continuous", os.path.join(proc_dir, "horn_cgvi_continuous.tif")),
    ("drought_hazard_1km", os.path.join(proc_dir, "drought_hazard_1km.tif")),
    ("female_exposure_1km", os.path.join(proc_dir, "female_exposure_1km.tif")),
    ("slope_sensitivity_1km", os.path.join(proc_dir, "slope_sensitivity_1km.tif")),
]

qgis_root = ET.Element("qgis", version="4.0.0-Master", projectname="Horn of Africa Climate & Gender Vulnerability")
ET.SubElement(qgis_root, "title").text = "Horn of Africa Climate & Gender Vulnerability"
project_crs = ET.SubElement(qgis_root, "projectCrs")
srs = ET.SubElement(project_crs, "spatialrefsys", nativeFormat="Wkt")
ET.SubElement(srs, "authid").text = "EPSG:4326"

layer_tree = ET.SubElement(qgis_root, "layer-tree-group")
project_layers = ET.SubElement(qgis_root, "projectlayers")

for idx, (lyr_name, lyr_path) in enumerate(layers):
    lyr_id = f"{lyr_name}_{idx:02d}"
    ET.SubElement(layer_tree, "layer-tree-layer", name=lyr_name, id=lyr_id, source=lyr_path, checked="Qt::Checked", expanded="1")

    pl = ET.SubElement(project_layers, "maplayer", type="raster", refreshOnNotifyEnabled="0")
    ET.SubElement(pl, "id").text = lyr_id
    ET.SubElement(pl, "datasource").text = lyr_path
    ET.SubElement(pl, "layername").text = lyr_name
    ET.SubElement(pl, "provider").text = "gdal"
    pl_srs = ET.SubElement(pl, "srs")
    pl_auth = ET.SubElement(pl_srs, "spatialrefsys")
    ET.SubElement(pl_auth, "authid").text = "EPSG:4326"

qgs_path = os.path.join(qgis_dir, "horn_vulnerability.qgs")
ET.ElementTree(qgis_root).write(qgs_path, encoding="utf-8", xml_declaration=True)
print(f"Saved QGIS project: {qgs_path}")
