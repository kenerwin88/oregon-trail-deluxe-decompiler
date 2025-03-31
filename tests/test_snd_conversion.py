#!/usr/bin/env python3
"""
Tests for SND audio format converter.

This module tests the SND audio converter functionality, including:
- Converting SND to WAV
- Verifying WAV file properties
"""

import sys
import unittest
import tempfile
import shutil
import wave
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from tools.convert_snd import convert_snd


class SNDConverterTest(unittest.TestCase):
    """Test SND audio file conversion functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.output_dir = cls.temp_dir / "output"
        cls.output_dir.mkdir(exist_ok=True)

        # Original SND files directory
        cls.raw_dir = Path(parent_dir) / "raw_extracted"
        
        # Create a test SND file with synthetic audio data
        cls.test_snd_file = cls.temp_dir / "TEST.SND"
        with open(cls.test_snd_file, "wb") as f:
            # Create 1 second of simple 8-bit sine wave (simplified)
            f.write(bytes([128] * 11025))  # 1 second of silence

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        shutil.rmtree(cls.temp_dir)

    def test_convert_snd_file(self):
        """Test converting an SND file to WAV"""
        result = convert_snd(self.test_snd_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "sounds" / "TEST.wav"
        self.assertTrue(output_path.exists())
        
        # Verify WAV file properties
        with wave.open(str(output_path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)  # Mono
            self.assertEqual(wav.getsampwidth(), 1)  # 8-bit
            self.assertEqual(wav.getframerate(), 11025)  # 11025 Hz
            self.assertEqual(wav.getnframes(), 11025)  # 1 second
    
    def test_convert_real_snd_file(self):
        """Test converting a real SND file if available"""
        # Try to find a real SND file
        real_snd_files = list(self.raw_dir.glob("*.SND"))
        
        if not real_snd_files:
            self.skipTest("No real SND files found to test")
            
        # Test with first found SND file
        snd_file = real_snd_files[0]
        result = convert_snd(snd_file, self.output_dir)
        self.assertTrue(result)
        
        # Check if the output file exists
        output_path = self.output_dir / "sounds" / f"{snd_file.stem}.wav"
        self.assertTrue(output_path.exists())
        
        # Verify WAV file properties
        with wave.open(str(output_path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)  # Mono
            self.assertEqual(wav.getsampwidth(), 1)  # 8-bit
            self.assertEqual(wav.getframerate(), 11025)  # 11025 Hz
            
            # Get file size for verification
            file_size = os.path.getsize(snd_file)
            # WAV files have a 44-byte header, so frames should be file size - 44
            self.assertEqual(wav.getnframes(), file_size)


if __name__ == "__main__":
    unittest.main()