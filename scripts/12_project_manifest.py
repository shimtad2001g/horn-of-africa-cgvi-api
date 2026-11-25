# 12_project_manifest.py
# Audits all files under C:\GeoProjects\HornVulnerability and generates a structured
# deliverable manifest (JSON + human-readable TXT) with raster CRS/shape metadata and provenance.
import os
import json
import datetime
import rioxarray as rxr

root_dir = r"C:\GeoProjects\HornVulnerability"
out_dir = os.path.join(root_dir, "output")
os.makedirs(out_dir, exist_ok=True)

subdirs = ["scripts", "data\\raw", "data\\processed", "output", "qgis_project", "logs"]
inventory = []

for sub in subdirs:
    full_sub = os.path.join(root_dir, sub)
    if not os.path.exists(full_sub):
        continue
    for entry in sorted(os.listdir(full_sub)):
        p = os.path.join(full_sub, entry)
        if not os.path.isfile(p):
            continue
        stat = os.stat(p)
        item = {
            "category": sub,
            "name": entry,
            "path": p,
            "size_bytes": stat.st_size,
            "modified_utc": datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat(),
        }
        if entry.lower().endswith(".tif"):
            try:
                da = rxr.open_rasterio(p, masked=True).squeeze()
                item["crs"] = str(da.rio.crs) if da.rio.crs else "None"
                item["shape"] = list(da.shape)
                item["res"] = [float(abs(x)) for x in da.rio.resolution()]
            except Exception as exc:
                item["raster_inspect_error"] = str(exc)
        inventory.append(item)

manifest = {
    "project": "Horn of Africa Climate & Gender Vulnerability Map (CGVI)",
    "author": "Shimeles Tadesse Zelelew",
    "gee_cloud_project": "ee-shimtad2001g",
    "open_source_sources": [
        "UCSB CHIRPS (Drought / SPI)",
        "WorldPop 2020 (Female Population Exposure)",
        "NASA SRTM (Terrain Slope Sensitivity)",
    ],
    "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "total_files": len(inventory),
    "files": inventory,
}

json_path = os.path.join(out_dir, "horn_cgvi_deliverable_manifest.json")
with open(json_path, "w", encoding="utf-8") as fj:
    json.dump(manifest, fj, indent=2)

txt_lines = [
    "Horn of Africa Climate & Gender Vulnerability Map (CGVI) - Deliverable Manifest",
    f"Author          : {manifest['author']}",
    f"GEE Project ID  : {manifest['gee_cloud_project']}",
    f"Open-Source Data: {', '.join(manifest['open_source_sources'])}",
    f"Total Files     : {manifest['total_files']}",
    "-" * 88,
]

for it in inventory:
    extra = ""
    if "crs" in it:
        extra = f" | CRS={it['crs']} | Shape={it['shape']} | Res={it['res']}"
    txt_lines.append(f"[{it['category']:15s}] {it['name']:42s} | {it['size_bytes']:10,d} B{extra}")

txt_path = os.path.join(out_dir, "horn_cgvi_deliverable_manifest.txt")
with open(txt_path, "w", encoding="utf-8") as ft:
    ft.write("\n".join(txt_lines) + "\n")

print("Saved JSON manifest:", json_path)
print("Saved TXT manifest :", txt_path)
