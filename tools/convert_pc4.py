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
from typing import Optional # Import Optional here
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


def read_pcx_palette(pcx_path: Path, num_colors: int = 16) -> Optional[list[tuple[int, int, int]]]:
    """
    Reads the color palette from a PCX file.
    Handles different PCX versions and potential errors.
    Returns the first `num_colors` entries.
    """
    # Optional is now imported globally

    try:
        with open(pcx_path, "rb") as f:
            # Read header to check version
            header = f.read(128)
            if len(header) < 128:
                logger.error(f"Palette file {pcx_path.name} is too small to be a valid PCX.")
                return None
                
            signature, version = struct.unpack("<BB", header[0:2])
            if signature != 0x0A:
                logger.error(f"Palette file {pcx_path.name} does not have PCX signature.")
                return None

            marker = None # Initialize marker
            # For version 5 (256 colors), palette is usually at the end
            if version == 5:
                try:
                    f.seek(-769, 2)  # Go to EOF - (256*3 + 1 marker byte)
                    marker = f.read(1)
                except OSError: # Handle files too small for seek
                     logger.warning(f"Could not seek to palette marker position in {pcx_path.name}. File might be too small or corrupted.")

                if marker and marker[0] == 0x0C:
                    palette_data = f.read(768) # Read 256 * 3 bytes
                    if len(palette_data) != 768:
                         logger.error(f"Could not read full 256-color palette from {pcx_path.name}.")
                         return None
                    palette = []
                    for i in range(num_colors): # Extract only the first num_colors
                        r, g, b = palette_data[i*3 : i*3 + 3]
                        palette.append((r, g, b))
                    return palette
                else:
                    # Palette marker not found where expected, try header
                    logger.warning(f"Palette marker 0x0C not found at expected position in {pcx_path.name} (Version 5). Will attempt header palette.")
                    # Fall through to attempt reading from header below

            # Attempt to read palette from header (Versions 0, 2, 3 or fallback for V5)
            if version in [0, 2, 3] or (version == 5 and (not marker or marker[0] != 0x0C)):
                 logger.info(f"Attempting to read palette from header of {pcx_path.name} (Version {version}).")
                 header_palette_data = header[16:16 + 48] # 16 colors * 3 bytes
                 if len(header_palette_data) == 48:
                     palette = []
                     for i in range(num_colors):
                          r, g, b = header_palette_data[i*3 : i*3 + 3]
                          palette.append((r, g, b))
                     if version == 5:
                         logger.warning(f"Used header palette from {pcx_path.name} as fallback.")
                     return palette
                 else:
                     logger.error(f"Could not read expected 48 bytes for header palette in {pcx_path.name}.")
                     return None
            elif version == 4: # Version 4 (PC Paintbrush III) has no palette
                 logger.warning(f"PCX version {version} detected in {pcx_path.name}. This version does not contain a palette.")
                 return None # Or potentially return a default EGA palette here? For now, None.
            else:
                # Includes other unsupported versions
                logger.error(f"Unsupported or unexpected PCX version {version} for palette reading in {pcx_path.name}.")
                return None

    except FileNotFoundError:
        logger.error(f"Palette file not found: {pcx_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading palette from {pcx_path.name}: {str(e)}")
        return None


def convert_pc4(input_path: Path, output_path: Path, color16_path: Path, debug_mode: bool = False) -> bool:
    """Convert PC4 image to PNG using palette from COLOR16.PCX.

    Args:
        input_path: Path to PC4 image file
        output_path: Path to save PNG output
        color16_path: Path to COLOR16.PCX for palette
        debug_mode: Enable debug output

    Returns:
        True if conversion successful
    """
    try:
        # Read the first 16 colors from COLOR16.PCX palette
        palette = read_pcx_palette(color16_path, 16)
        if not palette:
            logger.error(f"Failed to read palette from {color16_path.name}. Cannot convert {input_path.name}.")
            return False

        logger.debug(f"Using palette from {color16_path.name}:")
        if debug_mode:
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
            logger.debug(f"Bytes per line (from header): {bytes_per_line}")

            # Calculate expected bytes per line for one plane
            expected_bpl = (width + 7) // 8
            logger.debug(f"Expected bytes per line (calculated): {expected_bpl}")
            if bytes_per_line < expected_bpl:
                 logger.warning(f"Header 'bytes_per_line' ({bytes_per_line}) is less than calculated minimum ({expected_bpl}) for width {width}. This might indicate corruption or an unusual format.")
            elif bytes_per_line > expected_bpl:
                 logger.info(f"Header 'bytes_per_line' ({bytes_per_line}) includes padding beyond calculated minimum ({expected_bpl}). Using header value.")


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

    # Find COLOR16.PCX relative to the input file
    color16_path = None
    search_paths = [
        filepath.parent,
        filepath.parent.parent, # Check one level up
    ]
    # Try to find a 'raw_extracted' directory by traversing up
    current = filepath.parent
    while current != current.parent: # Traverse up until root
        # Check if current directory itself is named 'raw_extracted'
        if current.name == 'raw_extracted':
            search_paths.append(current)
            break
        # Check if 'raw_extracted' exists as a subdirectory
        elif (current / 'raw_extracted').is_dir():
            search_paths.append(current / 'raw_extracted')
            # If found, no need to search further up for it
            break
        current = current.parent
        
    # Add project root as a last resort search path if needed
    # This assumes pcx_utils might be located relative to project root
    try:
        # Attempt relative import first for module usage
        from .pcx_utils import PROJECT_ROOT 
    except ImportError:
        try:
             # Fallback for script usage
             from pcx_utils import PROJECT_ROOT
        except (ImportError, AttributeError):
             PROJECT_ROOT = None # Indicate PROJECT_ROOT couldn't be imported

    if PROJECT_ROOT:
        project_root_path = Path(PROJECT_ROOT)
        if project_root_path not in search_paths:
             search_paths.append(project_root_path)
        # Also check for raw_extracted within the project root
        raw_extracted_in_root = project_root_path / 'raw_extracted'
        if raw_extracted_in_root.is_dir() and raw_extracted_in_root not in search_paths:
             search_paths.append(raw_extracted_in_root)
    else:
         logger.debug("Could not determine PROJECT_ROOT for palette search.")


    # Deduplicate search paths while preserving order (Python 3.7+)
    unique_search_paths = list(dict.fromkeys(search_paths))

    logger.debug(f"Searching for COLOR16.PCX in: {unique_search_paths}")

    for search_dir in unique_search_paths:
        potential_path = search_dir / "COLOR16.PCX"
        if potential_path.is_file(): # Check if it's actually a file
            color16_path = potential_path
            logger.info(f"Found COLOR16.PCX at: {color16_path}")
            break
            
    if not color16_path:
        logger.error(f"COLOR16.PCX not found near {filepath} or in standard locations. Searched: {unique_search_paths}. Cannot determine palette.")
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
