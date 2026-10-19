"""
sao-ttrpg/scripts/generate_manunka_chunk_tactical.py
Zone 3 Tactical Plate Generator: Manunka Chunk Twin Cliff Tunnels (map3b_manunka_chunk_tunnels.png)
Renders the authoritative 2000 x 1560 high-resolution tactical plate:
  - Focused on Manunka Chunk Twin Tunnels (40.826° N, 75.068° W) through the cliffs above Delaware River
  - Dual 938-ft cliff bores: DL&W (1856) North Bore & PRR (1869) South Bore
  - DL&W Railroad / PRR junction, portal collars, Delaware River water gap shoreline
  - Martinsburg Shale cliff escarpment and 50-ft tactical coordinate grid (Zoom Level 17)
  - Underground vertical datum (+435 ft ASL collar, +420 ft ASL sump, 0.0 PSI hydrostatic)
  - Post-initialization Boss Lair overlay: Gorgon-Plated Ore Colossus of Manunka
"""

import os
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "assets" / "maps" / "raw"
OPT_DIR = REPO_ROOT / "assets" / "maps" / "optimized"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OPT_DIR.mkdir(parents=True, exist_ok=True)

# Plate Constants
TEMPLATE_WIDTH = 2000
TEMPLATE_HEIGHT = 1560
HEADER_HEIGHT = 120
FOOTER_HEIGHT = 100
VIEWPORT_X0 = 90
VIEWPORT_Y0 = HEADER_HEIGHT
VIEWPORT_X1 = TEMPLATE_WIDTH - 90
VIEWPORT_Y1 = TEMPLATE_HEIGHT - FOOTER_HEIGHT
VIEWPORT_WIDTH = VIEWPORT_X1 - VIEWPORT_X0  # 1820
VIEWPORT_HEIGHT = VIEWPORT_Y1 - VIEWPORT_Y0  # 1340

# Target Coordinates & Engineering Spec
TARGET_LAT = 40.8260
TARGET_LNG = -75.0680
BORE_LENGTH_FT = 938.0
COLLAR_ASL_FT = 435.0
BOTTOM_ASL_FT = 420.0
HYDROSTATIC_PSI = 0.0
GEOLOGY = "Ordovician Martinsburg Shale"
ZOOM_LEVEL = 17

# Colors
DARK_SLATE = (15, 23, 42)
CANVAS_BG = (11, 15, 25)
BORDER_LINE = (51, 65, 85)
BORDER_ACCENT = (56, 189, 248)
CYAN_ACCENT = (56, 189, 248)
AMBER_ACCENT = (251, 191, 36)
TEXT_PRIMARY = (248, 250, 252)
TEXT_SECONDARY = (203, 213, 225)
TEXT_MUTED = (100, 116, 139)
PURPLE_ACCENT = (168, 85, 247)
RED_ACCENT = (239, 68, 68)
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


def render_tactical_viewport() -> Image.Image:
    """Renders the high-resolution tactical terrain, twin tunnels, and river gap."""
    img = Image.new("RGB", (VIEWPORT_WIDTH, VIEWPORT_HEIGHT), (16, 24, 38))
    draw = ImageDraw.Draw(img)
    w, h = VIEWPORT_WIDTH, VIEWPORT_HEIGHT

    # 1. Martinsburg Shale Hillshade & Cliff Topography
    # Cliff rises from west (x ~ 380, Delaware River shoreline) to east (x ~ 1400, ridge crest)
    for x in range(w):
        if x < 380:
            # Delaware River Water Gap (deep navy / teal water)
            wave = int(math.sin(x * 0.05) * 4)
            col = (12 + wave, 44 + wave, 72 + wave)
        elif x < 420:
            # River gravel shoreline & embankment
            col = (54, 60, 68)
        elif x < 1350:
            # Mountain Cliff Face (Martinsburg Shale - rolling contour shading)
            frac = (x - 420) / (1350 - 420)
            elevation = 285 + frac * 295  # 285' river to 580' crest
            contour = int(math.sin(x * 0.02 + y_var * 0.01) * 8) if 'y_var' in locals() else 0
            base_shade = int(32 + frac * 48)
            col = (base_shade, base_shade + 6, base_shade + 12)
        else:
            # Eastern Valley & Rail Approach
            col = (28, 36, 46)
        draw.line([(x, 0), (x, h)], fill=col, width=1)

    # 2. Render Contour Elevation Lines along cliff
    for elev in range(300, 600, 25):
        frac = (elev - 285) / 295.0
        base_x = int(420 + frac * 930)
        c_pts = []
        for y in range(0, h, 20):
            perturb = int(math.sin(y * 0.015 + elev) * 35 + math.cos(y * 0.04) * 15)
            c_pts.append((base_x + perturb, y))
        draw.line(c_pts, fill=(45, 62, 85), width=1)

    # 3. Delaware River Shoreline, Flow Currents & Sandbars
    # Shoreline path
    shore_pts = []
    for y in range(0, h, 15):
        sx = int(380 + math.sin(y * 0.01) * 25)
        shore_pts.append((sx, y))
    draw.line(shore_pts, fill=(56, 189, 248), width=3)

    # River flow vectors
    fnt_water = get_font(13, bold=True)
    draw.text((120, 250), "DELAWARE RIVER // WATER GAP CORRIDOR", fill=(125, 211, 252), font=fnt_water)
    draw.text((120, 275), "Flow Direction: Southbound -> 285 ft ASL Surface", fill=(100, 160, 210), font=get_font(11))
    for arrow_y in range(150, h - 150, 180):
        draw.line([(180, arrow_y), (180, arrow_y + 60)], fill=(56, 189, 248), width=2)
        draw.polygon([(175, arrow_y + 55), (185, arrow_y + 55), (180, arrow_y + 70)], fill=(56, 189, 248))

    # 4. Tactical Coordinate Grid (50-ft squares across tunnel corridor)
    fnt_grid = get_font(10, bold=False)
    grid_spacing = 50
    for gx in range(400, 1500, grid_spacing):
        draw.line([(gx, 350), (gx, 950)], fill=(35, 55, 80), width=1)
    for gy in range(350, 951, grid_spacing):
        draw.line([(400, gy), (1500, gy)], fill=(35, 55, 80), width=1)

    # 5. Dual 938-ft Cliff Bores:
    # Scale: 938 ft mapped across 900 horizontal pixels => ~0.96 px / foot
    # West Portals: x = 450 (facing Delaware River gap)
    # East Portals: x = 1388 (facing eastern rail junction)
    # North Bore y = 580 (DL&W 1856)
    # South Bore y = 660 (PRR 1869)
    tunnel_x0 = 460
    tunnel_x1 = 1398  # Exact 938-ft scaled bore length

    north_bore_y = 570
    south_bore_y = 660

    # Subterranean bedrock cut corridor
    draw.rectangle([tunnel_x0, north_bore_y - 25, tunnel_x1, south_bore_y + 25], fill=(12, 18, 28))

    # Exterior rail approach tracks (surface rail lines approaching portals)
    # West approach (along river embankment)
    draw.line([(150, north_bore_y - 80), (tunnel_x0, north_bore_y)], fill=(180, 140, 80), width=3)
    draw.line([(150, south_bore_y + 80), (tunnel_x0, south_bore_y)], fill=(180, 140, 80), width=3)
    # East approach (DL&W / PRR mainline junction)
    draw.line([(tunnel_x1, north_bore_y), (w - 60, north_bore_y - 120)], fill=(180, 140, 80), width=3)
    draw.line([(tunnel_x1, south_bore_y), (w - 60, south_bore_y + 60)], fill=(180, 140, 80), width=3)
    # Junction crossover track
    draw.line([(tunnel_x1 + 80, north_bore_y - 15), (tunnel_x1 + 180, south_bore_y + 10)], fill=(251, 191, 36), width=2)
    draw.text((tunnel_x1 + 100, north_bore_y + 15), "DL&W / PRR JUNCTION", fill=AMBER_ACCENT, font=get_font(12, bold=True))

    # Render Dual Tunnel Bores (938 ft each)
    # North Bore (DL&W 1856)
    draw.line([(tunnel_x0, north_bore_y), (tunnel_x1, north_bore_y)], fill=(168, 85, 247), width=8)
    draw.line([(tunnel_x0, north_bore_y), (tunnel_x1, north_bore_y)], fill=(240, 200, 255), width=2)
    # South Bore (PRR 1869)
    draw.line([(tunnel_x0, south_bore_y), (tunnel_x1, south_bore_y)], fill=(56, 189, 248), width=8)
    draw.line([(tunnel_x0, south_bore_y), (tunnel_x1, south_bore_y)], fill=(220, 245, 255), width=2)

    # Portal Collars (Cut stone masonry arches)
    # West Portals
    draw.rectangle([tunnel_x0 - 15, north_bore_y - 18, tunnel_x0 + 4, north_bore_y + 18], fill=(80, 90, 105), outline="white", width=2)
    draw.rectangle([tunnel_x0 - 15, south_bore_y - 18, tunnel_x0 + 4, south_bore_y + 18], fill=(80, 90, 105), outline="white", width=2)
    # East Portals
    draw.rectangle([tunnel_x1 - 4, north_bore_y - 18, tunnel_x1 + 15, north_bore_y + 18], fill=(80, 90, 105), outline="white", width=2)
    draw.rectangle([tunnel_x1 - 4, south_bore_y - 18, tunnel_x1 + 15, south_bore_y + 18], fill=(80, 90, 105), outline="white", width=2)

    # Labels for Portals
    fnt_portal = get_font(12, bold=True)
    draw.text((tunnel_x0 - 190, north_bore_y - 28), "WEST PORTAL COLLAR", fill=TEXT_PRIMARY, font=fnt_portal)
    draw.text((tunnel_x0 - 190, north_bore_y - 12), "(River Approach // 435' ASL)", fill=TEXT_MUTED, font=get_font(11))

    draw.text((tunnel_x1 + 25, north_bore_y - 28), "EAST PORTAL COLLAR", fill=TEXT_PRIMARY, font=fnt_portal)
    draw.text((tunnel_x1 + 25, north_bore_y - 12), "(Manunka Siding // 435' ASL)", fill=TEXT_MUTED, font=get_font(11))

    # Tunnel Bore Dimension & Title Annotations
    fnt_bore_title = get_font(14, bold=True)
    fnt_bore_sub = get_font(12, bold=False)

    # North Bore Callout
    draw.rectangle([tunnel_x0 + 120, north_bore_y - 95, tunnel_x0 + 580, north_bore_y - 30], fill=(15, 23, 42, 230), outline=PURPLE_ACCENT, width=1)
    draw.text((tunnel_x0 + 135, north_bore_y - 90), "NORTH BORE: DL&W RAILROAD (1856)", fill=(240, 200, 255), font=fnt_bore_title)
    draw.text((tunnel_x0 + 135, north_bore_y - 68), f"Length: Exactly {BORE_LENGTH_FT:.0f} Feet | Ordovician Martinsburg Shale | Crown Overburden: +145 ft", fill=(180, 215, 245), font=fnt_bore_sub)
    draw.text((tunnel_x0 + 135, north_bore_y - 50), f"Datum: Underground | Collar: +{COLLAR_ASL_FT:.0f}' ASL | Sump: +{BOTTOM_ASL_FT:.0f}' ASL | PSI: {HYDROSTATIC_PSI:.1f}", fill=TEXT_MUTED, font=fnt_bore_sub)

    # South Bore Callout
    draw.rectangle([tunnel_x0 + 120, south_bore_y + 35, tunnel_x0 + 580, south_bore_y + 100], fill=(15, 23, 42, 230), outline=CYAN_ACCENT, width=1)
    draw.text((tunnel_x0 + 135, south_bore_y + 40), "SOUTH BORE: PRR BELVIDERE DELAWARE DIV (1869)", fill=(200, 240, 255), font=fnt_bore_title)
    draw.text((tunnel_x0 + 135, south_bore_y + 62), f"Length: Exactly {BORE_LENGTH_FT:.0f} Feet | Parallel Alignment (60 ft Center-to-Center)", fill=(180, 215, 245), font=fnt_bore_sub)
    draw.text((tunnel_x0 + 135, south_bore_y + 80), "Constructed to avoid grade-crossing collisions at the Manunka Chunk junction", fill=TEXT_MUTED, font=fnt_bore_sub)

    # Dimension Leader Bar (938 FT)
    dim_y = 615
    draw.line([(tunnel_x0, dim_y), (tunnel_x1, dim_y)], fill=AMBER_ACCENT, width=2)
    draw.line([(tunnel_x0, dim_y - 6), (tunnel_x0, dim_y + 6)], fill=AMBER_ACCENT, width=2)
    draw.line([(tunnel_x1, dim_y - 6), (tunnel_x1, dim_y + 6)], fill=AMBER_ACCENT, width=2)
    draw.rectangle([(tunnel_x0 + tunnel_x1)//2 - 80, dim_y - 12, (tunnel_x0 + tunnel_x1)//2 + 80, dim_y + 12], fill=(15, 23, 42), outline=AMBER_ACCENT)
    draw.text(((tunnel_x0 + tunnel_x1)//2 - 68, dim_y - 9), "938.0 FT BORE SPAN", fill=AMBER_ACCENT, font=get_font(12, bold=True))

    # 6. Post-Initialization Cardinal System Overlay (Floor 1 Sector Bastion Lair)
    bastion_x = tunnel_x0 + 640
    bastion_y = 570
    draw.rectangle([bastion_x, bastion_y - 20, bastion_x + 180, bastion_y + 110], fill=(30, 10, 20, 220), outline=RED_ACCENT, width=2)
    fnt_boss = get_font(12, bold=True)
    draw.text((bastion_x + 10, bastion_y - 12), "APEX BOSS LAIR", fill=RED_ACCENT, font=fnt_boss)
    draw.text((bastion_x + 10, bastion_y + 8), "Gorgon-Plated", fill=TEXT_PRIMARY, font=fnt_boss)
    draw.text((bastion_x + 10, bastion_y + 26), "Ore Colossus", fill=TEXT_PRIMARY, font=fnt_boss)
    draw.text((bastion_x + 10, bastion_y + 46), "(Lv 1–12 Threat)", fill=AMBER_ACCENT, font=get_font(11))
    draw.text((bastion_x + 10, bastion_y + 66), "Faction: Iron Mtn", fill=(200, 180, 220), font=get_font(10))
    draw.text((bastion_x + 10, bastion_y + 82), "Foundry Guild", fill=(200, 180, 220), font=get_font(10))

    # 7. Longitudinal Geological Elevation Cross-Section Inset (Bottom Right of Viewport)
    inset_x0 = w - 580
    inset_y0 = h - 330
    inset_w = 540
    inset_h = 280
    draw.rectangle([inset_x0, inset_y0, inset_x0 + inset_w, inset_y0 + inset_h], fill=(10, 16, 26, 240), outline=CYAN_ACCENT, width=2)
    draw.text((inset_x0 + 15, inset_y0 + 12), "VERTICAL OVERBURDEN PROFILE // 938-FT CROSS-SECTION", fill=CYAN_ACCENT, font=get_font(12, bold=True))

    # Profile terrain line
    prof_baseline = inset_y0 + inset_h - 50
    prof_tunnel_y = prof_baseline - 35  # +420 ft ASL
    prof_cliff_top_y = inset_y0 + 70   # +580 ft ASL crest
    draw.line([(inset_x0 + 30, prof_baseline), (inset_x0 + inset_w - 30, prof_baseline)], fill=(51, 65, 85), width=1)
    draw.text((inset_x0 + 30, prof_baseline + 8), "Base 350' ASL", fill=TEXT_MUTED, font=get_font(10))

    # Ridge profile polygon
    ridge_pts = [
        (inset_x0 + 40, prof_baseline - 10),
        (inset_x0 + 100, prof_cliff_top_y + 40),
        (inset_x0 + 260, prof_cliff_top_y),
        (inset_x0 + 420, prof_cliff_top_y + 20),
        (inset_x0 + 500, prof_baseline - 15)
    ]
    draw.line(ridge_pts, fill=(148, 163, 184), width=2)
    draw.text((inset_x0 + 220, prof_cliff_top_y - 20), "Cliff Crest (+580' ASL)", fill=TEXT_PRIMARY, font=get_font(11, bold=True))

    # Tunnel horizontal bore inside mountain
    draw.line([(inset_x0 + 80, prof_tunnel_y), (inset_x0 + 460, prof_tunnel_y)], fill=PURPLE_ACCENT, width=5)
    draw.text((inset_x0 + 150, prof_tunnel_y + 12), "Twin Bores: Collar +435' | Sump +420' ASL", fill=(240, 200, 255), font=get_font(11))

    # Overburden vertical arrow
    ov_x = inset_x0 + 260
    draw.line([(ov_x, prof_cliff_top_y + 4), (ov_x, prof_tunnel_y - 4)], fill=AMBER_ACCENT, width=1)
    draw.text((ov_x + 8, (prof_cliff_top_y + prof_tunnel_y)//2 - 8), "Overburden: +145 FT", fill=AMBER_ACCENT, font=get_font(11))

    # 8. Compass Rose & Coordinate Telemetry Inset (Top Right)
    hud_x0 = w - 460
    hud_y0 = 30
    draw.rectangle([hud_x0, hud_y0, hud_x0 + 420, hud_y0 + 150], fill=(15, 23, 42, 230), outline=BORDER_LINE, width=1)
    draw.text((hud_x0 + 15, hud_y0 + 15), "GEOSPATIAL REFERENCE TELEMETRY", fill=CYAN_ACCENT, font=get_font(12, bold=True))
    draw.text((hud_x0 + 15, hud_y0 + 38), f"Center Coordinates: {TARGET_LAT:.4f}° N, {abs(TARGET_LNG):.4f}° W", fill=TEXT_PRIMARY, font=get_font(12))
    draw.text((hud_x0 + 15, hud_y0 + 58), "Distance from Hub: 8.56 Miles (Azimuth 324° NW)", fill=TEXT_SECONDARY, font=get_font(11))
    draw.text((hud_x0 + 15, hud_y0 + 78), "Topographic Quad: Belvidere / Delaware Water Gap", fill=TEXT_SECONDARY, font=get_font(11))
    draw.text((hud_x0 + 15, hud_y0 + 98), f"Geological Unit: {GEOLOGY}", fill=AMBER_ACCENT, font=get_font(11))
    draw.text((hud_x0 + 15, hud_y0 + 118), f"Hydrostatic Head: {HYDROSTATIC_PSI:.1f} PSI (Dry Bedrock Above 400' WT)", fill=EMERALD_ACCENT, font=get_font(11))

    return img


def generate_manunka_chunk_tactical_plate() -> Path:
    """Generates the full 2000 x 1560 tactical plate map3b_manunka_chunk_tunnels.png."""
    out_path = RAW_DIR / "map3b_manunka_chunk_tunnels.png"
    canvas = Image.new("RGB", (TEMPLATE_WIDTH, TEMPLATE_HEIGHT), CANVAS_BG)
    draw = ImageDraw.Draw(canvas)

    # 1. Header Band (y: 0 to 120)
    draw.rectangle([0, 0, TEMPLATE_WIDTH, HEADER_HEIGHT], fill=DARK_SLATE)
    draw.line([(0, HEADER_HEIGHT), (TEMPLATE_WIDTH, HEADER_HEIGHT)], fill=BORDER_LINE, width=2)
    draw.line([(0, HEADER_HEIGHT - 3), (TEMPLATE_WIDTH, HEADER_HEIGHT - 3)], fill=BORDER_ACCENT, width=1)

    fnt_title = get_font(26, bold=True)
    fnt_sub = get_font(18, bold=True)
    fnt_tele = get_font(13, bold=False)

    draw.text((VIEWPORT_X0, 15), "ZONE 3 TACTICAL SURVEY // MANUNKA CHUNK TWIN CLIFF TUNNELS", fill=TEXT_PRIMARY, font=fnt_title)
    draw.text((VIEWPORT_X0, 52), "DL&W (1856) & PRR (1869) DUAL 938-FT SHALE BORES // DELAWARE WATER GAP", fill=CYAN_ACCENT, font=fnt_sub)
    draw.text((VIEWPORT_X0, 86), f"TARGET: {TARGET_LAT:.4f}° N, {abs(TARGET_LNG):.4f}° W | BORE SPAN: {BORE_LENGTH_FT:.0f} FT | OVERBURDEN: +145 FT | DATUM: UNDERGROUND (+435' ASL) | PSI: {HYDROSTATIC_PSI:.1f}", fill=TEXT_MUTED, font=fnt_tele)

    # Tactical Zoom Badge (Header Right)
    draw.rectangle([TEMPLATE_WIDTH - 380, 20, TEMPLATE_WIDTH - 30, 80], fill=(24, 34, 53), outline=CYAN_ACCENT, width=1)
    draw.text((TEMPLATE_WIDTH - 365, 30), "TACTICAL RECONNAISSANCE", fill=TEXT_MUTED, font=fnt_tele)
    draw.text((TEMPLATE_WIDTH - 365, 48), f"ZOOM LEVEL {ZOOM_LEVEL} (1:2,400 SCALE)", fill=AMBER_ACCENT, font=get_font(14, bold=True))

    # 2. Render and Paste Tactical Viewport Content
    viewport_img = render_tactical_viewport()
    canvas.paste(viewport_img, (VIEWPORT_X0, VIEWPORT_Y0))

    # 3. Viewport Neatlines & Coordinate Border Ticks
    draw.rectangle([VIEWPORT_X0, VIEWPORT_Y0, VIEWPORT_X1, VIEWPORT_Y1], outline=BORDER_ACCENT, width=2)
    draw.rectangle([VIEWPORT_X0 - 4, VIEWPORT_Y0 - 4, VIEWPORT_X1 + 4, VIEWPORT_Y1 + 4], outline=BORDER_LINE, width=1)

    fnt_ticks = get_font(11, bold=False)
    # Latitude ticks (Left & Right margins)
    lat_min, lat_max = 40.820, 40.832
    for i in range(7):
        frac = i / 6.0
        y_pos = int(VIEWPORT_Y0 + frac * VIEWPORT_HEIGHT)
        tick_lat = lat_max - frac * (lat_max - lat_min)
        draw.line([(VIEWPORT_X0 - 8, y_pos), (VIEWPORT_X0, y_pos)], fill=BORDER_ACCENT, width=2)
        draw.text((VIEWPORT_X0 - 64, y_pos - 6), f"{tick_lat:.3f}°N", fill=TEXT_SECONDARY, font=fnt_ticks)
        draw.line([(VIEWPORT_X1, y_pos), (VIEWPORT_X1 + 8, y_pos)], fill=BORDER_ACCENT, width=2)
        draw.text((VIEWPORT_X1 + 14, y_pos - 6), f"{tick_lat:.3f}°N", fill=TEXT_SECONDARY, font=fnt_ticks)

    # Longitude ticks (Top & Bottom margins)
    lng_min, lng_max = -75.078, -75.058
    for i in range(9):
        frac = i / 8.0
        x_pos = int(VIEWPORT_X0 + frac * VIEWPORT_WIDTH)
        tick_lng = lng_min + frac * (lng_max - lng_min)
        draw.line([(x_pos, VIEWPORT_Y0 - 8), (x_pos, VIEWPORT_Y0)], fill=BORDER_ACCENT, width=2)
        draw.line([(x_pos, VIEWPORT_Y1), (x_pos, VIEWPORT_Y1 + 8)], fill=BORDER_ACCENT, width=2)
        draw.text((x_pos - 24, VIEWPORT_Y1 + 12), f"{abs(tick_lng):.3f}°W", fill=TEXT_SECONDARY, font=fnt_ticks)

    # 4. Footer Bar & Tactical Legend (y: 1460 to 1560)
    draw.rectangle([0, VIEWPORT_Y1, TEMPLATE_WIDTH, TEMPLATE_HEIGHT], fill=DARK_SLATE)
    draw.line([(0, VIEWPORT_Y1), (TEMPLATE_WIDTH, VIEWPORT_Y1)], fill=BORDER_LINE, width=2)
    draw.line([(0, VIEWPORT_Y1 + 3), (TEMPLATE_WIDTH, VIEWPORT_Y1 + 3)], fill=BORDER_ACCENT, width=1)

    fnt_legend_header = get_font(13, bold=True)
    fnt_legend_item = get_font(12, bold=False)

    draw.text((VIEWPORT_X0, VIEWPORT_Y1 + 45), "TACTICAL SYMBOLOGY:", fill=TEXT_MUTED, font=fnt_legend_header)

    tactical_legend = [
        ("DL&W North Bore (1856)", PURPLE_ACCENT),
        ("PRR South Bore (1869)", CYAN_ACCENT),
        ("Stone Portal Collars", (148, 163, 184)),
        ("Delaware River Shore", (56, 189, 248)),
        ("Colossus Apex Lair", RED_ACCENT),
        ("50-ft Tactical Grid", (60, 90, 130))
    ]

    leg_start_x = VIEWPORT_X0 + 220
    leg_spacing = 210
    for i, (leg_label, leg_col) in enumerate(tactical_legend):
        lx = leg_start_x + i * leg_spacing
        ly = VIEWPORT_Y1 + 48
        draw.rectangle([lx, ly, lx + 14, ly + 14], fill=leg_col, outline="white", width=1)
        draw.text((lx + 20, ly), leg_label, fill=TEXT_PRIMARY, font=fnt_legend_item)

    # Graphic Scale Bar (0 to 938 FT)
    scale_x1 = TEMPLATE_WIDTH - VIEWPORT_X0 - 20
    scale_x0 = scale_x1 - 240
    scale_y = VIEWPORT_Y1 + 46
    draw.rectangle([scale_x0, scale_y, scale_x1, scale_y + 8], fill="white", outline=BORDER_LINE, width=1)
    draw.rectangle([scale_x0, scale_y, scale_x0 + 120, scale_y + 8], fill=DARK_SLATE)
    draw.text((scale_x0 - 4, scale_y + 14), "0 FT", fill=TEXT_SECONDARY, font=fnt_ticks)
    draw.text((scale_x0 + 105, scale_y + 14), "500 FT", fill=TEXT_SECONDARY, font=fnt_ticks)
    draw.text((scale_x1 - 24, scale_y + 14), "938 FT", fill=AMBER_ACCENT, font=get_font(11, bold=True))

    # North arrow badge
    north_cx = scale_x0 - 50
    north_cy = scale_y + 10
    draw.polygon([(north_cx, north_cy - 16), (north_cx - 6, north_cy + 8), (north_cx, north_cy + 4)], fill=CYAN_ACCENT)
    draw.polygon([(north_cx, north_cy - 16), (north_cx + 6, north_cy + 8), (north_cx, north_cy + 4)], fill="white")
    draw.text((north_cx - 4, north_cy - 28), "N", fill=TEXT_PRIMARY, font=fnt_legend_header)

    # Save output
    canvas.save(out_path, "PNG", optimize=True)
    size_bytes = out_path.stat().st_size
    print(f"[COMPLETE] Generated Zone 3 Tactical Plate: {out_path.name}")
    print(f"  Resolution: {canvas.size} | File size: {size_bytes:,} bytes")

    # Save web-optimized JPEG version
    opt_file = OPT_DIR / "map3b_manunka_chunk_tunnels.jpg"
    opt_img = canvas.resize((1024, 798), Image.Resampling.LANCZOS)
    opt_img.save(opt_file, "JPEG", quality=88, optimize=True)
    print(f"  Web-optimized: {opt_file.name} -> {opt_img.size} ({opt_file.stat().st_size:,} bytes)")
    return out_path


if __name__ == "__main__":
    generate_manunka_chunk_tactical_plate()
