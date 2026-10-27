import os
import io
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np

from src.config import ROOT_DIR

DEFAULT_TEMPLATES_DIR = Path("D:/FairytaleCompass/A+ content samples banners")

# Predefined slot templates for pixel-perfect alignment
PRESET_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "a-plus-banner-botanical.png": {
        "title": "Botanical Watercolor (A4)",
        "theme": "botanical",
        "format": "a4",
        "slots": [
            {"x": 69, "y": 246, "width": 341, "height": 482},
            {"x": 440, "y": 246, "width": 341, "height": 482},
            {"x": 811, "y": 246, "width": 340, "height": 482},
            {"x": 1182, "y": 246, "width": 341, "height": 482}
        ]
    },
    "a-plus-banner-christmas.png": {
        "title": "Rustic Christmas (A4)",
        "theme": "christmas",
        "format": "a4",
        "slots": [
            {"x": 69, "y": 244, "width": 340, "height": 481},
            {"x": 439, "y": 244, "width": 342, "height": 481},
            {"x": 811, "y": 244, "width": 341, "height": 481},
            {"x": 1182, "y": 244, "width": 341, "height": 481}
        ]
    },
    "a-plus-banner-halloween.png": {
        "title": "Watercolor Halloween (A4)",
        "theme": "halloween",
        "format": "a4",
        "slots": [
            {"x": 69, "y": 245, "width": 340, "height": 482},
            {"x": 439, "y": 245, "width": 342, "height": 482},
            {"x": 811, "y": 245, "width": 341, "height": 482},
            {"x": 1182, "y": 245, "width": 341, "height": 482}
        ]
    },
    "a-plus-banner-botanical-squere-1.png": {
        "title": "Botanical Staggered (Square)",
        "theme": "botanical",
        "format": "8.5x8.5",
        "slots": [
            {"x": 101, "y": 277, "width": 316, "height": 288},
            {"x": 455, "y": 372, "width": 316, "height": 289},
            {"x": 815, "y": 291, "width": 310, "height": 289},
            {"x": 1169, "y": 386, "width": 318, "height": 283}
        ]
    },
    "a-plus-banner-botanical-squere-2.png": {
        "title": "Botanical Square (Square)",
        "theme": "botanical",
        "format": "8.5x8.5",
        "slots": [
            {"x": 63, "y": 308, "width": 342, "height": 343},
            {"x": 439, "y": 308, "width": 343, "height": 343},
            {"x": 816, "y": 308, "width": 343, "height": 343},
            {"x": 1190, "y": 308, "width": 345, "height": 343}
        ]
    },
    "a-plus-banner-christmas-squere.png": {
        "title": "Watercolor Christmas (Square)",
        "theme": "christmas",
        "format": "8.5x8.5",
        "slots": [
            {"x": 45, "y": 309, "width": 356, "height": 352},
            {"x": 431, "y": 309, "width": 350, "height": 352},
            {"x": 812, "y": 309, "width": 348, "height": 352},
            {"x": 1193, "y": 309, "width": 354, "height": 352}
        ]
    },
    "a-plus-banner-halloween-squere.png": {
        "title": "Autumn Halloween (Square)",
        "theme": "halloween",
        "format": "8.5x8.5",
        "slots": [
            {"x": 72, "y": 305, "width": 341, "height": 337},
            {"x": 441, "y": 305, "width": 341, "height": 337},
            {"x": 810, "y": 305, "width": 342, "height": 337},
            {"x": 1180, "y": 305, "width": 342, "height": 337}
        ]
    }
}


def detect_template_slots(img: Image.Image) -> List[Dict[str, int]]:
    """
    Automatically detects bounding boxes of rectangular white cards/frames within a template banner.
    Works for any newly added custom template banners.
    """
    arr = np.array(img.convert("RGB"))
    # Pixels that are bright white
    white = (arr[:, :, 0] > 248) & (arr[:, :, 1] > 248) & (arr[:, :, 2] > 248)
    
    col_counts = white.sum(axis=0)
    thresh = int(img.height * 0.15)
    white_cols = np.where(col_counts > thresh)[0]
    
    segments = []
    if len(white_cols) > 0:
        start = white_cols[0]
        prev = white_cols[0]
        for c in white_cols[1:]:
            if c == prev + 1:
                prev = c
            else:
                if prev - start > 60:
                    segments.append((start, prev))
                start = c
                prev = c
        if prev - start > 60:
            segments.append((start, prev))
            
    slots = []
    for c1, c2 in segments:
        sub = white[:, c1:c2+1]
        row_counts = sub.sum(axis=1)
        r_thresh = (c2 - c1) * 0.65
        white_rows = np.where(row_counts > r_thresh)[0]
        if len(white_rows) > 0:
            r1, r2 = int(white_rows[0]), int(white_rows[-1])
            if (r2 - r1) > 60:
                slots.append({
                    "x": int(c1),
                    "y": int(r1),
                    "width": int(c2 - c1),
                    "height": int(r2 - r1)
                })
    return slots


class APlusBuilder:
    @classmethod
    def get_templates_dir(cls, custom_dir: Optional[str] = None) -> Path:
        if custom_dir and Path(custom_dir).exists():
            return Path(custom_dir).resolve()
        if DEFAULT_TEMPLATES_DIR.exists():
            return DEFAULT_TEMPLATES_DIR.resolve()
        # Fallback to templates/aplus under ROOT_DIR
        local_dir = ROOT_DIR / "templates" / "aplus"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir.resolve()

    @classmethod
    def list_templates(cls, custom_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans templates directory and returns metadata for all detected banner templates.
        """
        templates_dir = cls.get_templates_dir(custom_dir)
        if not templates_dir.exists():
            return []

        templates = []
        extensions = (".png", ".jpg", ".jpeg", ".webp")

        for entry in sorted(templates_dir.iterdir()):
            if not entry.is_file() or entry.suffix.lower() not in extensions:
                continue
            
            fname = entry.name
            preset = PRESET_TEMPLATES.get(fname)

            try:
                with Image.open(entry) as img:
                    w, h = img.size
                    if preset:
                        slots = preset["slots"]
                        fmt = preset["format"]
                        title = preset["title"]
                        theme = preset.get("theme", "general")
                    else:
                        slots = detect_template_slots(img)
                        if not slots:
                            # Skip images without detected slots (e.g. non-template graphics)
                            continue
                        avg_w = np.mean([s["width"] for s in slots])
                        avg_h = np.mean([s["height"] for s in slots])
                        is_sq = (avg_w / avg_h) > 0.82
                        fmt = "8.5x8.5" if is_sq else "a4"
                        title = entry.stem.replace("-", " ").replace("_", " ").title()
                        theme = "custom"

                    templates.append({
                        "filename": fname,
                        "path": str(entry.resolve()),
                        "title": title,
                        "theme": theme,
                        "format": fmt,
                        "width": w,
                        "height": h,
                        "slots_count": len(slots),
                        "slots": slots
                    })
            except Exception:
                continue

        return templates

    @classmethod
    def get_template_slots(cls, template_path: str) -> List[Dict[str, int]]:
        p = Path(template_path)
        if p.name in PRESET_TEMPLATES:
            return PRESET_TEMPLATES[p.name]["slots"]
        with Image.open(p) as img:
            return detect_template_slots(img)

    @classmethod
    def composite_banner(
        cls,
        template_path: str,
        image_paths: List[str],
        fit_mode: str = "contain",
        padding: int = 1
    ) -> Image.Image:
        """
        Composites book illustrations into template slots.
        Preserves template background, shadows, and watercolor elements.
        """
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template_img = Image.open(template_file).convert("RGBA")
        slots = cls.get_template_slots(str(template_file))

        for slot, img_path in zip(slots, image_paths):
            if not img_path:
                continue
            path_obj = Path(img_path)
            if not path_obj.exists():
                continue

            try:
                with Image.open(path_obj) as art:
                    art = art.convert("RGBA")
                    
                    sx = slot["x"] + padding
                    sy = slot["y"] + padding
                    sw = max(1, slot["width"] - 2 * padding)
                    sh = max(1, slot["height"] - 2 * padding)

                    art_ratio = art.width / art.height
                    slot_ratio = sw / sh

                    if fit_mode == "cover":
                        if art_ratio > slot_ratio:
                            new_h = sh
                            new_w = int(sh * art_ratio)
                        else:
                            new_w = sw
                            new_h = int(sw / art_ratio)
                        resized = art.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        cx = (new_w - sw) // 2
                        cy = (new_h - sh) // 2
                        cropped = resized.crop((cx, cy, cx + sw, cy + sh))
                        template_img.paste(cropped, (sx, sy), cropped)
                    else:  # contain / fit
                        if art_ratio > slot_ratio:
                            new_w = sw
                            new_h = int(sw / art_ratio)
                        else:
                            new_h = sh
                            new_w = int(sh * art_ratio)
                        resized = art.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        ox = sx + (sw - new_w) // 2
                        oy = sy + (sh - new_h) // 2
                        template_img.paste(resized, (ox, oy), resized)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue

        return template_img

    @classmethod
    def generate_preview_base64(
        cls,
        template_path: str,
        image_paths: List[str],
        fit_mode: str = "contain",
        max_preview_width: int = 970
    ) -> str:
        """
        Generates a fast base64-encoded JPEG data URL for live preview in the browser.
        """
        composite = cls.composite_banner(template_path, image_paths, fit_mode=fit_mode, padding=1)
        # Downscale for preview
        if composite.width > max_preview_width:
            scale = max_preview_width / composite.width
            preview_size = (max_preview_width, int(composite.height * scale))
            composite = composite.resize(preview_size, Image.Resampling.BILINEAR)

        rgb_preview = composite.convert("RGB")
        buffer = io.BytesIO()
        rgb_preview.save(buffer, format="JPEG", quality=88)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    @classmethod
    def build_banner(
        cls,
        template_path: str,
        image_paths: List[str],
        output_folder: str,
        custom_output_name: Optional[str] = None,
        export_amazon_size: bool = True,
        fit_mode: str = "contain",
        padding: int = 1
    ) -> Dict[str, Any]:
        """
        Builds the banner and saves it into the book folder.
        Creates:
          1. Full HD master banner (<name>.png, 1594x986)
          2. Amazon A+ ready banner (<name>_970x600.png) if export_amazon_size is True
        """
        out_dir = Path(output_folder)
        if not out_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_folder}")

        template_file = Path(template_path)
        slug = template_file.stem.replace("a-plus-banner-", "").replace(" ", "_")
        
        base_name = custom_output_name.strip() if custom_output_name and custom_output_name.strip() else f"a_plus_banner_{slug}"
        if base_name.lower().endswith(".png"):
            base_name = base_name[:-4]

        # Generate composite
        composite = cls.composite_banner(template_path, image_paths, fit_mode=fit_mode, padding=padding)

        created_files = []

        # 1. Save Full HD Master
        master_path = out_dir / f"{base_name}.png"
        composite.save(master_path, format="PNG")
        created_files.append({
            "path": str(master_path.resolve()),
            "filename": master_path.name,
            "width": composite.width,
            "height": composite.height,
            "size_kb": round(master_path.stat().st_size / 1024, 1),
            "type": "Full HD Master"
        })

        # 2. Save Amazon A+ standard 970 x 600 px banner
        if export_amazon_size:
            amazon_w = 970
            amazon_h = int(round(composite.height * (amazon_w / composite.width)))
            # If close to 600, make it exactly 600
            if 595 <= amazon_h <= 605:
                amazon_h = 600
                
            amazon_img = composite.resize((amazon_w, amazon_h), Image.Resampling.LANCZOS)
            amazon_path = out_dir / f"{base_name}_970x600.png"
            amazon_img.save(amazon_path, format="PNG")
            created_files.append({
                "path": str(amazon_path.resolve()),
                "filename": amazon_path.name,
                "width": amazon_w,
                "height": amazon_h,
                "size_kb": round(amazon_path.stat().st_size / 1024, 1),
                "type": "Amazon A+ Module (970 × 600)"
            })

        return {
            "success": True,
            "template_name": template_file.name,
            "output_folder": str(out_dir.resolve()),
            "files": created_files
        }
