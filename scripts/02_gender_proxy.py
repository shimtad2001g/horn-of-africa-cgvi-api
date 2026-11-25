# 02_gender_proxy.py
import ee
import geemap

try:
    ee.Initialize(project='ee-shimtad2001g')
except Exception:
    ee.Initialize()

aoi = ee.Geometry.Rectangle([33.0, -5.0, 51.0, 15.0])
worldpop = (
    ee.ImageCollection('WorldPop/GP/100m/pop_age_sex')
    .filterBounds(aoi)
    .filter(ee.Filter.eq('year', 2020))
    .mosaic()
)

female_bands = [
    'F_0', 'F_1', 'F_5', 'F_10', 'F_15', 'F_20', 'F_25', 'F_30', 'F_35',
    'F_40', 'F_45', 'F_50', 'F_55', 'F_60', 'F_65', 'F_70', 'F_75', 'F_80'
]
female_pop = worldpop.select(female_bands).reduce(ee.Reducer.sum()).unmask(0).rename('female_pop')
female_norm = female_pop.divide(500).clamp(0, 1).rename('female_norm')

geemap.ee_export_image(
    female_norm,
    filename=r'C:\GeoProjects\HornVulnerability\data\raw\female_norm.tif',
    scale=2000,
    region=aoi,
)
print("Gender proxy layer exported to data\\raw\\female_norm.tif")
