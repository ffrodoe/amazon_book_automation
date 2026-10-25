import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BookFormat, FORMAT_SPECS, DEFAULT_INTRO_COUNT
from src.core.image_processor import ImageProcessor
from src.core.pdf_builder import PDFBuilder
from src.core.image_cleaner import ImageCleaner



def main():
    parser = argparse.ArgumentParser(
        description="Amazon KDP Coloring Book PDF Generator (Interior)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli -i reference/FarmAdventures -f a4
  python -m src.cli -i "C:/path/to/images" -f 8.5x8.5 -o "output/MyBook.pdf"
        """
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to folder containing coloring book images"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["a4", "8.5x8.5"],
        default="a4",
        help="Target book format: 'a4' (default) or '8.5x8.5'"
    )
    parser.add_argument(
        "--intro-count",
        type=int,
        default=DEFAULT_INTRO_COUNT,
        help=f"Number of initial consecutive images without blanks (default: {DEFAULT_INTRO_COUNT})"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Custom output PDF path (optional)"
    )
    parser.add_argument(
        "--clean-background",
        action="store_true",
        help="Automatically whiten ChatGPT image backgrounds before assembly"
    )
    parser.add_argument(
        "--clean-brightness",
        type=int,
        default=40,
        help="Brightness whitening offset (default: 40, equivalent to Photoshop +40)"
    )

    args = parser.parse_args()


    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input directory does not exist: {input_path}")
        sys.exit(1)

    book_format = BookFormat.A4 if args.format == "a4" else BookFormat.SQUARE_8_5
    spec = FORMAT_SPECS[book_format]

    print("=" * 60)
    print(" Amazon KDP Coloring Book Generator")
    print("=" * 60)
    print(f" Source Folder: {input_path.resolve()}")
    print(f" Target Format: {spec.name} ({spec.description})")
    print(f" Intro Pages:   {args.intro_count}")
    print("-" * 60)

    try:
        source_dir = input_path
        if args.clean_background:
            print(f"[0/3] Whitening ChatGPT background (offset: +{args.clean_brightness})...")
            out_cleaned = input_path / "cleaned"
            ImageCleaner.clean_folder(
                input_dir=str(input_path),
                output_dir=str(out_cleaned),
                brightness_offset=args.clean_brightness
            )
            print(f"      Cleaned images saved to: {out_cleaned}")
            source_dir = out_cleaned

        print("[1/3] Scanning and analyzing images...")
        plan = ImageProcessor.build_book_plan(
            directory=str(source_dir),
            book_format=book_format,
            intro_count=args.intro_count
        )

        print(f"      Found {plan.total_images} images.")
        print(f"      Calculated {plan.total_pages} total PDF pages.")
        print(f"      (Right/Recto = Drawings, Left/Verso = Blank protection sheets)")

        print("\n[2/3] Building Amazon KDP print-ready PDF...")
        def progress(curr, total, msg):
            pct = int((curr / total) * 100)
            bar_len = 30
            filled = int(bar_len * curr // total)
            bar = "#" * filled + "-" * (bar_len - filled)
            sys.stdout.write(f"\r      [{bar}] {pct}% | {msg[:40]:<40}")
            sys.stdout.flush()

        out_path = PDFBuilder.build_pdf(
            plan=plan,
            output_path=args.output,
            progress_callback=progress
        )
        print()

        file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
        print("\n[3/3] Successfully generated PDF!")
        print(f"      Output: {out_path}")
        print(f"      Size:   {file_size_mb:.2f} MB")
        print(f"      Pages:  {plan.total_pages} pages (Even page count for KDP)")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed to build PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
