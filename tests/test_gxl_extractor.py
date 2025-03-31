#!/usr/bin/env python3
"""
Tests for the GXL archive extractor.

This module tests the GXL archive extraction functionality, including:
- Archive analysis
- File extraction
- Integrity verification
- Error handling
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from tools.gxl_extractor import GXLExtractor

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class GXLExtractorTest(unittest.TestCase):
    """Test GXL archive extraction functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.output_dir = cls.temp_dir / "extracted"
        cls.output_dir.mkdir(exist_ok=True)

        # Original GXL file
        cls.gxl_file = Path(parent_dir) / "original_game" / "OREGON.GXL"

        # Try alternate locations if not found
        if not cls.gxl_file.exists():
            alternate_locations = [
                Path(parent_dir) / "OREGON.GXL",
                Path(parent_dir).parent / "OREGON.GXL",
            ]
            for alt in alternate_locations:
                if alt.exists():
                    cls.gxl_file = alt
                    break

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Set up each test"""
        if not self.gxl_file.exists():
            self.skipTest(f"GXL file not found at {self.gxl_file}")

    def test_archive_analysis(self):
        """Test GXL archive analysis"""
        extractor = GXLExtractor(self.gxl_file)
        info = extractor.analyze()

        # Verify basic archive information
        self.assertIsNotNone(info)
        self.assertEqual(info["type"], "GXL")
        self.assertGreater(info["num_entries"], 0)
        self.assertGreater(info["total_file_size"], 0)

        # Verify file type statistics
        self.assertIn("file_types", info)
        self.assertIsInstance(info["file_types"], dict)

        # Verify image statistics
        self.assertIn("images", info)
        self.assertIn("count", info["images"])
        self.assertIn("total_size", info["images"])
        self.assertIn("avg_size", info["images"])
        self.assertIn("dimensions", info["images"])

        # Verify completeness information
        self.assertIn("completeness", info)
        self.assertIn("complete", info["completeness"])
        self.assertIn("unaccounted_bytes", info["completeness"])
        self.assertIn("unaccounted_percentage", info["completeness"])

    def test_file_extraction(self):
        """Test extracting files from GXL archive"""
        extractor = GXLExtractor(self.gxl_file)

        # Extract all files
        result = extractor.extract_all_files(self.output_dir)
        self.assertTrue(result)

        # Verify some known files exist
        expected_files = ["BANKS.PC8", "DEATH.XMI", "BEEP.SND", "GUIDE.CTR"]

        for filename in expected_files:
            file_path = self.output_dir / filename
            self.assertTrue(
                file_path.exists(),
                f"Expected file {filename} not found in extracted files",
            )

    def test_integrity_verification(self):
        """Test file integrity verification during extraction"""
        extractor = GXLExtractor(self.gxl_file)

        # Extract with integrity verification
        result = extractor.extract_all_files(self.output_dir, verify_integrity=True)
        self.assertTrue(result)

        # Get archive analysis
        info = extractor.analyze()

        # Verify extracted file count matches archive entry count
        extracted_count = sum(1 for _ in self.output_dir.glob("*"))
        self.assertEqual(extracted_count, info["num_entries"])

    def test_extraction_to_nonexistent_directory(self):
        """Test extraction to a directory that doesn't exist"""
        extractor = GXLExtractor(self.gxl_file)
        output_dir = self.temp_dir / "nonexistent"

        # Should create directory and extract successfully
        result = extractor.extract_all_files(output_dir)
        self.assertTrue(result)
        self.assertTrue(output_dir.exists())
        self.assertGreater(sum(1 for _ in output_dir.glob("*")), 0)


if __name__ == "__main__":
    unittest.main()
