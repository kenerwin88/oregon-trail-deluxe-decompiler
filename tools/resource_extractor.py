#!/usr/bin/env python3
"""
Base Resource Extractor for Oregon Trail DOS
Provides common functionality for extracting various resource types.
"""

import os
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class ResourceType(Enum):
    """Enumeration of known resource types"""

    GXL = auto()  # Graphics library
    PC8 = auto()  # 8-bit image
    PC4 = auto()  # 4-bit image
    PCC = auto()  # Compressed image
    XMI = auto()  # MIDI music
    SND = auto()  # Sound effect
    LST = auto()  # Data list
    CNF = auto()  # Configuration
    PF = auto()  # Product info

    def __str__(self):
        """String representation of the resource type"""
        return self.name

    def __repr__(self):
        """String representation for debug/logging"""
        return f"ResourceType.{self.name}"


@dataclass
class ResourceHeader:
    """Base class for resource file headers"""

    magic: bytes
    version: int
    size: int
    type: ResourceType


class ResourceExtractor:
    """Base class for resource extraction"""

    def __init__(self, filename: str):
        """Initialize the resource extractor

        Args:
            filename: Path to the resource file
        """
        self.filename = filename
        self.file_size = os.path.getsize(filename)
        self.header: Optional[ResourceHeader] = None

    def analyze(self) -> dict:
        """Analyze the resource file and return information about its contents

        Returns:
            dict containing analysis results
        """
        return {
            "filename": self.filename,
            "size": self.file_size,
            "type": str(self.header.type) if self.header else "Unknown",
            "version": self.header.version if self.header else 0,
        }
