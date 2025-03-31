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


def decode_rle_scanline(f, expected_length, debug_info=None):
    """Decode a single RLE-compressed scanline without seeking back."""
    decoded = bytearray()
    start_pos = f.tell()
    
    if debug_info:
        logger.debug(f"\nDecoding scanline at offset {start_pos}, expected length: {expected_length}")

    try:
        while len(decoded) < expected_length:
            byte = f.read(1)
            if not byte:  # EOF check
                raise EOFError(f"Unexpected EOF during RLE decoding at offset {f.tell()}. Expected {expected_length} bytes, got {len(decoded)}.")
            byte = byte[0]
            
            if (byte & 0xC0) == 0xC0:  # RLE marker (top 2 bits set)
                run_count = byte & 0x3F  # Get run length from bottom 6 bits
                run_value_byte = f.read(1)
                if not run_value_byte:
                    raise EOFError(f"Unexpected EOF reading RLE value at offset {f.tell()}.")
                run_value = run_value_byte[0]
                
                # Calculate how many bytes we actually need for this scanline
                remaining = expected_length - len(decoded)
                bytes_to_add = min(run_count, remaining)
                
                if debug_info:
                    logger.debug(f"RLE at {f.tell()-2}: count={run_count}, value=0x{run_value:02x}. Adding {bytes_to_add} bytes.")
                
                decoded.extend([run_value] * bytes_to_add)
                
                # If the run was longer than needed (run_count > bytes_to_add),
                # the file pointer is already correctly positioned after run_value_byte.
                # The next read for the subsequent scanline/plane will continue from here.
                
            else:  # Literal byte
                if debug_info:
                    logger.debug(f"Literal at {f.tell()-1}: 0x{byte:02x}")
                decoded.append(byte)

        # After the loop, check if we decoded exactly the expected length
        if len(decoded) != expected_length:
             # This case should ideally not be reached if EOF checks are robust
             # and expected_length is correct. But if it happens, log a warning.
             logger.warning(f"Decoded length mismatch: got {len(decoded)}, expected {expected_length}. Possible data corruption or incorrect header info.")
             # Truncate or pad if necessary? For now, just return what we have.

    except EOFError as e:
        logger.error(f"EOFError during RLE decode: {str(e)}")
        logger.error(f"Decoded {len(decoded)} of {expected_length} bytes before error.")
        # Return partially decoded data or raise? Raising is probably better.
        raise
    except Exception as e:
        logger.error(f"Unexpected error during RLE decode: {str(e)}")
        logger.error(f"File position: {f.tell()}, Decoded {len(decoded)} of {expected_length} bytes.")
        raise
        
    if debug_info:
        logger.debug(f"Finished decoding scanline. Final length: {len(decoded)}")
            
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


def convert_pc4(input_path: Path, output_path: Path, color16_path: Path, debug_mode: bool = False) -> bool:
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
                if debug_mode and y == 0:
                    logger.debug(f"\nDecoding first scanline for each plane:")
                
                for plane in range(planes):
                    try:
                        debug_info = debug_mode and y == 0
                        scanline = decode_rle_scanline(f, bytes_per_line, debug_info)
                        if len(scanline) != bytes_per_line:
                            raise ValueError(f"Scanline length mismatch: got {len(scanline)}, expected {bytes_per_line}")
                        plane_data[plane].append(scanline)
                    except Exception as e:
                        logger.error(f"Error decoding plane {plane}, scanline {y}: {str(e)}")
                        logger.error(f"File position: {f.tell()}")
                        return False

            # Create output image
            img = Image.new("RGB", (width, height))
            pixels = img.load()

            # Combine planes to create final image
            for y in range(height):
                for x in range(width):
                    bit_pos = 7 - (x % 8)  # Bits are stored from MSB to LSB
                    byte_pos = x // 8

                    # Get bits from each plane
                    # In EGA, planes are ordered:
                    # Plane 0 -> Blue (Bit 0)
                    # Plane 1 -> Green (Bit 1)
                    # Plane 2 -> Red (Bit 2)
                    # Plane 3 -> Intensity (Bit 3)
                    color_index = 0
                    for p in range(planes):
                        if byte_pos < len(plane_data[p][y]):
                            # Extract bit from MSB to LSB order
                            bit = (plane_data[p][y][byte_pos] >> bit_pos) & 1
                            # Map plane bits to color index
                            color_index |= (bit << p)

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

    return convert_pc4(filepath, output_path, color16_path, debug_mode)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 convert_pc4.py <input_pc4_file> <output_dir>")
        sys.exit(1)
        
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    # Enable debug logging
    setup_logging(True)
    logger.setLevel(logging.DEBUG)
    
    success = convert_image(input_path, output_dir, debug_mode=True)
    sys.exit(0 if success else 1)
