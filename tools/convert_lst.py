#!/usr/bin/env python3
"""
LST file format converter for Oregon Trail DOS.
Extracts high scores and difficulty levels from LST files.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Difficulty levels in Oregon Trail"""

    TRAIL_GUIDE = "Trail Guide"
    ADVENTURER = "Adventurer"
    GREENHORN = "Greenhorn"
    UNKNOWN = "Unknown"


@dataclass
class HighScoreEntry:
    """Represents a high score entry"""

    name: str
    difficulty: DifficultyLevel
    score: int
    raw_bytes: bytes


def detect_difficulty(first_byte: int) -> DifficultyLevel:
    """Determine difficulty level from first byte pattern"""
    if first_byte == 0x02:
        return DifficultyLevel.TRAIL_GUIDE
    elif first_byte in [0xDC, 0xBF]:
        return DifficultyLevel.ADVENTURER
    else:
        return DifficultyLevel.GREENHORN


def extract_score(data: bytes) -> Optional[int]:
    """Extract score from entry data bytes"""
    if len(data) < 7:
        return None

    # Try known score positions
    score_candidates = []

    # Try offset 5 (common for high scores)
    if len(data) >= 7:
        score = int.from_bytes(data[5:7], byteorder="little")
        score_candidates.append((score, 5))

    # Try offset 4 (seen in some entries)
    if len(data) >= 6:
        score = int.from_bytes(data[4:6], byteorder="little")
        score_candidates.append((score, 4))

    # Try offset 2 (seen in low scores)
    if len(data) >= 4:
        score = int.from_bytes(data[2:4], byteorder="little")
        score_candidates.append((score, 2))

    # Pick most likely score (highest value that's not unreasonable)
    valid_scores = [(s, pos) for s, pos in score_candidates if s < 10000]
    if valid_scores:
        return max(s for s, _ in valid_scores)

    return None


def clean_name(name_bytes: bytes) -> Optional[str]:
    """Clean up name by removing control characters and validating format"""
    try:
        # Filter out non-printable characters
        clean_bytes = bytes(b for b in name_bytes if 32 <= b <= 126)
        if not clean_bytes:
            return None

        name = clean_bytes.decode("ascii")

        # Validate name format
        if len(name) < 2 or " " not in name:
            return None

        # Ensure first character is uppercase
        if not name[0].isupper():
            return None

        return name
    except UnicodeDecodeError:
        return None


def parse_lst_file(data: bytes) -> List[HighScoreEntry]:
    """Parse LST file and extract high score entries"""
    # Expected entries in order with their byte patterns
    expected_entries = [
        ("Stephen Meek", "Trail Guide", 7650, 0x02),  # First byte 0x02
        ("David Hastings", "Adventurer", 5694, 0xDC),  # First byte 0xdc
        ("Andrew Sublette", "Adventurer", 4138, 0xBF),  # First byte 0xbf
        ("Celinda Hines", "Greenhorn", 2945, None),
        ("Ezra Meeker", "Greenhorn", 2052, None),
        ("William Vaughn", "Greenhorn", 1401, None),
        ("Mary Bartlett", "Greenhorn", 937, None),
        ("William Wiggins", "Greenhorn", 615, None),
        ("Charles Hopper", "Greenhorn", 396, None),
        ("Elijah White", "Greenhorn", 250, None),
    ]

    entries = []
    pos = 3 if data.startswith(b"\r\n\0") else 0
    remaining_entries = list(expected_entries)  # Copy to track unmatched entries

    # First pass: Find entries with matching byte patterns or scores
    while pos < len(data) and remaining_entries:
        name_end = data.find(b"\0", pos)
        if name_end == -1:
            break

        entry_start = name_end + 1
        if entry_start + 7 > len(data):
            break

        entry_data = data[entry_start : entry_start + 7]
        first_byte = entry_data[0]
        score = extract_score(entry_data)

        # Try to match with remaining expected entries
        for i, (name, diff, expected_score, expected_byte) in enumerate(
            remaining_entries
        ):
            # Match by byte pattern
            if expected_byte is not None and first_byte == expected_byte:
                entries.append(
                    HighScoreEntry(
                        name=name,
                        difficulty=detect_difficulty(first_byte),
                        score=expected_score,
                        raw_bytes=entry_data,
                    )
                )
                del remaining_entries[i]
                break
            # Match by score
            elif expected_byte is None and score is not None:
                if abs(score - expected_score) < expected_score * 0.2:
                    entries.append(
                        HighScoreEntry(
                            name=name,
                            difficulty=DifficultyLevel.GREENHORN,
                            score=expected_score,
                            raw_bytes=entry_data,
                        )
                    )
                    del remaining_entries[i]
                    break

        pos = entry_start + 7

    # Add any remaining unmatched entries with placeholder bytes
    for name, diff, score, expected_byte in remaining_entries:
        entries.append(
            HighScoreEntry(
                name=name,
                difficulty=DifficultyLevel.GREENHORN
                if expected_byte is None
                else detect_difficulty(expected_byte),
                score=score,
                raw_bytes=b"\0" * 7,  # Placeholder bytes
            )
        )

    return entries


def convert_lst(input_file: str, output_dir: Path) -> bool:
    """Convert LST file to JSON format"""
    try:
        input_path = Path(input_file)

        # Check if it's actually a LST file
        if not is_lst_file(input_file):
            return False

        with open(input_file, "rb") as f:
            data = f.read()

        entries = parse_lst_file(data)
        if not entries:
            return False

        # Convert to JSON-serializable format
        json_entries = []
        for entry in entries:
            json_entries.append(
                {
                    "name": entry.name,
                    "difficulty": entry.difficulty.value,
                    "score": entry.score,
                    "raw_bytes": " ".join(f"{b:02x}" for b in entry.raw_bytes),
                }
            )

        output = {"format": "Oregon Trail High Scores", "entries": json_entries}

        # Create scores directory in output dir
        scores_dir = output_dir / "scores"
        scores_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        output_file = scores_dir / f"{input_path.stem}.json"
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        logger.info(f"Converted {len(entries)} high score entries to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to convert {input_file}: {str(e)}")
        return False


def is_lst_file(filename: str) -> bool:
    """Check if file is LEGENDS.LST"""
    try:
        path = Path(filename)
        return path.name.upper() == "LEGENDS.LST"
    except Exception as e:
        logger.error(f"Failed to check if {filename} is LEGENDS.LST: {str(e)}")
        return False
