#!/usr/bin/env python3
"""
Shared utility functions for PCX format image conversion.

This module provides a common set of tools for working with PCX image files,
including header parsing, RLE decompression, and special file handling.
All converters can leverage these utilities for consistent behavior.
"""

import logging
import struct
from pathlib import Path
from typing import Tuple

# Constants for PCX format
PCX_HEADER_SIZE = 128
PCX_SIGNATURE = 0x0A
PCX_VERSION = 0x05
PCX_ENCODING_RLE = 0x01
PCX_BPP_PC4 = 0x01  # 1 bit per pixel × 4 planes = 16 colors
PCX_BPP_PC8 = 0x08  # 8 bits per pixel = 256 colors
PCX_PLANES_PC4 = 4  # 4 color planes for PC4
PCX_PLANES_PC8 = 1  # 1 color plane for PC8
PCX_PALETTE_MARKER = 0x0C  # Marker byte before palette in PC8 files
PCX_PALETTE_SIZE_PC4 = 48  # 16 colors × 3 bytes per color
PCX_PALETTE_SIZE_PC8 = 768  # 256 colors × 3 bytes per color

# Constants for dimension validation
MAX_NORMAL_WIDTH = 800
MAX_NORMAL_HEIGHT = 600

# Constants for RLE encoding
RLE_MARKER_BIT = 0xC0
RLE_LENGTH_MASK = 0x3F

# Special file names that can exceed normal dimensions
SPECIAL_FILES = [
    "METHOD3.PC4",
    "METHOD3.PC8",
    "MAPMNT.PC4",
    "MAPMNT.PC8",
    "MAPGRSS.PC4",
    "MAPGRSS.PC8",
]

# Special TALK file dimensions
TALK_PREFIX = "TALK"
TALK_WIDTH = 262
TALK_HEIGHT = 201

# Set up logging
logger = logging.getLogger("pcx_converter")


def setup_logging(debug_mode: bool = False) -> logging.Logger:
    """Set up logging for PCX converters.

    Configures the logging system with appropriate levels and formats
    based on whether debug mode is enabled.

    Args:
        debug_mode: Whether to enable debug logging

    Returns:
        Logger instance for PCX converter

    Example:
        >>> logger = setup_logging(True)
        >>> logger.debug("Detailed information")
        >>> logger.info("General information")
    """
    # Configure root logger
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(levelname).1s %(module)s: %(message)s", force=True
    )

    # Get logger for PCX converter
    pcx_logger = logging.getLogger("pcx_converter")
    pcx_logger.setLevel(log_level)

    return pcx_logger


def debug(msg: str) -> None:
    """Print debug message using logger.

    Args:
        msg: Debug message to log
    """
    logger.debug(msg)


def dump_bytes(data: bytes, offset: int, length: int) -> str:
    """Format bytes as a hex string for debugging.

    Creates a space-separated string of hexadecimal byte values
    for easy inspection of binary data.

    Args:
        data: Binary data to dump
        offset: Starting offset in bytes
        length: Number of bytes to dump

    Returns:
        Formatted string of hex values

    Example:
        >>> dump_bytes(b'\\x01\\x02\\x03\\x04', 1, 2)
        '02 03'
    """
    return " ".join(f"{b:02x}" for b in data[offset : offset + length])


def decompress_rle(data: bytes, expected_size: int) -> bytes:
    """Decompress PCX RLE-encoded image data.

    Implements the PCX Run-Length Encoding decompression algorithm:
    - If a byte has the high bits set (≥ 0xC0), the lower 6 bits indicate
      a run length, and the next byte is the value to repeat.
    - Otherwise, the byte is treated as a literal value.

    Args:
        data: Compressed RLE data
        expected_size: Expected size of decompressed data

    Returns:
        Decompressed data as bytes

    Raises:
        ValueError: If decompression fails

    Example:
        >>> decompress_rle(b'\\xC3A', 3)
        b'AAA'
    """
    if not data or expected_size <= 0:
        return bytes([0] * expected_size)

    output = bytearray(expected_size)
    output_pos = 0
    input_pos = 0

    try:
        while input_pos < len(data) and output_pos < expected_size:
            byte = data[input_pos]
            input_pos += 1

            if byte >= RLE_MARKER_BIT:  # Run of pixels
                # Get run length from lower 6 bits
                run_length = byte & RLE_LENGTH_MASK
                if input_pos >= len(data):
                    # If we hit EOF, treat the marker as a literal
                    if output_pos < expected_size:
                        output[output_pos] = byte
                        output_pos += 1
                    continue

                pixel = data[input_pos]
                input_pos += 1

                # Don't exceed expected size
                run_length = min(run_length, expected_size - output_pos)
                # Fill run pixels
                output[output_pos : output_pos + run_length] = (
                    bytes([pixel]) * run_length
                )
                output_pos += run_length
            else:  # Literal pixel
                if output_pos < expected_size:
                    output[output_pos] = byte
                    output_pos += 1

    except Exception as e:
        raise ValueError(f"RLE error at offset {input_pos}: {str(e)}")

    # Fill remaining space with zeros if we're short
    if output_pos < expected_size:
        output[output_pos:] = bytes([0]) * (expected_size - output_pos)

    return bytes(output)


def verify_pcx_header(data: bytes) -> Tuple[bool, str]:
    """Verify that a byte array contains a valid PCX header.

    Checks the PCX signature, version, and encoding bytes to ensure
    the data represents a valid PCX file.

    Args:
        data: File data with PCX header

    Returns:
        Tuple of (success, error_message)

    Example:
        >>> success, error = verify_pcx_header(pcx_data)
        >>> if not success:
        ...     print(f"Invalid PCX file: {error}")
    """
    if len(data) < PCX_HEADER_SIZE:
        return (
            False,
            f"Invalid header size: {len(data)} bytes (expected {PCX_HEADER_SIZE})",
        )

    # Verify PCX header
    if data[0] != PCX_SIGNATURE:
        return (
            False,
            f"Invalid PCX identifier: {data[0]:#x} (expected {PCX_SIGNATURE:#x})",
        )
    if data[1] != PCX_VERSION:
        return False, f"Invalid PCX version: {data[1]:#x} (expected {PCX_VERSION:#x})"
    if data[2] != PCX_ENCODING_RLE:
        return (
            False,
            f"Invalid encoding: {data[2]:#x} (expected {PCX_ENCODING_RLE:#x} for RLE)",
        )

    return True, ""


def get_dimensions(data: bytes) -> Tuple[int, int]:
    """Extract image dimensions from PCX header.

    Reads the min/max coordinates from the PCX header to determine
    the image dimensions.

    Args:
        data: File data with PCX header

    Returns:
        Tuple of (width, height)

    Example:
        >>> width, height = get_dimensions(pcx_data)
        >>> print(f"Image size: {width}x{height}")
    """
    # Get dimensions (xmin, ymin, xmax, ymax)
    xmin, ymin, xmax, ymax = struct.unpack("<HHHH", data[4:12])
    width = xmax + 1
    height = ymax + 1
    return width, height


def get_bytes_per_line(data: bytes) -> int:
    """Get bytes per scanline from PCX header.

    Extracts the bytes_per_line value which indicates the number of bytes
    in each scanline, including any padding.

    Args:
        data: File data with PCX header

    Returns:
        Bytes per scanline
    """
    return struct.unpack("<H", data[66:68])[0]


def is_special_file(filepath: Path) -> bool:
    """Check if file is one of the special files with overridden parameters.

    Some files in the Oregon Trail have special handling requirements,
    particularly for dimension validation.

    Args:
        filepath: Path to the file to check

    Returns:
        True if it's a special file

    Example:
        >>> if is_special_file(path):
        ...     print("This file needs special handling")
    """
    return filepath.name.upper() in SPECIAL_FILES


def is_talk_file(filepath: Path) -> bool:
    """Check if file is a TALK file with special dimensions.

    TALK files have fixed dimensions regardless of their header values.

    Args:
        filepath: Path to the file to check

    Returns:
        True if it's a TALK file
    """
    return filepath.stem.upper().startswith(TALK_PREFIX)


def get_talk_dimensions() -> Tuple[int, int]:
    """Get the fixed dimensions for TALK files.

    Returns:
        Tuple of (width, height)
    """
    # TALK files have fixed dimensions regardless of header
    return TALK_WIDTH, TALK_HEIGHT


class PCXFormatError(Exception):
    """Exception raised for errors in PCX file format."""

    pass


def validate_dimensions(width: int, height: int, filepath: Path) -> None:
    """Validate image dimensions, considering special files.

    Ensures dimensions are positive and within maximum bounds,
    unless the file is in the special files list.

    Args:
        width: Image width
        height: Image height
        filepath: Path to the image file

    Raises:
        PCXFormatError: If dimensions are invalid
    """
    if width <= 0 or height <= 0:
        raise PCXFormatError(f"Invalid dimensions: {width}x{height}")

    if width > MAX_NORMAL_WIDTH or height > MAX_NORMAL_HEIGHT:
        if not is_special_file(filepath):
            raise PCXFormatError(f"Dimensions too large: {width}x{height}")
