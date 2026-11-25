# 03_terrain.py
import ee
import geemap

try:
    ee.Initialize(project='ee-shimtad2001g')
except Exception:
    ee.Initialize()

aoi = ee.Geometry.Rectangle([33.0, -5.0, 51.0, 15.0])
srtm = ee.Image('USGS/SRTMGL1_003').select('elevation')
slope = ee.Terrain.slope(srtm).unmask(0)
slope_norm = slope.divide(60).clamp(0, 1).rename('slope_norm')

geemap.ee_export_image(
    slope_norm,
    filename=r'C:\GeoProjects\HornVulnerability\data\raw\slope_norm.tif',
    scale=1000,
    region=aoi,
)
print("Terrain layer exported to data\\raw\\slope_norm.tif")
