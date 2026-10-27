import os
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import pymupdf as fitz

from src.config import (
    BookFormat,
    FORMAT_SPECS,
    BLEED_MM,
    SPINE_PAGE_THICKNESS_MM,
    COVER_LAYOUT_SPEC,
    DEFAULT_LOGO_PATH,
    mm_to_pt
)


def hex_to_rgb_float(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex string (e.g. '#2d5a27' or '2d5a27') to RGB float tuple (0.0 - 1.0)."""
    hex_clean = hex_color.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join([c * 2 for c in hex_clean])
    if len(hex_clean) != 6:
        # Default forest green fallback
        return (0.176, 0.353, 0.153)
    try:
        r = int(hex_clean[0:2], 16) / 255.0
        g = int(hex_clean[2:4], 16) / 255.0
        b = int(hex_clean[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return (0.176, 0.353, 0.153)


class CoverBuilder:
    @staticmethod
    def calculate_spine_width_mm(page_count: int) -> float:
        """
        Calculates spine thickness in millimeters based on Amazon KDP specs for standard B&W white paper:
        Spine (inches) = page_count * 0.002252 -> mm = page_count * 0.0572.
        Enforces a practical minimum of 1.5 mm.
        """
        calculated = page_count * SPINE_PAGE_THICKNESS_MM
        return max(1.5, round(calculated, 2))

    @classmethod
    def calculate_cover_geometry(
        cls,
        book_format: BookFormat,
        spine_width_mm: float
    ) -> dict:
        """
        Calculates all geometric dimensions, positions, and percentage coordinates
        for both the print PDF builder and the web UI live preview.
        Uses COVER_LAYOUT_SPEC as the single source of truth.
        """
        spec = FORMAT_SPECS[book_format]
        trim_w, trim_h = spec.dimensions_pt
        bleed_pt = mm_to_pt(BLEED_MM)
        spine_pt = mm_to_pt(spine_width_mm)

        total_width_pt = 2 * bleed_pt + 2 * trim_w + spine_pt
        total_height_pt = trim_h + 2 * bleed_pt
        back_pane_w_pt = bleed_pt + trim_w

        # Thumbnail cards
        aspect_ratio = trim_w / trim_h
        thumb_ratio = COVER_LAYOUT_SPEC["thumb_width_ratio"]  # 0.29 (+5% size)
        card_w = trim_w * thumb_ratio
        if book_format == BookFormat.A4:
            card_h = card_w / aspect_ratio
        else:
            card_h = card_w * 1.25

        gap_x = COVER_LAYOUT_SPEC["thumb_gap_x_pt"]
        gap_y = COVER_LAYOUT_SPEC["thumb_gap_y_pt"]
        grid_total_w = 2 * card_w + gap_x
        grid_total_h = 2 * card_h + gap_y

        # HORIZONTAL CENTERING on the back cover trim:
        # (left margin from bleed = right margin to spine)
        start_x = bleed_pt + (trim_w - grid_total_w) / 2.0

        # VERTICAL POSITIONING (ends at 65% of trim height)
        target_bottom_y = bleed_pt + (trim_h * COVER_LAYOUT_SPEC["thumb_grid_bottom_ratio"])
        start_y = target_bottom_y - grid_total_h

        # Brand logo
        logo_w = trim_w * COVER_LAYOUT_SPEC["logo_width_ratio"]
        logo_left = bleed_pt + trim_w * COVER_LAYOUT_SPEC["logo_left_ratio"]
        logo_bottom = bleed_pt + trim_h * (1.0 - COVER_LAYOUT_SPEC["logo_bottom_ratio"])

        # Percentages relative to the Back Cover pane (for CSS/JS UI preview)
        grid_left_pct = (start_x / back_pane_w_pt) * 100.0
        grid_top_pct = (start_y / total_height_pt) * 100.0
        grid_width_pct = (grid_total_w / back_pane_w_pt) * 100.0
        grid_height_pct = (grid_total_h / total_height_pt) * 100.0

        logo_left_pct = (logo_left / back_pane_w_pt) * 100.0
        logo_bottom_pct = ((total_height_pt - logo_bottom) / total_height_pt) * 100.0
        logo_width_pct = (logo_w / back_pane_w_pt) * 100.0

        return {
            "book_format": book_format.value,
            "spine_width_mm": spine_width_mm,
            "bleed_mm": BLEED_MM,
            "bleed_pt": bleed_pt,
            "trim_w_pt": trim_w,
            "trim_h_pt": trim_h,
            "total_width_pt": total_width_pt,
            "total_height_pt": total_height_pt,
            "total_width_mm": round(total_width_pt * 25.4 / 72.0, 1),
            "total_height_mm": round(total_height_pt * 25.4 / 72.0, 1),
            "back_pane_w_pt": back_pane_w_pt,
            "spine_pt": spine_pt,
            "front_pane_w_pt": back_pane_w_pt,
            "grid": {
                "start_x_pt": start_x,
                "start_y_pt": start_y,
                "card_w_pt": card_w,
                "card_h_pt": card_h,
                "grid_w_pt": grid_total_w,
                "grid_h_pt": grid_total_h,
                "gap_x_pt": gap_x,
                "gap_y_pt": gap_y,
                "card_padding_pt": COVER_LAYOUT_SPEC["thumb_card_padding_pt"],
                "frame_gap_pt": COVER_LAYOUT_SPEC["thumb_frame_gap_pt"],
                "line_w_pt": COVER_LAYOUT_SPEC["thumb_frame_line_pt"],
                "left_pct": round(grid_left_pct, 2),
                "top_pct": round(grid_top_pct, 2),
                "width_pct": round(grid_width_pct, 2),
                "height_pct": round(grid_height_pct, 2),
            },
            "logo": {
                "left_pt": logo_left,
                "bottom_pt": logo_bottom,
                "width_pt": logo_w,
                "left_pct": round(logo_left_pct, 2),
                "bottom_pct": round(logo_bottom_pct, 2),
                "width_pct": round(logo_width_pct, 2),
            },
            "panes": {
                "back_pct": round((back_pane_w_pt / total_width_pt) * 100.0, 2),
                "spine_pct": round((spine_pt / total_width_pt) * 100.0, 2),
                "front_pct": round((back_pane_w_pt / total_width_pt) * 100.0, 2),
            }
        }

    @classmethod
    def build_cover_pdf(
        cls,
        book_format: BookFormat,
        front_cover_path: str,
        back_cover_path: str,
        interior_image_paths: List[str],
        spine_width_mm: float,
        spine_color_hex: str = "#2d5a27",
        logo_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Builds a single-page print-ready Amazon KDP cover PDF:
        - Layout: [Back Cover] + [Spine] + [Front Cover]
        - 0.125" (3.175mm) Bleed on all 4 outside edges
        - 4 horizontally centered interior thumbnails in double-framed mini-cards on the back cover
        - Brand logo in the bottom-left corner
        - Spine with solid fill color
        """
        front_file = Path(front_cover_path)
        back_file = Path(back_cover_path)
        if not front_file.exists():
            raise FileNotFoundError(f"Front cover not found: {front_cover_path}")
        if not back_file.exists():
            raise FileNotFoundError(f"Back cover not found: {back_cover_path}")

        # Resolve logo
        resolved_logo = None
        if logo_path and Path(logo_path).exists():
            resolved_logo = Path(logo_path)
        elif DEFAULT_LOGO_PATH.exists():
            resolved_logo = DEFAULT_LOGO_PATH

        # Get unified geometry
        geom = cls.calculate_cover_geometry(book_format, spine_width_mm)

        # Determine output path if not specified
        if not output_path:
            parent_dir = front_file.parent
            folder_name = parent_dir.name
            output_path = str((parent_dir / f"{folder_name}_{book_format.value}_cover.pdf").resolve())
        else:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            output_path = str(out_p.resolve())

        doc = fitz.open()
        page = doc.new_page(width=geom["total_width_pt"], height=geom["total_height_pt"])

        # 1. Back Cover Area (Left): extends from 0 to back_pane_w_pt
        back_rect = fitz.Rect(0, 0, geom["back_pane_w_pt"], geom["total_height_pt"])
        page.insert_image(back_rect, filename=str(back_file.resolve()), keep_proportion=False)

        # 2. Spine Area (Center): extends from back_pane_w_pt to back_pane_w_pt + spine_pt
        spine_rect = fitz.Rect(geom["back_pane_w_pt"], 0, geom["back_pane_w_pt"] + geom["spine_pt"], geom["total_height_pt"])
        spine_rgb = hex_to_rgb_float(spine_color_hex)
        page.draw_rect(spine_rect, color=spine_rgb, fill=spine_rgb)

        # 3. Front Cover Area (Right): extends from spine end to total_width_pt
        front_rect = fitz.Rect(geom["back_pane_w_pt"] + geom["spine_pt"], 0, geom["total_width_pt"], geom["total_height_pt"])
        page.insert_image(front_rect, filename=str(front_file.resolve()), keep_proportion=False)

        # 4. Draw 4 Interior Thumbnails on the Back Cover (horizontally centered, ending at 65% height)
        if interior_image_paths and len(interior_image_paths) > 0:
            cls._draw_interior_thumbnails(
                page=page,
                image_paths=interior_image_paths[:4],
                geom=geom
            )

        # 5. Draw Brand Logo in Bottom-Left Corner of Back Cover
        if resolved_logo and resolved_logo.exists():
            cls._draw_brand_logo(
                page=page,
                logo_path=str(resolved_logo.resolve()),
                geom=geom
            )

        doc.save(output_path, deflate=True)
        doc.close()
        return output_path

    @classmethod
    def _draw_interior_thumbnails(
        cls,
        page: fitz.Page,
        image_paths: List[str],
        geom: dict
    ) -> None:
        """
        Draws up to 4 interior thumbnail cards arranged in a 2x2 grid,
        using unified geometry (horizontally centered, ending at 65% height).
        """
        count = len(image_paths)
        if count == 0:
            return

        grid = geom["grid"]
        start_x = grid["start_x_pt"]
        start_y = grid["start_y_pt"]
        card_w = grid["card_w_pt"]
        card_h = grid["card_h_pt"]
        gap_x = grid["gap_x_pt"]
        gap_y = grid["gap_y_pt"]
        card_padding = grid["card_padding_pt"]
        frame_gap = grid["frame_gap_pt"]
        line_w = grid["line_w_pt"]

        for idx, img_path in enumerate(image_paths):
            if not img_path or not Path(img_path).exists():
                continue

            row = idx // 2
            col = idx % 2

            x0 = start_x + col * (card_w + gap_x)
            y0 = start_y + row * (card_h + gap_y)
            x1 = x0 + card_w
            y1 = y0 + card_h

            outer_card_rect = fitz.Rect(x0, y0, x1, y1)

            # 1. Crisp white background card
            page.draw_rect(
                outer_card_rect,
                color=(0.85, 0.85, 0.85),
                fill=(1, 1, 1),
                width=0.5
            )

            # 2. Outer frame line
            outer_frame = fitz.Rect(
                x0 + card_padding,
                y0 + card_padding,
                x1 - card_padding,
                y1 - card_padding
            )
            page.draw_rect(
                outer_frame,
                color=(0.15, 0.15, 0.15),
                width=line_w
            )

            # 3. Inner frame line
            inner_frame = fitz.Rect(
                outer_frame.x0 + frame_gap,
                outer_frame.y0 + frame_gap,
                outer_frame.x1 - frame_gap,
                outer_frame.y1 - frame_gap
            )
            page.draw_rect(
                inner_frame,
                color=(0.15, 0.15, 0.15),
                width=line_w
            )

            # 4. Insert interior artwork inside inner frame
            art_rect = fitz.Rect(
                inner_frame.x0 + 0.5,
                inner_frame.y0 + 0.5,
                inner_frame.x1 - 0.5,
                inner_frame.y1 - 0.5
            )
            try:
                page.insert_image(
                    art_rect,
                    filename=str(Path(img_path).resolve()),
                    keep_proportion=False  # Fit neatly to frame geometry
                )
            except Exception as e:
                print(f"Warning: could not insert thumbnail {img_path}: {e}")

    @classmethod
    def _draw_brand_logo(
        cls,
        page: fitz.Page,
        logo_path: str,
        geom: dict
    ) -> None:
        """
        Draws the brand logo in the bottom-left corner of the back cover,
        preserving its native aspect ratio using unified geometry.
        """
        try:
            with Image.open(logo_path) as img:
                orig_w, orig_h = img.size
                logo_aspect = orig_w / orig_h if orig_h > 0 else 1.0

            logo_spec = geom["logo"]
            target_w = logo_spec["width_pt"]
            target_h = target_w / logo_aspect

            x0 = logo_spec["left_pt"]
            y1 = logo_spec["bottom_pt"]
            y0 = y1 - target_h
            x1 = x0 + target_w

            logo_rect = fitz.Rect(x0, y0, x1, y1)
            page.insert_image(
                logo_rect,
                filename=logo_path,
                keep_proportion=True
            )
        except Exception as e:
            print(f"Warning: could not draw brand logo {logo_path}: {e}")
