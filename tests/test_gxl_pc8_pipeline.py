#!/usr/bin/env python3
"""
Tests for the full GXL extraction to PC8/PC4 conversion pipeline.

This module tests the integration between GXL extraction and PC8/PC4 conversion,
ensuring the entire pipeline produces consistent results (byte-for-byte identical).
"""

import sys
import unittest
import hashlib
import tempfile
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageChops
from tools.convert_pc8 import convert_image
from tools.pcx_utils import setup_logging

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class GxlPc8PipelineTest(unittest.TestCase):
    """Test the full GXL extraction to PC8 conversion pipeline"""

    @classmethod
    def setUpClass(cls):
        """Set up common test resources"""
        # Create temp directories for test outputs
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.extracted_dir = cls.temp_dir / "extracted"
        cls.extracted_dir.mkdir(exist_ok=True)
        cls.converted_dir = cls.temp_dir / "converted"
        cls.converted_dir.mkdir(exist_ok=True)

        # Reference images directory (current images in modern/images)
        cls.reference_dir = Path(parent_dir) / "modern" / "images"

        # Original GXL file (if available)
        cls.gxl_file = Path(parent_dir) / "original_game" / "OREGON.GXL"

        # If GXL file not found in expected location, try alternate locations
        if not cls.gxl_file.exists():
            alternate_locations = [
                Path(parent_dir) / "OREGON.GXL",
                Path(parent_dir).parent / "OREGON.GXL",
            ]
            for alt in alternate_locations:
                if alt.exists():
                    cls.gxl_file = alt
                    break

        # list of test images to verify
        cls.test_images = [
            "CLIFFS.PC8",
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

    def test_pipeline_with_existing_extracted_files(self):
        """Test PC8 conversion with already extracted files"""
        for source_filename in self.test_images:
            # Extract filename without extension
            base_name = Path(source_filename).stem
            ext = Path(source_filename).suffix.lower().lstrip(".")

            # Source path in raw_extracted
            source_path = Path(parent_dir) / "raw_extracted" / source_filename

            # Reference image path (e.g., modern/images/pc8/CLIFFS.png)
            ref_path = f"{ext}/{base_name}.png"
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
            convert_image(source_path, self.converted_dir)

            # Get path to converted image
            converted_image_path = self.converted_dir / "images" / ref_path

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

    def test_full_pipeline_extraction_and_conversion(self):
        """Test the full pipeline from GXL extraction to PC8 conversion"""
        # Skip if original GXL file doesn't exist
        if not self.gxl_file.exists():
            self.skipTest(f"Original GXL file not found at {self.gxl_file}")

        # Test images to verify
        img_exts = [".pc8", ".pc4"]  # Fixed comma between extensions
        test_imgs = [
            img for img in self.test_images if Path(img).suffix.lower() in img_exts
        ]

        # Extract GXL file using main.py
        main_script = Path(parent_dir) / "main.py"
        if not main_script.exists():
            self.skipTest(f"Main script not found at {main_script}")

        try:
            # Run GXL extraction
            subprocess.run(
                [
                    sys.executable,
                    str(main_script),
                    "extract",
                    str(self.gxl_file),
                    "--output",
                    str(self.extracted_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Check if extraction produced our test files
            missing_files = []
            for img in test_imgs:
                if not (self.extracted_dir / img).exists():
                    missing_files.append(img)

            if missing_files:
                self.skipTest(f"Extraction didn't produce these files: {missing_files}")

            # Now convert the extracted files
            for img in test_imgs:
                base_name = Path(img).stem
                ext = Path(img).suffix.lower().lstrip(".")

                # Extract file to convert
                extract_path = self.extracted_dir / img

                # Reference image path
                ref_path = f"{ext}/{base_name}.png"
                ref_image_path = self.reference_dir / ref_path

                # Skip if reference image doesn't exist
                if not ref_image_path.exists():
                    continue

                # Get reference image hash
                ref_hash = self.get_file_hash(ref_image_path)

                # Convert the image
                convert_image(extract_path, self.converted_dir)

                # Get path to converted image
                converted_image_path = self.converted_dir / "images" / ref_path

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

        except subprocess.CalledProcessError as e:
            self.fail(f"GXL extraction failed: {e.stderr}")

        except Exception as e:
            self.fail(f"Test failed: {str(e)}")


class ReferenceImageTracker(unittest.TestCase):
    """Utility to track reference images for regression testing"""

    def test_generate_image_manifest(self):
        """Generate a manifest of reference images with metadata"""
        # Skip by default - only run manually
        self.skipTest("This test is only for manual execution")

        images_dir = Path(parent_dir) / "modern" / "images"

        # Output file for image manifest
        output_file = Path(parent_dir) / "tests" / "reference_image_manifest.py"

        image_info = {}

        # Process all image subdirectories
        for image_type in ["pc8", "pc4"]:
            type_dir = images_dir / image_type
            if not type_dir.exists():
                continue

            for img_path in type_dir.glob("*.png"):
                # Calculate hash
                hash_obj = hashlib.sha256()
                with open(img_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_obj.update(chunk)

                # Get image dimensions and mode
                with Image.open(img_path) as img:
                    width, height = img.size
                    mode = img.mode

                # Store info
                image_key = f"{image_type}/{img_path.name}"
                image_info[image_key] = {
                    "hash": hash_obj.hexdigest(),
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "source": f"{img_path.stem.upper()}.{image_type.upper()}",
                }

        # Generate Python file with image manifest
        with open(output_file, "w") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write('"""\n')
            f.write("Reference image manifest for regression testing.\n")
            f.write("\n")
            f.write(
                "This file contains metadata about reference images used in testing,\n"
            )
            f.write("including SHA-256 hashes, dimensions, and color modes.\n")
            f.write('"""\n\n')
            f.write("# Generated by ReferenceImageTracker\n\n")
            f.write("REFERENCE_IMAGES = {\n")
            for path, info in sorted(image_info.items()):
                f.write(f'    "{path}": {{\n')
                f.write(f'        "hash": "{info["hash"]}",\n')
                f.write(f'        "width": {info["width"]},\n')
                f.write(f'        "height": {info["height"]},\n')
                f.write(f'        "mode": "{info["mode"]}",\n')
                f.write(f'        "source": "{info["source"]}"\n')
                f.write("    },\n")
            f.write("}\n")


if __name__ == "__main__":
    unittest.main()
