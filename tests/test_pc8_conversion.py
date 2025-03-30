#!/usr/bin/env python3
"""
Tests for PC8/PC4 image conversion consistency.

This module ensures that PC8 image conversion produces consistent results
by comparing converted images against reference images.
"""

import sys
import unittest
import hashlib
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageChops
from tools.convert_pc8 import convert_image
from tools.pcx_utils import setup_logging

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class PC8ConversionConsistencyTest(unittest.TestCase):
    """Test PC8/PC4 image conversion consistency"""

    @classmethod
    def setUpClass(cls):
        """Set up common test resources"""
        # Create temp directory for test outputs
        cls.temp_dir = Path(tempfile.mkdtemp())

        # Reference images directory (current images in modern/images)
        cls.reference_dir = Path(parent_dir) / "modern" / "images"

        # list of test images to verify
        cls.test_images = [
            ("CLIFFS.PC8", "pc8/CLIFFS.png"),
            # Add more test cases here as needed
        ]

        # Make sure logging is set up
        setup_logging(False)

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        # Remove temp directory
        shutil.rmtree(cls.temp_dir)

    def get_file_hash(self, filepath):
        """Calculate SHA-256 hash of a file for comparison"""
        hash_obj = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read and update hash in chunks for memory efficiency
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def compare_images(self, img1_path, img2_path):
        """Compare two images for pixel-perfect equality"""
        with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
            # Check dimensions
            self.assertEqual(img1.size, img2.size, "Image dimensions don't match")

            # Check mode (color mode)
            self.assertEqual(img1.mode, img2.mode, "Image color modes don't match")

            # Check for pixel differences
            diff = ImageChops.difference(img1, img2)
            # If images are identical, the difference will be completely black
            self.assertEqual(diff.getbbox(), None, "Images have pixel differences")

    def test_pc8_conversion_consistency(self):
        """Test that PC8 image conversion produces consistent results"""
        for source_filename, ref_path in self.test_images:
            source_path = Path(parent_dir) / "raw_extracted" / source_filename
            ref_image_path = self.reference_dir / ref_path

            # Skip if source file doesn't exist
            if not source_path.exists():
                self.skipTest(f"Source file {source_path} not found")

            # Skip if reference image doesn't exist
            if not ref_image_path.exists():
                self.skipTest(f"Reference image {ref_image_path} not found")

            # Get reference image hash
            ref_hash = self.get_file_hash(ref_image_path)

            # Convert the PC8 file
            convert_image(source_path, self.temp_dir)

            # Get path to converted image
            converted_image_path = self.temp_dir / "images" / ref_path

            # Verify the converted image exists
            self.assertTrue(
                converted_image_path.exists(),
                f"Conversion failed to produce {ref_path}",
            )

            # Get converted image hash
            converted_hash = self.get_file_hash(converted_image_path)

            # Compare hashes for byte-for-byte equality
            self.assertEqual(
                ref_hash,
                converted_hash,
                f"Converted image {ref_path} differs from reference",
            )

            # Also do a pixel-by-pixel comparison
            self.compare_images(ref_image_path, converted_image_path)

    def test_batch_conversion_consistency(self):
        """Test that batch conversion produces consistent results for all files"""
        # For this test, we'll manually convert a subset of PC8 files and check for consistency
        self.skipTest(
            "Skipping batch conversion test - will be replaced with a more targeted version"
        )

        # Create mock output directory
        mock_output = self.temp_dir / "mock_output"
        mock_output.mkdir(exist_ok=True)

        # Create subdirectories
        img_dir = mock_output / "images" / "pc8"
        img_dir.mkdir(parents=True, exist_ok=True)

        # Convert a sample of PC8 files
        pc8_files = list(Path(parent_dir).glob("raw_extracted/*.PC8"))
        # Take at most 3 files for a faster test
        sample_files = pc8_files[: min(3, len(pc8_files))]

        converted_files = []
        for src_file in sample_files:
            if convert_image(src_file, mock_output):
                # Get corresponding reference file
                ref_path = self.reference_dir / "pc8" / f"{src_file.stem}.png"
                out_path = img_dir / f"{src_file.stem}.png"

                # Skip if reference image doesn't exist
                if not ref_path.exists() or not out_path.exists():
                    continue

                converted_files.append((ref_path, out_path))

        # Skip test if no files were converted successfully
        if not converted_files:
            self.skipTest("No files were successfully converted for comparison")

        # Now compare the converted files with reference images
        for ref_path, out_path in converted_files:
            # Get reference image hash
            ref_hash = self.get_file_hash(ref_path)

            # Get converted image hash
            out_hash = self.get_file_hash(out_path)

            # Compare hashes for byte-for-byte equality
            self.assertEqual(
                ref_hash,
                out_hash,
                f"Converted image {out_path.name} differs from reference",
            )

            # Also do a pixel-by-pixel comparison
            self.compare_images(ref_path, out_path)


class ImageReferenceGenerator(unittest.TestCase):
    """Utility class to generate reference image hashes

    This test case is intended to be run manually to generate reference hashes
    for new images or when the conversion process is intentionally updated.
    """

    def test_generate_reference_hashes(self):
        """Generate reference hashes for PC8/PC4 images"""
        # Skip by default - only run manually
        self.skipTest("This test is only for manual execution")

        images_dir = Path(parent_dir) / "modern" / "images"

        # Output file for reference hashes
        output_file = Path(parent_dir) / "tests" / "reference_image_hashes.py"

        image_hashes = {}

        # PC8 images
        pc8_dir = images_dir / "pc8"
        if pc8_dir.exists():
            for img_path in pc8_dir.glob("*.png"):
                hash_obj = hashlib.sha256()
                with open(img_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_obj.update(chunk)
                image_hashes[f"pc8/{img_path.name}"] = hash_obj.hexdigest()

        # PC4 images
        pc4_dir = images_dir / "pc4"
        if pc4_dir.exists():
            for img_path in pc4_dir.glob("*.png"):
                hash_obj = hashlib.sha256()
                with open(img_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_obj.update(chunk)
                image_hashes[f"pc4/{img_path.name}"] = hash_obj.hexdigest()

        # Generate Python file with reference hashes
        with open(output_file, "w") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write('"""\n')
            f.write("Reference image hashes for PC8/PC4 conversion tests.\n")
            f.write('"""\n\n')
            f.write("# Generated by ImageReferenceGenerator\n\n")
            f.write("REFERENCE_HASHES = {\n")
            for path, hash_val in sorted(image_hashes.items()):
                f.write(f'    "{path}": "{hash_val}",\n')
            f.write("}\n")


if __name__ == "__main__":
    unittest.main()
