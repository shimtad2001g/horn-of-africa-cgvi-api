# 06_equal_area_zonal.py
import os
import numpy as np
import rioxarray as rxr
from rasterio.enums import Resampling

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(out_dir, exist_ok=True)

# Standard Africa Albers Equal Area Conic PROJ string (meters)
africa_aea_proj = (
    "+proj=aea +lat_1=20 +lat_2=-23 +lat_0=0 +lon_0=25 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

print("1. Loading continuous and classified CGVI layers...")
cgvi_cont = rxr.open_rasterio(os.path.join(proc_dir, "horn_cgvi_continuous.tif"), masked=True).squeeze()
cgvi_cls = rxr.open_rasterio(os.path.join(proc_dir, "horn_cgvi_classified.tif"), masked=True).squeeze()

if cgvi_cont.rio.crs is None:
    cgvi_cont.rio.write_crs("EPSG:4326", inplace=True)
if cgvi_cls.rio.crs is None:
    cgvi_cls.rio.write_crs("EPSG:4326", inplace=True)

print("2. Reprojecting to Africa Albers Equal Area Conic (1,000 m resolution)...")
cgvi_aea = cgvi_cont.rio.reproject(
    africa_aea_proj,
    resolution=1000.0,
    resampling=Resampling.bilinear,
)
cls_aea = cgvi_cls.rio.reproject(
    africa_aea_proj,
    resolution=1000.0,
    resampling=Resampling.nearest,
)

aea_cont_path = os.path.join(proc_dir, "horn_cgvi_continuous_aea_1km.tif")
aea_cls_path = os.path.join(proc_dir, "horn_cgvi_classified_aea_1km.tif")
cgvi_aea.rio.to_raster(aea_cont_path, compress="LZW", tiled=True)
cls_aea.rio.to_raster(aea_cls_path, compress="LZW", tiled=True, dtype="uint8")

# Exact pixel area in sq km from transform cell width * height (in meters)
dx, dy = cgvi_aea.rio.resolution()
pixel_area_sq_km = abs(dx * dy) / 1e6

cls_vals = cls_aea.values
cont_vals = cgvi_aea.values
valid_cont = cont_vals[np.isfinite(cont_vals)]

labels = {
    1: "Very Low (0.00 - 0.20)",
    2: "Low      (0.20 - 0.40)",
    3: "Moderate (0.40 - 0.60)",
    4: "High     (0.60 - 0.80)",
    5: "Very High(0.80 - 1.00)",
}

valid_cls_mask = (cls_vals >= 1) & (cls_vals <= 5)
total_area_sq_km = int(valid_cls_mask.sum()) * pixel_area_sq_km

summary_lines = [
    "Horn of Africa Climate & Gender Vulnerability - Equal Area Summary",
    "Projection: Africa Albers Equal Area Conic (meters, 1000 m nominal cell)",
    f"Pixel Area: {pixel_area_sq_km:,.4f} sq km",
    f"Total Mapped Area (Classes 1-5): {total_area_sq_km:,.2f} sq km",
    f"Continuous CGVI -> Min: {valid_cont.min():.4f}, Mean: {valid_cont.mean():.4f}, Max: {valid_cont.max():.4f}, Std: {valid_cont.std():.4f}",
    "",
    "Class Breakdown:",
]

for k, desc in labels.items():
    px_cnt = int((cls_vals == k).sum())
    area_km2 = px_cnt * pixel_area_sq_km
    pct = (area_km2 / total_area_sq_km * 100.0) if total_area_sq_km > 0 else 0.0
    line = f"  Class {k} - {desc}: {px_cnt:,} px | {area_km2:,.2f} sq km ({pct:.2f}%)"
    summary_lines.append(line)

report_text = "\n".join(summary_lines)
print("\n" + report_text)

report_path = os.path.join(out_dir, "horn_cgvi_equal_area_summary.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_text + "\n")
print(f"\nSaved area summary report: {report_path}")
