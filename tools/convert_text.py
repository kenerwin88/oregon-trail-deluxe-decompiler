#!/usr/bin/env python3
"""
Text format converter for Oregon Trail files.
Converts CTR and TXT files to UTF-8 format.

Format details:
- CTR: Game text and dialog files
- TXT: General text files
- ASCII encoded
- No special header or formatting
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_text(filepath: Path, output_dir: Path) -> bool:
    """Convert text files to UTF-8

    Args:
        filepath: Path to text file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith((".CTR", ".TXT")):
            return False

        output_path = output_dir / "text" / f"{filepath.stem}.txt"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Read as ASCII and convert to UTF-8
        with open(filepath, "r", encoding="ascii") as f:
            text = f.read()

        # Save as UTF-8
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"Converted {filepath.name} to UTF-8")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
