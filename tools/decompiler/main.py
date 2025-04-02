"""
Main entry point for the DOS decompiler.
Implements a modular analyzer-based architecture for decompiling DOS executables.
"""

import argparse
import os
import logging
import matplotlib
# Force matplotlib to not use any Xwindows backend
matplotlib.use('Agg')

from .disassembler import DOSDecompiler
from .enhanced_disassembler import EnhancedDOSDecompiler
from .analyzers import (
    CallGraphAnalyzer,
    ResourceAnalyzer,
    StateMachineAnalyzer,
    DataStructureRecognizer
)
from .enhanced_output import enhance_dos_api_comments
from .utils import setup_logging


# Configure a logger for this module
logger = logging.getLogger(__name__)


class DecompilerManager:
    """
    Central manager for the decompilation process.
    Handles loading analyzers and coordinating the analysis process.
    """
    
    def __init__(self, exe_file, output_dir, options=None):
        """
        Initialize the decompiler manager.
        
        Args:
            exe_file: Path to the DOS executable
            output_dir: Directory for output files
            options: Dictionary of decompiler options
        """
        self.exe_file = exe_file
        self.output_dir = output_dir
        self.options = options or {}
        self.decompiler = None
        self.analyzers = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def initialize_decompiler(self):
        """Set up the appropriate decompiler based on options."""
        if self.options.get('enhanced', False):
            logger.info("Using enhanced Capstone-based disassembler")
            self.decompiler = EnhancedDOSDecompiler(self.exe_file)
            
            if self.options.get('improved', False):
                logger.info("Using improved decompiler with better variable naming")
                self.decompiler.use_improved_decompiler = True
        else:
            logger.info("Using standard disassembler")
            self.decompiler = DOSDecompiler(self.exe_file)
    
    def load_analyzers(self):
        """Load the requested analyzer modules."""
        options = self.options
        
        # Load DOS API analyzer (always on when any analyzer is enabled)
        if (options.get('all_analyzers', False) or 
                options.get('dos_api', False)):
            logger.info("Loading DOS API analyzer")
            self.analyzers.append(('dos_api', None))  # Special case, not a class
        
        # Load call graph analyzer
        if (options.get('all_analyzers', False) or 
                options.get('call_graph', False)):
            logger.info("Loading call graph analyzer")
            self.analyzers.append(('call_graph', 
                                  CallGraphAnalyzer(self.decompiler.functions)))
        
        # Load resource analyzer
        if (options.get('all_analyzers', False) or 
                options.get('resource_analysis', False)):
            logger.info("Loading resource analyzer")
            self.analyzers.append(('resource',
                                  ResourceAnalyzer(
                                      self.decompiler.functions,
                                      self.decompiler.strings,
                                      options.get('resource_dir', None)
                                  )))
        
        # Load state machine analyzer
        if (options.get('all_analyzers', False) or 
                options.get('state_analysis', False)):
            logger.info("Loading state machine analyzer")
            self.analyzers.append(('state_machine',
                                  StateMachineAnalyzer(self.decompiler.functions)))
        
        # Load data structure analyzer
        if (options.get('all_analyzers', False) or 
                options.get('data_structures', False)):
            logger.info("Loading data structure analyzer")
            self.analyzers.append(('data_structure',
                                  DataStructureRecognizer(
                                      self.decompiler.functions,
                                      self.decompiler.strings
                                  )))
    
    def run_decompilation(self):
        """Run the complete decompilation process."""
        logger.info(f"Decompiling {self.exe_file}")
        
        # First decompile the executable
        self.decompiler.decompile()
        
        # Then run each analyzer
        for analyzer_name, analyzer in self.analyzers:
            if analyzer_name == 'dos_api':
                # Special case for DOS API comments
                logger.info("Enhancing DOS API call recognition...")
                comments_added = enhance_dos_api_comments(self.decompiler.functions)
                logger.info(f"Added {comments_added} DOS API comments")
            else:
                logger.info(f"Running {analyzer_name} analysis...")
                analyzer.analyze()
                
                # Generate reports
                self._generate_analyzer_report(analyzer_name, analyzer)
                
                # Generate visualizations if requested
                if self.options.get('visualize', False):
                    self._generate_analyzer_visualization(analyzer_name, analyzer)
    
    def _generate_analyzer_report(self, analyzer_name, analyzer):
        """Generate a report for the given analyzer."""
        report = None
        filename = None
        
        if analyzer_name == 'call_graph':
            # Generate function relationships report
            relationships = analyzer.generate_function_relationships()
            filename = os.path.join(self.output_dir, "call_graph_report.txt")
            
            with open(filename, "w") as f:
                for func_addr, rel in relationships.items():
                    func_name = None
                    for func in self.decompiler.functions:
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
        
        elif analyzer_name == 'resource':
            # Generate resource report
            report = analyzer.generate_resource_report()
            filename = os.path.join(self.output_dir, "resource_report.txt")
        
        elif analyzer_name == 'state_machine':
            # Generate state machine report
            report = analyzer.generate_state_report()
            filename = os.path.join(self.output_dir, "state_report.txt")
        
        elif analyzer_name == 'data_structure':
            # Generate data structure report
            report = analyzer.generate_structure_report()
            filename = os.path.join(self.output_dir, "structure_report.txt")
        
        # Write the report if available
        if report and filename:
            with open(filename, "w") as f:
                f.write(report)
            logger.info(f"Saved {analyzer_name} report to {filename}")
    
    def _generate_analyzer_visualization(self, analyzer_name, analyzer):
        """Generate visualization for the given analyzer if supported."""
        if analyzer_name == 'call_graph':
            viz_file = analyzer.visualize_call_graph(
                os.path.join(self.output_dir, "call_graph.png")
            )
            logger.info(f"Call graph visualization saved to {viz_file}")
        
        elif analyzer_name == 'state_machine':
            viz_file = analyzer.visualize_state_machine(
                os.path.join(self.output_dir, "state_machine.png")
            )
            if viz_file:
                logger.info(f"State machine visualization saved to {viz_file}")
    
    def save_output_files(self):
        """Save all output files from the decompilation process."""
        output_dir = self.output_dir
        
        # Save header information
        with open(os.path.join(output_dir, "header.txt"), "w") as f:
            f.write(f"Filename: {self.decompiler.filename}\n")
            f.write(f"File size: {self.decompiler.file_size} bytes\n")
            f.write(f"Entry point: 0x{self.decompiler.entry_point:X}\n")
            f.write("\nSegments:\n")
            for segment in self.decompiler.segments:
                f.write(f"  {segment}\n")
        
        # Save disassembly
        with open(os.path.join(output_dir, "disassembly.asm"), "w") as f:
            for segment in self.decompiler.segments:
                f.write(f"; Segment {segment.name}\n")
                for instr in segment.instructions:
                    f.write(f"{instr.address:08X}: {instr.mnemonic} {instr.operands}\n")
        
        # Save strings
        with open(os.path.join(output_dir, "strings.txt"), "w") as f:
            for addr, string in sorted(self.decompiler.strings.items()):
                f.write(f'{addr:08X}: "{string}"\n')
        
        # Save code (pseudocode or C code)
        if (self.options.get('c_code', False) and 
                isinstance(self.decompiler, EnhancedDOSDecompiler) and 
                self.options.get('improved', False)):
            # Generate C code
            with open(os.path.join(output_dir, "code.c"), "w") as f:
                f.write(self.decompiler.generate_c_code())
            logger.info(f"C code saved to {os.path.join(output_dir, 'code.c')}")
        else:
            # Generate pseudocode
            with open(os.path.join(output_dir, "pseudocode.c"), "w") as f:
                f.write(self.decompiler.generate_pseudocode())
            logger.info(f"Pseudocode saved to {os.path.join(output_dir, 'pseudocode.c')}")
        
        logger.info(f"All output files saved to {output_dir}")
    
    def print_summary(self):
        """Print a summary of the decompilation process."""
        options = self.options
        
        if (options.get('all_analyzers', False) or 
                options.get('call_graph', False) or
                options.get('resource_analysis', False) or
                options.get('state_analysis', False) or
                options.get('dos_api', False) or
                options.get('data_structures', False)):
            
            logger.info("\nAnalysis Summary:")
            
            if options.get('call_graph', False) or options.get('all_analyzers', False):
                logger.info("- Call graph analysis completed")
            if options.get('resource_analysis', False) or options.get('all_analyzers', False):
                logger.info("- Resource file reference analysis completed")
            if options.get('state_analysis', False) or options.get('all_analyzers', False):
                logger.info("- State machine analysis completed")
            if options.get('dos_api', False) or options.get('all_analyzers', False):
                logger.info("- DOS API call recognition enhanced")
            if options.get('data_structures', False) or options.get('all_analyzers', False):
                logger.info("- Data structure recognition completed")


def main():
    """Main entry point for the DOS decompiler"""
    # Set up argument parser
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
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    # Convert args to options dict
    options = {
        'enhanced': args.enhanced,
        'visualize': args.visualize,
        'data_flow': args.data_flow,
        'improved': args.improved,
        'c_code': args.c_code,
        'call_graph': args.call_graph,
        'resource_analysis': args.resource_analysis,
        'resource_dir': args.resource_dir,
        'state_analysis': args.state_analysis,
        'dos_api': args.dos_api,
        'data_structures': args.data_structures,
        'all_analyzers': args.all_analyzers,
        'debug': args.debug,
    }
    
    try:
        # Create and run the decompiler manager
        manager = DecompilerManager(args.file, args.output, options)
        manager.initialize_decompiler()
        manager.load_analyzers()
        manager.run_decompilation()
        manager.save_output_files()
        manager.print_summary()
        
        logger.info(f"Decompilation completed: {args.file} -> {args.output}")
        return 0
    
    except Exception as e:
        logger.error(f"Error during decompilation: {str(e)}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
