import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image, ImageFilter

try:
    from src.config import BookFormat, FORMAT_SPECS
    from src.core.image_processor import natural_sort_key
    from src.core.file_utils import (
        atomic_replace,
        is_hidden_or_temp_file,
        lock_directories,
        make_temp_path,
        safe_unlink,
    )
except ImportError:
    from ..config import BookFormat, FORMAT_SPECS
    from .image_processor import natural_sort_key
    from .file_utils import (
        atomic_replace,
        is_hidden_or_temp_file,
        lock_directories,
        make_temp_path,
        safe_unlink,
    )


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = ROOT_DIR / "tools" / "realesrgan"
EXE_PATH = TOOLS_DIR / "realesrgan-ncnn-vulkan.exe"
MODELS_DIR = TOOLS_DIR / "models"

RELEASE_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"


class ImageUpscaler:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

    @classmethod
    def get_target_size(cls, book_format: BookFormat = BookFormat.A4) -> Tuple[int, int]:
        """Returns exact 300 DPI pixel dimensions (width, height) for the selected book format."""
        spec = FORMAT_SPECS.get(book_format, FORMAT_SPECS[BookFormat.A4])
        return (spec.width_px_300dpi, spec.height_px_300dpi)

    @classmethod
    def is_engine_installed(cls) -> bool:
        """Checks if the Real-ESRGAN NCNN Vulkan binary and models exist."""
        return EXE_PATH.exists() and MODELS_DIR.exists()

    @classmethod
    def ensure_engine(cls, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Downloads and extracts Real-ESRGAN standalone engine if not already present."""
        if cls.is_engine_installed():
            return True

        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = TOOLS_DIR / "realesrgan.zip"

        if progress_callback:
            progress_callback("Загрузка AI-движка Real-ESRGAN (25 МБ)...")

        try:
            urllib.request.urlretrieve(RELEASE_URL, zip_path)
            if progress_callback:
                progress_callback("Распаковка AI-движка...")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(TOOLS_DIR)

            if zip_path.exists():
                zip_path.unlink()

            # Clean unnecessary demo files
            for demo_file in ["input.jpg", "input2.jpg", "onepiece_demo.mp4", "README_windows.md"]:
                df = TOOLS_DIR / demo_file
                if df.exists():
                    df.unlink()

            return cls.is_engine_installed()
        except Exception as e:
            if zip_path.exists():
                zip_path.unlink()
            raise RuntimeError(f"Не удалось установить Real-ESRGAN: {e}")

    @classmethod
    def upscale_ai(
        cls,
        input_path: Path,
        output_path: Path,
        target_size: Tuple[int, int] = (2480, 3508),
        model: str = "realesrgan-x4plus-anime",
        tile_size: int = 200,
        threads: str = "1:1:1"
    ) -> None:
        """
        Upscales a smaller image using Real-ESRGAN in Safe/Eco mode (4x),
        then normalizes it to exact target_size (width, height) at 300 DPI.
        """
        cls.ensure_engine()
        target_w, target_h = target_size

        with Image.open(input_path) as src_img:
            orig_fmt = src_img.format or "PNG"

        ai_temp_path = make_temp_path(output_path.with_suffix(".png"), prefix=".tmp_ai_")
        try:
            cmd = [
                str(EXE_PATH),
                "-i", str(input_path),
                "-o", str(ai_temp_path),
                "-m", str(MODELS_DIR),
                "-n", model,
                "-s", "4",
                "-t", str(tile_size),
                "-j", threads
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0 or not ai_temp_path.exists():
                raise RuntimeError(f"Ошибка AI апскейла файла {input_path.name}: {result.stderr or result.stdout}")

            # Normalize AI output to exact target dimensions and embed 300 DPI metadata
            with Image.open(ai_temp_path) as ai_img:
                ai_img.load()
                if ai_img.size != (target_w, target_h):
                    final_img = ai_img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)
                else:
                    final_img = ai_img

                if orig_fmt.upper() in ("JPEG", "JPG") and final_img.mode in ("RGBA", "P"):
                    final_img = final_img.convert("RGB")

                final_img.save(output_path, format=orig_fmt, dpi=(300, 300))
        finally:
            safe_unlink(ai_temp_path)

    @classmethod
    def upscale_fast(
        cls,
        input_path: Path,
        output_path: Path,
        target_size: Tuple[int, int] = (2480, 3508),
    ) -> None:
        """
        Ultra-fast Lanczos normalization to exact target_size with line-art sharpening:
        - 0% GPU load, runs in milliseconds per image without any heating.
        - High-quality Lanczos interpolation to exact target (width, height).
        - Subtle unsharp mask to keep coloring outlines crisp.
        - Sets 300 DPI metadata.
        """
        target_w, target_h = target_size
        with Image.open(input_path) as img:
            img.load()
            fmt = img.format or "PNG"
            orig_mode = img.mode

            resized = img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)

            if orig_mode in ("RGB", "L"):
                sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))
            else:
                sharpened = resized

            sharpened.save(output_path, format=fmt, dpi=(300, 300))

    @classmethod
    def normalize_image(
        cls,
        input_path: Path,
        output_path: Path,
        target_size: Tuple[int, int],
        mode: str = "fast",
        model: str = "realesrgan-x4plus-anime",
        tile_size: int = 200
    ) -> str:
        """
        Smart normalization of a single image to exact target_size (width, height):
        - 'skipped': Already exact target_size (ensures 300 DPI metadata).
        - 'downscaled': Larger than or equal to target_size on both axes -> fast Lanczos downscale to target_size.
        - 'upscaled': Smaller than target_size -> upscales via 'ai' or 'fast' mode to exact target_size.
        """
        target_w, target_h = target_size
        is_same_file = (input_path.resolve() == output_path.resolve())

        img_for_dpi_fix: Optional[Image.Image] = None
        with Image.open(input_path) as img:
            orig_w, orig_h = img.size
            fmt = img.format or "PNG"
            dpi = img.info.get("dpi")
            has_300_dpi = bool(dpi and round(dpi[0]) == 300 and round(dpi[1]) == 300)
            if (orig_w, orig_h) == (target_w, target_h) and not has_300_dpi:
                img.load()
                img_for_dpi_fix = img.copy()

        # File handle on input_path is now guaranteed closed before any replace on Windows.

        # 1. Already at exact target size
        if (orig_w, orig_h) == (target_w, target_h):
            if is_same_file:
                if img_for_dpi_fix is not None:
                    temp_file = make_temp_path(output_path, prefix=".tmp_dpi_")
                    try:
                        img_for_dpi_fix.save(temp_file, format=fmt, dpi=(300, 300))
                    except Exception:
                        safe_unlink(temp_file)
                        raise
                    finally:
                        img_for_dpi_fix.close()
                    atomic_replace(temp_file, output_path)
            else:
                if has_300_dpi:
                    temp_file = make_temp_path(output_path, prefix=".tmp_copy_")
                    try:
                        shutil.copy2(input_path, temp_file)
                    except Exception:
                        safe_unlink(temp_file)
                        raise
                    atomic_replace(temp_file, output_path)
                elif img_for_dpi_fix is not None:
                    temp_file = make_temp_path(output_path, prefix=".tmp_dpi_")
                    try:
                        img_for_dpi_fix.save(temp_file, format=fmt, dpi=(300, 300))
                    except Exception:
                        safe_unlink(temp_file)
                        raise
                    finally:
                        img_for_dpi_fix.close()
                    atomic_replace(temp_file, output_path)
            return "skipped"

        # 2. Image is larger than target size (e.g. 4096x4096) -> downscale directly without AI
        if orig_w >= target_w and orig_h >= target_h:
            temp_file = make_temp_path(output_path, prefix=".tmp_norm_")
            try:
                cls.upscale_fast(input_path, temp_file, target_size=target_size)
            except Exception:
                safe_unlink(temp_file)
                raise
            atomic_replace(temp_file, output_path)
            return "downscaled"

        # 3. Image is smaller than target size -> upscale & normalize to target_size
        temp_file = make_temp_path(output_path, prefix=".tmp_upscale_")
        try:
            if mode == "ai":
                cls.upscale_ai(input_path, temp_file, target_size=target_size, model=model, tile_size=tile_size)
            else:
                cls.upscale_fast(input_path, temp_file, target_size=target_size)
        except Exception:
            safe_unlink(temp_file)
            raise
        atomic_replace(temp_file, output_path)
        return "upscaled"

    @classmethod
    def upscale_folder(
        cls,
        input_dir: str,
        output_dir: Optional[str] = None,
        mode: str = "fast",
        book_format: BookFormat = BookFormat.A4,
        target_size: Optional[Tuple[int, int]] = None,
        model: str = "realesrgan-x4plus-anime",
        tile_size: int = 200,
        include_covers: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Batch normalizes/upscales images in input_dir to the exact target format resolution (300 DPI):
        - A4: 2480 x 3508 px
        - Square (8.5x8.5 / 8x8): 2550 x 2550 px
        """
        in_path = Path(input_dir).resolve()
        if not in_path.exists() or not in_path.is_dir():
            raise FileNotFoundError(f"Каталог не найден: {in_path}")

        resolved_target = target_size or cls.get_target_size(book_format)

        if not output_dir:
            out_path = in_path
        else:
            out_path = Path(output_dir).resolve()

        out_path.mkdir(parents=True, exist_ok=True)

        with lock_directories(in_path, out_path):
            files = [
                f for f in in_path.iterdir()
                if (
                    f.is_file()
                    and not is_hidden_or_temp_file(f)
                    and f.suffix.lower() in cls.SUPPORTED_EXTENSIONS
                )
            ]
            if not include_covers:
                files = [f for f in files if not f.stem.lower().startswith("cover_")]

            files.sort(key=lambda f: natural_sort_key(f.name))

            if not files:
                raise ValueError(f"В папке {in_path} не найдено подходящих изображений для нормализации")

            processed_files: List[str] = []
            upscaled_count = 0
            downscaled_count = 0
            skipped_count = 0
            total = len(files)

            for idx, file_path in enumerate(files):
                num = idx + 1
                dest_file = out_path / file_path.name

                action = cls.normalize_image(
                    input_path=file_path,
                    output_path=dest_file,
                    target_size=resolved_target,
                    mode=mode,
                    model=model,
                    tile_size=tile_size
                )

                if action == "upscaled":
                    upscaled_count += 1
                elif action == "downscaled":
                    downscaled_count += 1
                else:
                    skipped_count += 1

                processed_files.append(str(dest_file))

                if progress_callback:
                    progress_callback(num, total, file_path.name)

            return {
                "files": processed_files,
                "total_files": total,
                "upscaled_count": upscaled_count,
                "downscaled_count": downscaled_count,
                "skipped_count": skipped_count,
                "target_width": resolved_target[0],
                "target_height": resolved_target[1],
                "format": book_format.value
            }
