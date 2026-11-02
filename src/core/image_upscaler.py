import os
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image, ImageFilter

try:
    from src.core.image_processor import natural_sort_key
except ImportError:
    from .image_processor import natural_sort_key


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = ROOT_DIR / "tools" / "realesrgan"
EXE_PATH = TOOLS_DIR / "realesrgan-ncnn-vulkan.exe"
MODELS_DIR = TOOLS_DIR / "models"

RELEASE_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"


class ImageUpscaler:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

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
        scale: int = 4,
        model: str = "realesrgan-x4plus-anime",
        tile_size: int = 200,
        threads: str = "1:1:1"
    ) -> None:
        """
        Upscales a single image using Real-ESRGAN in Safe/Eco mode:
        - tile_size=200 prevents high VRAM/GPU heating spikes.
        - threads='1:1:1' prevents CPU multi-core exhaustion.
        - Embeds 300 DPI metadata.
        """
        cls.ensure_engine()

        cmd = [
            str(EXE_PATH),
            "-i", str(input_path),
            "-o", str(output_path),
            "-m", str(MODELS_DIR),
            "-n", model,
            "-s", str(scale),
            "-t", str(tile_size),
            "-j", threads
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ошибка AI апскейла файла {input_path.name}: {result.stderr or result.stdout}")

        # Post-process with Pillow to ensure 300 DPI metadata is set
        if output_path.exists():
            with Image.open(output_path) as img:
                img.load()
                fmt = img.format or "PNG"
                img.save(output_path, format=fmt, dpi=(300, 300))

    @classmethod
    def upscale_fast(
        cls,
        input_path: Path,
        output_path: Path,
        scale: int = 4,
    ) -> None:
        """
        Ultra-fast Lanczos scaling with line-art sharpening:
        - 0% GPU load, runs in milliseconds per image without any heating.
        - High-quality Lanczos interpolation.
        - Subtle unsharp mask to keep coloring outlines crisp.
        - Sets 300 DPI metadata.
        """
        with Image.open(input_path) as img:
            img.load()
            fmt = img.format or "PNG"
            orig_mode = img.mode

            target_w = int(img.width * scale)
            target_h = int(img.height * scale)

            # High quality Lanczos resize
            resized = img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)

            # Sharpen outlines for coloring book drawings
            if orig_mode in ("RGB", "L"):
                sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))
            else:
                sharpened = resized

            sharpened.save(output_path, format=fmt, dpi=(300, 300))

    @classmethod
    def upscale_folder(
        cls,
        input_dir: str,
        output_dir: Optional[str] = None,
        mode: str = "ai",
        scale: int = 4,
        model: str = "realesrgan-x4plus-anime",
        tile_size: int = 200,
        include_covers: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Batch upscales images in input_dir.
        mode: 'ai' (Real-ESRGAN in eco mode) or 'fast' (Lanczos Pillow, 0% load)
        include_covers: If True, includes cover_* files. If False, skips cover_* files.
        If output_dir is same as input_dir (or None), overwrites existing files safely.
        """
        in_path = Path(input_dir).resolve()
        if not in_path.exists() or not in_path.is_dir():
            raise FileNotFoundError(f"Каталог не найден: {in_path}")

        if mode == "ai":
            cls.ensure_engine()

        if not output_dir:
            out_path = in_path
        else:
            out_path = Path(output_dir).resolve()

        out_path.mkdir(parents=True, exist_ok=True)
        is_same_dir = (in_path == out_path)

        files = [
            f for f in in_path.iterdir()
            if f.is_file() and f.suffix.lower() in cls.SUPPORTED_EXTENSIONS
        ]
        if not include_covers:
            files = [f for f in files if not f.stem.lower().startswith("cover_")]

        files.sort(key=lambda f: natural_sort_key(f.name))

        if not files:
            raise ValueError(f"В папке {in_path} не найдено подходящих изображений для апскейла")

        upscaled_files: List[str] = []
        total = len(files)

        for idx, file_path in enumerate(files):
            num = idx + 1
            dest_file = out_path / file_path.name

            if is_same_dir:
                temp_file = dest_file.with_name(f".tmp_upscale_{dest_file.name}")
                if mode == "ai":
                    cls.upscale_ai(file_path, temp_file, scale=scale, model=model, tile_size=tile_size)
                else:
                    cls.upscale_fast(file_path, temp_file, scale=scale)
                os.replace(temp_file, dest_file)
            else:
                if mode == "ai":
                    cls.upscale_ai(file_path, dest_file, scale=scale, model=model, tile_size=tile_size)
                else:
                    cls.upscale_fast(file_path, dest_file, scale=scale)

            upscaled_files.append(str(dest_file))

            if progress_callback:
                progress_callback(num, total, file_path.name)

        return upscaled_files
