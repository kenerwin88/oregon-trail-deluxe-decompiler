#!/usr/bin/env python3
"""
GXL (Graphics Library) Extractor for Oregon Trail DOS

This module provides tools for extracting and analyzing GXL (Graphics Library)
files from the Oregon Trail DOS game. It can:

1. Extract all files from a GXL archive while preserving their original format
2. Analyze GXL files to provide detailed information about their contents
3. Verify file integrity during extraction
4. Check for completeness to ensure all data is accounted for
5. Detect possible hidden files in gaps between known files

GXL Format Structure:
- Header section (0x00-0x88): Contains metadata about the file
- File table (0x89-?): list of files contained in the archive
  - Each entry contains filename, extension, offset, and size
  - First entry has special format (extension first)
  - Subsequent entries have name first, then extension
- File data: Raw file content at the offsets specified in the file table

This module is part of the Oregon Trail Decompilation Project, which aims to
reverse-engineer and document the original game's file formats and structure.

Usage:
    # Extract all files from OREGON.GXL to 'extracted' directory
    python gxl_extractor.py OREGON.GXL

    # Analyze without extracting
    python gxl_extractor.py OREGON.GXL --analyze

See help for more options:
    python gxl_extractor.py --help
"""

import os
import struct
import logging
import hashlib
from typing import BinaryIO, Optional
from collections import Counter
from dataclasses import dataclass

try:
    # When used as a module
    from .resource_extractor import ResourceExtractor, ResourceType, ResourceHeader
except ImportError:
    # When run as a script
    from resource_extractor import ResourceExtractor, ResourceType, ResourceHeader

# Define GXL-specific constants
GXL_FILE_TABLE_OFFSET = 0x89  # Offset where file table begins
GXL_HEADER_SIZE = GXL_FILE_TABLE_OFFSET  # Size of the header section
GXL_ENTRY_METADATA_SIZE = 5  # Size of metadata and separator after offset/size
GXL_SUPPORTED_IMAGE_EXTENSIONS = (".16", ".256")  # Supported image file extensions
GXL_PC_IMAGE_EXTENSIONS = (".PC4", ".PC8")  # PC image file extensions
GXL_ENTRY_NAME_SIZE = 8  # Size of name field in file table entry
GXL_ENTRY_EXT_SIZE = 5  # Size of extension field (including dot and null)
GXL_OFFSET_SIZE = 4  # Size of offset field (uint32)
GXL_SIZE_SIZE = 4  # Size of size field (uint32)

# Image format constants
IMAGE_MAX_WIDTH = 640  # Maximum valid image width
IMAGE_MAX_HEIGHT = 480  # Maximum valid image height
IMAGE_MIN_DIMENSION = 1  # Minimum valid dimension

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format="%(levelname).1s %(message)s",  # Shorter format with just first letter of level
)
logger = logging.getLogger(__name__)


def set_debug(enabled: bool):
    """Enable or disable debug logging"""
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)


@dataclass
class GXLEntry:
    """Represents an entry in the GXL file"""

    offset: int
    size: int
    width: int
    height: int
    bpp: int  # bits per pixel
    compressed: bool
    name: str

    @property
    def is_image(self) -> bool:
        """Check if this entry is an image file"""
        name_upper = self.name.upper()
        return name_upper.endswith(
            GXL_SUPPORTED_IMAGE_EXTENSIONS
        ) or name_upper.endswith(GXL_PC_IMAGE_EXTENSIONS)

    @property
    def file_type(self) -> str:
        """Get the file type based on extension"""
        if "." not in self.name:
            return "unknown"
        ext = self.name.split(".")[-1].upper()
        type_map = {
            "16": "image_16color",
            "256": "image_256color",
            "PC4": "image_pc4",
            "PC8": "image_pc8",
            "PCX": "image_pcx",
            "XMI": "music",
            "SND": "sound",
            "CTR": "text",
            "ANI": "animation",
            "GBT": "game_data",
            "GFT": "font",
            "TXT": "text",
        }
        return type_map.get(ext, f"other_{ext.lower()}")


class GXLExtractor(ResourceExtractor):
    """Extractor for GXL graphics library files"""

    def __init__(self, filename: str):
        super().__init__(filename)
        self.entries: list[GXLEntry] = []
        self._extraction_stats = Counter()  # Track statistics during extraction

    def read_header(self) -> Optional[ResourceHeader]:
        """Read GXL header and file table

        Returns:
            ResourceHeader if valid, None if invalid
        """
        try:
            with open(self.filename, "rb") as f:
                # Create header with basic info
                self.header = ResourceHeader(
                    b"GXL1", 1, self.file_size, ResourceType.GXL
                )

                # Process file table entries
                self._read_file_table(f)

                return self.header

        except Exception as e:
            logger.error(f"Error reading GXL header: {str(e)}")
            return None

    def _read_file_table(self, f: BinaryIO) -> None:
        """Read the GXL file table entries

        Args:
            f: Open file handle positioned at the start of the file
        """
        # Skip to first entry
        f.seek(GXL_FILE_TABLE_OFFSET)

        entry_index = 0
        while True:
            entry_start = f.tell()

            # Check if we've reached the end of the file table
            if not self._is_valid_entry_start(f):
                break

            try:
                # First entry has a special format
                if entry_start == GXL_FILE_TABLE_OFFSET:
                    entry = self._read_first_entry(f)
                else:
                    entry = self._read_normal_entry(f)

                # Validate entry data
                if entry.offset >= self.file_size or entry.size >= self.file_size:
                    logger.warning(
                        f"Invalid offset/size for {entry.name}: offset {entry.offset}, size {entry.size}, file size {self.file_size}"
                    )
                    continue

                # For image files, extract dimensions
                if entry.is_image:
                    self._read_image_dimensions(f, entry)

                # Add entry to list
                self.entries.append(entry)
                logger.info(
                    f"Found entry: {entry.name} at offset {entry.offset}, size {entry.size}"
                )
                entry_index += 1

            except Exception as e:
                logger.error(f"Error reading entry at offset {entry_start}: {str(e)}")
                # Skip to next entry or break if we can't recover
                next_entry = self._find_next_entry(f, entry_start + 1)
                if next_entry:
                    f.seek(next_entry)
                else:
                    break

    def _is_valid_entry_start(self, f: BinaryIO) -> bool:
        """Check if the current position is a valid entry start

        Args:
            f: Open file handle

        Returns:
            True if valid entry start, False otherwise
        """
        pos = f.tell()
        peek_data = f.read(1)
        f.seek(pos)  # Reset position

        return peek_data and peek_data[0] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ."

    def _find_next_entry(self, f: BinaryIO, start_pos: int) -> Optional[int]:
        """Find the next valid entry start position

        Args:
            f: Open file handle
            start_pos: Position to start searching from

        Returns:
            Position of next entry, or None if not found
        """
        f.seek(start_pos)
        data = f.read(1024)  # Read a chunk to search

        for i, byte in enumerate(data):
            if byte in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ.":
                # Verify this is actually an entry start
                f.seek(start_pos + i)
                if self._is_valid_entry_start(f):
                    return start_pos + i

        return None  # No valid entry found

    def _read_first_entry(self, f: BinaryIO) -> GXLEntry:
        """Read the first GXL file table entry (special format)

        Args:
            f: Open file handle positioned at the start of the entry

        Returns:
            GXLEntry object
        """
        # Read extension (4 chars + null)
        ext_data = f.read(5)
        if len(ext_data) < 5 or ext_data[-1] != 0 or not ext_data[1:4].isascii():
            raise ValueError("Invalid extension data in first entry")

        ext = ext_data[1:4].decode("ascii")  # Skip the dot

        # Read offset and size
        offset = struct.unpack("<I", f.read(4))[0]
        size = struct.unpack("<I", f.read(4))[0]

        # Skip metadata and separator
        f.read(GXL_ENTRY_METADATA_SIZE)

        # For first entry, name is always INDEX
        name = "INDEX"
        filename = f"{name}.{ext}"

        return GXLEntry(offset, size, 0, 0, 8, False, filename)

    def _read_normal_entry(self, f: BinaryIO) -> GXLEntry:
        """Read a normal GXL file table entry

        Args:
            f: Open file handle positioned at the start of the entry

        Returns:
            GXLEntry object
        """
        # Read name (8 chars)
        name_data = f.read(8)
        if len(name_data) < 8 or not name_data.rstrip(b" \0").isascii():
            raise ValueError("Invalid name data")

        name = name_data.rstrip(b" \0").decode("ascii")

        # Read extension (4 chars + null)
        ext_data = f.read(5)
        if len(ext_data) < 5 or ext_data[-1] != 0 or not ext_data[1:4].isascii():
            raise ValueError(f"Invalid extension data for {name}")

        ext = ext_data[1:4].decode("ascii")  # Skip the dot

        # Read offset and size
        offset = struct.unpack("<I", f.read(4))[0]
        size = struct.unpack("<I", f.read(4))[0]

        # Skip metadata and separator
        f.read(GXL_ENTRY_METADATA_SIZE)

        # Combine name and extension
        filename = f"{name}.{ext}"

        return GXLEntry(offset, size, 0, 0, 8, False, filename)

    def _is_valid_dimension(self, width: int, height: int) -> bool:
        """Check if image dimensions are within valid range

        Args:
            width: Image width
            height: Image height

        Returns:
            True if dimensions are valid, False otherwise
        """
        return (
            IMAGE_MIN_DIMENSION <= width <= IMAGE_MAX_WIDTH
            and IMAGE_MIN_DIMENSION <= height <= IMAGE_MAX_HEIGHT
        )

    def _read_standard_image_dimensions(self, f: BinaryIO, entry: GXLEntry) -> bool:
        """Read dimensions from standard image formats (.16, .256)

        Args:
            f: Open file handle positioned at start of image data
            entry: GXLEntry to update with dimension information

        Returns:
            True if successful, False otherwise
        """
        # Standard image formats have dimensions as first 4 bytes (2 uint16)
        dim_data = f.read(4)
        if len(dim_data) != 4:
            return False

        width, height = struct.unpack("<HH", dim_data)
        if not self._is_valid_dimension(width, height):
            return False

        # Update entry with dimension information
        entry.width = width
        entry.height = height
        entry.bpp = 8 if entry.name.upper().endswith(".256") else 4
        entry.compressed = True

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Image dimensions for {entry.name}: {width}x{height}, {entry.bpp}bpp"
            )

        return True

    def _read_pc_image_dimensions(self, f: BinaryIO, entry: GXLEntry) -> bool:
        """Read dimensions from PC image formats (PC4, PC8)

        Args:
            f: Open file handle positioned at start of image data
            entry: GXLEntry to update with dimension information

        Returns:
            True if successful, False otherwise
        """
        # PC image formats have header with dimensions in first 4 bytes
        header_data = f.read(8)  # Read header
        if len(header_data) != 8:
            return False

        width, height = struct.unpack("<HH", header_data[0:4])
        if not self._is_valid_dimension(width, height):
            return False

        # Update entry with dimension information
        entry.width = width
        entry.height = height
        entry.bpp = 8 if entry.name.upper().endswith(".PC8") else 4
        entry.compressed = True

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"PC image dimensions for {entry.name}: {width}x{height}, {entry.bpp}bpp"
            )

        return True

    def _read_image_dimensions(self, f: BinaryIO, entry: GXLEntry) -> None:
        """Read dimensions from an image file entry

        Args:
            f: Open file handle
            entry: GXLEntry to update with dimension information
        """
        # Save current position
        curr_pos = f.tell()

        try:
            # Jump to file data
            f.seek(entry.offset)

            name_upper = entry.name.upper()

            # Different handling based on image type
            if name_upper.endswith(GXL_SUPPORTED_IMAGE_EXTENSIONS):
                self._read_standard_image_dimensions(f, entry)

            elif name_upper.endswith(GXL_PC_IMAGE_EXTENSIONS):
                self._read_pc_image_dimensions(f, entry)

        except Exception as e:
            logger.debug(f"Failed to read dimensions for {entry.name}: {str(e)}")
        finally:
            # Restore position
            f.seek(curr_pos)

    def extract_file_data(self, entry: GXLEntry, f: BinaryIO) -> Optional[bytes]:
        """Extract raw file data from the GXL file

        Args:
            entry: GXLEntry describing the file
            f: Open binary file handle

        Returns:
            Raw file data if successful, None if failed
        """
        try:
            # Seek to file data
            f.seek(entry.offset)

            # Read entire file data
            data = f.read(entry.size)
            if len(data) != entry.size:
                raise ValueError(f"Failed to read {entry.size} bytes for {entry.name}")

            return data

        except Exception as e:
            logger.error(f"Error extracting {entry.name}: {str(e)}")
            return None

    def extract_all_files(self, output_dir: str, verify_integrity: bool = True) -> bool:
        """Extract all files from GXL file preserving original format

        Args:
            output_dir: Directory to save extracted files
            verify_integrity: Whether to verify file integrity after extraction

        Returns:
            bool: True if extraction successful, False otherwise
        """
        # Reset extraction statistics
        self._extraction_stats.clear()

        # Make sure we've read the header
        if not self.header:
            if not self.read_header():
                logger.error("Failed to read GXL header")
                return False

        if not self.entries:
            logger.error("No entries found in GXL file")
            return False

        try:
            with open(self.filename, "rb") as f:
                total_entries = len(self.entries)

                # Create output directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)

                logger.info(
                    f"Extracting {total_entries} files from {os.path.basename(self.filename)} to {output_dir}"
                )

                for i, entry in enumerate(self.entries, 1):
                    try:
                        # Extract file data
                        data = self.extract_file_data(entry, f)
                        if not data:
                            logger.error(f"Failed to extract data for {entry.name}")
                            self._extraction_stats["failed"] += 1
                            continue

                        # Calculate checksum for integrity verification
                        if verify_integrity:
                            file_hash = hashlib.md5(data).hexdigest()

                        # Save file data
                        output_path = os.path.join(output_dir, entry.name)
                        with open(output_path, "wb") as out:
                            out.write(data)

                        # Verify integrity if requested
                        if verify_integrity:
                            with open(output_path, "rb") as check_file:
                                check_data = check_file.read()
                                check_hash = hashlib.md5(check_data).hexdigest()

                                if check_hash != file_hash:
                                    logger.error(
                                        f"Integrity check failed for {entry.name} - checksum mismatch"
                                    )
                                    logger.debug(
                                        f"  Expected: {file_hash}, Got: {check_hash}"
                                    )
                                    self._extraction_stats["integrity_failed"] += 1
                                    continue

                        # Update statistics
                        if entry.is_image:
                            if i % 10 == 0 or logger.isEnabledFor(logging.DEBUG):
                                logger.info(f"Extracted {entry.name}")
                            self._extraction_stats["extracted"] += 1
                        else:
                            if i % 10 == 0 or logger.isEnabledFor(logging.DEBUG):
                                logger.info(f"Copied {entry.name}")
                            self._extraction_stats["copied"] += 1

                    except Exception as e:
                        logger.error(f"Error processing {entry.name}: {str(e)}")
                        self._extraction_stats["failed"] += 1

            # Report extraction results
            total = sum(self._extraction_stats.values())
            integrity_fails = self._extraction_stats.get("integrity_failed", 0)

            success = self._extraction_stats["failed"] == 0 and integrity_fails == 0

            if success:
                logger.info(
                    f"Successfully extracted all {total} files "
                    f"({self._extraction_stats['extracted']} images, "
                    f"{self._extraction_stats['copied']} other files)"
                )
                return True
            else:
                failures = self._extraction_stats["failed"]
                logger.warning(
                    f"Extracted {total - failures - integrity_fails} of {total} files "
                    f"({failures} failed, {integrity_fails} integrity checks failed)"
                )
                return False

        except Exception as e:
            logger.error(f"Error extracting GXL file: {str(e)}")
            return False

    def get_extraction_stats(self) -> dict[str, int]:
        """Get statistics from the last extraction operation

        Returns:
            dict containing extraction statistics
        """
        return dict(self._extraction_stats)

    def verify_completeness(self) -> dict:
        """Verify if all data in the file has been accounted for

        This method checks for:
        1. Gaps between file entries (unaccounted data regions)
        2. Checks if total extracted size + metadata matches file size
        3. Analyzes any unaccounted regions for potential file signatures

        Returns:
            dict with completeness check results
        """
        if not self.entries:
            return {"complete": False, "reason": "No entries found in file"}

        # Sort entries by offset
        sorted_entries = sorted(self.entries, key=lambda e: e.offset)

        # Calculate header and file table size
        first_data_offset = sorted_entries[0].offset
        file_table_size = first_data_offset - GXL_FILE_TABLE_OFFSET

        # Track gaps between entries
        gaps = []
        unaccounted_bytes = 0

        # Check for gaps between adjacent entries
        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_entry = sorted_entries[i + 1]

            current_end = current.offset + current.size
            next_start = next_entry.offset

            if current_end < next_start:
                # Found a gap
                gap_size = next_start - current_end
                unaccounted_bytes += gap_size
                gaps.append(
                    {
                        "after_file": current.name,
                        "before_file": next_entry.name,
                        "start_offset": current_end,
                        "end_offset": next_start - 1,
                        "size": gap_size,
                    }
                )

        # Check if there's data after the last file
        last_entry = sorted_entries[-1]
        last_data_end = last_entry.offset + last_entry.size
        if last_data_end < self.file_size:
            gap_size = self.file_size - last_data_end
            unaccounted_bytes += gap_size
            gaps.append(
                {
                    "after_file": last_entry.name,
                    "before_file": "EOF",
                    "start_offset": last_data_end,
                    "end_offset": self.file_size - 1,
                    "size": gap_size,
                }
            )

        # Calculate accounted size (header + file table + all files)
        accounted_size = first_data_offset + sum(entry.size for entry in self.entries)
        unaccounted_pct = (
            (unaccounted_bytes / self.file_size) * 100 if self.file_size > 0 else 0
        )

        # Check for file signatures in gaps if they exist
        signatures_found = []
        if gaps and unaccounted_bytes > 16:  # Only check substantial gaps
            try:
                with open(self.filename, "rb") as f:
                    for gap in gaps:
                        if gap["size"] < 16:  # Skip tiny gaps
                            continue

                        # Read the first 16 bytes of the gap
                        f.seek(gap["start_offset"])
                        header = f.read(min(16, gap["size"]))

                        # Check for common file signatures
                        file_type = self._identify_signature(header)
                        if file_type:
                            signatures_found.append(
                                {
                                    "offset": gap["start_offset"],
                                    "size": gap["size"],
                                    "potential_type": file_type,
                                }
                            )
            except Exception as e:
                logger.error(f"Error checking gap signatures: {str(e)}")

        return {
            "complete": unaccounted_bytes == 0,
            "file_size": self.file_size,
            "header_size": GXL_FILE_TABLE_OFFSET,
            "file_table_size": file_table_size,
            "total_entries": len(self.entries),
            "accounted_bytes": accounted_size,
            "unaccounted_bytes": unaccounted_bytes,
            "unaccounted_percentage": unaccounted_pct,
            "gaps": gaps,
            "potential_hidden_files": signatures_found,
        }

    def _identify_signature(self, header: bytes) -> Optional[str]:
        """Try to identify a file type from its signature bytes

        Args:
            header: First bytes of potential file

        Returns:
            String describing the file type if recognized, None otherwise
        """
        signatures = {
            b"\x89PNG\r\n\x1a\n": "PNG image",
            b"GIF8": "GIF image",
            b"BM": "BMP image",
            b"PK\x03\x04": "ZIP archive",
            b"MZ": "EXE file",
            b"ID3": "MP3 audio",
            b"RIFF": "WAV or AVI file",
            b"\xff\xd8\xff": "JPEG image",
            b"%PDF": "PDF document",
        }

        for sig, file_type in signatures.items():
            if header.startswith(sig):
                return file_type

        # Check for text files
        if all(byte < 127 and byte >= 32 or byte in (10, 13, 9) for byte in header):
            return "Possible text file"

        return None

    def analyze(self) -> dict:
        """Analyze GXL file and return detailed information

        Returns:
            dict containing analysis results
        """
        # Make sure we've read the header
        if not self.header:
            if not self.read_header():
                return {"error": "Failed to read GXL header"}

        result = super().analyze()

        # Count file types
        file_types = Counter(entry.file_type for entry in self.entries)

        # Calculate statistics
        image_entries = [entry for entry in self.entries if entry.is_image]
        total_image_size = sum(entry.size for entry in image_entries)
        avg_image_size = total_image_size / len(image_entries) if image_entries else 0

        # Add file statistics
        result.update(
            {
                "num_entries": len(self.entries),
                "total_file_size": sum(entry.size for entry in self.entries),
                "file_types": dict(file_types),
                "images": {
                    "count": len(image_entries),
                    "total_size": total_image_size,
                    "avg_size": avg_image_size,
                    "dimensions": {
                        "min_width": min(
                            (entry.width for entry in image_entries), default=0
                        ),
                        "max_width": max(
                            (entry.width for entry in image_entries), default=0
                        ),
                        "min_height": min(
                            (entry.height for entry in image_entries), default=0
                        ),
                        "max_height": max(
                            (entry.height for entry in image_entries), default=0
                        ),
                    },
                },
                "entries": [
                    {
                        "name": entry.name,
                        "type": entry.file_type,
                        "size": entry.size,
                        "width": entry.width if entry.is_image else 0,
                        "height": entry.height if entry.is_image else 0,
                        "bpp": entry.bpp if entry.is_image else 0,
                        "compressed": entry.compressed,
                    }
                    for entry in self.entries
                ],
            }
        )

        # Add completeness check results
        result["completeness"] = self.verify_completeness()

        return result
