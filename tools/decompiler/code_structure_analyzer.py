"""
Higher-level code structure analyzer for the Oregon Trail decompiler.

This module analyzes the control flow and data flow of the decompiled code
to identify higher-level structures and patterns, such as loops, conditionals,
and function calls. It then transforms the code into a more readable form.
"""

import re
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from collections import defaultdict

from .models import DOSFunction, X86Instruction, Variable
from .control_flow import ControlFlowGraph, BasicBlock


class FunctionRelationship:
    """Represents a relationship between two functions."""
    
    def __init__(self, caller: DOSFunction, callee: DOSFunction, call_count: int = 1):
        """
        Initialize a function relationship.
        
        Args:
            caller: The calling function
            callee: The called function
            call_count: Number of times the caller calls the callee
        """
        self.caller = caller
        self.callee = callee
        self.call_count = call_count
    
    def __str__(self) -> str:
        return f"{self.caller.name} -> {self.callee.name} ({self.call_count} calls)"


class FunctionGroup:
    """Represents a group of related functions."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a function group.
        
        Args:
            name: Name of the group
            description: Description of the group's purpose
        """
        self.name = name
        self.description = description
        self.functions: List[DOSFunction] = []
        self.relationships: List[FunctionRelationship] = []
    
    def add_function(self, function: DOSFunction) -> None:
        """
        Add a function to the group.
        
        Args:
            function: Function to add
        """
        if function not in self.functions:
            self.functions.append(function)
    
    def add_relationship(self, relationship: FunctionRelationship) -> None:
        """
        Add a relationship to the group.
        
        Args:
            relationship: Relationship to add
        """
        self.relationships.append(relationship)
    
    def __str__(self) -> str:
        return f"{self.name}: {len(self.functions)} functions, {len(self.relationships)} relationships"


class HigherLevelStructure:
    """Base class for higher-level code structures."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a higher-level structure.
        
        Args:
            name: Name of the structure
            description: Description of the structure's purpose
        """
        self.name = name
        self.description = description
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class Loop(HigherLevelStructure):
    """Represents a loop structure in the code."""
    
    def __init__(self, name: str, header_block: BasicBlock, body_blocks: List[BasicBlock], exit_blocks: List[BasicBlock], loop_variable: Optional[Variable] = None):
        """
        Initialize a loop structure.
        
        Args:
            name: Name of the loop
            header_block: Entry block of the loop
            body_blocks: Blocks in the loop body
            exit_blocks: Blocks that exit the loop
            loop_variable: Variable used as loop counter (if any)
        """
        super().__init__(name, "Loop structure")
        self.header_block = header_block
        self.body_blocks = body_blocks
        self.exit_blocks = exit_blocks
        self.loop_variable = loop_variable
    
    def __str__(self) -> str:
        return f"{self.name}: Loop with {len(self.body_blocks)} body blocks"


class Conditional(HigherLevelStructure):
    """Represents a conditional structure in the code."""
    
    def __init__(self, name: str, condition_block: BasicBlock, true_blocks: List[BasicBlock], false_blocks: List[BasicBlock], merge_block: Optional[BasicBlock] = None):
        """
        Initialize a conditional structure.
        
        Args:
            name: Name of the conditional
            condition_block: Block containing the condition
            true_blocks: Blocks executed when condition is true
            false_blocks: Blocks executed when condition is false
            merge_block: Block where control flow merges after the conditional
        """
        super().__init__(name, "Conditional structure")
        self.condition_block = condition_block
        self.true_blocks = true_blocks
        self.false_blocks = false_blocks
        self.merge_block = merge_block
    
    def __str__(self) -> str:
        return f"{self.name}: Conditional with {len(self.true_blocks)} true blocks, {len(self.false_blocks)} false blocks"


class Switch(HigherLevelStructure):
    """Represents a switch structure in the code."""
    
    def __init__(self, name: str, condition_block: BasicBlock, cases: Dict[int, List[BasicBlock]], default_blocks: List[BasicBlock], merge_block: Optional[BasicBlock] = None):
        """
        Initialize a switch structure.
        
        Args:
            name: Name of the switch
            condition_block: Block containing the condition
            cases: Dictionary mapping case values to blocks
            default_blocks: Blocks executed for the default case
            merge_block: Block where control flow merges after the switch
        """
        super().__init__(name, "Switch structure")
        self.condition_block = condition_block
        self.cases = cases
        self.default_blocks = default_blocks
        self.merge_block = merge_block
    
    def __str__(self) -> str:
        return f"{self.name}: Switch with {len(self.cases)} cases"


class FunctionCall(HigherLevelStructure):
    """Represents a function call structure in the code."""
    
    def __init__(self, name: str, caller_block: BasicBlock, callee: DOSFunction, return_block: Optional[BasicBlock] = None):
        """
        Initialize a function call structure.
        
        Args:
            name: Name of the function call
            caller_block: Block containing the call
            callee: Called function
            return_block: Block where control returns after the call
        """
        super().__init__(name, "Function call structure")
        self.caller_block = caller_block
        self.callee = callee
        self.return_block = return_block
    
    def __str__(self) -> str:
        return f"{self.name}: Call to {self.callee.name}"


class CodeStructureAnalyzer:
    """Analyzes code structure to identify higher-level patterns."""
    
    def __init__(self, functions: List[DOSFunction]):
        """
        Initialize the code structure analyzer.
        
        Args:
            functions: List of functions to analyze
        """
        self.functions = functions
        self.function_map: Dict[int, DOSFunction] = {func.start_address: func for func in functions}
        self.function_groups: List[FunctionGroup] = []
        self.higher_level_structures: Dict[DOSFunction, List[HigherLevelStructure]] = defaultdict(list)
    
    def analyze(self) -> None:
        """Analyze the code structure."""
        self._build_call_graph()
        self._identify_function_groups()
        self._identify_higher_level_structures()
    
    def _build_call_graph(self) -> None:
        """Build a call graph of function relationships."""
        self.call_graph: Dict[DOSFunction, List[Tuple[DOSFunction, int]]] = defaultdict(list)
        
        for func in self.functions:
            for call_addr in func.calls:
                if call_addr in self.function_map:
                    callee = self.function_map[call_addr]
                    
                    # Check if this call already exists
                    for existing_callee, count in self.call_graph[func]:
                        if existing_callee == callee:
                            # Increment call count
                            self.call_graph[func].remove((existing_callee, count))
                            self.call_graph[func].append((existing_callee, count + 1))
                            break
                    else:
                        # Add new call
                        self.call_graph[func].append((callee, 1))
    
    def _identify_function_groups(self) -> None:
        """Identify groups of related functions."""
        # Create initial groups based on common prefixes in function names
        name_groups: Dict[str, List[DOSFunction]] = defaultdict(list)
        
        for func in self.functions:
            # Extract prefix from function name
            match = re.match(r'^([a-zA-Z]+)_', func.name)
            if match:
                prefix = match.group(1)
                name_groups[prefix].append(func)
        
        # Create function groups
        for prefix, funcs in name_groups.items():
            if len(funcs) > 1:
                group = FunctionGroup(f"{prefix}_group", f"Functions with prefix {prefix}")
                for func in funcs:
                    group.add_function(func)
                self.function_groups.append(group)
        
        # Merge groups based on call relationships
        self._merge_function_groups()
        
        # Identify game-specific function groups
        self._identify_game_function_groups()
    
    def _merge_function_groups(self) -> None:
        """Merge function groups based on call relationships."""
        # Build a map of functions to their groups
        func_to_group: Dict[DOSFunction, FunctionGroup] = {}
        for group in self.function_groups:
            for func in group.functions:
                func_to_group[func] = group
        
        # Check for relationships between groups
        merged = True
        while merged:
            merged = False
            for func, callees in self.call_graph.items():
                if func not in func_to_group:
                    continue
                
                func_group = func_to_group[func]
                
                for callee, count in callees:
                    if callee in func_to_group and func_to_group[callee] != func_group:
                        # Merge groups
                        callee_group = func_to_group[callee]
                        for f in callee_group.functions:
                            func_group.add_function(f)
                            func_to_group[f] = func_group
                        
                        self.function_groups.remove(callee_group)
                        merged = True
                        break
                
                if merged:
                    break
    
    def _identify_game_function_groups(self) -> None:
        """Identify game-specific function groups."""
        # Travel-related functions
        travel_group = FunctionGroup("travel_group", "Functions related to travel mechanics")
        
        # Hunting-related functions
        hunting_group = FunctionGroup("hunting_group", "Functions related to hunting mechanics")
        
        # Trading-related functions
        trading_group = FunctionGroup("trading_group", "Functions related to trading mechanics")
        
        # River crossing functions
        river_group = FunctionGroup("river_group", "Functions related to river crossing")
        
        # Event-related functions
        event_group = FunctionGroup("event_group", "Functions related to game events")
        
        # UI-related functions
        ui_group = FunctionGroup("ui_group", "Functions related to user interface")
        
        # File I/O functions
        file_group = FunctionGroup("file_group", "Functions related to file I/O")
        
        # Add functions to groups based on their purpose
        for func in self.functions:
            if hasattr(func, 'purpose'):
                purpose = func.purpose.lower() if func.purpose else ""
                
                if "travel" in purpose or "distance" in purpose or "miles" in purpose:
                    travel_group.add_function(func)
                elif "hunt" in purpose or "animal" in purpose or "shoot" in purpose:
                    hunting_group.add_function(func)
                elif "trade" in purpose or "buy" in purpose or "sell" in purpose:
                    trading_group.add_function(func)
                elif "river" in purpose or "cross" in purpose or "ford" in purpose:
                    river_group.add_function(func)
                elif "event" in purpose or "random" in purpose:
                    event_group.add_function(func)
                elif "display" in purpose or "screen" in purpose or "menu" in purpose:
                    ui_group.add_function(func)
                elif "file" in purpose or "save" in purpose or "load" in purpose:
                    file_group.add_function(func)
        
        # Add non-empty groups
        for group in [travel_group, hunting_group, trading_group, river_group, event_group, ui_group, file_group]:
            if group.functions:
                self.function_groups.append(group)
    
    def _identify_higher_level_structures(self) -> None:
        """Identify higher-level structures in the code."""
        for func in self.functions:
            if not hasattr(func, 'cfg') or not func.cfg:
                continue
            
            # Identify loops
            self._identify_loops(func)
            
            # Identify conditionals
            self._identify_conditionals(func)
            
            # Identify switches
            self._identify_switches(func)
            
            # Identify function calls
            self._identify_function_calls(func)
    
    def _identify_loops(self, func: DOSFunction) -> None:
        """
        Identify loops in a function.
        
        Args:
            func: Function to analyze
        """
        if not hasattr(func, 'cfg') or not func.cfg or not hasattr(func.cfg, 'blocks'):
            return
        
        # Find back edges (edges from a node to a dominator)
        back_edges = []
        for block in func.cfg.blocks:
            for succ_addr in block.successors:
                # Find successor block
                succ_block = None
                for b in func.cfg.blocks:
                    if b.start_address == succ_addr:
                        succ_block = b
                        break
                
                if succ_block and self._dominates(succ_block, block, func.cfg):
                    back_edges.append((block, succ_block))
        
        # Identify natural loops
        for source, target in back_edges:
            loop_blocks = self._find_natural_loop(source, target, func.cfg)
            
            # Find loop variable
            loop_var = self._find_loop_variable(loop_blocks, func)
            
            # Find exit blocks
            exit_blocks = []
            for block in loop_blocks:
                for succ_addr in block.successors:
                    # Find successor block
                    succ_block = None
                    for b in func.cfg.blocks:
                        if b.start_address == succ_addr:
                            succ_block = b
                            break
                    
                    if succ_block and succ_block not in loop_blocks:
                        exit_blocks.append(succ_block)
            
            # Create loop structure
            loop = Loop(
                f"loop_{target.start_address:X}",
                target,
                loop_blocks,
                exit_blocks,
                loop_var
            )
            
            self.higher_level_structures[func].append(loop)
    
    def _dominates(self, dominator: BasicBlock, block: BasicBlock, cfg: ControlFlowGraph) -> bool:
        """
        Check if dominator dominates block.
        
        Args:
            dominator: Potential dominator block
            block: Block to check
            cfg: Control flow graph
            
        Returns:
            True if dominator dominates block, False otherwise
        """
        # Simple implementation: check if all paths from entry to block go through dominator
        if not hasattr(cfg, 'entry_block') or not cfg.entry_block:
            return False
        
        if dominator == block:
            return False
        
        # BFS from entry to block
        visited = set()
        queue = [cfg.entry_block]
        
        while queue:
            current = queue.pop(0)
            
            if current == block:
                return False
            
            if current == dominator:
                continue
            
            visited.add(current)
            
            for succ_addr in current.successors:
                # Find successor block
                succ_block = None
                for b in cfg.blocks:
                    if b.start_address == succ_addr:
                        succ_block = b
                        break
                
                if succ_block and succ_block not in visited:
                    queue.append(succ_block)
        
        return True
    
    def _find_natural_loop(self, source: BasicBlock, target: BasicBlock, cfg: ControlFlowGraph) -> List[BasicBlock]:
        """
        Find the natural loop formed by a back edge.
        
        Args:
            source: Source block of the back edge
            target: Target block of the back edge (loop header)
            cfg: Control flow graph
            
        Returns:
            List of blocks in the loop
        """
        loop_blocks = [target, source]
        
        # Add blocks that can reach source without going through target
        worklist = [source]
        while worklist:
            current = worklist.pop(0)
            
            # Find predecessors
            for block in cfg.blocks:
                if not hasattr(block, 'successors'):
                    continue
                
                for succ_addr in block.successors:
                    if succ_addr == current.start_address and block != target and block not in loop_blocks:
                        loop_blocks.append(block)
                        worklist.append(block)
        
        return loop_blocks
    
    def _find_loop_variable(self, loop_blocks: List[BasicBlock], func: DOSFunction) -> Optional[Variable]:
        """
        Find the loop variable for a loop.
        
        Args:
            loop_blocks: Blocks in the loop
            func: Function containing the loop
            
        Returns:
            Loop variable if found, None otherwise
        """
        if not hasattr(func, 'variables'):
            return None
        
        # Look for variables that are incremented or decremented in the loop
        for block in loop_blocks:
            for instr in block.instructions:
                if instr.mnemonic in ['inc', 'dec', 'add', 'sub']:
                    # Extract variable from operands
                    operands = instr.operands.split(',')
                    if len(operands) == 1:
                        var_name = operands[0].strip()
                    else:
                        var_name = operands[0].strip()
                    
                    # Find variable in function variables
                    for var in func.variables.values():
                        if hasattr(var, 'name') and var.name == var_name:
                            return var
        
        return None
    
    def _identify_conditionals(self, func: DOSFunction) -> None:
        """
        Identify conditionals in a function.
        
        Args:
            func: Function to analyze
        """
        if not hasattr(func, 'cfg') or not func.cfg or not hasattr(func.cfg, 'blocks'):
            return
        
        for block in func.cfg.blocks:
            if len(block.successors) == 2:
                # This is a potential conditional
                
                # Find successor blocks
                true_block = None
                false_block = None
                
                for b in func.cfg.blocks:
                    if b.start_address == block.successors[0]:
                        true_block = b
                    elif b.start_address == block.successors[1]:
                        false_block = b
                
                if true_block and false_block:
                    # Find true and false blocks
                    true_blocks = self._find_reachable_blocks(true_block, func.cfg, set())
                    false_blocks = self._find_reachable_blocks(false_block, func.cfg, set())
                    
                    # Find merge block (if any)
                    merge_block = self._find_merge_block(true_blocks, false_blocks, func.cfg)
                    
                    # Create conditional structure
                    conditional = Conditional(
                        f"cond_{block.start_address:X}",
                        block,
                        true_blocks,
                        false_blocks,
                        merge_block
                    )
                    
                    self.higher_level_structures[func].append(conditional)
    
    def _find_reachable_blocks(self, start_block: BasicBlock, cfg: ControlFlowGraph, visited: Set[BasicBlock]) -> List[BasicBlock]:
        """
        Find blocks reachable from a start block.
        
        Args:
            start_block: Starting block
            cfg: Control flow graph
            visited: Set of visited blocks
            
        Returns:
            List of reachable blocks
        """
        if start_block in visited:
            return []
        
        visited.add(start_block)
        reachable = [start_block]
        
        for succ_addr in start_block.successors:
            # Find successor block
            succ_block = None
            for b in cfg.blocks:
                if b.start_address == succ_addr:
                    succ_block = b
                    break
            
            if succ_block:
                reachable.extend(self._find_reachable_blocks(succ_block, cfg, visited))
        
        return reachable
    
    def _find_merge_block(self, true_blocks: List[BasicBlock], false_blocks: List[BasicBlock], cfg: ControlFlowGraph) -> Optional[BasicBlock]:
        """
        Find the merge block for a conditional.
        
        Args:
            true_blocks: Blocks in the true branch
            false_blocks: Blocks in the false branch
            cfg: Control flow graph
            
        Returns:
            Merge block if found, None otherwise
        """
        # Find blocks that both branches can reach
        true_successors = set()
        for block in true_blocks:
            for succ_addr in block.successors:
                # Find successor block
                for b in cfg.blocks:
                    if b.start_address == succ_addr and b not in true_blocks:
                        true_successors.add(b)
        
        false_successors = set()
        for block in false_blocks:
            for succ_addr in block.successors:
                # Find successor block
                for b in cfg.blocks:
                    if b.start_address == succ_addr and b not in false_blocks:
                        false_successors.add(b)
        
        # Find common successors
        common_successors = true_successors.intersection(false_successors)
        
        if common_successors:
            # Return the first common successor
            return list(common_successors)[0]
        
        return None
    
    def _identify_switches(self, func: DOSFunction) -> None:
        """
        Identify switches in a function.
        
        Args:
            func: Function to analyze
        """
        if not hasattr(func, 'cfg') or not func.cfg or not hasattr(func.cfg, 'blocks'):
            return
        
        for block in func.cfg.blocks:
            # Look for blocks with many successors or a jump table pattern
            if len(block.successors) > 2:
                # This is a potential switch
                
                # Find case blocks
                cases = {}
                default_blocks = []
                
                # Simple heuristic: assume successors are case blocks
                for i, succ_addr in enumerate(block.successors):
                    # Find successor block
                    succ_block = None
                    for b in func.cfg.blocks:
                        if b.start_address == succ_addr:
                            succ_block = b
                            break
                    
                    if succ_block:
                        if i == len(block.successors) - 1:
                            # Assume last successor is default case
                            default_blocks = [succ_block]
                        else:
                            # Assume other successors are case blocks
                            cases[i] = [succ_block]
                
                if cases:
                    # Find merge block (if any)
                    all_case_blocks = []
                    for case_blocks in cases.values():
                        all_case_blocks.extend(case_blocks)
                    
                    merge_block = self._find_merge_block(all_case_blocks, default_blocks, func.cfg)
                    
                    # Create switch structure
                    switch = Switch(
                        f"switch_{block.start_address:X}",
                        block,
                        cases,
                        default_blocks,
                        merge_block
                    )
                    
                    self.higher_level_structures[func].append(switch)
    
    def _identify_function_calls(self, func: DOSFunction) -> None:
        """
        Identify function calls in a function.
        
        Args:
            func: Function to analyze
        """
        if not hasattr(func, 'cfg') or not func.cfg or not hasattr(func.cfg, 'blocks'):
            return
        
        for block in func.cfg.blocks:
            for instr in block.instructions:
                if instr.mnemonic == 'call':
                    # This is a function call
                    
                    # Extract call address
                    try:
                        call_addr = int(instr.operands, 16)
                    except ValueError:
                        continue
                    
                    # Find called function
                    if call_addr in self.function_map:
                        callee = self.function_map[call_addr]
                        
                        # Find return block (if any)
                        return_block = None
                        if len(block.successors) == 1:
                            # Find successor block
                            for b in func.cfg.blocks:
                                if b.start_address == block.successors[0]:
                                    return_block = b
                                    break
                        
                        # Create function call structure
                        function_call = FunctionCall(
                            f"call_{block.start_address:X}_{call_addr:X}",
                            block,
                            callee,
                            return_block
                        )
                        
                        self.higher_level_structures[func].append(function_call)
    
    def get_function_groups(self) -> List[FunctionGroup]:
        """
        Get the identified function groups.
        
        Returns:
            List of function groups
        """
        return self.function_groups
    
    def get_higher_level_structures(self, func: DOSFunction) -> List[HigherLevelStructure]:
        """
        Get the higher-level structures for a function.
        
        Args:
            func: Function to get structures for
            
        Returns:
            List of higher-level structures
        """
        return self.higher_level_structures.get(func, [])
    
    def get_all_higher_level_structures(self) -> Dict[DOSFunction, List[HigherLevelStructure]]:
        """
        Get all higher-level structures.
        
        Returns:
            Dictionary mapping functions to their higher-level structures
        """
        return self.higher_level_structures
    
    def generate_structure_report(self) -> str:
        """
        Generate a report of the identified structures.
        
        Returns:
            Report string
        """
        report = []
        
        # Add function groups
        report.append("Function Groups:")
        for group in self.function_groups:
            report.append(f"  {group}")
            for func in group.functions:
                report.append(f"    {func.name}")
        
        report.append("")
        
        # Add higher-level structures
        report.append("Higher-Level Structures:")
        for func, structures in self.higher_level_structures.items():
            if structures:
                report.append(f"  {func.name}:")
                for structure in structures:
                    report.append(f"    {structure}")
        
        return "\n".join(report)


def analyze_code_structure(functions: List[DOSFunction]) -> CodeStructureAnalyzer:
    """
    Analyze the code structure of a set of functions.
    
    Args:
        functions: List of functions to analyze
        
    Returns:
        Code structure analyzer
    """
    analyzer = CodeStructureAnalyzer(functions)
    analyzer.analyze()
    return analyzer