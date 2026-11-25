# 01_climate_hazard.py
import ee
import geemap

try:
    ee.Initialize(project='ee-shimtad2001g')
except Exception:
    ee.Initialize()

aoi = ee.Geometry.Rectangle([33.0, -5.0, 51.0, 15.0])
chirps = (
    ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    .filterBounds(aoi)
    .filterDate('2000-01-01', '2024-12-31')
    .select('precipitation')
)

baseline = chirps.filterDate('2000-01-01', '2010-12-31')
mean = baseline.mean()
std = baseline.reduce(ee.Reducer.stdDev()).max(1e-6)
recent = chirps.filterDate('2020-01-01', '2024-12-31').mean()

spi = recent.subtract(mean).divide(std).rename('SPI')
spi_norm = spi.subtract(-3).divide(6).clamp(0, 1).unmask(0).rename('SPI_norm')

geemap.ee_export_image(
    spi_norm,
    filename=r'C:\GeoProjects\HornVulnerability\data\raw\spi_norm.tif',
    scale=5000,
    region=aoi,
)
print("Climate hazard layer exported to data\\raw\\spi_norm.tif")
