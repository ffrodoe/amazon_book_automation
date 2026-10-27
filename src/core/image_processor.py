import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from PIL import Image

from src.config import BookFormat, FORMAT_SPECS, DEFAULT_INTRO_COUNT


def natural_sort_key(s: str) -> List:
    """Key for natural sorting (e.g. '2.png' before '10.png')."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


@dataclass
class PagePlan:
    page_number: int       # 1-indexed
    is_blank: bool
    image_path: Optional[str] = None
    image_name: Optional[str] = None
    label: str = ""
    is_recto: bool = True  # True = Right page (odd), False = Left page (even)


@dataclass
class BookPlan:
    folder_path: str
    total_images: int
    total_pages: int
    format: BookFormat
    pages: List[PagePlan]


class ImageProcessor:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

    @classmethod
    def get_image_files(cls, directory: str, include_cover: bool = False) -> List[Path]:
        """Scan directory and return naturally sorted image file paths, excluding cover_* by default."""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # If an 'interior' subfolder exists and contains images, use it
        interior_sub = dir_path / "interior"
        target_dir = interior_sub if (interior_sub.exists() and interior_sub.is_dir()) else dir_path

        files = [
            f for f in target_dir.iterdir()
            if f.is_file() and f.suffix.lower() in cls.SUPPORTED_EXTENSIONS
        ]

        if not include_cover:
            # Exclude cover front/back/spine files from interior processing
            files = [f for f in files if not f.stem.lower().startswith("cover_")]

        # Natural sort by file name
        files.sort(key=lambda f: natural_sort_key(f.name))
        return files

    @classmethod
    def find_cover_files(cls, directory: str) -> dict:
        """
        Locates cover_front and cover_back in the given directory or a 'cover' subfolder.
        Returns dict with paths and filenames.
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"front": None, "back": None}

        # Check root dir first, then 'cover' subfolder
        search_dirs = [dir_path]
        cover_sub = dir_path / "cover"
        if cover_sub.exists() and cover_sub.is_dir():
            search_dirs.append(cover_sub)

        front_path = None
        back_path = None

        for d in search_dirs:
            for f in d.iterdir():
                if not f.is_file() or f.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
                    continue
                stem = f.stem.lower()
                if stem == "cover_front" or stem == "front":
                    if not front_path:
                        front_path = f
                elif stem == "cover_back" or stem == "back":
                    if not back_path:
                        back_path = f

        return {
            "front": str(front_path.resolve()) if front_path else None,
            "front_name": front_path.name if front_path else None,
            "back": str(back_path.resolve()) if back_path else None,
            "back_name": back_path.name if back_path else None,
        }

    @classmethod
    def build_book_plan(
        cls,
        directory: str,
        book_format: BookFormat = BookFormat.A4,
        intro_count: int = DEFAULT_INTRO_COUNT
    ) -> BookPlan:
        """
        Builds the structured sequence of pages for the book interior.
        Rule:
        - Pages 1..intro_count: sequential images (Title, Copyright, Intro).
        - From image (intro_count + 1) onwards:
            - Insert a blank page (even page / verso)
            - Place image on next page (odd page / recto)
        - Final blank page added after last image to guarantee an even total page count.
        """
        image_files = cls.get_image_files(directory)
        if not image_files:
            raise ValueError(f"No valid images found in directory: {directory}")

        pages: List[PagePlan] = []
        current_page = 1

        for idx, img_path in enumerate(image_files):
            img_num = idx + 1
            file_name = img_path.name

            if img_num <= intro_count:
                # Sequential intro pages (1, 2, 3)
                if img_num == 1:
                    label = "Title Page"
                elif img_num == 2:
                    label = "Copyright / Info"
                else:
                    label = f"Intro Page {img_num}"

                pages.append(PagePlan(
                    page_number=current_page,
                    is_blank=False,
                    image_path=str(img_path.resolve()),
                    image_name=file_name,
                    label=label,
                    is_recto=(current_page % 2 != 0)
                ))
                current_page += 1
            else:
                # Coloring pages start:
                # 1. Blank page (verso - back of previous drawing)
                pages.append(PagePlan(
                    page_number=current_page,
                    is_blank=True,
                    image_path=None,
                    image_name=None,
                    label="Blank Protection Page",
                    is_recto=(current_page % 2 != 0)
                ))
                current_page += 1

                # 2. Illustration page (recto - right page)
                coloring_index = img_num - intro_count
                pages.append(PagePlan(
                    page_number=current_page,
                    is_blank=False,
                    image_path=str(img_path.resolve()),
                    image_name=file_name,
                    label=f"Coloring Illustration #{coloring_index}",
                    is_recto=(current_page % 2 != 0)
                ))
                current_page += 1

        # Final blank page after the last illustration
        pages.append(PagePlan(
            page_number=current_page,
            is_blank=True,
            image_path=None,
            image_name=None,
            label="Blank Final Page",
            is_recto=(current_page % 2 != 0)
        ))

        # Ensure total page count is even (Amazon KDP paperback requirement)
        if len(pages) % 2 != 0:
            current_page += 1
            pages.append(PagePlan(
                page_number=current_page,
                is_blank=True,
                image_path=None,
                image_name=None,
                label="Padding Blank (KDP Even Requirement)",
                is_recto=(current_page % 2 != 0)
            ))

        return BookPlan(
            folder_path=str(Path(directory).resolve()),
            total_images=len(image_files),
            total_pages=len(pages),
            format=book_format,
            pages=pages
        )
