"""
State machine analysis for the Oregon Trail decompiler.

This module analyzes state machines in the decompiled code,
identifying state transitions and visualizing the state flow.
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from ..models import DOSFunction
from ..constants import GAME_STATES, MEMORY_ADDRESSES

# Configure logger
logger = logging.getLogger(__name__)


class StateMachineAnalyzer:
    """Analyzes state machines in the decompiled code."""

    def __init__(self, functions: List[DOSFunction]):
        """
        Initialize with the list of decompiled functions.
        
        Args:
            functions: List of decompiled functions to analyze
        """
        self.functions = functions
        self.state_writes = {}  # Maps function addresses to states they write
        self.state_reads = {}   # Maps function addresses to states they read
        self.state_machine = nx.DiGraph()  # State transition graph
        self.entry_states = set()  # States that are entered directly
        self.exit_states = set()   # States that exit the state machine
        self.analysis_complete = False
        
        # State address constants - could be extended as needed
        self.state_addresses = [addr for addr, name in MEMORY_ADDRESSES.items() 
                               if 'state' in name.lower()]
        
        # Main game state address from Oregon Trail
        self.game_state_addr = None
        for addr, name in MEMORY_ADDRESSES.items():
            if name == 'game_state':
                self.game_state_addr = addr
                break
    
    def analyze(self) -> bool:
        """
        Analyze the code for state machine patterns.
        
        Returns:
            True if analysis was successful, False otherwise
        """
        try:
            if not self.game_state_addr:
                logger.warning("Could not find game_state address in memory addresses")
                return False
                
            logger.info("Starting state machine analysis")
            
            # Step 1: Find all state reads and writes
            self._find_state_operations()
            
            # Step 2: Build the state transition graph
            self._build_state_machine()
            
            # Step 3: Identify entry and exit states
            self._identify_special_states()
            
            # Step 4: Enhance function purposes based on state machine role
            self._enhance_functions_with_state_info()
            
            logger.info(f"Found {len(self.state_writes)} functions that write states")
            logger.info(f"Found {len(self.state_reads)} functions that read states")
            logger.info(f"Identified {len(self.entry_states)} entry states and {len(self.exit_states)} exit states")
            
            self.analysis_complete = True
            return True
            
        except Exception as e:
            logger.error(f"Error in state machine analysis: {str(e)}")
            return False
    
    def _find_state_operations(self):
        """Find all state reads and writes in the code."""
        for func in self.functions:
            state_writes = set()
            state_reads = set()
            
            for instr in func.instructions:
                # Look for writes to game_state
                if self._is_write_to_state(instr):
                    state_value = self._extract_state_value(instr)
                    if state_value is not None:
                        state_writes.add(state_value)
                
                # Look for reads from game_state
                if self._is_read_from_state(instr):
                    state_value = self._extract_state_value(instr)
                    if state_value is not None:
                        state_reads.add(state_value)
            
            if state_writes:
                self.state_writes[func.start_address] = state_writes
            
            if state_reads:
                self.state_reads[func.start_address] = state_reads
    
    def _is_write_to_state(self, instr):
        """
        Check if an instruction writes to a state variable.
        
        Args:
            instr: The instruction to check
            
        Returns:
            True if the instruction writes to a state variable, False otherwise
        """
        if instr.mnemonic.lower() == "mov" and "ptr" in instr.operands:
            # Check for direct writes to game_state
            addr_pattern = f"0x{self.game_state_addr:X}"
            if addr_pattern in instr.operands:
                return True
                
            # Also check for the named version
            if "game_state" in instr.operands:
                return True
        
        return False
    
    def _is_read_from_state(self, instr):
        """
        Check if an instruction reads from a state variable.
        
        Args:
            instr: The instruction to check
            
        Returns:
            True if the instruction reads from a state variable, False otherwise
        """
        if "cmp" in instr.mnemonic.lower() and "ptr" in instr.operands:
            # Check for comparisons with game_state
            addr_pattern = f"0x{self.game_state_addr:X}"
            if addr_pattern in instr.operands:
                return True
                
            # Also check for the named version
            if "game_state" in instr.operands:
                return True
        
        return False
    
    def _extract_state_value(self, instr):
        """
        Extract the state value from an instruction.
        
        Args:
            instr: The instruction to extract state value from
            
        Returns:
            The state value if found, None otherwise
        """
        # For moves to game_state
        if instr.mnemonic.lower() == "mov":
            # Pattern: mov word ptr [game_state], X
            operands = instr.operands.split(',')
            if len(operands) == 2:
                dest, src = operands
                if "game_state" in dest or f"0x{self.game_state_addr:X}" in dest:
                    # Extract the source value
                    src = src.strip()
                    try:
                        # Handle immediate values
                        if src.startswith('0x'):
                            return int(src, 16)
                        elif src.isdigit():
                            return int(src)
                        # Handle named constants
                        for state_id, state_name in GAME_STATES.items():
                            if state_name in src:
                                return state_id
                    except ValueError:
                        pass
        
        # For comparisons with game_state
        elif "cmp" in instr.mnemonic.lower():
            # Pattern: cmp word ptr [game_state], X
            operands = instr.operands.split(',')
            if len(operands) == 2:
                src, val = operands
                if "game_state" in src or f"0x{self.game_state_addr:X}" in src:
                    # Extract the comparison value
                    val = val.strip()
                    try:
                        # Handle immediate values
                        if val.startswith('0x'):
                            return int(val, 16)
                        elif val.isdigit():
                            return int(val)
                        # Handle named constants
                        for state_id, state_name in GAME_STATES.items():
                            if state_name in val:
                                return state_id
                    except ValueError:
                        pass
        
        return None
    
    def _build_state_machine(self):
        """Build a state transition graph based on the analyzed functions."""
        # Create nodes for each state
        for state_id, state_name in GAME_STATES.items():
            self.state_machine.add_node(state_id, name=state_name)
        
        # Add transitions based on function analysis
        for func_addr, writes in self.state_writes.items():
            # Get the function that writes these states
            func = None
            for f in self.functions:
                if f.start_address == func_addr:
                    func = f
                    break
            
            if not func:
                continue
            
            # Get states this function reads
            reads = self.state_reads.get(func_addr, set())
            
            # For each read state, add transitions to each write state
            for from_state in reads:
                for to_state in writes:
                    if from_state in GAME_STATES and to_state in GAME_STATES:
                        self.state_machine.add_edge(
                            from_state, 
                            to_state, 
                            function=func.name,
                            address=func_addr
                        )
        
        # Fill in missing transitions based on call graph
        self._infer_transitions_from_calls()
    
    def _infer_transitions_from_calls(self):
        """Infer state transitions from function calls."""
        # Map functions to the states they write
        func_to_written_states = {}
        for func in self.functions:
            writes = self.state_writes.get(func.start_address, set())
            if writes:
                func_to_written_states[func.start_address] = writes
        
        # Check each function for calls to state-writing functions
        for func in self.functions:
            reads = self.state_reads.get(func.start_address, set())
            
            # Only process functions that read states but don't write them
            writes = self.state_writes.get(func.start_address, set())
            if reads and not writes:
                for call_addr in func.calls:
                    target_writes = func_to_written_states.get(call_addr, set())
                    
                    # For each read state in this function, add transitions to states written by called functions
                    for from_state in reads:
                        for to_state in target_writes:
                            if from_state in GAME_STATES and to_state in GAME_STATES:
                                # Find the called function
                                called_func = None
                                for f in self.functions:
                                    if f.start_address == call_addr:
                                        called_func = f
                                        break
                                
                                if called_func:
                                    self.state_machine.add_edge(
                                        from_state, 
                                        to_state, 
                                        function=called_func.name,
                                        caller=func.name,
                                        address=call_addr
                                    )
    
    def _identify_special_states(self):
        """Identify entry points and exit points in the state machine."""
        # Entry states: states with no incoming transitions or written by the entry function
        for state in self.state_machine.nodes():
            if self.state_machine.in_degree(state) == 0:
                self.entry_states.add(state)
        
        # Also check states written by the entry function
        for func in self.functions:
            if func.name == "entry":
                writes = self.state_writes.get(func.start_address, set())
                self.entry_states.update(writes)
        
        # Exit states: states with no outgoing transitions
        for state in self.state_machine.nodes():
            if self.state_machine.out_degree(state) == 0:
                self.exit_states.add(state)
        
        # Game end state from Oregon Trail
        if 9 in GAME_STATES:  # GAME_STATE_END_GAME
            self.exit_states.add(9)
    
    def _enhance_functions_with_state_info(self):
        """Enhance function documentation with state machine information."""
        # Enhance functions that write to states
        for func_addr, writes in self.state_writes.items():
            for func in self.functions:
                if func.start_address == func_addr:
                    # Convert state IDs to names
                    state_names = []
                    for state_id in writes:
                        if state_id in GAME_STATES:
                            state_names.append(GAME_STATES[state_id])
                        else:
                            state_names.append(f"State_{state_id}")
                    
                    # Add or update function purpose
                    if not hasattr(func, "purpose") or not func.purpose:
                        if len(state_names) == 1:
                            func.purpose = f"Transitions to {state_names[0]} state"
                        else:
                            func.purpose = f"State handler for multiple states: {', '.join(state_names)}"
                    
                    # Add comments about state transitions
                    state_comment = f"Sets game state to: {', '.join(state_names)}"
                    if hasattr(func, "comments"):
                        func.comments.append(state_comment)
                    else:
                        func.comments = [state_comment]
                    
                    # Tag functions that transition to entry/exit states
                    for state_id in writes:
                        if state_id in self.entry_states:
                            if hasattr(func, "comments"):
                                func.comments.append("Handles entry state")
                            
                        if state_id in self.exit_states:
                            if hasattr(func, "comments"):
                                func.comments.append("Handles exit state")
    
    def visualize_state_machine(self, output_file: str = "state_machine.png"):
        """
        Generate a visualization of the state machine.
        
        Args:
            output_file: Path to save the visualization image
            
        Returns:
            Path to the generated visualization file or None if no state machine found
        """
        if not self.analysis_complete:
            logger.warning("State machine analysis not complete, running analyze() first")
            self.analyze()
            
        if not self.state_machine:
            logger.warning("No state machine found to visualize")
            return None
            
        # Create labels and node colors
        labels = {}
        node_colors = []
        
        for node in self.state_machine.nodes():
            if node in GAME_STATES:
                labels[node] = GAME_STATES[node]
            else:
                labels[node] = f"State_{node}"
                
            if node in self.entry_states:
                node_colors.append('green')
            elif node in self.exit_states:
                node_colors.append('red')
            else:
                node_colors.append('skyblue')
        
        # Create edge labels
        edge_labels = {}
        for u, v, data in self.state_machine.edges(data=True):
            if 'function' in data:
                edge_labels[(u, v)] = data['function']
                
        # Generate the visualization
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(self.state_machine, seed=42)  # Consistent layout with seed
        nx.draw_networkx_nodes(self.state_machine, pos, node_color=node_colors, alpha=0.8, node_size=2000)
        nx.draw_networkx_edges(self.state_machine, pos, alpha=0.5, arrows=True, arrowsize=20)
        nx.draw_networkx_labels(self.state_machine, pos, labels, font_size=10)
        nx.draw_networkx_edge_labels(self.state_machine, pos, edge_labels, font_size=8)
        
        plt.title("Oregon Trail Game State Machine")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        logger.info(f"State machine visualization saved to {output_file}")
        return output_file
    
    def generate_state_report(self):
        """
        Generate a report of the state machine analysis.
        
        Returns:
            A formatted report string
        """
        if not self.analysis_complete:
            logger.warning("State machine analysis not complete, running analyze() first")
            self.analyze()
            
        report = []
        report.append("=== State Machine Analysis Report ===")
        report.append("")
        
        # List all states
        report.append("Game States:")
        for state_id, state_name in sorted(GAME_STATES.items()):
            in_deg = self.state_machine.in_degree(state_id) if state_id in self.state_machine else 0
            out_deg = self.state_machine.out_degree(state_id) if state_id in self.state_machine else 0
            report.append(f"  {state_name} (ID: {state_id})")
            report.append(f"    Incoming transitions: {in_deg}")
            report.append(f"    Outgoing transitions: {out_deg}")
        report.append("")
        
        # Entry states
        if self.entry_states:
            report.append("Entry States:")
            for state in sorted(self.entry_states):
                if state in GAME_STATES:
                    report.append(f"  {GAME_STATES[state]} (ID: {state})")
                else:
                    report.append(f"  State_{state}")
            report.append("")
        
        # Exit states
        if self.exit_states:
            report.append("Exit States:")
            for state in sorted(self.exit_states):
                if state in GAME_STATES:
                    report.append(f"  {GAME_STATES[state]} (ID: {state})")
                else:
                    report.append(f"  State_{state}")
            report.append("")
        
        # State transitions
        if self.state_machine.edges():
            report.append("State Transitions:")
            for u, v, data in sorted(self.state_machine.edges(data=True)):
                from_state = GAME_STATES.get(u, f"State_{u}")
                to_state = GAME_STATES.get(v, f"State_{v}")
                function = data.get('function', 'Unknown')
                report.append(f"  {from_state} -> {to_state}")
                report.append(f"    Handled by: {function}")
                if 'caller' in data:
                    report.append(f"    Called from: {data['caller']}")
            report.append("")
        
        # Function roles in state machine
        report.append("Functions Handling State Transitions:")
        state_handlers = {}
        for func_addr in self.state_writes:
            for func in self.functions:
                if func.start_address == func_addr:
                    writes = self.state_writes[func_addr]
                    state_names = []
                    for state_id in writes:
                        state_names.append(GAME_STATES.get(state_id, f"State_{state_id}"))
                    state_handlers[func.name] = ", ".join(state_names)
        
        for func_name, states in sorted(state_handlers.items()):
            report.append(f"  {func_name}: Sets state to {states}")
        
        return "\n".join(report)