#!/usr/bin/env python3
"""
Main conversion script for Oregon Trail files.
Handles conversion of all file types to modern formats.
"""

import logging
from pathlib import Path

from .convert_pc8 import convert_image as convert_pc8
from .convert_pc4 import convert_image as convert_pc4
from .convert_snd import convert_snd
from .convert_text import convert_text
from .convert_xmi import convert_xmi
from .convert_ctr import convert_ctr
from .convert_ani import convert_ani
from .convert_lst import convert_lst

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname).1s %(module)s: %(message)s", force=True
)
logger = logging.getLogger(__name__)


def set_debug(enabled: bool):
    """Enable or disable debug logging"""
    if enabled:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)


def clean_output_dir(output_dir: Path, file_type: str = None) -> None:
    """Clean output directories by removing all existing files

    Args:
        output_dir: Base output directory
        file_type: Optional specific type to clean ('pc8', 'xmi', 'snd', 'text')
    """
    # Map file types to subdirectories
    type_dirs = {
        "pc8": "images",
        "pc4": "images",
        "256": "images",  # .256 files go in images directory
        "xmi": "music",
        "snd": "sounds",
        "text": "text",
        "ctr": "controls",
        "ani": "animations",
        "lst": "scores",  # High scores go in scores directory
    }

    # Create base output directory if it doesn't exist
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # Determine which subdirectories to clean
    subdirs = [type_dirs[file_type]] if file_type else type_dirs.values()

    # Create and clean subdirectories
    for subdir in subdirs:
        dir_path = output_dir / subdir
        if dir_path.exists():
            logger.info(f"Cleaning {subdir} directory")
            for file in dir_path.glob("*"):
                if file.is_file():
                    file.unlink()
        else:
            dir_path.mkdir(parents=True)
            logger.info(f"Created {subdir} directory")


def convert_all(
    input_dir: str, output_dir: str, file_type: str = None, clean: bool = True
) -> bool:
    """Convert files in input directory

    Args:
        input_dir: Directory containing extracted GXL files
        output_dir: Output directory for converted files
        file_type: Optional specific type to convert ('pc8', 'xmi', 'snd', 'text')
        clean: Whether to clean output directories before converting (default: True)

    Returns:
        bool: True if all conversions successful
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Clean output directories if requested
    if clean:
        clean_output_dir(output_path, file_type)
    elif not output_path.exists():
        output_path.mkdir(parents=True)

    # Map file types to converter functions
    converters = {
        "pc8": convert_pc8,
        "pc4": convert_pc4,
        "256": convert_pc8,  # Use same converter for .256 files
        "xmi": convert_xmi,
        "snd": convert_snd,
        "text": convert_text,
        "ctr": convert_ctr,
        "ani": convert_ani,
        "lst": convert_lst,
    }

    success = True
    for filepath in input_path.rglob("*"):
        if filepath.is_file():
            if file_type:
                # Run only specified converter
                if converters[file_type](filepath, output_path):
                    logger.debug(f"Converted {filepath.name}")
                else:
                    logger.debug(f"Skipped {filepath.name} - not a {file_type} file")
            else:
                # Try each converter
                if not any(
                    [
                        convert_pc8(filepath, output_path),
                        convert_pc4(filepath, output_path),
                        convert_xmi(filepath, output_path),
                        convert_snd(filepath, output_path),
                        convert_text(filepath, output_path),
                        convert_ctr(filepath, output_path),
                        convert_ani(filepath, output_path),
                        convert_lst(filepath, output_path),
                    ]
                ):
                    logger.debug(f"Skipped {filepath.name} - unknown format")

    return success
