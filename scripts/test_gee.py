# test_gee.py
import ee
import geemap

try:
    ee.Initialize()
except Exception:
    ee.Initialize(project='ee-shimtad2001g')

print("GEE initialized successfully.")
print("geemap version:", geemap.__version__)

aoi = ee.Geometry.Rectangle([33.0, -5.0, 51.0, 15.0])
area_sq_km = aoi.area().divide(1e6).getInfo()
print(f"Horn of Africa AOI area (sq km): {area_sq_km:,.2f}")
