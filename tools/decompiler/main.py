"""
Main entry point for the DOS decompiler.
"""

import argparse
import os
import matplotlib
# Force matplotlib to not use any Xwindows backend
matplotlib.use('Agg')

from .disassembler import DOSDecompiler
from .enhanced_disassembler import EnhancedDOSDecompiler
from .call_graph_analyzer import CallGraphAnalyzer
from .resource_analyzer import ResourceAnalyzer
from .state_machine_analyzer import StateMachineAnalyzer
from .improved_dos_api import enhance_dos_api_comments
from .data_structure_recognizer import DataStructureRecognizer


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
    parser.add_argument(
        "--call-graph",
        action="store_true",
        help="Generate call graph visualization and analysis",
    )
    parser.add_argument(
        "--resource-analysis",
        action="store_true",
        help="Perform resource file reference analysis",
    )
    parser.add_argument(
        "--resource-dir",
        help="Directory containing game resource files for resource analysis",
    )
    parser.add_argument(
        "--state-analysis",
        action="store_true",
        help="Perform state machine analysis",
    )
    parser.add_argument(
        "--dos-api",
        action="store_true",
        help="Enhance DOS API call recognition and comments",
    )
    parser.add_argument(
        "--data-structures",
        action="store_true",
        help="Perform advanced data structure recognition",
    )
    parser.add_argument(
        "--all-analyzers",
        "-a",
        action="store_true",
        help="Enable all analyzers (call graph, resources, state machine, DOS API, data structures)",
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
    
    # Apply DOS API enhancements
    if args.dos_api or args.all_analyzers:
        print("Enhancing DOS API call recognition...")
        comments_added = enhance_dos_api_comments(decompiler.functions)
        print(f"Added {comments_added} DOS API comments")

    # Call graph analysis
    if args.call_graph or args.all_analyzers:
        print("Performing call graph analysis...")
        call_graph_analyzer = CallGraphAnalyzer(decompiler.functions)
        call_graph = call_graph_analyzer.build_call_graph()
        
        # Enhance function purposes based on call graph
        call_graph_analyzer.enhance_function_purposes()
        
        # Generate visualization
        if args.visualize:
            viz_file = call_graph_analyzer.visualize_call_graph(
                os.path.join(args.output, "call_graph.png")
            )
            print(f"Call graph visualization saved to {viz_file}")
            
        # Generate function relationships report
        relationships = call_graph_analyzer.generate_function_relationships()
        with open(os.path.join(args.output, "call_graph_report.txt"), "w") as f:
            for func_addr, rel in relationships.items():
                func_name = None
                for func in decompiler.functions:
                    if func.start_address == func_addr:
                        func_name = func.name
                        break
                        
                if not func_name:
                    continue
                    
                f.write(f"Function: {func_name} (0x{func_addr:X})\n")
                f.write(f"  Calls: {len(rel['calls'])} functions\n")
                f.write(f"  Called by: {len(rel['callers'])} functions\n")
                f.write(f"  Call depth: {rel['call_depth']}\n")
                f.write(f"  Is entry point: {rel['is_entry_point']}\n")
                f.write(f"  Is leaf function: {rel['is_leaf']}\n")
                f.write(f"  Is highly called: {rel['is_highly_called']}\n\n")
        
        print(f"Call graph report saved to {os.path.join(args.output, 'call_graph_report.txt')}")

    # Resource analysis
    if args.resource_analysis or args.all_analyzers:
        print("Performing resource file reference analysis...")
        resource_analyzer = ResourceAnalyzer(
            decompiler.functions, decompiler.strings, args.resource_dir
        )
        resource_analyzer.analyze()
        
        # Generate resource report
        resource_report = resource_analyzer.generate_resource_report()
        with open(os.path.join(args.output, "resource_report.txt"), "w") as f:
            f.write(resource_report)
        print(f"Resource analysis report saved to {os.path.join(args.output, 'resource_report.txt')}")

    # State machine analysis
    if args.state_analysis or args.all_analyzers:
        print("Performing state machine analysis...")
        state_analyzer = StateMachineAnalyzer(decompiler.functions)
        state_analyzer.analyze()
        
        # Generate state report
        state_report = state_analyzer.generate_state_report()
        with open(os.path.join(args.output, "state_report.txt"), "w") as f:
            f.write(state_report)
        print(f"State machine report saved to {os.path.join(args.output, 'state_report.txt')}")
        
        # Generate visualization
        if args.visualize:
            viz_file = state_analyzer.visualize_state_machine(
                os.path.join(args.output, "state_machine.png")
            )
            if viz_file:
                print(f"State machine visualization saved to {viz_file}")

    # Data structure recognition
    if args.data_structures or args.all_analyzers:
        print("Performing data structure recognition...")
        structure_recognizer = DataStructureRecognizer(
            decompiler.functions, decompiler.strings
        )
        structure_recognizer.analyze()
        
        # Generate structure report
        structure_report = structure_recognizer.generate_structure_report()
        with open(os.path.join(args.output, "structure_report.txt"), "w") as f:
            f.write(structure_report)
        print(f"Data structure report saved to {os.path.join(args.output, 'structure_report.txt')}")

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
    
    # Print summary of analyses
    if args.all_analyzers or args.call_graph or args.resource_analysis or args.state_analysis or args.dos_api or args.data_structures:
        print("\nAnalysis Summary:")
        if args.call_graph or args.all_analyzers:
            print("- Call graph analysis completed")
        if args.resource_analysis or args.all_analyzers:
            print("- Resource file reference analysis completed")
        if args.state_analysis or args.all_analyzers:
            print("- State machine analysis completed")
        if args.dos_api or args.all_analyzers:
            print("- DOS API call recognition enhanced")
        if args.data_structures or args.all_analyzers:
            print("- Data structure recognition completed")


if __name__ == "__main__":
    main()
