"""
Main entry point for the DOS decompiler.
"""

import argparse
import os

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
    parser.add_argument(
        "--c-code",
        "-c",
        action="store_true",
        help="Generate readable C code instead of pseudocode",
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

    # Save output
    os.makedirs(args.output, exist_ok=True)

    # Save header information
    with open(os.path.join(args.output, "header.txt"), "w") as f:
        f.write(f"Filename: {decompiler.filename}\n")
        f.write(f"File size: {decompiler.file_size} bytes\n")
        f.write(f"Entry point: 0x{decompiler.entry_point:X}\n")
        f.write("\nSegments:\n")
        for segment in decompiler.segments:
            f.write(f"  {segment}\n")

    # Save disassembly
    with open(os.path.join(args.output, "disassembly.asm"), "w") as f:
        for segment in decompiler.segments:
            f.write(f"; Segment {segment.name}\n")
            for instr in segment.instructions:
                f.write(f"{instr.address:08X}: {instr.mnemonic} {instr.operands}\n")

    # Save strings
    with open(os.path.join(args.output, "strings.txt"), "w") as f:
        for addr, string in sorted(decompiler.strings.items()):
            f.write(f'{addr:08X}: "{string}"\n')

    # Save code (pseudocode or C code)
    if args.c_code and isinstance(decompiler, EnhancedDOSDecompiler) and args.improved:
        # Generate C code
        with open(os.path.join(args.output, "code.c"), "w") as f:
            f.write(decompiler.generate_c_code())
        print(f"C code saved to {os.path.join(args.output, 'code.c')}")
    else:
        # Generate pseudocode
        with open(os.path.join(args.output, "pseudocode.c"), "w") as f:
            f.write(decompiler.generate_pseudocode())

    print(f"Output saved to {args.output}")


if __name__ == "__main__":
    main()
