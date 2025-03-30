#!/usr/bin/env python3
"""
Raw image format analyzer.
Does a detailed byte-level analysis of image files without making format assumptions.
"""

from pathlib import Path
import struct


def dump_bytes(data: bytes, offset: int = 0, width: int = 16) -> str:
    """
    Create a detailed hex dump with ASCII representation.
    """
    result = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        # Hex values
        hex_values = " ".join(f"{b:02x}" for b in chunk)
        # ASCII representation (printable chars only)
        ascii_values = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        # Pad hex values for alignment
        hex_values = hex_values.ljust(width * 3)
        result.append(f"{offset + i:08x}  {hex_values}  |{ascii_values}|")
    return "\n".join(result)


def analyze_byte_patterns(data: bytes, min_length: int = 3) -> list[dict]:
    """
    Find repeating byte patterns in the data.
    """
    patterns = []
    for length in range(min_length, min(32, len(data))):
        for i in range(len(data) - length):
            pattern = data[i : i + length]
            # Look for immediate repetitions
            count = 1
            pos = i + length
            while pos + length <= len(data) and data[pos : pos + length] == pattern:
                count += 1
                pos += length
            if count > 1:
                patterns.append(
                    {
                        "offset": i,
                        "length": length,
                        "pattern": list(pattern),
                        "count": count,
                        "total_bytes": length * count,
                    }
                )
    return sorted(patterns, key=lambda x: x["total_bytes"], reverse=True)[:10]


def analyze_value_ranges(data: bytes) -> dict:
    """
    Analyze the range and distribution of byte values.
    """
    value_counts = {}
    ranges = {
        "0-31": 0,  # Control chars
        "32-127": 0,  # ASCII printable
        "128-191": 0,  # High ASCII
        "192-255": 0,  # Potential RLE markers
    }

    for b in data:
        value_counts[b] = value_counts.get(b, 0) + 1
        if b < 32:
            ranges["0-31"] += 1
        elif b < 128:
            ranges["32-127"] += 1
        elif b < 192:
            ranges["128-191"] += 1
        else:
            ranges["192-255"] += 1

    # Find most common values
    common_values = sorted([(v, k) for k, v in value_counts.items()], reverse=True)[:10]

    return {
        "ranges": ranges,
        "unique_values": len(value_counts),
        "most_common": [{"value": k, "count": v} for v, k in common_values],
    }


def find_potential_headers(data: bytes) -> list[dict]:
    """
    Look for potential header structures in the data.
    """
    headers = []

    # Look for common header markers
    markers = [
        (b"\x0a", "PCX-like"),
        (b"BM", "BMP-like"),
        (b"\xff\xd8", "JPEG-like"),
        (b"\x89PNG", "PNG-like"),
    ]

    for marker, desc in markers:
        pos = data.find(marker)
        if pos >= 0:
            headers.append({"offset": pos, "type": desc, "marker": list(marker)})

    # Look for potential dimension fields (16-bit values in reasonable ranges)
    for i in range(len(data) - 4):
        try:
            w = struct.unpack("<H", data[i : i + 2])[0]
            h = struct.unpack("<H", data[i + 2 : i + 4])[0]
            if 1 <= w <= 4096 and 1 <= h <= 4096:  # Reasonable image dimensions
                headers.append(
                    {
                        "offset": i,
                        "type": "Possible dimensions",
                        "values": {"width": w, "height": h},
                    }
                )
        except Exception as e:
            print(f"Error analyzing potential header at offset {i}: {e}")
            continue

    return headers


def analyze_file(filepath: Path) -> dict:
    """
    Perform detailed analysis of a file's binary content.
    """
    results = {
        "filename": filepath.name,
        "filesize": filepath.stat().st_size,
        "sections": [],
        "patterns": [],
        "byte_analysis": {},
        "potential_headers": [],
        "structure_hints": [],
    }

    try:
        with open(filepath, "rb") as f:
            data = f.read()

            # Analyze file in sections
            section_size = min(256, len(data))
            sections = [
                ("header", 0, section_size),
                (
                    "middle",
                    len(data) // 2 - section_size // 2,
                    len(data) // 2 + section_size // 2,
                ),
                ("end", max(0, len(data) - section_size), len(data)),
            ]

            for name, start, end in sections:
                section_data = data[start:end]
                results["sections"].append(
                    {
                        "name": name,
                        "offset": start,
                        "size": len(section_data),
                        "hex_dump": dump_bytes(section_data, start),
                    }
                )

            # Find repeating patterns
            results["patterns"] = analyze_byte_patterns(data)

            # Analyze byte value distribution
            results["byte_analysis"] = analyze_value_ranges(data)

            # Look for potential headers
            results["potential_headers"] = find_potential_headers(data)

            # Generate structure hints
            if results["byte_analysis"]["ranges"]["192-255"] > 0:
                results["structure_hints"].append(
                    "Contains bytes >= 192, possible RLE compression markers"
                )

            # Look for potential palette data (sequences of RGB triplets)
            for i in range(0, len(data) - 768, 768):
                rgb_triplets = data[i : i + 768]
                if all(
                    v < 64 for v in rgb_triplets
                ):  # Common for 6-bit color components
                    results["structure_hints"].append(
                        f"Possible 256-color palette at offset {i} "
                        "(768 bytes of RGB triplets with values < 64)"
                    )

            # Check for common section sizes
            if len(data) > 768:  # Size of a 256-color palette
                results["structure_hints"].append(
                    "File is large enough to contain a 256-color palette"
                )

    except Exception as e:
        results["error"] = str(e)

    return results
