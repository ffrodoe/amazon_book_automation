import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import BookFormat, FORMAT_SPECS, DEFAULT_INTRO_COUNT, DEFAULT_BRIGHTNESS_OFFSET
from src.core.image_processor import ImageProcessor
from src.core.pdf_builder import PDFBuilder
from src.core.image_cleaner import ImageCleaner

app = FastAPI(title="Amazon KDP Coloring Book Studio", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class BuildRequest(BaseModel):
    folder_path: str
    format: str = "a4"
    intro_count: int = DEFAULT_INTRO_COUNT
    custom_output_name: Optional[str] = None


class CleanBackgroundRequest(BaseModel):
    folder_path: str
    brightness_offset: int = DEFAULT_BRIGHTNESS_OFFSET
    custom_output_dir: Optional[str] = None



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
    """Serves an image file for UI thumbnail preview."""
    img_path = Path(path)
    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(str(img_path))


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

        output_dir = ROOT_DIR / "output"
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
            "file_name": Path(generated_pdf).name,
            "size_mb": round(size_mb, 2),
            "total_pages": plan.total_pages,
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
        out_dir = req.custom_output_dir
        if out_dir:
            out_path = Path(out_dir)
            if not out_path.is_absolute():
                out_path = (ROOT_DIR / out_dir).resolve()
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
            "brightness_offset": req.brightness_offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static directory for the Web UI
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

