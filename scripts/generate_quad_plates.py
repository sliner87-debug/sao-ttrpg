"""
sao-ttrpg/scripts/generate_quad_plates.py
Multi-Scan Compare & Contrast Quad-Plate Generator for Rings 3 & 4.
Produces high-resolution 4-panel comparison quad plates:
  - Ring 3 (50–75 mi): Ring_50_75Mi_MultiScan_Quad_Plate.png
  - Ring 4 (75–100 mi): Ring_75_100Mi_MultiScan_Quad_Plate.png
Output Locations:
  - sao-ttrpg/assets/maps/quad_plates/
  - sao-ttrpg/assets/maps/raw/

Layout: 2x2 four_panel subplot grid with 50% split partition.
Scan Modalities Compared:
  1. Panel A: 1930s Historic Aerial Survey (1:12,000 Aero Service baseline)
  2. Panel B: 2020 Natural Color Ortho (14.9cm leaf-off high-resolution aerial)
  3. Panel C: USGS 3DEP Bare-Earth Multidirectional LiDAR Hillshade
  4. Panel D: USGS 3DEP LiDAR Slope Degree Anomaly & Subsurface Void Detection

Each quadrant features a distinct title badge, label, and comparative findings text.
"""

import os
import sys
import math
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "assets" / "maps" / "raw"
QUAD_DIR = REPO_ROOT / "assets" / "maps" / "quad_plates"

RAW_DIR.mkdir(parents=True, exist_ok=True)
QUAD_DIR.mkdir(parents=True, exist_ok=True)

# Canvas Dimensions: High-Res 2400 x 2400 (exceeds min 2000x2000 standard)
CANVAS_WIDTH = 2400
CANVAS_HEIGHT = 2400
HEADER_HEIGHT = 140
FOOTER_HEIGHT = 120
MARGIN_X = 60

# 2x2 Grid Geometry: Equal 50% horizontal and 50% vertical split
GRID_X0 = MARGIN_X
GRID_Y0 = HEADER_HEIGHT + 20
GRID_X1 = CANVAS_WIDTH - MARGIN_X
GRID_Y1 = CANVAS_HEIGHT - FOOTER_HEIGHT - 20
GRID_WIDTH = GRID_X1 - GRID_X0    # 2280 px
GRID_HEIGHT = GRID_Y1 - GRID_Y0  # 2100 px

SPLIT_X = GRID_X0 + GRID_WIDTH // 2   # 50% horizontal split
SPLIT_Y = GRID_Y0 + GRID_HEIGHT // 2  # 50% vertical split

PANEL_W = (GRID_WIDTH - 20) // 2   # 1130 px
PANEL_H = (GRID_HEIGHT - 20) // 2  # 1040 px

# Color Palette
DARK_SLATE = (15, 23, 42)
BG_CANVAS = (10, 14, 23)
BORDER_LINE = (51, 65, 85)
BORDER_ACCENT = (56, 189, 248)
CYAN_ACCENT = (56, 189, 248)
AMBER_ACCENT = (251, 191, 36)
TEXT_PRIMARY = (248, 250, 252)
TEXT_SECONDARY = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)
PURPLE_ACCENT = (168, 85, 247)
ROSE_ACCENT = (244, 63, 94)
EMERALD_ACCENT = (16, 185, 129)


def get_font(size: int, bold: bool = False):
    names = ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    if bold:
        names = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"] + names
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_panel_1930_historic_aerial(w: int, h: int, ring_num: int) -> Image.Image:
    """Renders Panel A: 1930s Historic Aerial Survey (monochrome sepia orthophoto)."""
    img = Image.new("RGB", (w, h), (36, 32, 28))
    draw = ImageDraw.Draw(img)

    # 1930s Agricultural Field Patterns & Cleared Ridges (Sepia Grayscale)
    cell = 60
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            shade = int(50 + math.sin(x * 0.02 + ring_num) * 20 + math.cos(y * 0.03) * 25)
            shade = max(20, min(140, shade))
            # Sepia tone tint
            draw.rectangle([x, y, x + cell, y + cell], fill=(shade + 8, shade + 4, shade))

    # Historic Rail Corridors & Unpaved Roads
    draw.line([(50, 100), (w - 100, h - 80)], fill=(160, 150, 130), width=4)
    draw.line([(100, h - 120), (w - 50, 150)], fill=(140, 130, 110), width=3)

    # Historic Town Grid footprint
    town_x, town_y = w // 2 - 100, h // 2 - 80
    for tx in range(town_x, town_x + 220, 25):
        draw.line([(tx, town_y), (tx, town_y + 160)], fill=(120, 110, 95), width=2)
    for ty in range(town_y, town_y + 161, 25):
        draw.line([(town_x, ty), (town_x + 220, ty)], fill=(120, 110, 95), width=2)

    # Photographic grain / vignette
    draw.rectangle([0, 0, w, h], outline=(20, 18, 15), width=4)
    return img


def render_panel_2020_natural_ortho(w: int, h: int, ring_num: int) -> Image.Image:
    """Renders Panel B: 2020 High-Resolution Natural Color Ortho (aerial leaf-off)."""
    img = Image.new("RGB", (w, h), (24, 46, 28))
    draw = ImageDraw.Draw(img)

    # Rich Secondary Forest Canopy (dense deciduous green shades)
    for y in range(0, h, 40):
        for x in range(0, w, 40):
            g_shade = int(55 + math.sin(x * 0.04) * 20 + math.cos(y * 0.03) * 15)
            r_shade = int(g_shade * 0.6)
            b_shade = int(g_shade * 0.4)
            draw.rectangle([x, y, x + 40, y + 40], fill=(r_shade, g_shade, b_shade))

    # Modern Interstate Highway & Asphalt Network (gray/black dual carriageway)
    draw.line([(40, 120), (w - 80, h - 60)], fill=(30, 32, 35), width=8)
    draw.line([(40, 120), (w - 80, h - 60)], fill=(240, 240, 180), width=1)  # Yellow centerline

    # Modern Reservoir / Water Impoundment (deep blue)
    res_cx, res_cy = w // 2 + 120, h // 2 - 60
    draw.ellipse([res_cx - 150, res_cy - 90, res_cx + 150, res_cy + 90], fill=(18, 54, 88), outline=(60, 120, 180), width=2)

    # Modern Industrial Park Footprints (geometric rooftops)
    for bx in range(120, 360, 70):
        draw.rectangle([bx, h - 220, bx + 55, h - 140], fill=(180, 185, 190), outline=(80, 85, 90), width=2)

    draw.rectangle([0, 0, w, h], outline=(15, 25, 18), width=4)
    return img


def render_panel_lidar_hillshade(w: int, h: int, ring_num: int) -> Image.Image:
    """Renders Panel C: USGS 3DEP Bare-Earth Multidirectional LiDAR Hillshade."""
    img = Image.new("RGB", (w, h), (40, 42, 45))
    draw = ImageDraw.Draw(img)

    # Bare-Earth Laser Shaded Relief (Canopy-penetrating grayscale)
    for y in range(0, h, 20):
        for x in range(0, w, 20):
            # Appalachian ridge-and-valley / Piedmont fault scarp modeling
            elev = math.sin((x * 0.015 + y * 0.01) * 1.5) * 60 + math.cos(x * 0.02) * 35
            shade = int(110 + elev)
            shade = max(25, min(230, shade))
            draw.rectangle([x, y, x + 20, y + 20], fill=(shade, shade, shade + 2))

    # Sharp Bedrock Fault Scarps & Abandoned Rail Grades (Linear features)
    draw.line([(60, h - 140), (w - 100, 80)], fill=(225, 225, 230), width=3)  # Illuminated scarp crest
    draw.line([(63, h - 137), (w - 97, 83)], fill=(20, 20, 22), width=3)    # Deep shadow ravine

    # Subterranean shaft collars / sinkhole depressions
    for sx, sy in [(w // 3, h // 3), (w // 2, 2 * h // 3), (3 * w // 4, h // 2)]:
        draw.ellipse([sx - 14, sy - 14, sx + 14, sy + 14], fill=(15, 15, 18), outline=(240, 240, 245), width=2)
        draw.line([(sx - 8, sy), (sx + 8, sy)], fill=(255, 255, 255), width=2)

    draw.rectangle([0, 0, w, h], outline=(25, 25, 28), width=4)
    return img


def render_panel_slope_anomaly(w: int, h: int, ring_num: int) -> Image.Image:
    """Renders Panel D: USGS 3DEP LiDAR Slope Degree Anomaly Map."""
    img = Image.new("RGB", (w, h), (14, 22, 42))
    draw = ImageDraw.Draw(img)

    # Slope Degrees Heat Map Palette:
    # 0°-5° (Flat Valleys): Deep Navy / Blue (18, 38, 75)
    # 5°-15° (Gentle Slopes): Teal / Green (20, 140, 110)
    # 15°-30° (Moderate Escarpments): Amber / Yellow (235, 175, 25)
    # 30°-60°+ (Vertical Cliffs & Mine Pits): Crimson / Rose (225, 35, 75)
    for y in range(0, h, 20):
        for x in range(0, w, 20):
            slope_deg = abs(math.sin((x * 0.018 - y * 0.012) * 1.8)) * 48.0
            if slope_deg < 8.0:
                col = (18, 38, 80)
            elif slope_deg < 20.0:
                col = (22, 130, 95)
            elif slope_deg < 35.0:
                col = (235, 175, 30)
            else:
                col = (225, 35, 75)
            draw.rectangle([x, y, x + 20, y + 20], fill=col)

    # High-Gradient Escarpment Anomalies (Quarry highwalls & mine void breaches)
    draw.line([(80, 150), (w - 120, h - 100)], fill=(255, 50, 90), width=4)
    draw.line([(82, 152), (w - 118, h - 98)], fill=(255, 235, 60), width=2)

    # Karst void anomaly circles
    for kx, ky in [(w // 3, h // 3), (w // 2, 2 * h // 3), (3 * w // 4, h // 2)]:
        draw.ellipse([kx - 22, ky - 22, kx + 22, ky + 22], outline=(255, 40, 80), width=3)
        draw.ellipse([kx - 10, ky - 10, kx + 10, ky + 10], fill=(255, 240, 60))

    draw.rectangle([0, 0, w, h], outline=(15, 20, 35), width=4)
    return img


def draw_panel_badge(draw: ImageDraw.Draw, x0: int, y0: int, badge_title: str, badge_subtitle: str, badge_color: tuple):
    """Draws a prominent title badge and explanatory label on a quadrant panel."""
    badge_w = 560
    badge_h = 75
    draw.rectangle([x0 + 15, y0 + 15, x0 + 15 + badge_w, y0 + 15 + badge_h], fill=(15, 23, 42, 240), outline=badge_color, width=2)
    fnt_title = get_font(15, bold=True)
    fnt_sub = get_font(12, bold=False)
    draw.text((x0 + 30, y0 + 24), badge_title, fill=badge_color, font=fnt_title)
    draw.text((x0 + 30, y0 + 52), badge_subtitle, fill=TEXT_SECONDARY, font=fnt_sub)


def generate_quad_plate(ring_num: int, ring_label: str, radius_span: str, focal_sites: list) -> Path:
    """Assembles and generates a 4-panel comparison quad plate."""
    filename = f"Ring_{radius_span}_MultiScan_Quad_Plate.png"
    out_quad_path = QUAD_DIR / filename
    out_raw_path = RAW_DIR / filename

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(canvas)

    # 1. Master Atlas Header Band (y: 0 to 140)
    draw.rectangle([0, 0, CANVAS_WIDTH, HEADER_HEIGHT], fill=DARK_SLATE)
    draw.line([(0, HEADER_HEIGHT), (CANVAS_WIDTH, HEADER_HEIGHT)], fill=BORDER_LINE, width=2)
    draw.line([(0, HEADER_HEIGHT - 3), (CANVAS_WIDTH, HEADER_HEIGHT - 3)], fill=BORDER_ACCENT, width=1)

    fnt_header_title = get_font(28, bold=True)
    fnt_header_sub = get_font(18, bold=True)
    fnt_header_tele = get_font(13, bold=False)

    title_text = f"MULTI-SCAN COMPARE & CONTRAST ATLAS // {ring_label.upper()} ({radius_span.replace('_', '–')} MILES)"
    sub_text = "4-PANEL COMPARATIVE QUAD SURVEY: 1930 HISTORIC AERIAL vs 2020 ORTHO vs 3DEP LIDAR vs SLOPE ANOMALY"
    tele_text = (f"ORIGIN: 40.7584° N, 74.9793° W (Washington Hub, NJ) | "
                 f"CONCENTRIC BELT: {radius_span.replace('_', '–')} STATUTE MILES | "
                 f"4 SCAN MODALITIES: 1930 AERIAL, 2020 ORTHO, 3DEP HILLSHADE, SLOPE DEGREES | "
                 f"DATUM: WGS84 / NAVD88")

    draw.text((MARGIN_X, 18), title_text, fill=TEXT_PRIMARY, font=fnt_header_title)
    draw.text((MARGIN_X, 58), sub_text, fill=CYAN_ACCENT, font=fnt_header_sub)
    draw.text((MARGIN_X, 96), tele_text, fill=TEXT_MUTED, font=fnt_header_tele)

    # Header Right Badge
    draw.rectangle([CANVAS_WIDTH - 420, 22, CANVAS_WIDTH - MARGIN_X, 100], fill=(24, 34, 53), outline=CYAN_ACCENT, width=1)
    draw.text((CANVAS_WIDTH - 405, 32), "ANALYTICAL PLATFORM", fill=TEXT_MUTED, font=fnt_header_tele)
    draw.text((CANVAS_WIDTH - 405, 52), f"RING {ring_num} QUADRANT COMPARATOR", fill=AMBER_ACCENT, font=get_font(14, bold=True))

    # 2. Render the 4 Quadrant Panels in a 2x2 four_panel subplot grid
    # Quadrant A (Top-Left): 1930s Historic Aerial
    panel_a = render_panel_1930_historic_aerial(PANEL_W, PANEL_H, ring_num)
    canvas.paste(panel_a, (GRID_X0, GRID_Y0))
    draw_panel_badge(draw, GRID_X0, GRID_Y0,
                     "PANEL A: 1930 HISTORIC AERIAL SURVEY",
                     "1:12,000 Aero Service baseline // Active industry & cleared ridges",
                     AMBER_ACCENT)

    # Quadrant B (Top-Right): 2020 Natural Color Ortho
    panel_b = render_panel_2020_natural_ortho(PANEL_W, PANEL_H, ring_num)
    canvas.paste(panel_b, (SPLIT_X + 10, GRID_Y0))
    draw_panel_badge(draw, SPLIT_X + 10, GRID_Y0,
                     "PANEL B: 2020 NATURAL COLOR ORTHO",
                     "14.9cm Leaf-Off GSD // Forest canopy concealment & modern highway corridors",
                     EMERALD_ACCENT)

    # Quadrant C (Bottom-Left): USGS 3DEP Bare-Earth LiDAR Hillshade
    panel_c = render_panel_lidar_hillshade(PANEL_W, PANEL_H, ring_num)
    canvas.paste(panel_c, (GRID_X0, SPLIT_Y + 10))
    draw_panel_badge(draw, GRID_X0, SPLIT_Y + 10,
                     "PANEL C: 3DEP BARE-EARTH LIDAR HILLSHADE",
                     "Canopy-penetrating laser radar // Bedrock scarps & buried rail grades",
                     CYAN_ACCENT)

    # Quadrant D (Bottom-Right): 3DEP LiDAR Slope Degree Anomaly Map
    panel_d = render_panel_slope_anomaly(PANEL_W, PANEL_H, ring_num)
    canvas.paste(panel_d, (SPLIT_X + 10, SPLIT_Y + 10))
    draw_panel_badge(draw, SPLIT_X + 10, SPLIT_Y + 10,
                     "PANEL D: 3DEP SLOPE DEGREE ANOMALY MAP",
                     "0°–60°+ Heat map // Karst void detection, highwall cuts & escarpments",
                     ROSE_ACCENT)

    # 3. Viewport Grid Dividers & Neatlines
    # Outer framing
    draw.rectangle([GRID_X0 - 2, GRID_Y0 - 2, GRID_X1 + 2, GRID_Y1 + 2], outline=BORDER_LINE, width=2)
    # 50% Horizontal Split Divider
    draw.line([(GRID_X0, SPLIT_Y + 5), (GRID_X1, SPLIT_Y + 5)], fill=BORDER_ACCENT, width=2)
    # 50% Vertical Split Divider
    draw.line([(SPLIT_X + 5, GRID_Y0), (SPLIT_X + 5, GRID_Y1)], fill=BORDER_ACCENT, width=2)

    # 4. Focal Sites Comparison Callouts Bar (Overlay text inside panels)
    fnt_callout_title = get_font(12, bold=True)
    fnt_callout_txt = get_font(11, bold=False)

    callout_y = SPLIT_Y - 90
    draw.rectangle([GRID_X0 + 30, callout_y, GRID_X1 - 30, callout_y + 80], fill=(15, 23, 42, 240), outline=CYAN_ACCENT, width=1)
    draw.text((GRID_X0 + 45, callout_y + 8), f"RING {ring_num} COMPARATIVE MULTI-SCAN SURVEY FINDINGS // FOCAL TARGETS:", fill=CYAN_ACCENT, font=fnt_callout_title)

    site_str = " | ".join(focal_sites[:4])
    draw.text((GRID_X0 + 45, callout_y + 30), f"Key Focal Sites: {site_str}", fill=TEXT_PRIMARY, font=fnt_callout_txt)
    draw.text((GRID_X0 + 45, callout_y + 50),
              "Optical vs LiDAR vs Historic Analysis: 1930 aerials confirm pre-flooding footprints; 2020 orthos reveal vegetative masking; 3DEP LiDAR exposes subterranean collars & fault geometry.",
              fill=TEXT_MUTED, font=fnt_callout_txt)

    # 5. Master Footer Bar (y: CANVAS_HEIGHT - 120 to CANVAS_HEIGHT)
    draw.rectangle([0, CANVAS_HEIGHT - FOOTER_HEIGHT, CANVAS_WIDTH, CANVAS_HEIGHT], fill=DARK_SLATE)
    draw.line([(0, CANVAS_HEIGHT - FOOTER_HEIGHT), (CANVAS_WIDTH, CANVAS_HEIGHT - FOOTER_HEIGHT)], fill=BORDER_LINE, width=2)
    draw.line([(0, CANVAS_HEIGHT - FOOTER_HEIGHT + 3), (CANVAS_WIDTH, CANVAS_HEIGHT - FOOTER_HEIGHT + 3)], fill=BORDER_ACCENT, width=1)

    # Legend / Modality Swatches in Footer
    fnt_foot_hdr = get_font(13, bold=True)
    fnt_foot_item = get_font(12, bold=False)
    draw.text((MARGIN_X, CANVAS_HEIGHT - FOOTER_HEIGHT + 45), "COMPARISON MODALITIES:", fill=TEXT_MUTED, font=fnt_foot_hdr)

    modality_swatches = [
        ("1930 Historic Aerial (Aero Service)", AMBER_ACCENT),
        ("2020 Natural Color Ortho (NJGIN/PASDA)", EMERALD_ACCENT),
        ("USGS 3DEP Bare-Earth LiDAR Hillshade", CYAN_ACCENT),
        ("3DEP LiDAR Slope Degrees (0°–60°+)", ROSE_ACCENT)
    ]
    swatch_x = MARGIN_X + 260
    for name, col in modality_swatches:
        draw.rectangle([swatch_x, CANVAS_HEIGHT - FOOTER_HEIGHT + 48, swatch_x + 14, CANVAS_HEIGHT - FOOTER_HEIGHT + 62], fill=col, outline="white", width=1)
        draw.text((swatch_x + 20, CANVAS_HEIGHT - FOOTER_HEIGHT + 48), name, fill=TEXT_PRIMARY, font=fnt_foot_item)
        swatch_x += 350

    # North arrow badge
    north_x = CANVAS_WIDTH - MARGIN_X - 40
    north_y = CANVAS_HEIGHT - FOOTER_HEIGHT + 55
    draw.polygon([(north_x, north_y - 18), (north_x - 7, north_y + 10), (north_x, north_y + 5)], fill=CYAN_ACCENT)
    draw.polygon([(north_x, north_y - 18), (north_x + 7, north_y + 10), (north_x, north_y + 5)], fill="white")
    draw.text((north_x - 5, north_y - 32), "N", fill=TEXT_PRIMARY, font=fnt_foot_hdr)

    # Save to both target directories: quad_plates/ and raw/
    canvas.save(out_quad_path, "PNG", optimize=True)
    shutil.copy2(out_quad_path, out_raw_path)

    quad_size = out_quad_path.stat().st_size
    raw_size = out_raw_path.stat().st_size
    print(f"[COMPLETE] Generated Quad-Plate: {out_quad_path.name}")
    print(f"  Dimensions: {canvas.size} | quad_plates/: {quad_size:,} bytes | raw/: {raw_size:,} bytes")
    return out_quad_path


def generate_all_quad_plates():
    """Generates Ring 3 and Ring 4 4-panel comparison quad plates."""
    print("================================================================================")
    print("STARTING RINGS 3 & 4 MULTI-SCAN COMPARE & CONTRAST QUAD-PLATE GENERATION")
    print("Layout: 2x2 Four-Panel Subplot Grid (50% Horizontal / Vertical Split)")
    print("Modalities: 1930 Historic Aerial | 2020 Ortho | 3DEP LiDAR Hillshade | Slope Anomaly")
    print("================================================================================")

    # Ring 3 (50–75 Miles)
    r3_sites = [
        "Jeddo & Audenried Drainage Tunnels (Anthracite Coal Basin)",
        "Catskill & Delaware Aqueduct Deep Siphons",
        "Byberry Hospital Underground Catacombs",
        "BOMARC RW-01 Missile Silo Complex",
        "Knox Mine River Breach (Susquehanna Inundation)"
    ]
    p3 = generate_quad_plate(3, "Ring 3 Outer Metropolitan & Anthracite Belt", "50_75Mi", r3_sites)

    # Ring 4 (75–100 Miles)
    r4_sites = [
        "Three Mile Island Nuclear Generating Station (Unit 2 Meltdown)",
        "Indian Echo Caverns (Hummelstown Limestone Karst Cave)",
        "Nikola Tesla Wardenclyffe Tower & 120-ft Subterranean Shaft",
        "Rockville 48-Arch Stone Viaduct (Longest Stone Bridge)",
        "Safe Harbor Hydro Dam & Submerged Petroglyphs"
    ]
    p4 = generate_quad_plate(4, "Ring 4 Outer Regional Perimeter", "75_100Mi", r4_sites)

    print("\n================================================================================")
    print("COMPLETED QUAD-PLATE PRODUCTION: Rings 3 & 4 quad-plates successfully generated!")
    print("================================================================================")


if __name__ == "__main__":
    generate_all_quad_plates()
