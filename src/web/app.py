import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import (
    BookFormat,
    FORMAT_SPECS,
    DEFAULT_INTRO_COUNT,
    DEFAULT_BRIGHTNESS_OFFSET,
    DEFAULT_LOGO_PATH
)
from src.core.image_processor import ImageProcessor
from src.core.pdf_builder import PDFBuilder
from src.core.cover_builder import CoverBuilder
from src.core.image_cleaner import ImageCleaner
from src.core.border_remover import BorderRemover
from src.core.aplus_builder import APlusBuilder

app = FastAPI(title="Amazon KDP Coloring Book Studio", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".js", ".css", ".html", ".ico", ".png")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

STATIC_DIR = Path(__file__).resolve().parent / "static"


class BuildRequest(BaseModel):
    folder_path: str
    format: str = "a4"
    intro_count: int = DEFAULT_INTRO_COUNT
    custom_output_name: Optional[str] = None


class CleanBackgroundRequest(BaseModel):
    folder_path: str
    brightness_offset: int = DEFAULT_BRIGHTNESS_OFFSET
    overwrite: bool = True
    custom_output_dir: Optional[str] = None


class CropBordersRequest(BaseModel):
    folder_path: str
    overwrite: bool = True
    debug: bool = False
    skip_count: int = 2
    custom_output_dir: Optional[str] = None


class BuildCoverRequest(BaseModel):
    folder_path: str
    format: str = "a4"
    front_cover_path: Optional[str] = None
    back_cover_path: Optional[str] = None
    interior_image_paths: List[str] = []
    spine_width_mm: float
    spine_color: str = "#2d5a27"
    custom_output_name: Optional[str] = None


class APlusPreviewRequest(BaseModel):
    template_path: str
    image_paths: List[str] = []
    fit_mode: str = "contain"


class APlusBuildRequest(BaseModel):
    folder_path: str
    template_path: str
    image_paths: List[str] = []
    custom_output_name: Optional[str] = None
    export_amazon_size: bool = True
    fit_mode: str = "contain"



def select_folder_native(initial_dir: Optional[str] = None) -> Optional[str]:
    """Opens a native Windows folder browser dialog and returns selected path."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)

        init_dir = None
        if initial_dir and os.path.isdir(initial_dir):
            init_dir = initial_dir

        folder = filedialog.askdirectory(
            parent=root,
            title="Выберите папку с изображениями",
            initialdir=init_dir
        )
        root.destroy()
        return str(Path(folder).resolve()) if folder else None
    except Exception as e:
        # Fallback to PowerShell FolderBrowserDialog
        try:
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$f.Description = 'Выберите папку с изображениями'; "
                "$f.ShowNewFolderButton = $true; "
                "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }"
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
            out = res.stdout.strip()
            return str(Path(out).resolve()) if out and os.path.isdir(out) else None
        except Exception:
            return None


@app.get("/api/browse-folder")
def browse_folder(current: Optional[str] = None):
    """Opens native Windows folder selection dialog and returns chosen directory path."""
    chosen = select_folder_native(current)
    if not chosen:
        return {"cancelled": True, "path": None}
    return {"cancelled": False, "path": chosen}


@app.get("/api/formats")
def get_formats():
    """Returns available KDP formats and specifications."""
    return [
        {
            "id": fmt.value,
            "name": spec.name,
            "description": spec.description,
            "width_pt": spec.width_pt,
            "height_pt": spec.height_pt,
            "width_px_300dpi": spec.width_px_300dpi,
            "height_px_300dpi": spec.height_px_300dpi,
        }
        for fmt, spec in FORMAT_SPECS.items()
    ]


@app.get("/api/scan")
def scan_directory(
    path: str = Query(..., description="Path to folder containing coloring images"),
    format: str = Query("a4", description="Book format (a4 or 8.5x8.5)"),
    intro_count: int = Query(DEFAULT_INTRO_COUNT, description="Intro pages count")
):
    """Scans image folder and returns the book layout plan for live preview."""
    target_path = Path(path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory does not exist: {target_path}")

    book_format = BookFormat.A4 if format == "a4" else BookFormat.SQUARE_8_5

    try:
        plan = ImageProcessor.build_book_plan(
            directory=str(target_path),
            book_format=book_format,
            intro_count=intro_count
        )

        return {
            "folder_path": str(target_path),
            "folder_name": target_path.name,
            "total_images": plan.total_images,
            "total_pages": plan.total_pages,
            "format": plan.format.value,
            "intro_count": intro_count,
            "pages": [
                {
                    "page_number": p.page_number,
                    "is_blank": p.is_blank,
                    "image_name": p.image_name,
                    "image_path": p.image_path,
                    "modified_time": int(os.path.getmtime(p.image_path)) if p.image_path and os.path.exists(p.image_path) else 0,
                    "label": p.label,
                    "is_recto": p.is_recto
                }
                for p in plan.pages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/image")
def get_image(path: str = Query(..., description="Absolute path to image")):
    """Serves an image file for UI thumbnail preview with caching disabled."""
    img_path = Path(path)
    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return FileResponse(str(img_path), headers=headers)


@app.post("/api/build")
def build_pdf(req: BuildRequest):
    """Builds the print-ready Amazon KDP PDF interior."""
    target_path = Path(req.folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / req.folder_path).resolve()

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")

    book_format = BookFormat.A4 if req.format == "a4" else BookFormat.SQUARE_8_5

    try:
        plan = ImageProcessor.build_book_plan(
            directory=str(target_path),
            book_format=book_format,
            intro_count=req.intro_count
        )

        output_dir = target_path
        output_dir.mkdir(parents=True, exist_ok=True)

        if req.custom_output_name:
            out_name = req.custom_output_name
            if not out_name.lower().endswith(".pdf"):
                out_name += ".pdf"
            output_file = output_dir / out_name
        else:
            output_file = output_dir / f"{target_path.name}_{book_format.value}_interior.pdf"

        generated_pdf = PDFBuilder.build_pdf(
            plan=plan,
            output_path=str(output_file)
        )

        size_bytes = os.path.getsize(generated_pdf)
        size_mb = size_bytes / (1024 * 1024)

        return {
            "success": True,
            "output_path": str(generated_pdf),
            "output_dir": str(Path(generated_pdf).parent),
            "file_name": Path(generated_pdf).name,
            "size_mb": round(size_mb, 2),
            "total_pages": plan.total_pages,
            "format": book_format.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/brand-logo")
def get_brand_logo():
    """Serves brand logo image for the UI preview."""
    if not DEFAULT_LOGO_PATH.exists():
        raise HTTPException(status_code=404, detail="Brand logo file not found")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return FileResponse(str(DEFAULT_LOGO_PATH), headers=headers)


@app.get("/api/cover-details")
def get_cover_details(
    folder_path: str = Query(..., description="Path to book folder"),
    format: str = Query("a4", description="Book format (a4 or 8.5x8.5)")
):
    """
    Checks for cover_front and cover_back in the directory,
    calculates recommended spine width based on interior pages count,
    and returns list of interior images for thumbnail selection.
    """
    target_path = Path(folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / folder_path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")

    book_format = BookFormat.A4 if format == "a4" else BookFormat.SQUARE_8_5

    try:
        cover_files = ImageProcessor.find_cover_files(str(target_path))
        interior_files = ImageProcessor.get_image_files(str(target_path), include_cover=False)

        # Estimate interior page count
        total_pages = 0
        if interior_files:
            try:
                plan = ImageProcessor.build_book_plan(str(target_path), book_format=book_format)
                total_pages = plan.total_pages
            except Exception:
                total_pages = len(interior_files) * 2 + 2

        recommended_spine_mm = CoverBuilder.calculate_spine_width_mm(total_pages if total_pages > 0 else 60)

        # First 4 interior illustrations for default thumbnails
        default_thumb_paths = [str(f.resolve()) for f in interior_files[:4]]

        layout = CoverBuilder.calculate_cover_geometry(book_format, recommended_spine_mm)

        return {
            "folder_path": str(target_path),
            "folder_name": target_path.name,
            "format": book_format.value,
            "front_cover": cover_files["front"],
            "front_cover_name": cover_files["front_name"],
            "back_cover": cover_files["back"],
            "back_cover_name": cover_files["back_name"],
            "has_front": bool(cover_files["front"]),
            "has_back": bool(cover_files["back"]),
            "has_both_covers": bool(cover_files["front"] and cover_files["back"]),
            "total_interior_images": len(interior_files),
            "total_interior_pages": total_pages,
            "recommended_spine_mm": recommended_spine_mm,
            "default_thumbnails": default_thumb_paths,
            "layout": layout,
            "interior_images": [
                {
                    "path": str(f.resolve()),
                    "name": f.name,
                    "preview_url": f"/api/image?path={str(f.resolve())}"
                }
                for f in interior_files
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/cover-layout")
def get_cover_layout(
    format: str = Query("a4", description="Book format (a4 or 8.5x8.5)"),
    spine_width_mm: float = Query(4.6, description="Spine width in mm")
):
    """Returns the unified layout coordinates and percentage metrics for UI preview."""
    book_format = BookFormat.A4 if format == "a4" else BookFormat.SQUARE_8_5
    return CoverBuilder.calculate_cover_geometry(book_format, spine_width_mm)


@app.post("/api/build-cover")
def build_cover(req: BuildCoverRequest):
    """Builds a print-ready Amazon KDP cover PDF."""
    target_path = Path(req.folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / req.folder_path).resolve()

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")

    book_format = BookFormat.A4 if req.format == "a4" else BookFormat.SQUARE_8_5

    # Auto-detect covers if not explicitly passed
    front_p = req.front_cover_path
    back_p = req.back_cover_path
    if not front_p or not back_p:
        found = ImageProcessor.find_cover_files(str(target_path))
        front_p = front_p or found["front"]
        back_p = back_p or found["back"]

    if not front_p or not Path(front_p).exists():
        raise HTTPException(status_code=400, detail="Front cover image (cover_front.*) not found")
    if not back_p or not Path(back_p).exists():
        raise HTTPException(status_code=400, detail="Back cover image (cover_back.*) not found")

    # If thumbnails not provided, take first 4 from interior
    thumb_paths = req.interior_image_paths
    if not thumb_paths:
        int_files = ImageProcessor.get_image_files(str(target_path), include_cover=False)
        thumb_paths = [str(f.resolve()) for f in int_files[:4]]

    output_dir = target_path
    output_dir.mkdir(parents=True, exist_ok=True)

    if req.custom_output_name:
        out_name = req.custom_output_name
        if not out_name.lower().endswith(".pdf"):
            out_name += ".pdf"
        output_file = output_dir / out_name
    else:
        output_file = output_dir / f"{target_path.name}_{book_format.value}_cover.pdf"

    try:
        generated_pdf = CoverBuilder.build_cover_pdf(
            book_format=book_format,
            front_cover_path=front_p,
            back_cover_path=back_p,
            interior_image_paths=thumb_paths,
            spine_width_mm=req.spine_width_mm,
            spine_color_hex=req.spine_color,
            output_path=str(output_file)
        )

        size_bytes = os.path.getsize(generated_pdf)
        size_mb = size_bytes / (1024 * 1024)

        return {
            "success": True,
            "output_path": str(generated_pdf),
            "output_dir": str(Path(generated_pdf).parent),
            "file_name": Path(generated_pdf).name,
            "size_mb": round(size_mb, 2),
            "spine_width_mm": req.spine_width_mm,
            "format": book_format.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/open-folder")
def open_folder(path: str = Query(..., description="Path to folder or file to highlight")):
    """Opens Windows Explorer at the designated path."""
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT_DIR / path).resolve()

    if p.is_file():
        subprocess.run(["explorer", f"/select,{str(p)}"])
    elif p.is_dir():
        subprocess.run(["explorer", str(p)])
    else:
        raise HTTPException(status_code=404, detail="Path does not exist")
    return {"success": True}


@app.get("/api/download")
def download_file(path: str = Query(...)):
    """Downloads the generated PDF file directly."""
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT_DIR / path).resolve()

    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        str(p),
        media_type="application/pdf",
        filename=p.name
    )


@app.post("/api/clean-background")
def clean_background(req: CleanBackgroundRequest):
    """Batch cleans/whitens background of images in folder using Photoshop-equivalent levels."""
    target_path = Path(req.folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / req.folder_path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")

    try:
        if req.custom_output_dir:
            out_path = Path(req.custom_output_dir)
            if not out_path.is_absolute():
                out_path = (ROOT_DIR / req.custom_output_dir).resolve()
        elif req.overwrite:
            out_path = target_path
        else:
            out_path = target_path / "cleaned"

        cleaned_files = ImageCleaner.clean_folder(
            input_dir=str(target_path),
            output_dir=str(out_path),
            brightness_offset=req.brightness_offset
        )

        # Relative path for convenience
        try:
            rel_output = str(out_path.relative_to(ROOT_DIR))
        except ValueError:
            rel_output = str(out_path)

        return {
            "success": True,
            "input_dir": str(target_path),
            "output_dir": str(out_path),
            "relative_output_dir": rel_output,
            "total_cleaned": len(cleaned_files),
            "brightness_offset": req.brightness_offset,
            "is_overwrite": (out_path.resolve() == target_path.resolve())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/crop-borders")
def crop_borders(req: CropBordersRequest):
    """Batch removes borders/frames from coloring images and stretches them back to 100%."""
    target_path = Path(req.folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / req.folder_path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")

    try:
        if req.custom_output_dir:
            out_path = Path(req.custom_output_dir)
            if not out_path.is_absolute():
                out_path = (ROOT_DIR / req.custom_output_dir).resolve()
        elif req.overwrite:
            out_path = target_path
        else:
            out_path = target_path / "cropped"

        results = BorderRemover.process_directory(
            input_dir=target_path,
            output_dir=out_path,
            debug=req.debug,
            skip_count=req.skip_count
        )

        try:
            rel_output = str(out_path.relative_to(ROOT_DIR))
        except ValueError:
            rel_output = str(out_path)

        return {
            "success": True,
            "input_dir": str(target_path),
            "output_dir": str(out_path),
            "relative_output_dir": rel_output,
            "total_files": results["total_files"],
            "cropped_count": results["cropped_count"],
            "copied_count": results["copied_count"],
            "error_count": results["error_count"],
            "is_overwrite": (out_path.resolve() == target_path.resolve())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# A+ CONTENT BANNER BUILDER ENDPOINTS
# ==============================================================================

@app.get("/api/aplus/templates")
def get_aplus_templates(templates_dir: Optional[str] = Query(None, description="Custom templates folder")):
    """Returns available banner templates with slot configurations."""
    resolved_dir = APlusBuilder.get_templates_dir(templates_dir)
    templates = APlusBuilder.list_templates(str(resolved_dir))
    return {
        "templates_dir": str(resolved_dir),
        "exists": resolved_dir.exists(),
        "total_templates": len(templates),
        "templates": templates
    }


@app.get("/api/aplus/browse-templates-folder")
def browse_templates_folder(current: Optional[str] = None):
    """Opens native Windows folder selection dialog to choose templates directory."""
    chosen = select_folder_native(current)
    if not chosen:
        return {"cancelled": True, "path": None}
    return {"cancelled": False, "path": chosen}


@app.post("/api/aplus/preview")
def generate_aplus_preview(req: APlusPreviewRequest):
    """Generates an instant base64 preview of the composite banner."""
    try:
        preview_b64 = APlusBuilder.generate_preview_base64(
            template_path=req.template_path,
            image_paths=req.image_paths,
            fit_mode=req.fit_mode,
            max_preview_width=970
        )
        return {
            "success": True,
            "preview_url": preview_b64
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/aplus/build")
def build_aplus_banner(req: APlusBuildRequest):
    """Generates the final banner and saves it into the active book folder."""
    target_path = Path(req.folder_path)
    if not target_path.is_absolute():
        target_path = (ROOT_DIR / req.folder_path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Book directory not found: {target_path}")

    try:
        result = APlusBuilder.build_banner(
            template_path=req.template_path,
            image_paths=req.image_paths,
            output_folder=str(target_path),
            custom_output_name=req.custom_output_name,
            export_amazon_size=req.export_amazon_size,
            fit_mode=req.fit_mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static directory for the Web UI
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


