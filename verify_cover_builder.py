import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import BookFormat, FORMAT_SPECS, mm_to_pt, BLEED_MM
from src.core.cover_builder import CoverBuilder, hex_to_rgb_float
from src.core.image_processor import ImageProcessor
import pymupdf as fitz

def test_cover_builder():
    print("Testing CoverBuilder geometry and PDF creation...")

    # Create dummy images for test in a test directory
    test_dir = ROOT / "test_book_sample"
    test_dir.mkdir(exist_ok=True)

    front_img = test_dir / "cover_front.png"
    back_img = test_dir / "cover_back.png"
    int1 = test_dir / "001.png"
    int2 = test_dir / "002.png"
    int3 = test_dir / "003.png"
    int4 = test_dir / "004.png"

    # Draw dummy images
    for p, color in [(front_img, "blue"), (back_img, "orange"), (int1, "white"), (int2, "white"), (int3, "white"), (int4, "white")]:
        im = Image.new("RGB", (600, 800), color=color)
        draw = ImageDraw.Draw(im)
        draw.rectangle([20, 20, 580, 780], outline="black", width=5)
        im.save(p)

    # 1. Test image_processor exclusions and find_cover_files
    cover_files = ImageProcessor.find_cover_files(str(test_dir))
    assert cover_files["front"] == str(front_img.resolve()), f"Expected front cover, got {cover_files['front']}"
    assert cover_files["back"] == str(back_img.resolve()), f"Expected back cover, got {cover_files['back']}"

    interior_files = ImageProcessor.get_image_files(str(test_dir), include_cover=False)
    assert len(interior_files) == 4, f"Expected 4 interior files, got {len(interior_files)}"
    for f in interior_files:
        assert not f.stem.lower().startswith("cover_"), f"Cover file leaked into interior: {f}"

    # 2. Test spine calculation
    spine_mm = CoverBuilder.calculate_spine_width_mm(80)
    print(f"Calculated spine for 80 pages: {spine_mm} mm")
    assert spine_mm > 4.0, f"Spine width unexpected: {spine_mm}"

    # 3. Test build_cover_pdf
    out_pdf = test_dir / "test_cover.pdf"
    res = CoverBuilder.build_cover_pdf(
        book_format=BookFormat.A4,
        front_cover_path=str(front_img),
        back_cover_path=str(back_img),
        interior_image_paths=[str(int1), str(int2), str(int3), str(int4)],
        spine_width_mm=spine_mm,
        spine_color_hex="#2d5a27",
        output_path=str(out_pdf)
    )

    assert Path(res).exists(), "Output PDF was not generated"

    # Verify generated PDF dimensions
    doc = fitz.open(res)
    assert len(doc) == 1, f"Cover PDF must have exactly 1 page, got {len(doc)}"
    page = doc[0]
    rect = page.rect
    print(f"Generated PDF Page Size (pt): {rect.width:.2f} x {rect.height:.2f}")

    spec = FORMAT_SPECS[BookFormat.A4]
    bleed_pt = mm_to_pt(BLEED_MM)
    expected_w = 2 * bleed_pt + 2 * spec.width_pt + mm_to_pt(spine_mm)
    expected_h = spec.height_pt + 2 * bleed_pt

    assert abs(rect.width - expected_w) < 0.5, f"Width mismatch: {rect.width} vs expected {expected_w}"
    assert abs(rect.height - expected_h) < 0.5, f"Height mismatch: {rect.height} vs expected {expected_h}"
    doc.close()

    print("ALL TESTS PASSED SUCCESSFULLY!")

    # Clean up test files
    for p in [front_img, back_img, int1, int2, int3, int4, out_pdf]:
        if p.exists():
            p.unlink()
    test_dir.rmdir()

if __name__ == "__main__":
    test_cover_builder()
