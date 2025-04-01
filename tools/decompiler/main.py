"""
Main entry point for the DOS decompiler.
"""

import argparse

from .disassembler import DOSDecompiler
from .enhanced_disassembler import EnhancedDOSDecompiler


def main():
    """Main entry point for the DOS decompiler"""
    parser = argparse.ArgumentParser(description="DOS Executable Decompiler")
    parser.add_argument("file", help="DOS executable file to decompile")
    parser.add_argument("--output", "-o", default="decompiled", help="Output directory")
    parser.add_argument(
        "--enhanced",
        "-e",
        action="store_true",
        help="Use enhanced Capstone-based disassembler",
    )
    parser.add_argument(
        "--visualize",
        "-v",
        action="store_true",
        help="Generate control flow graph visualizations",
    )
    parser.add_argument(
        "--data-flow", "-d", action="store_true", help="Perform data flow analysis"
    )
    parser.add_argument(
        "--improved",
        "-i",
        action="store_true",
        help="Use improved decompiler with better variable naming, function analysis, and comments",
    )
    args = parser.parse_args()

    if args.enhanced:
        print("Using enhanced Capstone-based disassembler")
        decompiler = EnhancedDOSDecompiler(args.file)
        if args.improved:
            print(
                "Using improved decompiler with better variable naming, function analysis, and comments"
            )
            decompiler.use_improved_decompiler = True
    else:
        decompiler = DOSDecompiler(args.file)

    decompiler.decompile()
    decompiler.save_output(args.output, args.visualize)


if __name__ == "__main__":
    main()
