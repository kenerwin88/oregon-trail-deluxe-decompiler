"""
Resource reference analysis for the Oregon Trail decompiler.
"""

import os
import re
from typing import Dict, List, Set, Tuple
from .models import DOSFunction

# Resource file extensions in Oregon Trail
RESOURCE_EXTENSIONS = {
    '.CTR': 'Control file',
    '.PC4': '4-color graphics',
    '.PC8': '8-color graphics',
    '.SND': 'Sound data',
    '.ANI': 'Animation data',
    '.XMI': 'MIDI music data',
    '.16': '16-color graphics',
    '.256': '256-color graphics',
    '.GFT': 'Game font',
    '.GBT': 'Game data table'
}

# Common patterns for resource loading in DOS games
RESOURCE_LOAD_PATTERNS = [
    r'open.*\.(ctr|pc4|pc8|snd|ani|xmi|16|256|gft|gbt)',
    r'load.*\.(ctr|pc4|pc8|snd|ani|xmi|16|256|gft|gbt)',
    r'read.*\.(ctr|pc4|pc8|snd|ani|xmi|16|256|gft|gbt)',
    r'access.*\.(ctr|pc4|pc8|snd|ani|xmi|16|256|gft|gbt)'
]

# File name patterns in string literals
FILENAME_PATTERNS = [
    r'([A-Z0-9_]+\.(CTR|PC4|PC8|SND|ANI|XMI|16|256|GFT|GBT))',
    r'([A-Z0-9_]+\.(ctr|pc4|pc8|snd|ani|xmi|16|256|gft|gbt))'
]


class ResourceAnalyzer:
    """Analyzes references to resource files in the game code."""

    def __init__(self, functions: List[DOSFunction], strings: Dict[int, str], resource_dir: str = None):
        """
        Initialize the analyzer with functions, strings, and an optional resource directory.
        
        Args:
            functions: List of functions from the decompiled code
            strings: Dictionary of strings from the decompiled code
            resource_dir: Directory containing the game's resource files (optional)
        """
        self.functions = functions
        self.strings = strings
        self.resource_dir = resource_dir
        self.function_resources = {}  # Maps function address to resource references
        self.resource_functions = {}  # Maps resource files to functions that use them
        self.available_resources = []  # List of available resource files if resource_dir is provided
        
        # Scan for available resources if a directory is provided
        if resource_dir and os.path.isdir(resource_dir):
            self._scan_resource_directory()
    
    def _scan_resource_directory(self):
        """Scan the resource directory for resource files."""
        for root, _, files in os.walk(self.resource_dir):
            for file in files:
                ext = os.path.splitext(file)[1].upper()
                if ext in RESOURCE_EXTENSIONS:
                    self.available_resources.append(os.path.join(root, file))
    
    def analyze(self):
        """Analyze the code for resource references."""
        # First, find all string references to resource files
        resource_strings = {}
        for addr, string in self.strings.items():
            for pattern in FILENAME_PATTERNS:
                matches = re.findall(pattern, string, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):  # Some regex implementations return tuples
                            resource_strings[addr] = match[0]
                        else:
                            resource_strings[addr] = match
        
        # Now match functions that reference these strings
        for func in self.functions:
            resources_used = set()
            
            # Check all instructions for string references
            for instr in func.instructions:
                # Look for memory references that might be to string addresses
                for addr in resource_strings:
                    # This is a simple heuristic - in reality, you'd need more sophisticated analysis
                    if f"0x{addr:X}" in instr.operands or f"0x{addr:x}" in instr.operands:
                        resources_used.add(resource_strings[addr])
                
                # Also check instruction text for resource loading patterns
                instr_text = f"{instr.mnemonic} {instr.operands}"
                for pattern in RESOURCE_LOAD_PATTERNS:
                    if re.search(pattern, instr_text, re.IGNORECASE):
                        # Extract the filename if possible
                        for filename_pattern in FILENAME_PATTERNS:
                            filename_matches = re.findall(filename_pattern, instr_text, re.IGNORECASE)
                            if filename_matches:
                                for match in filename_matches:
                                    if isinstance(match, tuple):
                                        resources_used.add(match[0])
                                    else:
                                        resources_used.add(match)
            
            # Store the resources used by this function
            if resources_used:
                self.function_resources[func.start_address] = resources_used
                
                # Also update the reverse mapping
                for resource in resources_used:
                    if resource not in self.resource_functions:
                        self.resource_functions[resource] = set()
                    self.resource_functions[resource].add(func.start_address)
                    
                # Tag the function with resource information
                resource_types = set()
                for resource in resources_used:
                    ext = os.path.splitext(resource)[1].upper()
                    if ext in RESOURCE_EXTENSIONS:
                        resource_types.add(RESOURCE_EXTENSIONS[ext])
                
                # Add purpose information if not already present
                if not hasattr(func, "purpose") or not func.purpose:
                    if len(resource_types) == 1:
                        func.purpose = f"Handles {next(iter(resource_types))} resources"
                    else:
                        func.purpose = f"Handles multiple resource types: {', '.join(resource_types)}"
                
                # Add a comment about resources
                resource_comment = f"Uses resources: {', '.join(resources_used)}"
                if hasattr(func, "comments"):
                    func.comments.append(resource_comment)
                else:
                    func.comments = [resource_comment]
        
        return self.function_resources, self.resource_functions
    
    def find_resource_handlers(self) -> Dict[str, List[DOSFunction]]:
        """
        Find functions that handle specific types of resources.
        
        Returns:
            Dictionary mapping resource types to lists of handler functions
        """
        handlers = {}
        
        for ext, desc in RESOURCE_EXTENSIONS.items():
            handlers[desc] = []
            
            # Find functions that use resources of this type
            for resource, func_addrs in self.resource_functions.items():
                if resource.upper().endswith(ext):
                    for addr in func_addrs:
                        for func in self.functions:
                            if func.start_address == addr:
                                handlers[desc].append(func)
        
        return handlers
    
    def generate_resource_report(self) -> str:
        """
        Generate a report of resource usage.
        
        Returns:
            A formatted report string
        """
        report = []
        report.append("=== Resource Analysis Report ===")
        report.append("")
        
        # Count by resource type
        resource_type_counts = {}
        for resource in self.resource_functions:
            ext = os.path.splitext(resource)[1].upper()
            if ext in RESOURCE_EXTENSIONS:
                if ext not in resource_type_counts:
                    resource_type_counts[ext] = 0
                resource_type_counts[ext] += 1
        
        report.append("Resource Types Referenced:")
        for ext, count in sorted(resource_type_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {ext} ({RESOURCE_EXTENSIONS.get(ext, 'Unknown')}): {count} files")
        report.append("")
        
        # Most referenced resources
        if self.resource_functions:
            report.append("Most Referenced Resources:")
            sorted_resources = sorted(
                self.resource_functions.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            for resource, funcs in sorted_resources[:10]:  # Top 10
                report.append(f"  {resource}: Used by {len(funcs)} functions")
            report.append("")
        
        # Functions using the most resources
        if self.function_resources:
            report.append("Functions Using Most Resources:")
            sorted_funcs = sorted(
                self.function_resources.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            for func_addr, resources in sorted_funcs[:10]:  # Top 10
                func_name = "Unknown"
                for func in self.functions:
                    if func.start_address == func_addr:
                        func_name = func.name
                        break
                report.append(f"  {func_name}: Uses {len(resources)} resources")
            report.append("")
        
        # Resources in directory but not referenced
        if self.available_resources:
            referenced_files = set(res.upper() for res in self.resource_functions.keys())
            unreferenced = []
            
            for path in self.available_resources:
                filename = os.path.basename(path).upper()
                if filename not in referenced_files:
                    unreferenced.append(filename)
            
            if unreferenced:
                report.append("Resources Not Referenced in Code:")
                for res in sorted(unreferenced):
                    report.append(f"  {res}")
                report.append("")
        
        return "\n".join(report)