#!/usr/bin/env python3
"""
SND audio format converter for Oregon Trail files.
Converts SND files to WAV format.

Format details:
- Raw 8-bit unsigned PCM audio
- Mono channel
- 11025 Hz sample rate (standard PC speaker rate)
- No header, just raw sample data
"""

import logging
from pathlib import Path
import wave

logger = logging.getLogger(__name__)


def convert_snd(filepath: Path, output_dir: Path) -> bool:
    """Convert SND to WAV

    Args:
        filepath: Path to SND file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith(".SND"):
            return False

        output_path = output_dir / "sounds" / f"{filepath.stem}.wav"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Read raw audio data
        with open(filepath, "rb") as f:
            data = f.read()

        # Create WAV file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(1)  # 8-bit
            wav.setframerate(11025)  # Standard PC speaker rate
            wav.writeframes(data)

        logger.info(f"Converted {filepath.name} to WAV")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
