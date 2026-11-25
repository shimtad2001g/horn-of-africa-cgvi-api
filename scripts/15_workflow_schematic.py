# 15_workflow_schematic.py
# Generates a publication-grade white-background methodology & architecture schematic
# at 300 and 600 DPI and writes an executive technical summary brief.
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_DIR = r"C:\GeoProjects\HornVulnerability\output"
os.makedirs(OUT_DIR, exist_ok=True)

def draw_box(ax, x, y, w, h, title, body, edge="#1f4e78", fill="#f4f8fb", title_color="#102a43"):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.5, edgecolor=edge, facecolor=fill
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.026, title, ha="center", va="top", fontsize=9.5, fontweight="bold", color=title_color)
    ax.text(x + w / 2, (y + h - 0.055) / 2, body, ha="center", va="center", fontsize=8.0, color="#1f2933", linespacing=1.35)

def draw_arrow(ax, x1, y1, x2, y2, color="#334e68"):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>,head_length=6,head_width=3.5",
        linewidth=1.4, color=color
    )
    ax.add_patch(arr)

def build_schematic(out_path, dpi):
    fig, ax = plt.subplots(figsize=(13.5, 7.6), dpi=dpi, facecolor="white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5, 0.96,
        "Horn of Africa Climate & Gender Vulnerability (CGVI) — End-to-End Geospatial Architecture",
        ha="center", va="top", fontsize=13.5, fontweight="bold", color="#0f172a"
    )
    ax.text(
        0.5, 0.922,
        "Open-Source Earth Observation Pipeline  |  GEE Project: ee-shimtad2001g  |  Author: Shimeles Tadesse Zelelew",
        ha="center", va="top", fontsize=9.0, color="#475569"
    )

    # Column 1: Open-Source Inputs (GEE)
    draw_box(
        ax, 0.03, 0.64, 0.21, 0.22,
        "1. Drought Hazard",
        "UCSB CHIRPS\nHorn BBox [33°E, -5°S, 51°E, 15°N]\n~4.45M sq km Regional Window",
        edge="#b45309", fill="#fffbeb", title_color="#92400e"
    )
    draw_box(
        ax, 0.03, 0.38, 0.21, 0.21,
        "2. Female Exposure",
        "WorldPop 2020\nDemographically Explicit\n1 km Population Surface",
        edge="#0f766e", fill="#f0fdfa", title_color="#115e59"
    )
    draw_box(
        ax, 0.03, 0.13, 0.21, 0.20,
        "3. Slope Sensitivity",
        "NASA SRTM Elevation\nTerrain Slope & Topographic\nAccessibility Proxy",
        edge="#334155", fill="#f8fafc", title_color="#1e293b"
    )

    # Column 2: Harmonization & MCDA
    draw_box(
        ax, 0.29, 0.52, 0.20, 0.34,
        "1 km Grid Harmonization",
        "Conda: geospatial_auditor / gee_horn\nrioxarray, rasterio, xarray, geopandas\nAligned Spatial Grid & CRS Audit\n4,517,016 Valid 1 km Cells",
        edge="#1d4ed8", fill="#eff6ff", title_color="#1e3a8a"
    )
    draw_box(
        ax, 0.29, 0.13, 0.20, 0.33,
        "MCDA & P2–P98 Sensitivity",
        "Baseline Weights: 0.45 / 0.40 / 0.15\nDriver Dominance Attribution\n2nd–98th Percentile Rescaling\nBalanced Composites (balanced_*.tif)",
        edge="#7c3aed", fill="#f5f3ff", title_color="#5b21b6"
    )

    # Column 3: Regional & Ethiopia Focus
    draw_box(
        ax, 0.54, 0.52, 0.20, 0.34,
        "Ethiopia Focus (UTM 37N)",
        "Clip [33.0°E, 3.3°N, 48.0°E, 15.0°N]\nReprojected to EPSG:32637\n2,131,163.00 sq km Focus Domain\n300 & 600 DPI Cartographic Plates",
        edge="#0369a1", fill="#f0f9ff", title_color="#0c4a6e"
    )
    draw_box(
        ax, 0.54, 0.13, 0.20, 0.33,
        "QGIS & Manifest Governance",
        "QGIS Project: horn_vulnerability_styled.qgz\nA3 PDF & 300 DPI Layout Exports\n50-File JSON/TXT Deliverable Manifest\nZonal Stats & Archive Pipeline",
        edge="#047857", fill="#ecfdf5", title_color="#065f46"
    )

    # Column 4: Portable & Interactive Outputs
    draw_box(
        ax, 0.79, 0.52, 0.18, 0.34,
        "OGC GeoPackage",
        "horn_cgvi_master.gpkg\n(~65.35 MB Multi-Layer)\nDrought, Exposure, Slope,\nContinuous, Class & Driver",
        edge="#b91c1c", fill="#fef2f2", title_color="#991b1b"
    )
    draw_box(
        ax, 0.79, 0.13, 0.18, 0.33,
        "Streamlit Explorer",
        "13_streamlit_explorer.py\nLive Weights & P2–P98 Toggle\nHorn & Ethiopia (UTM 37N) Views\nSide-by-Side, Diff & CSV/TIF Export",
        edge="#be185d", fill="#fdf2f8", title_color="#9d174d"
    )

    # Arrows
    draw_arrow(ax, 0.24, 0.75, 0.29, 0.72)
    draw_arrow(ax, 0.24, 0.49, 0.29, 0.65)
    draw_arrow(ax, 0.24, 0.23, 0.29, 0.58)
    draw_arrow(ax, 0.39, 0.52, 0.39, 0.46)
    draw_arrow(ax, 0.49, 0.69, 0.54, 0.69)
    draw_arrow(ax, 0.49, 0.28, 0.54, 0.28)
    draw_arrow(ax, 0.74, 0.69, 0.79, 0.69)
    draw_arrow(ax, 0.74, 0.28, 0.79, 0.28)
    draw_arrow(ax, 0.88, 0.52, 0.88, 0.46)

    ax.text(
        0.5, 0.045,
        "Key Finding: Raw MCDA is strongly drought-driven (98.63% dominance); 2nd–98th percentile rescaling balances multi-factor sensitivity (56.81% drought, 25.55% female exposure, 17.63% slope).",
        ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1e293b"
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    print(f"[OK] Saved schematic: {out_path} ({dpi} DPI)")

build_schematic(os.path.join(OUT_DIR, "horn_cgvi_workflow_schematic_300dpi.png"), 300)
build_schematic(os.path.join(OUT_DIR, "horn_cgvi_workflow_schematic_600dpi.png"), 600)

brief_text = """HORN OF AFRICA CLIMATE & GENDER VULNERABILITY (CGVI) — EXECUTIVE TECHNICAL BRIEF
=======================================================================================
Author: Shimeles Tadesse Zelelew
GEE Cloud Project: ee-shimtad2001g
Environment & Stack: Conda (geospatial_auditor / gee_horn, Python 3.11), rioxarray, rasterio, geopandas, matplotlib, QGIS, Streamlit

1. STUDY SCOPE & OPEN-SOURCE INPUTS
- Regional Bounding Box: [33.0°E, -5.0°S, 51.0°E, 15.0°N] (~4.45M sq km across the Horn of Africa)
- Ethiopia Regional Focus: [33.0°E, 3.3°N, 48.0°E, 15.0°N], reprojected to UTM Zone 37N (EPSG:32637, 1,000 m resolution; 2,131,163.00 sq km focus domain)
- Core Datasets: UCSB CHIRPS (drought hazard), WorldPop 2020 (female population exposure), NASA SRTM (slope sensitivity)
- Valid Regional Grid: 4,517,016 valid 1 km cells

2. MCDA & SENSITIVITY DIAGNOSTICS
- Baseline MCDA Weights: 0.45 Drought Hazard + 0.40 Female Exposure + 0.15 Slope Sensitivity
- Active Reference Readout (0.45 / 0.40 / 0.15, P2-P98 rescaled, threshold >= 0.40): Mean CGVI = 0.1997, Max CGVI = 0.8670, Hotspots = 1,446,616 px (32.03%)
- Sensitivity Shift (P2-P98 Rescaling): Shifts from strong raw drought dominance (98.63%) toward balanced multi-factor sensitivity (56.81% drought, 25.55% female exposure, 17.63% slope), preventing extreme tails from masking demographic and terrain exposure.

3. DELIVERABLES & INTERACTIVE TOOLS
- Master OGC GeoPackage: output\\horn_cgvi_master.gpkg (~65.35 MB) consolidating harmonized 1 km rasters, continuous/classified/balanced composites, and dominant driver layers.
- Cartography & GIS: 300 & 600 DPI publication figures, QGIS project (qgis_project\\horn_vulnerability_styled.qgz), A3 PDF & 300 DPI layout exports, and workflow schematics.
- Interactive Explorer: scripts\\13_streamlit_explorer.py supporting Horn (EPSG:4326) and Ethiopia (EPSG:32637) views, scenario presets, direct GPKG subdatasets, side-by-side/difference maps, live histograms/5-class charts, and CSV/GeoTIFF snapshot exports.
"""

brief_path = os.path.join(OUT_DIR, "horn_cgvi_executive_brief.txt")
with open(brief_path, "w", encoding="utf-8") as fb:
    fb.write(brief_text.strip() + "\n")
print(f"[OK] Saved executive brief: {brief_path}")

