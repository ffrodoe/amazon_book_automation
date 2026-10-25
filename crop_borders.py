import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.border_remover import BorderRemover


def main():
    parser = argparse.ArgumentParser(
        description="Automated Frame / Border Removal for AI Coloring Book Images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crop_borders.py -i reference/FarmAdventures
  python crop_borders.py -i "C:/path/to/images" -o "C:/path/to/images/cleaned" --debug
        """
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to folder containing coloring book images"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Custom output folder (default: <input>/cropped)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save debug visualization images with marked crop borders to <output>/debug"
    )
    parser.add_argument(
        "--density",
        type=float,
        default=0.60,
        help="Line density threshold for border detection (default: 0.60)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_dir():
        print(f"[ERROR] Input directory does not exist or is not a folder: {input_path}")
        sys.exit(1)

    out_path = Path(args.output) if args.output else input_path / "cropped"

    print("=" * 65)
    print(" Amazon KDP Coloring Book - Frame & Border Remover")
    print("=" * 65)
    print(f" Source Folder: {input_path.resolve()}")
    print(f" Target Folder: {out_path.resolve()}")
    print(f" Debug Overlays: {'Enabled' if args.debug else 'Disabled'}")
    print("-" * 65)

    def print_progress(curr, total, msg):
        pct = int((curr / total) * 100)
        bar_len = 30
        filled = int(bar_len * curr // total)
        bar = "#" * filled + "-" * (bar_len - filled)
        sys.stdout.write(f"\r [{bar}] {pct}% | {msg[:40]:<40}")
        sys.stdout.flush()

    start_time = time.time()

    try:
        results = BorderRemover.process_directory(
            input_dir=input_path,
            output_dir=out_path,
            debug=args.debug,
            density_thresh=args.density,
            progress_callback=print_progress
        )
        print()  # newline after progress bar

        elapsed = time.time() - start_time
        print("\n" + "=" * 65)
        print(" Processing Summary:")
        print(f" Total files:     {results['total_files']}")
        print(f" Borders removed: {results['cropped_count']} images (cropped & scaled to 100%)")
        print(f" Kept as-is:      {results['copied_count']} images (no borders detected)")
        if results['error_count'] > 0:
            print(f" Errors:          {results['error_count']} files")
        print(f" Output folder:   {results['output_dir']}")
        if args.debug:
            print(f" Debug folder:    {out_path / 'debug'}")
        print(f" Time elapsed:    {elapsed:.1f}s")
        print("=" * 65)

        # Print per-file details if any skipped or errored
        for r in results['results']:
            if r.error:
                print(f" [ERROR] {r.filename}: {r.error}")
            elif not r.has_border:
                print(f" [INFO]  {r.filename}: No border detected, copied original file as-is.")

    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
