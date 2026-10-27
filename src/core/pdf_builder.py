import os
from pathlib import Path
from typing import Callable, Optional
import pymupdf as fitz

from src.config import (
    BookFormat,
    FORMAT_SPECS,
    MARGIN_DEFAULT_MM,
    MARGIN_GUTTER_MM,
    FRAME_LINE_WIDTH_PT,
    FRAME_GAP_MM,
    mm_to_pt
)
from src.core.image_processor import BookPlan


class PDFBuilder:
    @staticmethod
    def build_pdf(
        plan: BookPlan,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Builds a high-quality print-ready PDF according to Amazon KDP specifications,
        applying safe margins (20mm gutter, 15mm outside) and double framing for coloring illustrations.
        """
        spec = FORMAT_SPECS[plan.format]
        width_pt, height_pt = spec.dimensions_pt
        page_full_rect = fitz.Rect(0, 0, width_pt, height_pt)

        margin_default_pt = mm_to_pt(MARGIN_DEFAULT_MM)
        margin_gutter_pt = mm_to_pt(MARGIN_GUTTER_MM)
        frame_gap_pt = mm_to_pt(FRAME_GAP_MM)
        line_width = FRAME_LINE_WIDTH_PT

        # Determine output path if not specified (save directly into the images folder)
        if not output_path:
            folder_path = Path(plan.folder_path)
            folder_name = folder_path.name
            output_path = str((folder_path / f"{folder_name}_{plan.format.value}_interior.pdf").resolve())
        else:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            output_path = str(out_file.resolve())

        doc = fitz.open()

        total = len(plan.pages)
        for idx, page_plan in enumerate(plan.pages):
            page_num = idx + 1
            # Create page with exact KDP dimensions
            pdf_page = doc.new_page(width=width_pt, height=height_pt)

            if page_plan.is_blank:
                # Explicit clean white background for printers
                pdf_page.draw_rect(page_full_rect, color=(1, 1, 1), fill=(1, 1, 1))
                msg = f"Page {page_num}/{total}: Blank Page"
            else:
                # Calculate margins with KDP spine (gutter) positioning:
                # Spine is on LEFT for all illustration pages (odd pages / Recto) and page 1.
                # Spine is on RIGHT only for page 2 (copyright / Verso).
                if page_num == 2:
                    left_m = margin_default_pt
                    right_m = margin_gutter_pt
                else:
                    left_m = margin_gutter_pt
                    right_m = margin_default_pt

                top_m = margin_default_pt
                bottom_m = margin_default_pt

                outer_rect = fitz.Rect(
                    left_m,
                    top_m,
                    width_pt - right_m,
                    height_pt - bottom_m
                )

                if page_num in (1, 2):
                    # Pages 1 & 2: margins applied without frame
                    pdf_page.insert_image(
                        outer_rect,
                        filename=page_plan.image_path,
                        keep_proportion=True
                    )
                    msg = f"Page {page_num}/{total}: {page_plan.image_name} (Margins only)"
                else:
                    # Page 3 and subsequent coloring pages:
                    # Draw double frame: two identical thin lines (1.5 pt) with 3mm gap
                    inner_rect = fitz.Rect(
                        outer_rect.x0 + frame_gap_pt,
                        outer_rect.y0 + frame_gap_pt,
                        outer_rect.x1 - frame_gap_pt,
                        outer_rect.y1 - frame_gap_pt
                    )

                    # 1. Insert artwork stretched strictly to the inner frame format
                    pdf_page.insert_image(
                        inner_rect,
                        filename=page_plan.image_path,
                        keep_proportion=False
                    )

                    # 2. Draw double frame ON TOP of the image (top layer)
                    # Vector inner line (cleanly borders and covers image edges)
                    pdf_page.draw_rect(inner_rect, color=(0, 0, 0), width=line_width)
                    # Vector outer line (at margin boundary)
                    pdf_page.draw_rect(outer_rect, color=(0, 0, 0), width=line_width)

                    msg = f"Page {page_num}/{total}: {page_plan.image_name} (Double Framed)"

            if progress_callback:
                progress_callback(page_num, total, msg)

        # Save with clean compression and garbage collection for Amazon KDP compliance
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )
        doc.close()

        return output_path
