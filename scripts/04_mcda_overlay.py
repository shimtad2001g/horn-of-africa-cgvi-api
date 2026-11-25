# 04_mcda_overlay.py
import os
import numpy as np
import rioxarray as rxr
from rasterio.enums import Resampling

raw_dir = r"C:\GeoProjects\HornVulnerability\data\raw"
proc_dir = r"C:\GeoProjects\HornVulnerability\data\processed"
os.makedirs(proc_dir, exist_ok=True)

print("1. Loading raw GeoTIFF layers...")
slope_da = rxr.open_rasterio(os.path.join(raw_dir, "slope_norm.tif"), masked=True).squeeze()
female_da = rxr.open_rasterio(os.path.join(raw_dir, "female_norm.tif"), masked=True).squeeze()
spi_da = rxr.open_rasterio(os.path.join(raw_dir, "spi_norm.tif"), masked=True).squeeze()

# Ensure CRS is explicitly EPSG:4326
for da in (slope_da, female_da, spi_da):
    if da.rio.crs is None:
        da.rio.write_crs("EPSG:4326", inplace=True)

print("2. Harmonizing grids to 1 km master grid (matching slope_norm.tif)...")
female_aligned = female_da.rio.reproject_match(slope_da, resampling=Resampling.bilinear).fillna(0.0).clip(0.0, 1.0)
spi_aligned = spi_da.rio.reproject_match(slope_da, resampling=Resampling.bilinear).fillna(0.5).clip(0.0, 1.0)
slope_aligned = slope_da.fillna(0.0).clip(0.0, 1.0)

# Invert SPI_norm so higher values represent stronger drying/drought hazard
drought_hazard = (1.0 - spi_aligned).clip(0.0, 1.0)

# Save harmonized inputs
drought_hazard.rio.to_raster(os.path.join(proc_dir, "drought_hazard_1km.tif"), compress="LZW", tiled=True)
female_aligned.rio.to_raster(os.path.join(proc_dir, "female_exposure_1km.tif"), compress="LZW", tiled=True)
slope_aligned.rio.to_raster(os.path.join(proc_dir, "slope_sensitivity_1km.tif"), compress="LZW", tiled=True)

print("3. Computing Weighted MCDA Composite Vulnerability Index (CGVI)...")
w_climate = 0.45
w_gender = 0.40
w_terrain = 0.15

cgvi = (
    w_climate * drought_hazard
    + w_gender * female_aligned
    + w_terrain * slope_aligned
).clip(0.0, 1.0)
cgvi.name = "CGVI"
cgvi.rio.write_crs("EPSG:4326", inplace=True)

cgvi_path = os.path.join(proc_dir, "horn_cgvi_continuous.tif")
cgvi.rio.to_raster(cgvi_path, compress="LZW", tiled=True)

print("4. Classifying CGVI into 5 vulnerability classes (1=Very Low to 5=Very High)...")
vals = cgvi.values
classes = np.zeros(vals.shape, dtype=np.uint8)
classes[(vals >= 0.0) & (vals < 0.20)] = 1
classes[(vals >= 0.20) & (vals < 0.40)] = 2
classes[(vals >= 0.40) & (vals < 0.60)] = 3
classes[(vals >= 0.60) & (vals < 0.80)] = 4
classes[(vals >= 0.80) & (vals <= 1.00)] = 5

cgvi_class = cgvi.copy(data=classes)
cgvi_class.name = "CGVI_Class"
cgvi_class.rio.write_nodata(0, inplace=True)

class_path = os.path.join(proc_dir, "horn_cgvi_classified.tif")
cgvi_class.rio.to_raster(class_path, compress="LZW", tiled=True, dtype="uint8")

# Summary diagnostics
valid_vals = vals[np.isfinite(vals)]
print("\n--- MCDA Composite Vulnerability Summary ---")
print(f"Grid Dimensions (rows x cols): {cgvi.shape[0]} x {cgvi.shape[1]}")
print(f"Min CGVI : {valid_vals.min():.4f}")
print(f"Mean CGVI: {valid_vals.mean():.4f}")
print(f"Max CGVI : {valid_vals.max():.4f}")
print(f"Std Dev  : {valid_vals.std():.4f}")

labels = {
    1: "Very Low (0.00 - 0.20)",
    2: "Low      (0.20 - 0.40)",
    3: "Moderate (0.40 - 0.60)",
    4: "High     (0.60 - 0.80)",
    5: "Very High(0.80 - 1.00)",
}
total_px = classes[classes > 0].size
print("\nClass Distribution:")
for k, label in labels.items():
    cnt = int((classes == k).sum())
    pct = (cnt / total_px) * 100.0 if total_px > 0 else 0.0
    print(f"  Class {k} - {label}: {cnt:,} pixels ({pct:.2f}%)")

print("\nPhase 3 MCDA processing completed successfully.")
