# 13_streamlit_explorer.py
# Enhanced interactive Streamlit explorer for Horn of Africa & Ethiopia Focus CGVI
import io
import os
import tempfile
import numpy as np
import rioxarray as rxr
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Horn of Africa & Ethiopia CGVI Explorer",
    page_icon="🌍",
    layout="wide",
)

PROC_DIR = r"C:\GeoProjects\HornVulnerability\data\processed"
OUT_DIR = r"C:\GeoProjects\HornVulnerability\output"
ETH_BBOX = [33.0, 3.3, 48.0, 15.0]

@st.cache_data
def load_region_data(region_mode: str):
    d_da = rxr.open_rasterio(os.path.join(PROC_DIR, "drought_hazard_1km.tif"), masked=True).squeeze()
    f_da = rxr.open_rasterio(os.path.join(PROC_DIR, "female_exposure_1km.tif"), masked=True).squeeze()
    s_da = rxr.open_rasterio(os.path.join(PROC_DIR, "slope_sensitivity_1km.tif"), masked=True).squeeze()
    b_da = rxr.open_rasterio(os.path.join(PROC_DIR, "horn_cgvi_continuous.tif"), masked=True).squeeze()

    for da in (d_da, f_da, s_da, b_da):
        if da.rio.crs is None:
            da.rio.write_crs("EPSG:4326", inplace=True)

    if region_mode == "Ethiopia Focus (UTM 37N / EPSG:32637)":
        d_da = d_da.rio.clip_box(*ETH_BBOX).rio.reproject("EPSG:32637", resolution=1000.0, resampling=Resampling.bilinear)
        f_da = f_da.rio.clip_box(*ETH_BBOX).rio.reproject("EPSG:32637", resolution=1000.0, resampling=Resampling.bilinear)
        s_da = s_da.rio.clip_box(*ETH_BBOX).rio.reproject("EPSG:32637", resolution=1000.0, resampling=Resampling.bilinear)
        b_da = b_da.rio.clip_box(*ETH_BBOX).rio.reproject("EPSG:32637", resolution=1000.0, resampling=Resampling.bilinear)
        minx, miny, maxx, maxy = b_da.rio.bounds()
        extent = [float(minx) / 1000.0, float(maxx) / 1000.0, float(miny) / 1000.0, float(maxy) / 1000.0]
        xlabel = "Easting (km, EPSG:32637)"
        ylabel = "Northing (km, EPSG:32637)"
    else:
        minx, miny, maxx, maxy = b_da.rio.bounds()
        extent = [float(minx), float(maxx), float(miny), float(maxy)]
        xlabel = "Longitude (°E)"
        ylabel = "Latitude (°N / °S)"

    return {
        "d": d_da.values.astype(np.float32),
        "f": f_da.values.astype(np.float32),
        "s": s_da.values.astype(np.float32),
        "base": b_da.values.astype(np.float32),
        "template": b_da,
        "extent": extent,
        "xlabel": xlabel,
        "ylabel": ylabel,
    }

def p2_p98(arr, mask):
    v = arr[mask]
    if v.size == 0:
        return np.clip(arr, 0.0, 1.0).astype(np.float32)
    lo, hi = np.percentile(v, [2, 98])
    if hi <= lo:
        return np.clip(arr, 0.0, 1.0).astype(np.float32)
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)

st.title("Horn of Africa & Ethiopia Climate & Gender Vulnerability (CGVI) Explorer")
st.caption("Open-Source EO Pipeline • GEE: ee-shimtad2001g • Sources: UCSB CHIRPS, WorldPop 2020, NASA SRTM • Author: Shimeles Tadesse Zelelew")

with st.sidebar:
    st.header("Spatial Extent & Layer")
    region_mode = st.radio(
        "Study Extent",
        ["Horn of Africa (EPSG:4326)", "Ethiopia Focus (UTM 37N / EPSG:32637)"],
        index=0,
    )
    layer_choice = st.selectbox(
        "Display Layer",
        [
            "Custom / Active CGVI Composite",
            "Drought Hazard (1 km)",
            "Female Exposure (1 km)",
            "Slope Sensitivity (1 km)",
        ],
    )

    st.header("MCDA Weights & Rescaling")
    w_d = st.slider("Drought Hazard Weight", 0.0, 1.0, 0.45, 0.05)
    w_f = st.slider("Female Exposure Weight", 0.0, 1.0, 0.40, 0.05)
    w_s = st.slider("Slope Sensitivity Weight", 0.0, 1.0, 0.15, 0.05)

    total_w = w_d + w_f + w_s
    if total_w > 0:
        w_d, w_f, w_s = w_d / total_w, w_f / total_w, w_s / total_w

    use_rescaled = st.checkbox("Apply 2nd-98th Percentile Rescaling", value=True)
    hotspot_thresh = st.slider("Hotspot Threshold", 0.10, 0.80, 0.40, 0.05)

data = load_region_data(region_mode)
d_arr, f_arr, s_arr, base_arr = data["d"], data["f"], data["s"], data["base"]
valid = np.isfinite(d_arr) & np.isfinite(f_arr) & np.isfinite(s_arr) & np.isfinite(base_arr)

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
valid_px = int(valid.sum())
hotspot_px = int((v_vals >= hotspot_thresh).sum()) if valid_px > 0 else 0
hotspot_pct = (hotspot_px / valid_px * 100.0) if valid_px > 0 else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Normalized Weights", f"{w_d:.2f} / {w_f:.2f} / {w_s:.2f}")
c2.metric("Mean CGVI", f"{np.nanmean(v_vals):.4f}" if valid_px > 0 else "N/A")
c3.metric("Max CGVI", f"{np.nanmax(v_vals):.4f}" if valid_px > 0 else "N/A")
c4.metric(f"Hotspots (greater than or equal to {hotspot_thresh:.2f})", f"{hotspot_px:,} px ({hotspot_pct:.2f}%)")

finite_plot = plot_arr[np.isfinite(plot_arr)]
vmax_val = max(0.5, float(np.nanpercentile(finite_plot, 99))) if finite_plot.size > 0 else 1.0

fig, ax = plt.subplots(figsize=(9.5, 7.2), dpi=200, facecolor="white")
ax.set_facecolor("white")
im = ax.imshow(plot_arr, extent=data["extent"], origin="upper", cmap=cmap_name, vmin=0.0, vmax=vmax_val, interpolation="nearest")
ax.set_title(f"{region_mode} - {layer_choice}", fontsize=11, fontweight="bold")
ax.set_xlabel(data["xlabel"])
ax.set_ylabel(data["ylabel"])
ax.grid(True, linestyle="--", linewidth=0.35, alpha=0.4)
cbar = fig.colorbar(im, ax=ax, fraction=0.038, pad=0.02, shrink=0.88)
cbar.set_label(cbar_lbl)
st.pyplot(fig, use_container_width=True)

st.subheader("Export Active Snapshot")
exp_c1, exp_c2 = st.columns(2)

csv_buf = io.StringIO()
csv_buf.write("extent,rescaling_p2_p98,w_drought,w_female,w_slope,hotspot_threshold,valid_pixels,hotspot_pixels,hotspot_pct,mean_cgvi,max_cgvi\n")
csv_buf.write(
    f"\"{region_mode}\",{use_rescaled},{w_d:.4f},{w_f:.4f},{w_s:.4f},{hotspot_thresh:.2f},"
    f"{valid_px},{hotspot_px},{hotspot_pct:.4f},{np.nanmean(v_vals):.6f},{np.nanmax(v_vals):.6f}\n"
)
exp_c1.download_button(
    label="Download Summary CSV",
    data=csv_buf.getvalue().encode("utf-8"),
    file_name="cgvi_active_snapshot_summary.csv",
    mime="text/csv",
)

out_da = data["template"].copy(data=cgvi_custom)
out_da.rio.write_nodata(np.nan, encoded=True, inplace=True)
with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp_tif:
    tmp_path = tmp_tif.name
out_da.rio.to_raster(tmp_path, compress="LZW")
with open(tmp_path, "rb") as ft:
    tif_bytes = ft.read()
os.remove(tmp_path)

exp_c2.download_button(
    label="Download Active Composite GeoTIFF",
    data=tif_bytes,
    file_name="cgvi_active_composite.tif",
    mime="image/tiff",
)

gpkg_out = os.path.join(OUT_DIR, "horn_cgvi_master.gpkg")
if os.path.exists(gpkg_out):
    st.info(f"Master OGC GeoPackage on disk: {gpkg_out} ({os.path.getsize(gpkg_out):,} bytes)")
