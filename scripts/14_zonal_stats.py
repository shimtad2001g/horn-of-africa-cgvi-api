# 14_zonal_stats.py
# Computes zonal CGVI statistics over polygon boundaries when available.
import argparse
import glob
import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import rioxarray as rxr
from rasterstats import zonal_stats

BASE_DIR = r"C:\GeoProjects\HornVulnerability"
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR = os.path.join(BASE_DIR, "output")

def find_boundary_file(explicit_path: str | None):
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path
    candidates = []
    for folder in (RAW_DIR, PROC_DIR, BASE_DIR):
        for ext in ("*.gpkg", "*.shp"):
            for p in glob.glob(os.path.join(folder, "**", ext), recursive=True):
                if os.path.basename(p).lower() == "horn_cgvi_master.gpkg":
                    continue
                candidates.append(p)
    return candidates[0] if candidates else None

def main():
    parser = argparse.ArgumentParser(description="Compute zonal CGVI statistics over polygons.")
    parser.add_argument("--boundaries", type=str, default=None, help="Path to polygon boundary file (.gpkg or .shp)")
    parser.add_argument("--threshold", type=float, default=0.40, help="Hotspot threshold")
    args = parser.parse_args()

    b_path = find_boundary_file(args.boundaries)
    if not b_path:
        print("[INFO] No external polygon boundary (.gpkg/.shp) found in data\\raw or data\\processed; skipping zonal stats.")
        sys.exit(0)

    raster_path = os.path.join(PROC_DIR, "horn_cgvi_continuous.tif")
    if not os.path.exists(raster_path):
        print(f"[WARN] Raster not found: {raster_path}")
        sys.exit(0)

    gdf = gpd.read_file(b_path)
    gdf = gdf[gdf.geometry.notnull() & (~gdf.geometry.is_empty)].copy()
    if gdf.empty:
        print("[WARN] Boundary file contains no valid geometries.")
        sys.exit(0)

    da = rxr.open_rasterio(raster_path, masked=True).squeeze()
    raster_crs = da.rio.crs or "EPSG:4326"
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf_proj = gdf.to_crs(raster_crs)

    transform = da.rio.transform()
    arr = da.values.astype(np.float32)
    nodata = da.rio.nodata if da.rio.nodata is not None else np.nan

    stats = zonal_stats(gdf_proj, arr, affine=transform, nodata=nodata, stats=["count", "mean", "max"], all_touched=False)

    # Compute hotspot count per feature
    hotspot_counts = []
    for geom in gdf_proj.geometry:
        sub = zonal_stats([geom], (arr >= args.threshold).astype(np.float32), affine=transform, nodata=0.0, stats=["sum"], all_touched=False)
        hotspot_counts.append(int(round((sub[0]["sum"] or 0.0))))

    name_col = next((c for c in ["NAME_1", "NAME_2", "name", "NAME", "ADM1_EN", "ADM2_EN", "Zone", "Region"] if c in gdf.columns), None)
    rows = []
    for idx, st_row in enumerate(stats):
        cnt = st_row.get("count") or 0
        h_cnt = hotspot_counts[idx]
        rows.append({
            "zone_id": idx,
            "zone_name": str(gdf.iloc[idx][name_col]) if name_col else f"Zone_{idx}",
            "valid_pixels_1km": int(cnt),
            "hotspot_pixels": h_cnt,
            "hotspot_pct": round((h_cnt / cnt * 100.0), 2) if cnt > 0 else 0.0,
            "mean_cgvi": round(float(st_row["mean"]), 4) if st_row.get("mean") is not None else np.nan,
            "max_cgvi": round(float(st_row["max"]), 4) if st_row.get("max") is not None else np.nan,
        })

    out_csv = os.path.join(OUT_DIR, "zonal_cgvi_summary.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"[OK] Zonal statistics written to: {out_csv} ({len(rows)} zones from {os.path.basename(b_path)})")

if __name__ == "__main__":
    main()
