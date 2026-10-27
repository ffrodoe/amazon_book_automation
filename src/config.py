from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple


class BookFormat(str, Enum):
    A4 = "a4"
    SQUARE_8_5 = "8.5x8.5"


@dataclass(frozen=True)
class FormatSpec:
    name: str
    width_pt: float
    height_pt: float
    width_px_300dpi: int
    height_px_300dpi: int
    description: str

    @property
    def dimensions_pt(self) -> Tuple[float, float]:
        return (self.width_pt, self.height_pt)


# Standard Amazon KDP Interior Dimensions
FORMAT_SPECS = {
    BookFormat.A4: FormatSpec(
        name="A4",
        width_pt=595.28,      # 210mm in points (72 pt/in)
        height_pt=841.89,     # 297mm in points
        width_px_300dpi=2480, # 210mm @ 300 DPI
        height_px_300dpi=3508,# 297mm @ 300 DPI
        description="Standard A4 (210 x 297 mm / 8.27 x 11.69 in)"
    ),
    BookFormat.SQUARE_8_5: FormatSpec(
        name="8.5x8.5",
        width_pt=612.0,       # 8.5 * 72 pt
        height_pt=612.0,      # 8.5 * 72 pt
        width_px_300dpi=2550, # 8.5 * 300 px
        height_px_300dpi=2550,# 8.5 * 300 px
        description="Square (8.5 x 8.5 in / 215.9 x 215.9 mm)"
    )
}

# Default ordering rule:
# Images 1, 2, 3 -> Sequential (pages 1, 2, 3)
# Images 4..N   -> Alternating (image, blank, image, blank...)
# Final page is blank (ensuring even page count for KDP)
DEFAULT_INTRO_COUNT = 3

# Margin and Gutter specifications (in millimeters)
# Amazon KDP Safe Zone: Gutter is on spine side, default 15mm on outer/top/bottom
MARGIN_DEFAULT_MM = 15.0  # Top, bottom, outside cut margin
MARGIN_GUTTER_MM = 20.0   # Spine / gutter margin

# Frame specifications
FRAME_LINE_WIDTH_PT = 1.5 # Line thickness
FRAME_GAP_MM = 3.0        # Gap between double lines

# Background whitening default offset
DEFAULT_BRIGHTNESS_OFFSET = 40


# Amazon KDP Cover Specifications
BLEED_MM = 3.175  # 0.125 inch bleed on all outside edges
SPINE_PAGE_THICKNESS_MM = 0.0572  # 0.002252 in / page for B&W white paper

# Cover Layout Specification (Single Source of Truth for PDF Builder & UI Preview)
COVER_LAYOUT_SPEC = {
    # 4 Miniature Interior Cards on Back Cover
    "thumb_width_ratio": 0.31,        # card_w = trim_w * 0.29 (+5% larger, horizontally centered)
    "thumb_grid_bottom_ratio": 0.67,   # bottom of grid ends at 65% of trim height
    "thumb_gap_x_pt": 14.0,            # horizontal gap between cards
    "thumb_gap_y_pt": 14.0,            # vertical gap between cards
    "thumb_card_padding_pt": 5.0,      # white border around artwork
    "thumb_frame_gap_pt": 1.5,         # gap between double frames
    "thumb_frame_line_pt": 0.65,       # border line width

    # Brand Logo on Back Cover
    "logo_width_ratio": 0.32,          # logo_w = trim_w * 0.44
    "logo_bottom_ratio": 0.04,         # 4% from bottom trim
    "logo_left_ratio": 0.07,           # 7% from left trim
}

# Default Assets
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOGO_PATH = ROOT_DIR / "brand_logo.png"


def mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF typographic points (72 points per inch, 25.4 mm/inch)."""
    return mm * 72.0 / 25.4

