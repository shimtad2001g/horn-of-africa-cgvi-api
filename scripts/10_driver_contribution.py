# 10_driver_contribution.py
# Dominant vulnerability driver mapping & weighted contribution diagnostics across the Horn of Africa (1 km)
import os
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(out_dir, exist_ok=True)

print("1. Loading harmonized 1 km component rasters...")
drought_da = rxr.open_rasterio(os.path.join(proc_dir, "drought_hazard_1km.tif"), masked=True).squeeze()
female_da = rxr.open_rasterio(os.path.join(proc_dir, "female_exposure_1km.tif"), masked=True).squeeze()
slope_da = rxr.open_rasterio(os.path.join(proc_dir, "slope_sensitivity_1km.tif"), masked=True).squeeze()
cgvi_da = rxr.open_rasterio(os.path.join(proc_dir, "horn_cgvi_continuous.tif"), masked=True).squeeze()

w_climate, w_gender, w_terrain = 0.45, 0.40, 0.15

c_drought = (w_climate * drought_da.values).astype(np.float32)
c_female = (w_gender * female_da.values).astype(np.float32)
c_slope = (w_terrain * slope_da.values).astype(np.float32)
cgvi = cgvi_da.values.astype(np.float32)

valid = np.isfinite(cgvi) & (cgvi > 0)

# Stack weighted contributions [3, rows, cols] and find dominant driver (1=Drought, 2=Female Exposure, 3=Slope)
stack = np.stack([c_drought, c_female, c_slope], axis=0)
dom_idx = np.argmax(stack, axis=0).astype(np.uint8) + 1
dom_idx[~valid] = 0

dom_da = xr.DataArray(
    dom_idx,
    coords={"y": cgvi_da.y, "x": cgvi_da.x},
    dims=("y", "x"),
    name="Dominant_Driver",
)
dom_da.rio.write_crs(cgvi_da.rio.crs or "EPSG:4326", inplace=True)
dom_da.rio.write_transform(cgvi_da.rio.transform(), inplace=True)
dom_da.rio.write_nodata(0, encoded=True, inplace=True)

dom_tif_path = os.path.join(proc_dir, "horn_cgvi_dominant_driver_1km.tif")
dom_da.rio.to_raster(dom_tif_path, compress="LZW", tiled=True, dtype="uint8")
print("Saved dominant driver raster:", dom_tif_path)

# Compute mean percentage share of CGVI across all valid pixels and within Moderate Vulnerability (CGVI >= 0.40)
mod_mask = valid & (cgvi >= 0.40)

share_drought_all = np.nanmean(c_drought[valid] / cgvi[valid]) * 100.0
share_female_all = np.nanmean(c_female[valid] / cgvi[valid]) * 100.0
share_slope_all = np.nanmean(c_slope[valid] / cgvi[valid]) * 100.0

share_drought_mod = np.nanmean(c_drought[mod_mask] / cgvi[mod_mask]) * 100.0
share_female_mod = np.nanmean(c_female[mod_mask] / cgvi[mod_mask]) * 100.0
share_slope_mod = np.nanmean(c_slope[mod_mask] / cgvi[mod_mask]) * 100.0

total_px = int(valid.sum())
d1_px = int((dom_idx == 1).sum())
d2_px = int((dom_idx == 2).sum())
d3_px = int((dom_idx == 3).sum())

summary_lines = [
    "Horn of Africa CGVI - Component Contribution & Dominant Driver Summary",
    f"Weights: Drought Hazard = {w_climate:.2f}, Female Exposure = {w_gender:.2f}, Slope Sensitivity = {w_terrain:.2f}",
    "",
    "1. Mean Relative Contribution to CGVI Score:",
    f"   All Valid Pixels (n={total_px:,}): Drought = {share_drought_all:.2f}% | Female Exposure = {share_female_all:.2f}% | Slope = {share_slope_all:.2f}%",
    f"   Moderate Hotspots (CGVI >= 0.40, n={int(mod_mask.sum()):,}): Drought = {share_drought_mod:.2f}% | Female Exposure = {share_female_mod:.2f}% | Slope = {share_slope_mod:.2f}%",
    "",
    "2. Dominant Driver Footprint (Pixel Share):",
    f"   Driver 1 - Drought Hazard (0.45 * SPI)   : {d1_px:,} px ({d1_px / total_px * 100.0:.2f}%)",
    f"   Driver 2 - Female Exposure (0.40 * Pop)  : {d2_px:,} px ({d2_px / total_px * 100.0:.2f}%)",
    f"   Driver 3 - Slope Sensitivity (0.15 * DEM): {d3_px:,} px ({d3_px / total_px * 100.0:.2f}%)",
]

report_path = os.path.join(out_dir, "horn_cgvi_driver_summary.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines) + "\n")
print("Saved driver summary:", report_path)

print("2. Rendering 300 & 600 DPI Dominant Driver & Contribution Figure...")
minx, miny, maxx, maxy = cgvi_da.rio.bounds()
extent = [minx, maxx, miny, maxy]

dom_plot = np.where(dom_idx > 0, dom_idx.astype(np.float32), np.nan)
cmap = ListedColormap(["#d95f02", "#7570b3", "#1b9e77"])
norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 6.8), dpi=600, facecolor="white", gridspec_kw={"width_ratios": [1.35, 1.0]})
fig.patch.set_facecolor("white")

# Left Panel: Spatial Dominant Driver Map
im = ax1.imshow(dom_plot, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
ax1.set_facecolor("white")
ax1.set_title("A. Primary Vulnerability Driver by 1 km Cell", fontsize=11, fontweight="bold", pad=10, color="#111111")
ax1.set_xlabel("Longitude (°E)", fontsize=9.5)
ax1.set_ylabel("Latitude (°N / °S)", fontsize=9.5)
ax1.grid(True, linestyle="--", linewidth=0.4, color="#888888", alpha=0.45)

cbar = fig.colorbar(im, ax=ax1, ticks=[1, 2, 3], fraction=0.042, pad=0.03, shrink=0.85)
cbar.ax.set_yticklabels(["Drought Hazard\n(0.45 × SPI)", "Female Exposure\n(0.40 × Pop)", "Slope Sensitivity\n(0.15 × DEM)"], fontsize=8)

# Right Panel: Grouped Bar Comparison (Regional Mean vs Moderate Hotspots)
categories = ["Drought Hazard\n(w=0.45)", "Female Exposure\n(w=0.40)", "Slope Sensitivity\n(w=0.15)"]
all_shares = [share_drought_all, share_female_all, share_slope_all]
mod_shares = [share_drought_mod, share_female_mod, share_slope_mod]

x = np.arange(len(categories))
width = 0.35

rects1 = ax2.bar(x - width / 2, all_shares, width, label="All Regional Pixels", color="#4c78a8", edgecolor="#222222", linewidth=0.6)
rects2 = ax2.bar(x + width / 2, mod_shares, width, label="Moderate Hotspots (CGVI ≥ 0.40)", color="#e45756", edgecolor="#222222", linewidth=0.6)

ax2.set_facecolor("white")
ax2.set_title("B. Mean Weighted Contribution to CGVI (%)", fontsize=11, fontweight="bold", pad=10, color="#111111")
ax2.set_ylabel("Share of Total CGVI Score (%)", fontsize=9.5)
ax2.set_xticks(x)
ax2.set_xticklabels(categories, fontsize=8.5)
ax2.set_ylim(0, max(max(all_shares), max(mod_shares)) * 1.22)
ax2.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#888888", alpha=0.45)
ax2.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.5, loc="upper right")

for rect in list(rects1) + list(rects2):
    h = rect.get_height()
    ax2.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                 textcoords="offset points", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#222222")

fig.suptitle("Horn of Africa CGVI: Component Contribution & Dominant Driver Analysis (~1 km)", fontsize=12.5, fontweight="bold", y=0.97, color="#111111")
footer = "Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM (GEE: ee-shimtad2001g)  |  Author: Shimeles Tadesse Zelelew"
fig.text(0.5, 0.015, footer, ha="center", va="bottom", fontsize=7.5, color="#333333")

plt.tight_layout(rect=[0.0, 0.04, 1.0, 0.93])
out_600 = os.path.join(out_dir, "horn_cgvi_driver_analysis_600dpi.png")
out_300 = os.path.join(out_dir, "horn_cgvi_driver_analysis_300dpi.png")
fig.savefig(out_600, dpi=600, facecolor="white")
fig.savefig(out_300, dpi=300, facecolor="white")
plt.close(fig)

print("Saved 600 DPI driver figure:", out_600)
print("Saved 300 DPI driver figure:", out_300)
