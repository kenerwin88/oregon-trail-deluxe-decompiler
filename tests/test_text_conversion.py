#!/usr/bin/env python3
"""
Tests for text format converter.

This module tests the text conversion functionality, including:
- Converting CTR and TXT files to UTF-8
- Handling various text encoding scenarios
"""

import sys
import unittest
import tempfile
import shutil
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from tools.convert_text import convert_text


class TextConverterTest(unittest.TestCase):
    """Test text file conversion functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.output_dir = cls.temp_dir / "output"
        cls.output_dir.mkdir(exist_ok=True)

        # Original text files directory
        cls.raw_dir = Path(parent_dir) / "raw_extracted"
        
        # Create a test text file
        cls.test_txt_file = cls.temp_dir / "TEST_PLAIN.TXT"
        with open(cls.test_txt_file, "w", encoding="ascii") as f:
            f.write("This is a test text file for Oregon Trail.\n")
            f.write("It contains sample text for conversion testing.\n")
            
        # Create a test CTR file (which is also text)
        cls.test_ctr_file = cls.temp_dir / "TEST.CTR"
        with open(cls.test_ctr_file, "w", encoding="ascii") as f:
            f.write("17,This is a comment\n")
            f.write("10,This is some text content\n")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        shutil.rmtree(cls.temp_dir)

    def test_convert_txt_file(self):
        """Test converting a TXT file to UTF-8"""
        # Use the already created file from setUpClass
        result = convert_text(self.test_txt_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "text" / "TEST_PLAIN.txt"
        self.assertTrue(output_path.exists())
        
        # Verify file content is preserved
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("This is a test text file for Oregon Trail", content)
        self.assertIn("It contains sample text for conversion testing", content)
        
        # Verify encoding is UTF-8
        with open(output_path, "rb") as f:
            raw_bytes = f.read()
        
        # UTF-8 files without BOM won't have special markers, but should be readable as UTF-8
        try:
            decoded = raw_bytes.decode("utf-8")
            self.assertIsNotNone(decoded)
        except UnicodeDecodeError:
            self.fail("Output file is not valid UTF-8")

    def test_convert_ctr_file(self):
        """Test converting a CTR file to UTF-8"""
        result = convert_text(self.test_ctr_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "text" / "TEST.txt"
        self.assertTrue(output_path.exists())
        
        # Verify file content is preserved
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("17,This is a comment", content)
        self.assertIn("10,This is some text content", content)

    def test_convert_real_text_file(self):
        """Test converting a real text file if available"""
        # Try to find a real text file
        real_txt_files = list(self.raw_dir.glob("*.TXT")) + list(self.raw_dir.glob("*.CTR"))
        
        if not real_txt_files:
            self.skipTest("No real text files found to test")
            
        # Test with first found text file
        txt_file = real_txt_files[0]
        result = convert_text(txt_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "text" / f"{txt_file.stem}.txt"
        self.assertTrue(output_path.exists())
        
        # Verify file exists and has content
        self.assertGreater(os.path.getsize(output_path), 0)
        
        # Verify file is valid UTF-8
        with open(output_path, "rb") as f:
            raw_bytes = f.read()
            
        try:
            decoded = raw_bytes.decode("utf-8")
            self.assertIsNotNone(decoded)
        except UnicodeDecodeError:
            self.fail("Output file is not valid UTF-8")


if __name__ == "__main__":
    unittest.main()