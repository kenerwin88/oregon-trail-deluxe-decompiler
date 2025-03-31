#!/usr/bin/env python3
"""
Tests for CTR control format converter.

This module tests the CTR conversion functionality, including:
- Parsing CTR files
- Converting CTR to JSON
- Command parsing
- Element structure
"""

import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from tools.convert_ctr import convert_ctr, parse_ctr_file, parse_command, split_commands, clean_text


class CTRConverterTest(unittest.TestCase):
    """Test CTR control file conversion functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.output_dir = cls.temp_dir / "output"
        cls.output_dir.mkdir(exist_ok=True)

        # Original CTR files directory
        cls.raw_dir = Path(parent_dir) / "raw_extracted"
        
        # Create a simple test CTR file
        cls.test_ctr_file = cls.temp_dir / "TEST.CTR"
        with open(cls.test_ctr_file, "w", encoding="ascii") as f:
            f.write("17,let's load the images\n")
            f.write("1,1\n")
            f.write("OKAY.PCC\n")
            f.write("17,icon buttons\n")
            f.write("4,200 5,350\n")
            f.write("6,135 7,120\n")
            f.write("12,0,6\n")
            f.write("6,215 7,290\n")
            f.write("8,0,0,1,28\n")
            f.write("6,315 7,290\n")
            f.write("8,0,1,99,1\n")
            f.write("6,135 7,120\n")
            f.write("11,4,1,2\n")
            f.write("6,135 7,120\n")
            f.write("11,2,1,3\n")
            f.write("6,135 7,120\n")
            f.write("11,1,1,4\n")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        shutil.rmtree(cls.temp_dir)

    def test_parse_command(self):
        """Test parsing individual CTR commands"""
        # Test image count command
        cmd = parse_command("1,1")
        self.assertEqual(cmd["type"], "image_count")
        self.assertEqual(cmd["count"], 1)
        
        # Test position command
        cmd = parse_command("6,135")
        self.assertEqual(cmd["type"], "position_x")
        self.assertEqual(cmd["x"], 135)
        
        # Test button properties command
        cmd = parse_command("8,0,0,1,28")
        self.assertEqual(cmd["type"], "button_properties")
        self.assertEqual(cmd["properties"]["group"], 0)
        self.assertEqual(cmd["properties"]["index"], 0)
        self.assertEqual(cmd["properties"]["action"]["id"], 1)
        self.assertEqual(cmd["properties"]["action"]["name"], "confirm")
        self.assertEqual(cmd["properties"]["state"]["value"], 28)
        self.assertEqual(cmd["properties"]["state"]["name"], "enabled")
        
        # Test color command
        cmd = parse_command("12,0,6")
        self.assertEqual(cmd["type"], "set_color")
        self.assertEqual(cmd["colors"]["background"]["value"], 0)
        self.assertEqual(cmd["colors"]["background"]["name"], "black")
        self.assertEqual(cmd["colors"]["foreground"]["value"], 6)
        self.assertEqual(cmd["colors"]["foreground"]["name"], "gold")

    def test_split_commands(self):
        """Test splitting a line containing multiple commands"""
        line = "4,200 5,350"
        cmds = split_commands(line)
        self.assertEqual(len(cmds), 2)
        self.assertEqual(cmds[0], "4,200")
        self.assertEqual(cmds[1], "5,350")
        
        # Test comment line
        line = "17,This is a comment"
        cmds = split_commands(line)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0], line)

    def test_clean_text(self):
        """Test text cleaning functionality"""
        # Test normal text
        text = "Hello world"
        cleaned = clean_text(text)
        self.assertEqual(cleaned, text)
        
        # Test text with extra whitespace
        text = "  Hello   world  "
        cleaned = clean_text(text)
        # The actual implementation normalizes whitespace
        self.assertEqual(cleaned, "Hello world")

    def test_parse_ctr_file(self):
        """Test parsing a CTR file"""
        data = parse_ctr_file(self.test_ctr_file)
        
        # Check basic structure
        self.assertIn("metadata", data)
        self.assertIn("ui_elements", data)
        self.assertEqual(data["filename"], "TEST.CTR")
        
        # Check metadata
        self.assertIn("images", data["metadata"])
        self.assertEqual(len(data["metadata"]["images"]), 1)
        self.assertEqual(data["metadata"]["images"][0], "OKAY.PCC")
        
        # Check UI elements
        self.assertGreaterEqual(len(data["ui_elements"]), 3)  # At least panel and buttons
        
        # Find the panel element
        panel = None
        for element in data["ui_elements"]:
            if element["type"] == "panel":
                panel = element
                break
                
        self.assertIsNotNone(panel, "Panel element not found")
        self.assertEqual(panel["dimensions"]["width"], 200)
        self.assertEqual(panel["dimensions"]["height"], 350)
        self.assertEqual(panel["position"]["x"], 135)
        self.assertEqual(panel["position"]["y"], 120)

    def test_convert_ctr_file(self):
        """Test converting a CTR file to JSON"""
        result = convert_ctr(self.test_ctr_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "controls" / "TEST.json"
        self.assertTrue(output_path.exists())
        
        # Verify JSON content
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        self.assertIn("metadata", json_data)
        self.assertIn("ui_elements", json_data)
        self.assertEqual(json_data["filename"], "TEST.CTR")

    def test_convert_real_ctr_file(self):
        """Test converting a real CTR file if available"""
        # Try to find a real CTR file
        real_ctr_files = list(self.raw_dir.glob("*.CTR"))
        
        if not real_ctr_files:
            self.skipTest("No real CTR files found to test")
            
        # Test with first found CTR file
        ctr_file = real_ctr_files[0]
        result = convert_ctr(ctr_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "controls" / f"{ctr_file.stem}.json"
        self.assertTrue(output_path.exists())
        
        # Verify JSON structure
        with open(output_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        self.assertIn("metadata", json_data)
        self.assertIn("ui_elements", json_data)
        self.assertEqual(json_data["filename"], f"{ctr_file.name}")


if __name__ == "__main__":
    unittest.main()