# 09_country_focus_ethiopia.py
# Country/sub-national focus extraction (Ethiopia regional extent), reprojected to UTM Zone 37N (EPSG:32637)
# plus equal-area area summary and 300/600 DPI clean white-background cartography.
import os
import numpy as np
import rioxarray as rxr
from rasterio.enums import Resampling
import matplotlib.pyplot as plt

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(out_dir, exist_ok=True)

cgvi_path = os.path.join(proc_dir, "horn_cgvi_continuous.tif")
cls_path = os.path.join(proc_dir, "horn_cgvi_classified.tif")
drought_path = os.path.join(proc_dir, "drought_hazard_1km.tif")
female_path = os.path.join(proc_dir, "female_exposure_1km.tif")
slope_path = os.path.join(proc_dir, "slope_sensitivity_1km.tif")

print("1. Loading processed 1 km layers...")
cgvi_da = rxr.open_rasterio(cgvi_path, masked=True).squeeze()
cls_da = rxr.open_rasterio(cls_path, masked=True).squeeze()
drought_da = rxr.open_rasterio(drought_path, masked=True).squeeze()
female_da = rxr.open_rasterio(female_path, masked=True).squeeze()
slope_da = rxr.open_rasterio(slope_path, masked=True).squeeze()

for da in (cgvi_da, cls_da, drought_da, female_da, slope_da):
    if da.rio.crs is None:
        da.rio.write_crs("EPSG:4326", inplace=True)

# Ethiopia regional clip window in EPSG:4326 [minx, miny, maxx, maxy]
eth_bbox = [33.0, 3.3, 48.0, 15.0]
print(f"2. Clipping to Ethiopia regional window {eth_bbox} (EPSG:4326)...")
cgvi_eth_4326 = cgvi_da.rio.clip_box(*eth_bbox)
cls_eth_4326 = cls_da.rio.clip_box(*eth_bbox)
drought_eth_4326 = drought_da.rio.clip_box(*eth_bbox)
female_eth_4326 = female_da.rio.clip_box(*eth_bbox)
slope_eth_4326 = slope_da.rio.clip_box(*eth_bbox)

# Reproject to UTM Zone 37N (EPSG:32637) at 1,000 m resolution for local cartography
target_crs = "EPSG:32637"
print(f"3. Reprojecting Ethiopia focus layers to {target_crs} (1,000 m)...")
cgvi_utm37 = cgvi_eth_4326.rio.reproject(target_crs, resolution=1000.0, resampling=Resampling.bilinear)
cls_utm37 = cls_eth_4326.rio.reproject(target_crs, resolution=1000.0, resampling=Resampling.nearest)

# Also compute equal-area (Africa Albers Equal Area) area stats for the clipped window
africa_aea_proj = (
    "+proj=aea +lat_1=20 +lat_2=-23 +lat_0=0 +lon_0=25 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
cls_aea = cls_eth_4326.rio.reproject(africa_aea_proj, resolution=1000.0, resampling=Resampling.nearest)
dx_aea, dy_aea = cls_aea.rio.resolution()
px_area_km2 = abs(dx_aea * dy_aea) / 1e6

# Save clipped & UTM Zone 37N GeoTIFFs
cgvi_utm37_path = os.path.join(proc_dir, "eth_focus_cgvi_utm37n_1km.tif")
cls_utm37_path = os.path.join(proc_dir, "eth_focus_cgvi_class_utm37n_1km.tif")
cgvi_utm37.rio.to_raster(cgvi_utm37_path, compress="LZW", tiled=True)
cls_utm37.rio.to_raster(cls_utm37_path, compress="LZW", tiled=True, dtype="uint8")

vals = cgvi_utm37.values.astype(np.float32)
valid = vals[np.isfinite(vals)]
cls_aea_vals = cls_aea.values
total_valid_px = int(((cls_aea_vals >= 1) & (cls_aea_vals <= 5)).sum())
total_area_km2 = total_valid_px * px_area_km2

labels = {
    1: "Very Low (0.00 - 0.20)",
    2: "Low      (0.20 - 0.40)",
    3: "Moderate (0.40 - 0.60)",
    4: "High     (0.60 - 0.80)",
    5: "Very High(0.80 - 1.00)",
}

report_lines = [
    "Ethiopia Regional Focus - Climate & Gender Vulnerability (CGVI)",
    f"Cartographic CRS: {target_crs} (UTM Zone 37N, 1,000 m) | Area CRS: Africa Albers Equal Area (1,000 m)",
    f"Clip Box (EPSG:4326): {eth_bbox}",
    f"CGVI Stats (UTM 37N) -> Min: {valid.min():.4f}, Mean: {valid.mean():.4f}, Max: {valid.max():.4f}, Std: {valid.std():.4f}",
    f"Mapped Area (Classes 1-5): {total_area_km2:,.2f} sq km",
    "",
    "Equal-Area Class Breakdown:",
]
for k, desc in labels.items():
    cnt = int((cls_aea_vals == k).sum())
    area = cnt * px_area_km2
    pct = (area / total_area_km2 * 100.0) if total_area_km2 > 0 else 0.0
    report_lines.append(f"  Class {k} - {desc}: {cnt:,} px | {area:,.2f} sq km ({pct:.2f}%)")

eth_report_path = os.path.join(out_dir, "eth_focus_cgvi_summary.txt")
with open(eth_report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")
print("Saved Ethiopia focus summary:", eth_report_path)

print("4. Rendering 300 & 600 DPI Ethiopia focus map (UTM Zone 37N, clean white background)...")
minx, miny, maxx, maxy = cgvi_utm37.rio.bounds()
extent = [minx / 1000.0, maxx / 1000.0, miny / 1000.0, maxy / 1000.0]

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8

fig, ax = plt.subplots(figsize=(9.5, 8.2), dpi=600, facecolor="white")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

im = ax.imshow(
    vals,
    extent=extent,
    origin="upper",
    cmap="YlOrRd",
    vmin=np.nanpercentile(valid, 1),
    vmax=np.nanpercentile(valid, 99),
    interpolation="nearest",
)
ax.set_title(
    "Ethiopia Regional Focus: Climate & Gender Vulnerability (CGVI, ~1 km)",
    fontsize=12,
    fontweight="bold",
    pad=12,
    color="#111111",
)
ax.set_xlabel("Easting (km, EPSG:32637 / UTM Zone 37N)", fontsize=9.5, color="#222222")
ax.set_ylabel("Northing (km, EPSG:32637 / UTM Zone 37N)", fontsize=9.5, color="#222222")
ax.grid(True, linestyle="--", linewidth=0.4, color="#888888", alpha=0.45)

cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03, shrink=0.88)
cbar.set_label("CGVI Score (0.45 SPI + 0.40 Female + 0.15 Slope)", fontsize=8.5, color="#222222")
cbar.ax.tick_params(labelsize=8)

# North arrow
ax.annotate(
    "N",
    xy=(extent[1] - 120, extent[3] - 140),
    xytext=(extent[1] - 120, extent[3] - 260),
    ha="center",
    va="bottom",
    fontsize=10,
    fontweight="bold",
    color="#111111",
    arrowprops=dict(facecolor="#111111", width=2.0, headwidth=6.5, headlength=6.5),
)

# Scale bar (~300 km)
sb_x0 = extent[0] + 100
sb_x1 = sb_x0 + 300
sb_y = extent[2] + 90
ax.plot([sb_x0, sb_x1], [sb_y, sb_y], color="#111111", linewidth=2.5)
ax.text((sb_x0 + sb_x1) / 2, sb_y + 28, "300 km", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#111111")

footer = (
    f"Clip: {eth_bbox} | Mean CGVI: {valid.mean():.4f} | Area: {total_area_km2:,.0f} sq km  |  "
    "Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM (GEE: ee-shimtad2001g)  |  Author: Shimeles Tadesse Zelelew"
)
fig.text(0.5, 0.012, footer, ha="center", va="bottom", fontsize=7.2, color="#333333")
plt.tight_layout(rect=[0.0, 0.035, 1.0, 0.95])

out_600 = os.path.join(out_dir, "eth_focus_cgvi_utm37n_600dpi.png")
out_300 = os.path.join(out_dir, "eth_focus_cgvi_utm37n_300dpi.png")
fig.savefig(out_600, dpi=600, facecolor="white")
fig.savefig(out_300, dpi=300, facecolor="white")
plt.close(fig)

print("Saved 600 DPI map:", out_600)
print("Saved 300 DPI map:", out_300)
