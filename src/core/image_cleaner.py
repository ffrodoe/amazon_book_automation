from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image

from src.core.image_processor import natural_sort_key


class ImageCleaner:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

    @staticmethod
    def get_whitening_lut(brightness_offset: int = 40) -> List[int]:
        """
        Creates a 256-entry Look-Up Table (LUT) emulating Photoshop's brightness/levels adjustment.
        Pixels with intensity >= (255 - brightness_offset) are clipped to pure white (255).
        Black outlines (0) remain 0.
        Intermediate tones are smoothly stretched.
        """
        threshold = max(1, min(254, 255 - brightness_offset))
        lut = [min(255, int(round(i * 255.0 / threshold))) for i in range(256)]
        return lut

    @classmethod
    def clean_image(cls, img: Image.Image, brightness_offset: int = 40) -> Image.Image:
        """
        Applies background whitening to a PIL Image instance using fast C-level LUT mapping.
        """
        lut = cls.get_whitening_lut(brightness_offset)

        # Handle different color modes
        if img.mode == "RGBA":
            r, g, b, a = img.split()
            r = r.point(lut)
            g = g.point(lut)
            b = b.point(lut)
            return Image.merge("RGBA", (r, g, b, a))
        elif img.mode == "RGB":
            # 3-channel LUT (256 * 3 entries)
            return img.point(lut * 3)
        elif img.mode == "L":
            return img.point(lut)
        else:
            converted = img.convert("RGB")
            return converted.point(lut * 3)

    @classmethod
    def clean_folder(
        cls,
        input_dir: str,
        output_dir: Optional[str] = None,
        brightness_offset: int = 40,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Batch whitens all images in input_dir and saves them to output_dir.
        """
        in_path = Path(input_dir).resolve()
        if not in_path.exists() or not in_path.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: {in_path}")

        if not output_dir:
            out_path = in_path / "cleaned"
        else:
            out_path = Path(output_dir).resolve()

        out_path.mkdir(parents=True, exist_ok=True)

        files = [
            f for f in in_path.iterdir()
            if f.is_file() and f.suffix.lower() in cls.SUPPORTED_EXTENSIONS and not f.stem.lower().startswith("cover_")
        ]
        files.sort(key=lambda f: natural_sort_key(f.name))

        if not files:
            raise ValueError(f"No images found in {in_path}")

        cleaned_files: List[str] = []
        total = len(files)

        import os
        is_same_dir = (in_path.resolve() == out_path.resolve())

        for idx, file_path in enumerate(files):
            num = idx + 1
            dest_file = out_path / file_path.name

            with Image.open(file_path) as img:
                img.load()
                fmt = img.format or "PNG"
                dpi = img.info.get("dpi")
                cleaned_img = cls.clean_image(img, brightness_offset=brightness_offset)

            if is_same_dir:
                temp_file = dest_file.with_name(f".tmp_{dest_file.name}")
                if dpi:
                    cleaned_img.save(temp_file, format=fmt, dpi=dpi)
                else:
                    cleaned_img.save(temp_file, format=fmt)
                os.replace(temp_file, dest_file)
            else:
                if dpi:
                    cleaned_img.save(dest_file, format=fmt, dpi=dpi)
                else:
                    cleaned_img.save(dest_file, format=fmt)

            cleaned_files.append(str(dest_file))

            if progress_callback:
                progress_callback(num, total, file_path.name)

        return cleaned_files
