#!/usr/bin/env python3
"""
PC8 Image format converter for Oregon Trail.
Converts .PC8 and .256 images to PNG format.

This module handles 8-bit PCX images (PC8/256 format) with direct pixel values
and a 256-color palette. Each pixel uses a single byte to index into the palette.
"""

import logging
from pathlib import Path
from PIL import Image

from .pcx_utils import (
    # Constants
    PCX_HEADER_SIZE,
    PCX_BPP_PC8,
    PCX_PALETTE_MARKER,
    PCX_PALETTE_SIZE_PC8,
    TALK_WIDTH,
    TALK_HEIGHT,
    # Functions
    debug,
    dump_bytes,
    decompress_rle,
    verify_pcx_header,
    get_dimensions,
    get_bytes_per_line,
    is_talk_file,
    validate_dimensions,
    PCXFormatError,
    setup_logging,
)

# Initialize logger
logger = logging.getLogger("pcx_converter.pc8")


class PC8Image:
    """Class representing a PC8 image file.

    Encapsulates the parsing, processing, and conversion of PC8-format
    image files to PNG format.

    Attributes:
        width: Image width in pixels
        height: Image height in pixels
        bytes_per_line: Bytes per scan line (may include padding)
        palette: Color palette for the image (256 RGB triplets)
        image_data: Uncompressed pixel data for the image
    """

    def __init__(self, filepath: Path):
        """Initialize a PC8Image from a file.

        Args:
            filepath: Path to the PC8 image file

        Raises:
            PCXFormatError: If the file is not a valid PC8 image
        """
        self.filepath = filepath
        self.width = 0
        self.height = 0
        self.bytes_per_line = 0
        self.palette = None
        self.image_data = None

        # Load and parse the file
        self._load()

    def _load(self) -> None:
        """Load and parse the PC8 image file.

        Reads the file, parses the header, extracts the palette,
        and decompresses the image data.

        Raises:
            PCXFormatError: If the file is not a valid PC8 image
        """
        # Read file data
        with open(self.filepath, "rb") as f:
            data = f.read()

        debug(f"File size: {len(data)} bytes")
        debug(f"First 16 bytes: {dump_bytes(data, 0, 16)}")

        # Verify PCX header
        success, error_msg = verify_pcx_header(data)
        if not success:
            raise PCXFormatError(error_msg)

        # Verify 8-bit format
        if data[3] != PCX_BPP_PC8:
            raise PCXFormatError(
                f"Not a PC8 file, bits per pixel is {data[3]} (expected {PCX_BPP_PC8})"
            )

        # Get dimensions
        self.width, self.height = get_dimensions(data)

        # Validate dimensions
        validate_dimensions(self.width, self.height, self.filepath)

        # Handle TALK files with special dimensions
        if is_talk_file(self.filepath):
            debug(f"TALK file: Original dimensions {self.width}x{self.height}")
            self.width, self.height = TALK_WIDTH, TALK_HEIGHT
            debug(f"TALK file: New dimensions {self.width}x{self.height}")

        # Get bytes per line
        self.bytes_per_line = get_bytes_per_line(data)
        debug(f"Dimensions: {self.width}x{self.height}")
        debug(f"Bytes per line: {self.bytes_per_line}")

        # Get palette from end of file
        if (
            len(data) >= PCX_PALETTE_SIZE_PC8 + 1
            and data[-PCX_PALETTE_SIZE_PC8 - 1] == PCX_PALETTE_MARKER
        ):
            # Found palette marker, use end palette
            self.palette = bytes(data[-PCX_PALETTE_SIZE_PC8:])
        else:
            # Fallback: use header palette (16 colors * 3 bytes) expanded to 256 colors
            palette_data = bytes(data[16:64])
            self.palette = bytes(palette_data * 16)

        # Read and decompress pixel data
        compressed_data = data[PCX_HEADER_SIZE : -PCX_PALETTE_SIZE_PC8 - 1]
        debug(f"Compressed data starts with: {dump_bytes(compressed_data, 0, 16)}")

        # Calculate expected size
        expected_size = self.bytes_per_line * self.height
        # Handle special case for truncated files
        if len(compressed_data) < expected_size and self.filepath.name == "SCROLL.PC8":
            expected_size = len(compressed_data)

        debug(f"Expected size: {expected_size} bytes")
        debug(f"Compressed data size: {len(compressed_data)}")

        # Decompress RLE data
        pixel_data = decompress_rle(compressed_data, expected_size)

        # Process image data - remove padding if present
        self._process_pixel_data(pixel_data)

    def _process_pixel_data(self, pixel_data: bytes) -> None:
        """Process raw pixel data into usable image data.

        Handles padding removal and ensures the data is properly formatted
        for image creation.

        Args:
            pixel_data: Raw decompressed pixel data
        """
        image_data = bytearray()
        for y in range(self.height):
            line_start = y * self.bytes_per_line

            # Skip processing if we're past the end of data
            if line_start >= len(pixel_data):
                image_data.extend([0] * self.width)
                continue

            # Handle TALK files specially
            if is_talk_file(self.filepath):
                image_data.extend(pixel_data[line_start : line_start + self.width])
            else:
                # For other files, handle potential padding
                available = min(self.width, len(pixel_data) - line_start)
                image_data.extend(pixel_data[line_start : line_start + available])
                if available < self.width:
                    image_data.extend([0] * (self.width - available))

        if is_talk_file(self.filepath):
            debug(f"TALK file: Final image data size {len(image_data)}")

        self.image_data = bytes(image_data)

    def to_pil_image(self) -> Image.Image:
        """Convert to a PIL Image.

        Returns:
            PIL Image object
        """
        # Create paletted image
        img = Image.frombytes("P", (self.width, self.height), self.image_data)

        # Apply palette
        img.putpalette(self.palette)

        return img

    def save_png(self, output_path: Path) -> None:
        """Save the image as a PNG file.

        Args:
            output_path: Path to save the PNG file
        """
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing file if it exists
        if output_path.exists():
            output_path.unlink()

        # Convert to PIL Image and save
        img = self.to_pil_image()
        img.save(output_path, "PNG")
        logger.info(f"Converted {self.filepath.name} to PNG")


def convert_pc8_pc4(filepath: Path, output_dir: Path, debug_mode: bool = False) -> bool:
    """Convert PC8/PC4 image to PNG.

    This is the main entry point for the converter, used by the tools package.

    Args:
        filepath: Path to image file
        output_dir: Output directory for converted files
        debug_mode: Enable debug output

    Returns:
        True if conversion successful
    """
    return convert_image(filepath, output_dir, debug_mode)


def convert_image(filepath: Path, output_dir: Path, debug_mode: bool = False) -> bool:
    """Convert PC8/256 image to PNG.

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
    if not filepath.name.lower().endswith((".pc8", ".256")):
        return False

    # Get file extension without dot and in lowercase
    ext = filepath.suffix.lower().replace(".", "")

    # Put files in their respective subdirectories
    output_path = output_dir / "images" / ext / f"{filepath.stem}.png"

    # Process image
    try:
        debug(f"\nProcessing file: {filepath.name}")

        # Parse and convert image
        pc8_image = PC8Image(filepath)
        pc8_image.save_png(output_path)
        return True

    except PCXFormatError as e:
        logger.warning(f"Invalid PC8 format in {filepath.name}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
