#!/usr/bin/env python3
"""
Tests for ANI animation format converter.

This module tests the ANI animation converter functionality, including:
- Parsing ANI animation files
- Converting ANI to JSON
- Validating frame data structure
"""

import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from tools.convert_ani import convert_ani, parse_animation

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class ANIConverterTest(unittest.TestCase):
    """Test ANI animation file conversion functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.output_dir = cls.temp_dir / "output"
        cls.output_dir.mkdir(exist_ok=True)

        # Original ANI files directory
        cls.raw_dir = Path(parent_dir) / "raw_extracted"

        # Create a test ANI file
        cls.test_ani_file = cls.temp_dir / "TEST.ANI"
        with open(cls.test_ani_file, "w", encoding="ascii") as f:
            f.write("TITLE.PC8\n")
            f.write("2\n")
            f.write("10,20\n")
            f.write("100,50\n")
            f.write("30,40\n")
            f.write("200,100\n")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        shutil.rmtree(cls.temp_dir)

    def test_parse_animation(self):
        """Test parsing ANI animation data"""
        # Test with the sample file we created
        with open(self.test_ani_file, "r", encoding="ascii") as f:
            ani_text = f.read()

        animation_data = parse_animation(ani_text)

        # Verify basic structure
        self.assertEqual(animation_data["image_file"], "TITLE.PC8")
        self.assertEqual(animation_data["frame_count"], 1)
        self.assertEqual(len(animation_data["frames"]), 1)

        # Verify the frame structure (the implementation parses multiple coordinates per frame)
        frame = animation_data["frames"][0]
        self.assertEqual(len(frame["coordinates"]), 2)
        self.assertEqual(frame["coordinates"][0]["x"], 10)
        self.assertEqual(frame["coordinates"][0]["y"], 20)
        self.assertEqual(frame["coordinates"][1]["x"], 30)
        self.assertEqual(frame["coordinates"][1]["y"], 40)
        self.assertEqual(len(frame["dimensions"]), 2)
        self.assertEqual(frame["dimensions"][0]["width"], 100)
        self.assertEqual(frame["dimensions"][0]["height"], 50)
        self.assertEqual(frame["dimensions"][1]["width"], 200)
        self.assertEqual(frame["dimensions"][1]["height"], 100)

    def test_parse_animation_single_coordinate(self):
        """Test parsing ANI animation with single coordinate format"""
        ani_text = "TITLE.PC8\n66,223\n30,24\n"

        animation_data = parse_animation(ani_text)

        # Verify basic structure
        self.assertEqual(animation_data["image_file"], "TITLE.PC8")
        self.assertEqual(animation_data["frame_count"], 2)

        # Verify frames
        self.assertEqual(animation_data["frames"][0]["coordinates"][0]["x"], 66)
        self.assertEqual(animation_data["frames"][0]["coordinates"][0]["y"], 223)
        self.assertEqual(animation_data["frames"][1]["coordinates"][0]["x"], 30)
        self.assertEqual(animation_data["frames"][1]["coordinates"][0]["y"], 24)

    def test_convert_ani_file(self):
        """Test converting an ANI file to JSON"""
        result = convert_ani(self.test_ani_file, self.output_dir)
        self.assertTrue(result)

        # Check if the output file exists
        output_path = self.output_dir / "animations" / "TEST.json"
        self.assertTrue(output_path.exists())

        # Verify JSON content
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        self.assertEqual(json_data["image_file"], "TITLE.PC8")
        self.assertEqual(json_data["frame_count"], 1)
        self.assertEqual(len(json_data["frames"]), 1)

    def test_convert_real_ani_file(self):
        """Test converting a real ANI file if available"""
        # Try to find a real ANI file
        real_ani_files = list(self.raw_dir.glob("*.ANI"))

        if not real_ani_files:
            self.skipTest("No real ANI files found to test")

        # Test with first found ANI file
        ani_file = real_ani_files[0]
        result = convert_ani(ani_file, self.output_dir)
        self.assertTrue(result)

        # Check if the output file exists
        output_path = self.output_dir / "animations" / f"{ani_file.stem}.json"
        self.assertTrue(output_path.exists())

        # Verify JSON structure
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        self.assertIn("image_file", json_data)
        self.assertIn("frame_count", json_data)
        self.assertIn("frames", json_data)
        self.assertIsInstance(json_data["frames"], list)


if __name__ == "__main__":
    unittest.main()
