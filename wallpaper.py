"""
Life Calendar Wallpaper
Genera una PNG che rappresenta la vita in settimane, sotto forma di griglia di pallini.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------------
# COSTANTI - DATI PERSONALI
# --------------------------------------------------------------------------

BIRTHDATE = datetime.date(1996, 8, 4)
LIFE_EXPECTANCY_YEARS = 83

# --------------------------------------------------------------------------
# COSTANTI - GRIGLIA
# --------------------------------------------------------------------------

GRID_ROWS = 83
GRID_COLS = 52
TOTAL_WEEKS = GRID_ROWS * GRID_COLS
RECENT_WEEKS_COUNT = 52

# --------------------------------------------------------------------------
# COSTANTI - CANVAS
# --------------------------------------------------------------------------

CANVAS_WIDTH = 1290
CANVAS_HEIGHT = 2796
SUPERSAMPLE_FACTOR = 4

# --------------------------------------------------------------------------
# COSTANTI - LAYOUT (percentuali, non pixel fissi)
# --------------------------------------------------------------------------

GRID_WIDTH_RATIO = 0.86   # larghezza griglia rispetto alla larghezza canvas
GRID_HEIGHT_RATIO = 0.50  # altezza griglia rispetto all'altezza canvas
VERTICAL_POSITION = 0.40  # offset verticale dell'inizio griglia (libera zona orologio)
DOT_SIZE_RATIO = 0.62     # diametro pallino rispetto alla cella disponibile

# --------------------------------------------------------------------------
# COSTANTI - COLORI
# --------------------------------------------------------------------------

BACKGROUND_COLOR = (0, 0, 0, 255)
FUTURE_COLOR = (0x25, 0x25, 0x25, 255)
PAST_COLOR = (0x8C, 0x8C, 0x8C, 255)
RECENT_COLOR = (0xF5, 0xF5, 0xF5, 255)
CURRENT_COLOR = (0x00, 0xA6, 0x93, 255)

# --------------------------------------------------------------------------
# COSTANTI - GLOW SETTIMANA CORRENTE
# --------------------------------------------------------------------------

GLOW_PADDING_RATIO = 2.2   # dimensione patch locale rispetto al diametro pallino
GLOW_BLUR_RADIUS_RATIO = 0.35  # blur rispetto al diametro pallino
GLOW_ALPHA = 90            # intensità alone (0-255), leggero e non appariscente

# --------------------------------------------------------------------------
# COSTANTI - OUTPUT
# --------------------------------------------------------------------------

OUTPUT_DIR = Path("output")
OUTPUT_FILENAME = "wallpaper.png"


@dataclass(frozen=True)
class Layout:
    cell_width: float
    cell_height: float
    dot_diameter: float
    start_x: float
    start_y: float


def calculate_weeks_lived(birthdate: datetime.date, today: datetime.date) -> int:
    """Calcolo simbolico delle settimane vissute, non calendariale-reale."""
    weeks = (today - birthdate).days // 7
    return max(0, min(weeks, TOTAL_WEEKS - 1))


def compute_layout(width: int, height: int) -> Layout:
    grid_width = width * GRID_WIDTH_RATIO
    grid_height = height * GRID_HEIGHT_RATIO

    cell_width = grid_width / GRID_COLS
    cell_height = grid_height / GRID_ROWS

    dot_diameter = min(cell_width, cell_height) * DOT_SIZE_RATIO

    start_x = (width - grid_width) / 2
    start_y = height * VERTICAL_POSITION

    return Layout(
        cell_width=cell_width,
        cell_height=cell_height,
        dot_diameter=dot_diameter,
        start_x=start_x,
        start_y=start_y,
    )


def get_week_color(index: int, weeks_lived: int) -> tuple[int, int, int, int]:
    if index > weeks_lived:
        return FUTURE_COLOR
    if index == weeks_lived:
        return CURRENT_COLOR
    if index >= weeks_lived - RECENT_WEEKS_COUNT:
        return RECENT_COLOR
    return PAST_COLOR


def cell_center(layout: Layout, row: int, col: int) -> tuple[float, float]:
    cx = layout.start_x + col * layout.cell_width + layout.cell_width / 2
    cy = layout.start_y + row * layout.cell_height + layout.cell_height / 2
    return cx, cy


def draw_dot(draw: ImageDraw.ImageDraw, center: tuple[float, float], diameter: float, color: tuple[int, int, int, int]) -> None:
    cx, cy = center
    radius = diameter / 2
    bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(bbox, fill=color)


def create_glow_patch(dot_diameter: float, color: tuple[int, int, int, int]) -> Image.Image:
    """Patch locale contenente solo l'alone, per evitare un layer grande quanto il canvas."""
    patch_size = int(dot_diameter * GLOW_PADDING_RATIO)
    blur_radius = dot_diameter * GLOW_BLUR_RADIUS_RATIO

    patch = Image.new("RGBA", (patch_size, patch_size), (0, 0, 0, 0))
    patch_draw = ImageDraw.Draw(patch)

    center = patch_size / 2
    radius = dot_diameter / 2
    glow_color = (color[0], color[1], color[2], GLOW_ALPHA)

    patch_draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill=glow_color,
    )

    return patch.filter(ImageFilter.GaussianBlur(blur_radius))


def apply_current_week_glow(image: Image.Image, center: tuple[float, float], dot_diameter: float) -> None:
    glow_patch = create_glow_patch(dot_diameter, CURRENT_COLOR)
    cx, cy = center
    paste_x = int(cx - glow_patch.width / 2)
    paste_y = int(cy - glow_patch.height / 2)
    image.paste(glow_patch, (paste_x, paste_y), glow_patch)


def draw_grid(image: Image.Image, draw: ImageDraw.ImageDraw, layout: Layout, weeks_lived: int) -> None:
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            index = row * GRID_COLS + col
            color = get_week_color(index, weeks_lived)
            center = cell_center(layout, row, col)

            if index == weeks_lived:
                apply_current_week_glow(image, center, layout.dot_diameter)

            draw_dot(draw, center, layout.dot_diameter, color)


def generate_wallpaper(weeks_lived: int) -> Image.Image:
    render_width = CANVAS_WIDTH * SUPERSAMPLE_FACTOR
    render_height = CANVAS_HEIGHT * SUPERSAMPLE_FACTOR

    image = Image.new("RGBA", (render_width, render_height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    layout = compute_layout(render_width, render_height)
    draw_grid(image, draw, layout, weeks_lived)

    final_image = image.resize(
        (CANVAS_WIDTH, CANVAS_HEIGHT),
        resample=Image.Resampling.LANCZOS,
    )
    return final_image.convert("RGB")


def save_output(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def main() -> None:
    today = datetime.date.today()
    weeks_lived = calculate_weeks_lived(BIRTHDATE, today)

    wallpaper = generate_wallpaper(weeks_lived)
    save_output(wallpaper, OUTPUT_DIR / OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
