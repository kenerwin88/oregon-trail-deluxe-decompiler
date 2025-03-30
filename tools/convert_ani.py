#!/usr/bin/env python3
"""
ANI animation format converter for Oregon Trail files.
Converts ANI files to JSON format with frame data.

Format details:
- ANI: Animation files
- Text-based format with frame coordinates
- References PCC/PC4/PC8 files for frame images
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_animation(text: str) -> dict:
    """Parse animation data from text

    Args:
        text: Raw animation text

    Returns:
        dict: Animation data including frames and coordinates
    """
    # Split into lines and remove empty lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # First line is the image file reference
    image_file = lines[0]
    pos = 1

    # Parse animation data
    frames = []
    while pos < len(lines):
        try:
            # Get number of coordinates for this frame
            # First try to parse as a single number
            try:
                num_coords = int(lines[pos])
            except ValueError:
                # If that fails, try to parse as coordinates
                coords = lines[pos].split(",")
                if len(coords) == 2:
                    frame_data = {
                        "coordinates": [{"x": int(coords[0]), "y": int(coords[1])}],
                        "dimensions": [],
                    }
                    pos += 1
                    frames.append(frame_data)
                    continue
                else:
                    logger.warning(f"Invalid frame data at line {pos}: {lines[pos]}")
                    break

            pos += 1

            frame_data = {"coordinates": [], "dimensions": []}

            # Read coordinates
            for i in range(num_coords):
                if pos >= len(lines):
                    break

                # Parse x,y coordinates
                coords = lines[pos].split(",")
                if len(coords) == 2:
                    frame_data["coordinates"].append(
                        {"x": int(coords[0]), "y": int(coords[1])}
                    )
                pos += 1

                # Parse width,height if available
                if pos < len(lines):
                    dims = lines[pos].split(",")
                    if len(dims) == 2:
                        frame_data["dimensions"].append(
                            {"width": int(dims[0]), "height": int(dims[1])}
                        )
                    pos += 1

            frames.append(frame_data)

        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing frame data: {str(e)}")
            break

    return {"image_file": image_file, "frame_count": len(frames), "frames": frames}


def convert_ani(filepath: Path, output_dir: Path) -> bool:
    """Convert ANI to JSON

    Args:
        filepath: Path to ANI file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith(".ANI"):
            return False

        output_path = output_dir / "animations" / f"{filepath.stem}.json"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Read animation file as text
        with open(filepath, "r", encoding="ascii") as f:
            text = f.read()

        # Parse animation data
        animation_data = parse_animation(text)

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(animation_data, f, indent=2)

        logger.info(f"Converted {filepath.name} to JSON")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
