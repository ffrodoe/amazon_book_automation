import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Callable, Dict, Any
import numpy as np
from PIL import Image, ImageDraw

from src.core.image_processor import natural_sort_key


@dataclass
class ImageProcessResult:
    filename: str
    original_size: Tuple[int, int]
    has_border: bool
    crop_box: Optional[Tuple[int, int, int, int]] = None
    output_path: Optional[str] = None
    debug_path: Optional[str] = None
    error: Optional[str] = None


class BorderRemover:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

    @staticmethod
    def _group_contiguous_indices(indices: List[int]) -> List[Tuple[int, int]]:
        """Groups a sorted list of indices into continuous ranges (start, end)."""
        if not indices:
            return []
        ranges = []
        start = indices[0]
        prev = indices[0]
        for x in indices[1:]:
            if x == prev + 1:
                prev = x
            else:
                ranges.append((start, prev))
                start = x
                prev = x
        ranges.append((start, prev))
        return ranges

    @classmethod
    def detect_crop_box(
        cls,
        image: Image.Image,
        density_thresh: float = 0.60,
        dark_thresh: int = 140,
        max_margin_ratio: float = 0.065,
        safety_margin: int = 2
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Detects the innermost rectangular border/frame of a coloring book illustration.
        Returns (left, top, right, bottom) crop coordinates strictly inside the innermost border lines,
        or None if no complete rectangular border is detected.
        """
        # Convert to grayscale for darkness analysis
        gray = image.convert("L")
        arr = np.array(gray)
        h, w = arr.shape

        dark = arr < dark_thresh
        max_d_x = int(w * max_margin_ratio)
        max_d_y = int(h * max_margin_ratio)

        # Look for horizontal and vertical continuous line bands in margins
        left_indices = [c for c in range(max_d_x) if np.mean(dark[:, c]) > density_thresh]
        right_indices = [c for c in range(w - max_d_x, w) if np.mean(dark[:, c]) > density_thresh]
        top_indices = [r for r in range(max_d_y) if np.mean(dark[r, :]) > density_thresh]
        bottom_indices = [r for r in range(h - max_d_y, h) if np.mean(dark[r, :]) > density_thresh]

        left_bands = cls._group_contiguous_indices(left_indices)
        right_bands = cls._group_contiguous_indices(right_indices)
        top_bands = cls._group_contiguous_indices(top_indices)
        bottom_bands = cls._group_contiguous_indices(bottom_indices)

        # Must have lines on all 4 borders to be considered a full frame
        if not (left_bands and right_bands and top_bands and bottom_bands):
            return None

        # Innermost lines (handling both single and double line frames):
        # Left: innermost is the rightmost edge of the last band on the left
        inner_left = left_bands[-1][1] + 1
        # Top: innermost is the bottom edge of the last band on the top
        inner_top = top_bands[-1][1] + 1
        # Right: innermost is the leftmost edge of the first band on the right
        inner_right = right_bands[0][0] - 1
        # Bottom: innermost is the top edge of the first band on the bottom
        inner_bottom = bottom_bands[0][0] - 1

        crop_box = (
            inner_left + safety_margin,
            inner_top + safety_margin,
            inner_right - safety_margin,
            inner_bottom - safety_margin
        )

        # Sanity check: valid positive dimensions and keeps at least 60% of original area
        cw = crop_box[2] - crop_box[0]
        ch = crop_box[3] - crop_box[1]
        if cw <= 0 or ch <= 0:
            return None
        if (cw * ch) < (w * h * 0.60):
            return None

        return crop_box

    @classmethod
    def crop_and_resize(
        cls,
        image: Image.Image,
        crop_box: Tuple[int, int, int, int]
    ) -> Image.Image:
        """
        Crops image to the crop_box and directly stretches it back to original canvas dimensions.
        """
        orig_size = image.size  # (width, height)
        cropped = image.crop(crop_box)
        return cropped.resize(orig_size, resample=Image.Resampling.LANCZOS)

    @classmethod
    def process_image(
        cls,
        input_path: Path,
        output_path: Path,
        debug_path: Optional[Path] = None,
        density_thresh: float = 0.60,
        safety_margin: int = 2
    ) -> ImageProcessResult:
        """
        Processes a single image:
        - If border detected: crops inside inner border, stretches to original size, saves to output_path.
        - If no border: copies file unchanged to output_path.
        - If debug_path given: generates visualization overlay.
        """
        is_same_file = input_path.resolve() == output_path.resolve()
        try:
            with Image.open(input_path) as img:
                img.load()
                orig_size = img.size
                dpi = img.info.get("dpi")
                crop_box = cls.detect_crop_box(
                    img,
                    density_thresh=density_thresh,
                    safety_margin=safety_margin
                )

                if debug_path and crop_box is not None:
                    debug_path.parent.mkdir(parents=True, exist_ok=True)
                    debug_img = img.convert("RGB")
                    draw = ImageDraw.Draw(debug_img)
                    draw.rectangle(crop_box, outline="red", width=max(4, int(orig_size[0] / 600)))
                    debug_img.save(debug_path)

                if crop_box is not None:
                    processed = cls.crop_and_resize(img, crop_box)
                else:
                    processed = None

            # File is now closed, safe for atomic replace on Windows
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if crop_box is not None:
                if is_same_file:
                    temp_file = output_path.with_name(f".tmp_{output_path.name}")
                    if dpi:
                        processed.save(temp_file, dpi=dpi)
                    else:
                        processed.save(temp_file)
                    os.replace(temp_file, output_path)
                else:
                    if dpi:
                        processed.save(output_path, dpi=dpi)
                    else:
                        processed.save(output_path)

                return ImageProcessResult(
                    filename=input_path.name,
                    original_size=orig_size,
                    has_border=True,
                    crop_box=crop_box,
                    output_path=str(output_path.resolve()),
                    debug_path=str(debug_path.resolve()) if debug_path else None
                )
            else:
                # No border detected
                if not is_same_file:
                    shutil.copy2(input_path, output_path)
                return ImageProcessResult(
                    filename=input_path.name,
                    original_size=orig_size,
                    has_border=False,
                    crop_box=None,
                    output_path=str(output_path.resolve()),
                    debug_path=None
                )
        except Exception as e:
            return ImageProcessResult(
                filename=input_path.name,
                original_size=(0, 0),
                has_border=False,
                error=str(e)
            )

    @classmethod
    def process_directory(
        cls,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        debug: bool = False,
        density_thresh: float = 0.60,
        safety_margin: int = 2,
        skip_count: int = 0,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Batch processes all supported images in input_dir.
        Default output_dir: input_dir (overwrites in place)
        skip_count: number of initial images to keep unchanged without border removal
        """
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

        if output_dir is None:
            output_dir = input_dir

        output_dir.mkdir(parents=True, exist_ok=True)
        debug_dir = (output_dir / "debug") if debug else None

        files = [
            f for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in cls.SUPPORTED_EXTENSIONS and not f.stem.lower().startswith("cover_")
        ]
        files.sort(key=lambda f: natural_sort_key(f.name))

        if not files:
            raise ValueError(f"No supported image files found in {input_dir}")

        total = len(files)
        results: List[ImageProcessResult] = []
        cropped_count = 0
        copied_count = 0
        error_count = 0

        for idx, file_path in enumerate(files):
            out_file = output_dir / file_path.name
            dbg_file = (debug_dir / file_path.name) if debug_dir else None

            if progress_callback:
                progress_callback(idx + 1, total, f"Processing {file_path.name}...")

            if idx < skip_count:
                # Skip initial images (e.g. title/copyright pages)
                is_same_file = file_path.resolve() == out_file.resolve()
                if not is_same_file:
                    shutil.copy2(file_path, out_file)
                results.append(ImageProcessResult(
                    filename=file_path.name,
                    original_size=(0, 0),
                    has_border=False,
                    crop_box=None,
                    output_path=str(out_file.resolve()),
                    debug_path=None
                ))
                copied_count += 1
                continue

            res = cls.process_image(
                input_path=file_path,
                output_path=out_file,
                debug_path=dbg_file,
                density_thresh=density_thresh,
                safety_margin=safety_margin
            )
            results.append(res)

            if res.error:
                error_count += 1
            elif res.has_border:
                cropped_count += 1
            else:
                copied_count += 1

        return {
            "input_dir": str(input_dir.resolve()),
            "output_dir": str(output_dir.resolve()),
            "total_files": total,
            "cropped_count": cropped_count,
            "copied_count": copied_count,
            "error_count": error_count,
            "results": results
        }
