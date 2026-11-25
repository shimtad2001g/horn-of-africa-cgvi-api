# 11_sensitivity_and_rescaling.py
# Component distribution diagnostics, weight sensitivity (0.45/0.40/0.15 vs equal weights),
# and 2nd-98th percentile rescaled balanced MCDA composite for the Horn of Africa (~1 km).
import os
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(out_dir, exist_ok=True)

print("1. Loading harmonized 1 km component rasters...")
drought_da = rxr.open_rasterio(os.path.join(proc_dir, "drought_hazard_1km.tif"), masked=True).squeeze()
female_da = rxr.open_rasterio(os.path.join(proc_dir, "female_exposure_1km.tif"), masked=True).squeeze()
slope_da = rxr.open_rasterio(os.path.join(proc_dir, "slope_sensitivity_1km.tif"), masked=True).squeeze()
base_cgvi_da = rxr.open_rasterio(os.path.join(proc_dir, "horn_cgvi_continuous.tif"), masked=True).squeeze()

d = drought_da.values.astype(np.float32)
f = female_da.values.astype(np.float32)
s = slope_da.values.astype(np.float32)
base = base_cgvi_da.values.astype(np.float32)

valid = np.isfinite(d) & np.isfinite(f) & np.isfinite(s) & np.isfinite(base)

def dist_stats(arr, mask):
    v = arr[mask]
    p2, p50, p95, p98, p99 = np.percentile(v, [2, 50, 95, 98, 99])
    return (
        f"min={v.min():.4f}, p2={p2:.4f}, median={p50:.4f}, mean={v.mean():.4f}, "
        f"p95={p95:.4f}, p98={p98:.4f}, p99={p99:.4f}, max={v.max():.4f}, std={v.std():.4f}"
    )

def p2_p98_rescale(arr, mask):
    v = arr[mask]
    lo, hi = np.percentile(v, [2, 98])
    if hi <= lo:
        return np.clip(arr, 0.0, 1.0)
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)

print("2. Computing distribution diagnostics and sensitivity scenarios...")
d_res = p2_p98_rescale(d, valid)
f_res = p2_p98_rescale(f, valid)
s_res = p2_p98_rescale(s, valid)

# Scenario A: Baseline (0.45 / 0.40 / 0.15 on raw normalized inputs)
scen_base = np.where(valid, base, np.nan).astype(np.float32)

# Scenario B: Equal Weights (1/3 each on raw normalized inputs)
scen_equal = np.where(valid, (d + f + s) / 3.0, np.nan).astype(np.float32)

# Scenario C: Balanced Percentile-Rescaled (0.45 / 0.40 / 0.15 on p2-p98 rescaled inputs)
scen_balanced = np.where(valid, 0.45 * d_res + 0.40 * f_res + 0.15 * s_res, np.nan).astype(np.float32)

# Save Balanced CGVI continuous & 5-class rasters for downstream comparison
bal_da = xr.DataArray(
    scen_balanced,
    coords={"y": base_cgvi_da.y, "x": base_cgvi_da.x},
    dims=("y", "x"),
    name="CGVI_Balanced",
)
bal_da.rio.write_crs(base_cgvi_da.rio.crs or "EPSG:4326", inplace=True)
bal_da.rio.write_transform(base_cgvi_da.rio.transform(), inplace=True)
bal_da.rio.write_nodata(np.nan, encoded=True, inplace=True)
bal_cont_path = os.path.join(proc_dir, "horn_cgvi_balanced_continuous.tif")
bal_da.rio.to_raster(bal_cont_path, compress="LZW", tiled=True)

# Classify balanced CGVI into 5 standard 0.20-interval classes
bal_cls = np.zeros(scen_balanced.shape, dtype=np.uint8)
bal_cls[valid & (scen_balanced < 0.20)] = 1
bal_cls[valid & (scen_balanced >= 0.20) & (scen_balanced < 0.40)] = 2
bal_cls[valid & (scen_balanced >= 0.40) & (scen_balanced < 0.60)] = 3
bal_cls[valid & (scen_balanced >= 0.60) & (scen_balanced < 0.80)] = 4
bal_cls[valid & (scen_balanced >= 0.80)] = 5

bal_cls_da = xr.DataArray(
    bal_cls,
    coords={"y": base_cgvi_da.y, "x": base_cgvi_da.x},
    dims=("y", "x"),
    name="CGVI_Balanced_Class",
)
bal_cls_da.rio.write_crs(base_cgvi_da.rio.crs or "EPSG:4326", inplace=True)
bal_cls_da.rio.write_transform(base_cgvi_da.rio.transform(), inplace=True)
bal_cls_da.rio.write_nodata(0, encoded=True, inplace=True)
bal_cls_path = os.path.join(proc_dir, "horn_cgvi_balanced_classified.tif")
bal_cls_da.rio.to_raster(bal_cls_path, compress="LZW", tiled=True, dtype="uint8")

# Effective driver shares under Balanced Rescaled scenario
bal_valid = valid & (scen_balanced > 0)
sh_d_bal = np.nanmean((0.45 * d_res[bal_valid]) / scen_balanced[bal_valid]) * 100.0
sh_f_bal = np.nanmean((0.40 * f_res[bal_valid]) / scen_balanced[bal_valid]) * 100.0
sh_s_bal = np.nanmean((0.15 * s_res[bal_valid]) / scen_balanced[bal_valid]) * 100.0

# Rank correlation (Spearman-like via rank Pearson) between Baseline and Balanced
r_base_eq = float(np.corrcoef(scen_base[valid], scen_equal[valid])[0, 1])
r_base_bal = float(np.corrcoef(scen_base[valid], scen_balanced[valid])[0, 1])

total_px = int(valid.sum())
cls_summary = []
for k, lbl in [(1, "Very Low (<0.20)"), (2, "Low (0.20-0.40)"), (3, "Moderate (0.40-0.60)"), (4, "High (0.60-0.80)"), (5, "Very High (>=0.80)")]:
    cnt = int((bal_cls == k).sum())
    cls_summary.append(f"   Class {k} - {lbl:19s}: {cnt:,} px ({cnt / total_px * 100.0:.2f}%)")

report_lines = [
    "Horn of Africa CGVI - Component Distribution & MCDA Sensitivity Report",
    f"Valid 1 km Cells Analyzed: {total_px:,}",
    "",
    "1. Raw Harmonized Input Distributions (0-1 scale):",
    f"   Drought Hazard (SPI)   : {dist_stats(d, valid)}",
    f"   Female Exposure (Pop)  : {dist_stats(f, valid)}",
    f"   Slope Sensitivity (DEM): {dist_stats(s, valid)}",
    "",
    "2. Composite Scenario Comparison:",
    f"   A. Baseline (0.45/0.40/0.15, raw)          : {dist_stats(scen_base, valid)}",
    f"   B. Equal Weights (0.33/0.33/0.33, raw)     : {dist_stats(scen_equal, valid)}",
    f"   C. Balanced Rescaled (0.45/0.40/0.15, p2-98): {dist_stats(scen_balanced, valid)}",
    f"   Pearson r (Baseline vs Equal Weights)      : {r_base_eq:.4f}",
    f"   Pearson r (Baseline vs Balanced Rescaled)  : {r_base_bal:.4f}",
    "",
    "3. Effective Mean Component Share in Scenario C (Balanced Rescaled):",
    f"   Drought Hazard = {sh_d_bal:.2f}% | Female Exposure = {sh_f_bal:.2f}% | Slope Sensitivity = {sh_s_bal:.2f}%",
    "",
    "4. Scenario C (Balanced Rescaled) 5-Class Pixel Breakdown:",
    *cls_summary,
]

report_path = os.path.join(out_dir, "horn_cgvi_sensitivity_report.txt")
with open(report_path, "w", encoding="utf-8") as fp:
    fp.write("\n".join(report_lines) + "\n")
print("Saved sensitivity report:", report_path)

print("3. Rendering 300 & 600 DPI 3-Panel Sensitivity Comparison Map...")
minx, miny, maxx, maxy = base_cgvi_da.rio.bounds()
extent = [minx, maxx, miny, maxy]

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8

fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.8), dpi=600, facecolor="white")
fig.patch.set_facecolor("white")

panels = [
    (scen_base, "A. Baseline CGVI\n(0.45 / 0.40 / 0.15, Raw)"),
    (scen_equal, "B. Equal-Weight CGVI\n(0.33 / 0.33 / 0.33, Raw)"),
    (scen_balanced, "C. Balanced Rescaled CGVI\n(0.45 / 0.40 / 0.15, P2–P98)"),
]

for ax, (arr, title) in zip(axes, panels):
    ax.set_facecolor("white")
    im = ax.imshow(arr, extent=extent, origin="upper", cmap="YlOrRd", vmin=0.0, vmax=0.85, interpolation="nearest")
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8, color="#111111")
    ax.set_xlabel("Longitude (°E)", fontsize=8.5)
    ax.grid(True, linestyle="--", linewidth=0.35, color="#888888", alpha=0.45)
    ax.tick_params(labelsize=8)

axes[0].set_ylabel("Latitude (°N / °S)", fontsize=8.5)

cbar = fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.022, pad=0.02, shrink=0.84)
cbar.set_label("Composite Vulnerability Index (0–1)", fontsize=8.5, color="#222222")
cbar.ax.tick_params(labelsize=8)

fig.suptitle("Horn of Africa CGVI: Weight & Percentile-Rescaling Sensitivity Analysis (~1 km)", fontsize=12, fontweight="bold", y=0.97, color="#111111")
footer = "Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM (GEE: ee-shimtad2001g)  |  Author: Shimeles Tadesse Zelelew"
fig.text(0.5, 0.015, footer, ha="center", va="bottom", fontsize=7.5, color="#333333")

plt.subplots_adjust(left=0.05, right=0.90, top=0.84, bottom=0.13, wspace=0.16)
out_600 = os.path.join(out_dir, "horn_cgvi_sensitivity_600dpi.png")
out_300 = os.path.join(out_dir, "horn_cgvi_sensitivity_300dpi.png")
fig.savefig(out_600, dpi=600, facecolor="white")
fig.savefig(out_300, dpi=300, facecolor="white")
plt.close(fig)

print("Saved 600 DPI sensitivity figure:", out_600)
print("Saved 300 DPI sensitivity figure:", out_300)
