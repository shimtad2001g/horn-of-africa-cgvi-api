# 13_package_gpkg_and_app.py
# Packages harmonized 1 km rasters into an OGC GeoPackage (horn_cgvi_master.gpkg)
# and writes the companion interactive Streamlit dashboard (13_streamlit_explorer.py).
import os
import json
import numpy as np
import rioxarray as rxr
from rasterio.transform import Affine
import rasterio

proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
out_dir = r"C:\GeoProjects\HornVulnerability\output"
scripts_dir = r"C:\GeoProjects\HornVulnerability\scripts"
os.makedirs(out_dir, exist_ok=True)

gpkg_path = os.path.join(out_dir, "horn_cgvi_master.gpkg")
if os.path.exists(gpkg_path):
    os.remove(gpkg_path)

layers = [
    ("drought_hazard_1km", os.path.join(proc_dir, "drought_hazard_1km.tif"), "float32"),
    ("female_exposure_1km", os.path.join(proc_dir, "female_exposure_1km.tif"), "float32"),
    ("slope_sensitivity_1km", os.path.join(proc_dir, "slope_sensitivity_1km.tif"), "float32"),
    ("horn_cgvi_continuous", os.path.join(proc_dir, "horn_cgvi_continuous.tif"), "float32"),
    ("horn_cgvi_classified", os.path.join(proc_dir, "horn_cgvi_classified.tif"), "uint8"),
    ("horn_cgvi_balanced_continuous", os.path.join(proc_dir, "horn_cgvi_balanced_continuous.tif"), "float32"),
    ("horn_cgvi_dominant_driver_1km", os.path.join(proc_dir, "horn_cgvi_dominant_driver_1km.tif"), "uint8"),
]

print("1. Writing OGC GeoPackage raster tables to:", gpkg_path)
written = []
for tbl_name, src_tif, out_dtype in layers:
    if not os.path.exists(src_tif):
        print(f"   [SKIP] Missing source raster: {src_tif}")
        continue
    da = rxr.open_rasterio(src_tif, masked=True).squeeze()
    crs = da.rio.crs or "EPSG:4326"
    transform = da.rio.transform()
    arr = da.values
    if out_dtype == "uint8":
        nodata_val = 0
        data_out = np.nan_to_num(arr, nan=0.0).astype(np.uint8)
    else:
        nodata_val = -9999.0
        data_out = np.where(np.isfinite(arr), arr, nodata_val).astype(np.float32)

    profile = {
        "driver": "GPKG",
        "height": data_out.shape[0],
        "width": data_out.shape[1],
        "count": 1,
        "dtype": out_dtype,
        "crs": crs,
        "transform": transform,
        "nodata": nodata_val,
        "RASTER_TABLE": tbl_name,
    }
    if os.path.exists(gpkg_path):
        profile["APPEND_SUBDATASET"] = "YES"

    with rasterio.open(gpkg_path, "w", **profile) as dst:
        dst.write(data_out, 1)
    print(f"   [OK] Added GeoPackage raster subdataset: {tbl_name} ({out_dtype})")
    written.append(tbl_name)

meta = {
    "package": "horn_cgvi_master.gpkg",
    "standard": "OGC GeoPackage",
    "author": "Shimeles Tadesse Zelelew",
    "gee_project": "ee-shimtad2001g",
    "sources": ["UCSB CHIRPS", "WorldPop 2020", "NASA SRTM"],
    "tables": written,
}
with open(os.path.join(out_dir, "horn_cgvi_master_gpkg_meta.json"), "w", encoding="utf-8") as fm:
    json.dump(meta, fm, indent=2)

app_code = '''# 13_streamlit_explorer.py
# Interactive Streamlit explorer for Horn of Africa Climate & Gender Vulnerability (CGVI)
import os
import numpy as np
import rioxarray as rxr
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Horn of Africa CGVI Explorer",
    page_icon="🌍",
    layout="wide",
)

PROC_DIR = r"C:\\GeoProjects\\HornVulnerability\\data\\processed"
OUT_DIR = r"C:\\GeoProjects\\HornVulnerability\\output"

@st.cache_data
def load_components():
    d = rxr.open_rasterio(os.path.join(PROC_DIR, "drought_hazard_1km.tif"), masked=True).squeeze()
    f = rxr.open_rasterio(os.path.join(PROC_DIR, "female_exposure_1km.tif"), masked=True).squeeze()
    s = rxr.open_rasterio(os.path.join(PROC_DIR, "slope_sensitivity_1km.tif"), masked=True).squeeze()
    base = rxr.open_rasterio(os.path.join(PROC_DIR, "horn_cgvi_continuous.tif"), masked=True).squeeze()
    minx, miny, maxx, maxy = base.rio.bounds()
    return (
        d.values.astype(np.float32),
        f.values.astype(np.float32),
        s.values.astype(np.float32),
        base.values.astype(np.float32),
        [float(minx), float(maxx), float(miny), float(maxy)],
    )

def p2_p98(arr, mask):
    v = arr[mask]
    lo, hi = np.percentile(v, [2, 98])
    if hi <= lo:
        return np.clip(arr, 0.0, 1.0)
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)

st.title("Horn of Africa Climate & Gender Vulnerability (CGVI) Explorer")
st.caption("Open-Source Earth Observation Pipeline • GEE Project: ee-shimtad2001g • Author: Shimeles Tadesse Zelelew")

d_arr, f_arr, s_arr, base_arr, extent = load_components()
valid = np.isfinite(d_arr) & np.isfinite(f_arr) & np.isfinite(s_arr) & np.isfinite(base_arr)

with st.sidebar:
    st.header("MCDA Weights & Rescaling")
    w_d = st.slider("Drought Hazard Weight (CHIRPS)", 0.0, 1.0, 0.45, 0.05)
    w_f = st.slider("Female Exposure Weight (WorldPop)", 0.0, 1.0, 0.40, 0.05)
    w_s = st.slider("Slope Sensitivity Weight (SRTM)", 0.0, 1.0, 0.15, 0.05)

    total_w = w_d + w_f + w_s
    if total_w > 0:
        w_d, w_f, w_s = w_d / total_w, w_f / total_w, w_s / total_w

    use_rescaled = st.checkbox("Apply 2nd–98th Percentile Rescaling", value=True)
    layer_choice = st.selectbox(
        "Display Layer",
        [
            "Custom / Active CGVI Composite",
            "Drought Hazard (1 km)",
            "Female Exposure (1 km)",
            "Slope Sensitivity (1 km)",
        ],
    )
    hotspot_thresh = st.slider("Hotspot Threshold", 0.10, 0.80, 0.40, 0.05)

if use_rescaled:
    d_in = p2_p98(d_arr, valid)
    f_in = p2_p98(f_arr, valid)
    s_in = p2_p98(s_arr, valid)
else:
    d_in, f_in, s_in = d_arr, f_arr, s_arr

cgvi_custom = np.where(valid, w_d * d_in + w_f * f_in + w_s * s_in, np.nan).astype(np.float32)

layer_map = {
    "Custom / Active CGVI Composite": (cgvi_custom, "YlOrRd", "CGVI Score"),
    "Drought Hazard (1 km)": (np.where(valid, d_in, np.nan), "OrRd", "Drought Hazard"),
    "Female Exposure (1 km)": (np.where(valid, f_in, np.nan), "PuBuGn", "Female Exposure"),
    "Slope Sensitivity (1 km)": (np.where(valid, s_in, np.nan), "Greys", "Slope Sensitivity"),
}

plot_arr, cmap_name, cbar_lbl = layer_map[layer_choice]
v_vals = cgvi_custom[valid]
hotspot_px = int((v_vals >= hotspot_thresh).sum())
valid_px = int(valid.sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Normalized Weights", f"{w_d:.2f} / {w_f:.2f} / {w_s:.2f}")
c2.metric("Mean CGVI", f"{np.nanmean(v_vals):.4f}")
c3.metric("Max CGVI", f"{np.nanmax(v_vals):.4f}")
c4.metric(f"Hotspots (≥ {hotspot_thresh:.2f})", f"{hotspot_px:,} px ({hotspot_px / valid_px * 100:.2f}%)")

fig, ax = plt.subplots(figsize=(9.5, 7.2), dpi=200, facecolor="white")
ax.set_facecolor("white")
im = ax.imshow(plot_arr, extent=extent, origin="upper", cmap=cmap_name, vmin=0.0, vmax=max(0.5, float(np.nanpercentile(plot_arr[np.isfinite(plot_arr)], 99))), interpolation="nearest")
ax.set_title(f"Horn of Africa — {layer_choice}", fontsize=11, fontweight="bold")
ax.set_xlabel("Longitude (°E)")
ax.set_ylabel("Latitude (°N / °S)")
ax.grid(True, linestyle="--", linewidth=0.35, alpha=0.4)
cbar = fig.colorbar(im, ax=ax, fraction=0.038, pad=0.02, shrink=0.88)
cbar.set_label(cbar_lbl)
st.pyplot(fig, use_container_width=True)

gpkg_out = os.path.join(OUT_DIR, "horn_cgvi_master.gpkg")
if os.path.exists(gpkg_out):
    st.success(f"OGC GeoPackage available at: {gpkg_out} ({os.path.getsize(gpkg_out):,} bytes)")
'''

app_path = os.path.join(scripts_dir, "13_streamlit_explorer.py")
with open(app_path, "w", encoding="utf-8") as fa:
    fa.write(app_code)
print("Wrote Streamlit explorer:", app_path)
