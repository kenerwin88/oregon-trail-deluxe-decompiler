#!/usr/bin/env python3
"""
GFT font format converter for Oregon Trail files.
Converts GFT files to PNG bitmap fonts.

Format details:
- GFT: Game Font files (BIG.GFT, SMALL.GFT, TINY.GFT)
- Contains bitmap data for each character
- Header contains character offsets
"""

import logging
from pathlib import Path
from PIL import Image
import struct

logger = logging.getLogger(__name__)


def parse_header(data: bytes) -> dict:
    """Parse GFT header

    Args:
        data: Raw file data

    Returns:
        dict: Header info including character count and offsets
    """
    # First 4 bytes contain header info
    char_count = struct.unpack("<H", data[2:4])[0]

    # Read character offsets
    offsets = []
    pos = 0x50  # Start of offset table
    for i in range(char_count):
        if pos + 2 > len(data):
            break
        offset = struct.unpack("<H", data[pos : pos + 2])[0]
        offsets.append(offset)
        pos += 2

    return {"char_count": char_count, "offsets": offsets}


def extract_character(data: bytes, offset: int) -> tuple[Image.Image, int]:
    """Extract single character bitmap

    Args:
        data: Raw file data
        offset: Start offset of character data

    Returns:
        tuple: (PIL Image of character, width of character)
    """
    # Each character has width and bitmap data
    width = data[offset]
    height = 16  # Fixed height for all characters

    # Create image for this character
    img = Image.new("1", (width, height), 0)  # Binary image (black background)
    pixels = img.load()

    # Read bitmap data
    pos = offset + 1
    for y in range(height):
        byte_count = (width + 7) // 8  # Round up to nearest byte
        for x_byte in range(byte_count):
            if pos >= len(data):
                break
            byte = data[pos]
            pos += 1

            # Process each bit in byte
            for bit in range(8):
                x = x_byte * 8 + bit
                if x < width:
                    pixels[x, y] = (byte >> (7 - bit)) & 1

    return img, width


def convert_gft(filepath: Path, output_dir: Path) -> bool:
    """Convert GFT to PNG bitmap font

    Args:
        filepath: Path to GFT file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith(".GFT"):
            return False

        output_path = output_dir / "fonts" / f"{filepath.stem}.png"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Read font file
        with open(filepath, "rb") as f:
            data = f.read()

        # Parse header
        header = parse_header(data)
        offsets = header["offsets"]

        # Calculate total width needed
        total_width = 0
        char_widths = []
        for offset in offsets:
            if offset == 0:
                char_widths.append(8)  # Default width for missing chars
                total_width += 8
                continue

            # Get character width
            if offset >= len(data):
                break
            width = data[offset]
            char_widths.append(width)
            total_width += width

        # Create output image
        height = 16  # Fixed height for all characters
        font_img = Image.new("1", (total_width, height), 0)

        # Extract each character
        x = 0
        for i, offset in enumerate(offsets):
            if offset == 0:
                # Skip missing characters
                x += char_widths[i]
                continue

            try:
                char_img, width = extract_character(data, offset)
                # Paste character into font image
                font_img.paste(char_img, (x, 0))
                x += width
            except Exception as e:
                logger.warning(f"Error extracting character {i}: {str(e)}")
                continue

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save metadata about character positions
        metadata = []
        x = 0
        for i, width in enumerate(char_widths):
            metadata.append(f"{i},{x},{width}")
            x += width

        metadata_path = output_dir / "fonts" / f"{filepath.stem}_metadata.txt"
        with open(metadata_path, "w") as f:
            f.write("\n".join(metadata))

        # Save font image
        font_img.save(output_path, "PNG")
        logger.info(f"Converted {filepath.name} to PNG bitmap font")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
