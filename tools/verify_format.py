#!/usr/bin/env python3
"""
Image format verification tool.
Analyzes image files to determine their actual format and validate assumptions.
"""

from pathlib import Path
import struct


def analyze_pcx_header(header: bytes) -> dict:
    """
    Analyze PCX header fields according to format specification.
    """
    if len(header) < 128:
        return {"error": "Header too short"}

    try:
        results = {
            "manufacturer": header[0],  # Should be 0x0A
            "version": header[1],  # 0=v2.5, 2=v2.8 w/palette, 3=v2.8 wo/palette, 5=v3.0
            "encoding": header[2],  # 1=RLE
            "bits_per_pixel": header[3],  # 1,2,4,8
            "window": {
                "xmin": struct.unpack("<H", header[4:6])[0],
                "ymin": struct.unpack("<H", header[6:8])[0],
                "xmax": struct.unpack("<H", header[8:10])[0],
                "ymax": struct.unpack("<H", header[10:12])[0],
            },
            "dpi": {
                "horizontal": struct.unpack("<H", header[12:14])[0],
                "vertical": struct.unpack("<H", header[14:16])[0],
            },
            "palette16": list(header[16:64]),  # 16-color palette
            "reserved": header[64],  # Should be 0
            "color_planes": header[65],  # Number of color planes
            "bytes_per_line": struct.unpack("<H", header[66:68])[0],  # Must be even
            "palette_type": struct.unpack("<H", header[68:70])[
                0
            ],  # 1=Color/BW, 2=Grayscale
            "padding": list(header[70:128]),  # Remaining header bytes
        }

        # Calculate dimensions
        results["dimensions"] = {
            "width": results["window"]["xmax"] - results["window"]["xmin"] + 1,
            "height": results["window"]["ymax"] - results["window"]["ymin"] + 1,
        }

        return results
    except Exception as e:
        return {"error": f"Header parsing failed: {str(e)}"}


def analyze_custom_header(header: bytes) -> dict:
    """
    Analyze potential custom format header (assumed 12 bytes).
    """
    if len(header) < 12:
        return {"error": "Header too short"}

    try:
        results = {
            "metadata": list(header[0:4]),  # Expected: [0x0A, 0x05, 0x01, bit_depth]
            "dimensions": {
                "width": struct.unpack("<H", header[4:6])[0],
                "height": struct.unpack("<H", header[6:8])[0],
            },
            "extra": list(header[8:12]),  # Additional header bytes
        }
        return results
    except Exception as e:
        return {"error": f"Header parsing failed: {str(e)}"}


def analyze_rle_sample(data: bytes, offset: int, sample_size: int = 32) -> dict:
    """
    Analyze a sample of potentially RLE-compressed data.
    """
    results = {"compression_markers": [], "byte_frequency": {}, "patterns": []}

    sample = data[offset : offset + sample_size]

    # Look for PCX RLE markers (bytes >= 192)
    for i, byte in enumerate(sample):
        if byte >= 192:
            results["compression_markers"].append(
                {
                    "offset": offset + i,
                    "marker": byte,
                    "count": byte & 0x3F,
                    "next_byte": sample[i + 1] if i + 1 < len(sample) else None,
                }
            )

        # Track byte frequency
        results["byte_frequency"][byte] = results["byte_frequency"].get(byte, 0) + 1

        # Look for repeating patterns
        if i > 0:
            if sample[i] == sample[i - 1]:
                pattern = {"start": offset + i - 1, "value": sample[i], "count": 2}
                while i + 1 < len(sample) and sample[i + 1] == sample[i]:
                    pattern["count"] += 1
                    i += 1
                if pattern["count"] > 2:
                    results["patterns"].append(pattern)

    return results


def verify_format(filepath: Path) -> dict:
    """
    Analyze a file to determine its format and validate assumptions.
    """
    results = {
        "filename": filepath.name,
        "filesize": filepath.stat().st_size,
        "format_confidence": {"pcx": 0, "custom": 0},
        "header_analysis": {},
        "compression_analysis": {},
        "warnings": [],
        "recommendations": [],
    }

    try:
        with open(filepath, "rb") as f:
            # Read potential headers
            header = f.read(128)  # PCX header size

            # Check for PCX signature
            if header[0] == 0x0A:
                results["format_confidence"]["pcx"] += 30
                results["header_analysis"]["pcx"] = analyze_pcx_header(header)

                # Validate PCX header fields
                if header[2] == 1:  # RLE encoding
                    results["format_confidence"]["pcx"] += 10
                if header[1] in [0, 2, 3, 5]:  # Valid version
                    results["format_confidence"]["pcx"] += 10

            # Check for custom format signature
            if header[0:3] == b"\x0a\x05\x01":
                results["format_confidence"]["custom"] += 30
                results["header_analysis"]["custom"] = analyze_custom_header(
                    header[:12]
                )

                # Validate custom header fields
                if header[3] in [4, 8]:  # Expected bit depths
                    results["format_confidence"]["custom"] += 10

            # Analyze potential RLE compression
            f.seek(
                128
                if results["format_confidence"]["pcx"]
                > results["format_confidence"]["custom"]
                else 12
            )
            data = f.read(32)  # Sample for compression analysis
            results["compression_analysis"] = analyze_rle_sample(data, 0)

            # Generate warnings and recommendations
            if (
                results["format_confidence"]["pcx"] < 20
                and results["format_confidence"]["custom"] < 20
            ):
                results["warnings"].append("Low confidence in format detection")

            if (
                results["format_confidence"]["pcx"] > 0
                and results["format_confidence"]["custom"] > 0
            ):
                results["warnings"].append("File matches multiple format signatures")

            if len(results["compression_analysis"]["compression_markers"]) == 0:
                results["warnings"].append("No RLE compression markers found in sample")

            # Add recommendations
            if (
                results["format_confidence"]["pcx"]
                > results["format_confidence"]["custom"]
            ):
                results["recommendations"].append("Consider using standard PCX decoder")
            elif (
                results["format_confidence"]["custom"]
                > results["format_confidence"]["pcx"]
            ):
                results["recommendations"].append(
                    "Consider using custom format decoder"
                )

    except Exception as e:
        results["error"] = str(e)

    return results
