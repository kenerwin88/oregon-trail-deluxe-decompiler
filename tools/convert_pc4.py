#!/usr/bin/env python3
"""
PC4 Image format converter for Oregon Trail.
Converts .PC4 images to PNG format.

This module handles 4-bit EGA planar images (PC4 format) where each pixel
is constructed from 4 color planes, with each plane contributing 1 bit to
the final 4-bit color value (16 colors total).
"""

import logging
from pathlib import Path
from PIL import Image
import struct

try:
    # When used as a module
    from .pcx_utils import setup_logging
except ImportError:
    # When run as a script
    from pcx_utils import setup_logging

# Initialize logger
logger = logging.getLogger("pcx_converter.pc4")


def decode_rle_scanline(f, expected_length):
    """Decode a single RLE-compressed scanline"""
    decoded = bytearray()
    while len(decoded) < expected_length:
        byte = f.read(1)[0]
        if (byte & 0xC0) == 0xC0:  # RLE marker (top 2 bits set)
            run_count = byte & 0x3F  # Get run length from bottom 6 bits
            run_value = f.read(1)[0]  # Get the value to repeat
            decoded.extend([run_value] * run_count)
        else:
            decoded.append(byte)
    return decoded


def get_palette_from_color16(color16_path):
    """Extract 16-color palette from COLOR16.PCX"""
    with open(color16_path, "rb") as f:
        # Go to end of file minus 769 bytes (256 color palette + marker byte)
        f.seek(-769, 2)
        if f.read(1)[0] == 0x0C:  # Palette marker
            palette = []
            for _ in range(16):  # Only need first 16 colors
                r, g, b = f.read(3)
                palette.append((r, g, b))
            return palette
    return None


def convert_pc4(input_path: Path, output_path: Path, color16_path: Path) -> bool:
    """Convert PC4 image to PNG using COLOR16.PCX palette.

    Args:
        input_path: Path to PC4 image file
        output_path: Path to save PNG output
        color16_path: Path to COLOR16.PCX for palette

    Returns:
        True if conversion successful
    """
    try:
        # First get the palette
        palette = get_palette_from_color16(color16_path)
        if not palette:
            logger.error("Could not extract palette from COLOR16.PCX")
            return False

        logger.debug("Palette from COLOR16.PCX:")
        for i, color in enumerate(palette):
            logger.debug(f"Color {i}: RGB{color}")

        with open(input_path, "rb") as f:
            # Read PCX header
            header = f.read(128)
            xmin, ymin, xmax, ymax = struct.unpack("<HHHH", header[4:12])
            width = xmax - xmin + 1
            height = ymax - ymin + 1
            planes = header[65]
            bytes_per_line = struct.unpack("<H", header[66:68])[0]

            logger.debug(f"\nDecoding {input_path.name}:")
            logger.debug(f"Image size: {width}x{height}")
            logger.debug(f"Color planes: {planes}")
            logger.debug(f"Bytes per line: {bytes_per_line}")

            # Create arrays for each plane
            plane_data = [[] for _ in range(planes)]

            # Read and decode RLE data for each scanline of each plane
            for y in range(height):
                for plane in range(planes):
                    scanline = decode_rle_scanline(f, bytes_per_line)
                    plane_data[plane].append(scanline)

            # Create output image
            img = Image.new("RGB", (width, height))
            pixels = img.load()

            # Combine planes to create final image
            for y in range(height):
                for x in range(width):
                    bit_pos = 7 - (x % 8)
                    byte_pos = x // 8

                    # Get bits from each plane
                    color_index = 0
                    for p in range(planes):
                        if byte_pos < len(plane_data[p][y]):
                            bit = (plane_data[p][y][byte_pos] >> bit_pos) & 1
                            color_index |= bit << p

                    # Map to color from palette
                    pixels[x, y] = palette[color_index]

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the image
            img.save(output_path)
            logger.info(f"Converted {input_path.name} to PNG")
            return True

    except Exception as e:
        logger.error(f"Error converting {input_path.name}: {str(e)}")
        return False


def convert_image(filepath: Path, output_dir: Path, debug_mode: bool = False) -> bool:
    """Convert PC4 image to PNG.

    Args:
        filepath: Path to image file
        output_dir: Output directory for converted files
        debug_mode: Enable debug output

    Returns:
        True if conversion successful
    """
    # Set up logging if debug mode is enabled
    if debug_mode:
        setup_logging(True)

    # Skip if not a supported file type
    if not filepath.name.lower().endswith(".pc4"):
        return False

    # Put files in their respective subdirectories
    output_path = output_dir / "images" / "pc4" / f"{filepath.stem}.png"

    # Get path to COLOR16.PCX
    color16_path = filepath.parent / "COLOR16.PCX"
    if not color16_path.exists():
        logger.error(f"COLOR16.PCX not found in {filepath.parent}")
        return False

    return convert_pc4(filepath, output_path, color16_path)
