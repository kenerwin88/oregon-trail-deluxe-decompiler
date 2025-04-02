#!/usr/bin/env python3
"""
Main entry point for Oregon Trail decompiler tools.
Provides command-line interface for extracting and converting game files.
"""

import argparse
import logging
import os
import sys
import importlib

from tools.gxl_extractor import GXLExtractor, set_debug as set_gxl_debug
from tools.convert import convert_all, set_debug as set_convert_debug

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname).1s %(module)s: %(message)s", force=True
)
logger = logging.getLogger(__name__)


def extract_gxl(args):
    """Handle GXL extraction command"""
    set_gxl_debug(args.debug)

    # Create output directory if needed
    if not args.analyze and not os.path.exists(args.output):
        os.makedirs(args.output)

    # Process each input file
    for filename in args.files:
        if not os.path.exists(filename):
            logger.error(f"File not found: {filename}")
            continue

        extractor = GXLExtractor(filename)

        # Analyze file
        info = extractor.analyze()

        # Output analysis in requested format
        if args.format == "json":
            import json

            try:
                json_output = json.dumps(
                    info, indent=2, default=lambda obj: str(obj), separators=(",", ": ")
                )
                print(json_output)
            except TypeError as e:
                logger.error(f"JSON serialization error: {str(e)}")
                logger.error("Falling back to text format")
                args.format = "text"
        else:
            logger.info(f"Analysis of {filename}:")
            logger.info(f"  File type: {info['type']}")
            logger.info(f"  Total entries: {info['num_entries']}")
            logger.info(f"  Total size: {info['total_file_size']} bytes")

            # File type statistics
            logger.info("  File types:")
            for ftype, count in info["file_types"].items():
                logger.info(f"    {ftype}: {count}")

            # Image statistics
            if info["images"]["count"] > 0:
                logger.info("  Images:")
                logger.info(f"    Count: {info['images']['count']}")
                logger.info(f"    Total size: {info['images']['total_size']} bytes")
                logger.info(f"    Average size: {info['images']['avg_size']:.1f} bytes")
                logger.info("    Dimensions:")
                logger.info(
                    f"      Width: {info['images']['dimensions']['min_width']} - {info['images']['dimensions']['max_width']}"
                )
                logger.info(
                    f"      Height: {info['images']['dimensions']['min_height']} - {info['images']['dimensions']['max_height']}"
                )

            # Show completeness information
            completeness = info["completeness"]
            logger.info("\n  Completeness check:")
            if completeness["complete"]:
                logger.info(
                    "    Status: COMPLETE - All bytes in the file are accounted for"
                )
            else:
                unaccounted = completeness["unaccounted_bytes"]
                percentage = completeness["unaccounted_percentage"]
                logger.info(
                    f"    Status: INCOMPLETE - {unaccounted} bytes ({percentage:.2f}%) not accounted for"
                )

                if completeness["gaps"]:
                    logger.info(
                        f"    Found {len(completeness['gaps'])} gaps between files:"
                    )
                    for i, gap in enumerate(completeness["gaps"]):
                        logger.info(
                            f"      Gap {i + 1}: {gap['size']} bytes between {gap['after_file']} and {gap['before_file']}"
                        )
                        logger.info(
                            f"             (offset 0x{gap['start_offset']:X} - 0x{gap['end_offset']:X})"
                        )

                if completeness["potential_hidden_files"]:
                    logger.info("    Potential hidden files detected:")
                    for i, file in enumerate(completeness["potential_hidden_files"]):
                        logger.info(
                            f"      File {i + 1}: {file['potential_type']} at offset 0x{file['offset']:X}, size {file['size']} bytes"
                        )

            logger.info("    File structure:")
            logger.info(f"      Total file size: {completeness['file_size']} bytes")
            logger.info(f"      Header size: {completeness['header_size']} bytes")
            logger.info(
                f"      File table size: {completeness['file_table_size']} bytes"
            )
            logger.info(
                f"      Data size: {sum(entry['size'] for entry in info['entries'])} bytes"
            )

        # Extract if requested
        if not args.analyze:
            verify_integrity = not args.no_verify
            if verify_integrity:
                logger.info("File integrity verification enabled")
            else:
                logger.info("File integrity verification disabled")

            if extractor.extract_all_files(
                args.output, verify_integrity=verify_integrity
            ):
                # Success already logged in extract_all_files
                pass
            else:
                logger.warning(
                    f"Extraction from {filename} had issues - check log for details"
                )


def convert_files(args):
    """Handle file conversion command"""
    set_convert_debug(args.debug)

    if convert_all(args.input_dir, args.output, args.type):
        logger.info("Successfully converted all files")
    else:
        logger.warning("Some conversions failed")
        sys.exit(1)


def clean_directories():
    """Remove raw_extracted and docs/modern directories"""
    for dir_path in ["raw_extracted", "docs/modern"]:
        if os.path.exists(dir_path):
            logger.info(f"Removing {dir_path} directory")
            import shutil

            shutil.rmtree(dir_path)


def process_all():
    """Extract and convert all files"""
    # Clean directories first
    clean_directories()

    # Extract all files from GXL archives
    extract_args = argparse.Namespace(
        files=["original_game/OREGON.GXL"],
        output="raw_extracted",
        analyze=False,
        debug=False,
        format="text",
        no_verify=False,
    )
    extract_gxl(extract_args)

    # Convert all files (both extracted and original)
    logger.info("Converting all game files")
    convert_args = argparse.Namespace(
        input_dir="raw_extracted",
        output="docs/modern",
        type=None,  # Convert all types
        debug=False,
    )
    convert_files(convert_args)

    # Process additional files from original_game
    logger.info("Processing additional game files")
    convert_args = argparse.Namespace(
        input_dir="original_game", output="docs/modern", type=None, debug=False
    )
    # Don't clean directories again
    convert_all(
        convert_args.input_dir, convert_args.output, convert_args.type, clean=False
    )


def decompile_executable(args):
    """Run the decompiler with powerful options enabled by default"""
    try:
        # Import the module dynamically to avoid circular imports
        logger.info("Importing decompiler module...")
        decompiler_main = importlib.import_module("tools.decompiler.main")
        
        # Build argument list for decompiler with defaults enabled
        sys_args = [args.file]
        
        # Add output directory
        sys_args.extend(["--output", args.output])
        
        # Add default powerful options unless explicitly disabled
        if not args.no_enhanced:
            sys_args.append("--enhanced")
        
        if not args.no_data_flow:
            sys_args.append("--data-flow")
            
        if not args.no_improved:
            sys_args.append("--improved")
            
        if not args.no_c_code:
            sys_args.append("--c-code")
            
        if not args.no_all_analyzers:
            sys_args.append("--all-analyzers")
            
        # Add visualization if requested
        if args.visualize:
            sys_args.append("--visualize")
            
        # Add resource directory if specified
        if args.resource_dir:
            sys_args.extend(["--resource-dir", args.resource_dir])
        
        # Check if file exists
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            return
            
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        logger.info(f"Running decompiler with command: python -m tools.decompiler.main {' '.join(sys_args)}")
        
        # Use subprocess instead of directly calling the module
        import subprocess
        full_command = [sys.executable, "-m", "tools.decompiler.main"] + sys_args
        
        logger.info(f"Executing: {' '.join(full_command)}")
        result = subprocess.run(full_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Decompiler failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
        else:
            logger.info(f"Decompiler completed successfully")
            logger.info(f"Output: {result.stdout}")
            
    except Exception as e:
        logger.error(f"Error running decompiler: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Oregon Trail Decompiler Tools - Extracts and converts game assets to modern formats"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract files from GXL archives and process other game files"
    )
    extract_parser.add_argument("files", nargs="+", help="GXL files to process")
    extract_parser.add_argument(
        "--output",
        "-o",
        default="raw_extracted",
        help="Output directory for extracted files",
    )
    extract_parser.add_argument(
        "--analyze",
        "-a",
        action="store_true",
        help="Only analyze files without extracting",
    )
    extract_parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    extract_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format for analysis results",
    )
    extract_parser.add_argument(
        "--no-verify", action="store_true", help="Disable file integrity verification"
    )

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert game files to modern formats"
    )
    convert_parser.add_argument(
        "input_dir", help="Directory containing game files to convert"
    )
    convert_parser.add_argument(
        "--output", "-o", default="modern", help="Output directory for converted files"
    )
    convert_parser.add_argument(
        "--type",
        "-t",
        choices=["pc8", "pc4", "256", "xmi", "snd", "text", "ctr", "ani", "lst"],
        help="Convert only specific file type (pc8=PC8/PCX images, pc4=PC4 images, 256=.256 images, xmi=music, snd=sounds, text=text files, ctr=controls, ani=animations, lst=high scores)",
    )
    convert_parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    
    # Decompile command - new addition for easier decompilation
    decompile_parser = subparsers.add_parser(
        "decompile", help="Decompile DOS executable with powerful options enabled by default"
    )
    decompile_parser.add_argument(
        "file",
        nargs="?",
        default="original_game/OREGON.EXE",
        help="DOS executable file to decompile (default: original_game/OREGON.EXE)"
    )
    decompile_parser.add_argument(
        "--output", "-o", default="decompiled_output",
        help="Output directory for decompiled files (default: decompiled_output)"
    )
    decompile_parser.add_argument(
        "--visualize", "-v", action="store_true",
        help="Generate visualizations (call graph, state machine, etc.)"
    )
    decompile_parser.add_argument(
        "--resource-dir",
        help="Directory containing game resource files for resource analysis"
    )
    
    # Add disable options (all powerful features are enabled by default)
    decompile_parser.add_argument(
        "--no-enhanced", action="store_true",
        help="Disable enhanced Capstone-based disassembler"
    )
    decompile_parser.add_argument(
        "--no-data-flow", action="store_true",
        help="Disable data flow analysis"
    )
    decompile_parser.add_argument(
        "--no-improved", action="store_true",
        help="Disable improved decompiler with better variable naming"
    )
    decompile_parser.add_argument(
        "--no-c-code", action="store_true",
        help="Disable C code generation (use pseudocode instead)"
    )
    decompile_parser.add_argument(
        "--no-all-analyzers", action="store_true",
        help="Disable all advanced analyzers"
    )

    args = parser.parse_args()

    # If no command given, process everything
    if not args.command:
        process_all()
    elif args.command == "extract":
        extract_gxl(args)
    elif args.command == "convert":
        convert_files(args)
    elif args.command == "decompile":
        decompile_executable(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
