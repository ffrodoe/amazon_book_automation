import sys
from pathlib import Path
import pymupdf as fitz

def verify(pdf_path: str):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Total Pages: {total_pages}")
    assert total_pages == 62, f"Expected 62 pages, got {total_pages}"
    assert total_pages % 2 == 0, "Page count must be even for Amazon KDP"

    a4_w, a4_h = 595.28, 841.89

    blank_count = 0
    img_count = 0

    for idx, page in enumerate(doc):
        pno = idx + 1
        rect = page.rect
        assert abs(rect.width - a4_w) < 1.0, f"Page {pno} width mismatch: {rect.width} != {a4_w}"
        assert abs(rect.height - a4_h) < 1.0, f"Page {pno} height mismatch: {rect.height} != {a4_h}"

        images = page.get_images()
        has_image = len(images) > 0

        # Check our expected rules:
        if pno in (1, 2, 3):
            assert has_image, f"Page {pno} should have an image!"
            img_count += 1
        elif pno % 2 == 0:
            # Even pages from 4 onwards should be blank
            assert not has_image, f"Page {pno} (even) should be blank, but found image!"
            blank_count += 1
        else:
            # Odd pages from 5 onwards should have coloring illustrations
            assert has_image, f"Page {pno} (odd) should have an illustration!"
            img_count += 1

    doc.close()
    print(f"SUCCESS: All 62 pages verified!")
    print(f"  - Illustrations: {img_count} pages (Pages 1, 2, 3, and all odd pages 5, 7, ... 61)")
    print(f"  - Blank protective sheets: {blank_count} pages (All even pages 4, 6, ... 62)")
    print(f"  - All pages match exact Amazon KDP A4 dimensions (595.28 x 841.89 pt)")

if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "output/FarmAdventures_a4_interior.pdf"
    verify(pdf_file)
