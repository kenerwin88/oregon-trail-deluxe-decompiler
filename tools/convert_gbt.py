#!/usr/bin/env python3
"""
GBT guide format converter for Oregon Trail files.
Converts GBT files to JSON format.

Format details:
- GBT: Guide Book Text files
- Contains entries separated by backslashes
- Each entry is a topic about the Oregon Trail
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_guide_entries(text: str) -> list[dict]:
    """Parse guide entries from text

    Args:
        text: Raw guide text

    Returns:
        list: list of guide entries with titles and content
    """
    # Split on backslash
    entries = text.strip().split("\\")

    # Process each entry
    guide_entries = []
    for entry in entries:
        # Skip empty entries
        if not entry.strip():
            continue

        # Extract first line as title
        lines = entry.strip().split("\n")
        title = lines[0].strip()

        # Join remaining lines as content
        content = "\n".join(line.strip() for line in lines[1:] if line.strip())

        # Add to entries list
        guide_entries.append({"title": title, "content": content})

    return guide_entries


def convert_gbt(filepath: Path, output_dir: Path) -> bool:
    """Convert GBT to JSON

    Args:
        filepath: Path to GBT file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith(".GBT"):
            return False

        output_path = output_dir / "guide" / f"{filepath.stem}.json"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Read guide file as text
        with open(filepath, "rb") as f:
            text = f.read().decode(
                "latin1"
            )  # Use latin1 to handle extended ASCII characters

        # Parse entries
        entries = parse_guide_entries(text)

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"guide_entries": entries}, f, indent=2)

        logger.info(f"Converted {filepath.name} to JSON")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
