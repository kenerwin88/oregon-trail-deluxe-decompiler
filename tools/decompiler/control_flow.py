"""
Control flow structure improvement for the decompiler.
"""

from typing import Dict, List

from .models import BasicBlock, ControlFlowGraph


class ControlFlowStructure:
    """Base class for control flow structures"""

    def __init__(self, blocks: List[BasicBlock]):
        self.blocks = blocks

    def generate_code(self, indent_level: int) -> List[str]:
        """Generate code for this structure"""
        raise NotImplementedError("Subclasses must implement generate_code")


class SequenceStructure(ControlFlowStructure):
    """Represents a sequence of statements"""

    def generate_code(self, indent_level: int, code_generator) -> List[str]:
        """Generate code for a sequence"""
        lines = []
        for block in self.blocks:
            lines.extend(
                code_generator._generate_block_code(block, set(), indent_level)
            )
        return lines


class IfStructure(ControlFlowStructure):
    """Represents an if statement"""

    def __init__(
        self,
        condition_block: BasicBlock,
        true_blocks: List[BasicBlock],
        false_blocks: List[BasicBlock] = None,
    ):
        super().__init__([condition_block] + (true_blocks or []) + (false_blocks or []))
        self.condition_block = condition_block
        self.true_blocks = true_blocks or []
        self.false_blocks = false_blocks or []

    def generate_code(self, indent_level: int, code_generator) -> List[str]:
        """Generate code for an if statement"""
        lines = []

        # Generate condition
        last_instr = self.condition_block.instructions[-1]
        condition = code_generator._translate_condition(last_instr.mnemonic)

        # Add the if statement
        lines.append(f"{'    ' * indent_level}if ({condition}) {{")

        # Add the true branch
        for block in self.true_blocks:
            lines.extend(
                code_generator._generate_block_code(block, set(), indent_level + 1)
            )

        # Add the else branch if it exists
        if self.false_blocks:
            lines.append(f"{'    ' * indent_level}}} else {{")
            for block in self.false_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 1)
                )

        # Close the if statement
        lines.append(f"{'    ' * indent_level}}}")

        return lines


class LoopStructure(ControlFlowStructure):
    """Represents a loop"""

    def __init__(
        self,
        header_block: BasicBlock,
        body_blocks: List[BasicBlock],
        loop_type: str = "while",
    ):
        super().__init__([header_block] + body_blocks)
        self.header_block = header_block
        self.body_blocks = body_blocks
        self.loop_type = loop_type  # "while", "do-while", or "for"
        self.initialization = None  # For for loops
        self.condition = None  # For all loops
        self.increment = None  # For for loops

    def generate_code(self, indent_level: int, code_generator) -> List[str]:
        """Generate code for a loop"""
        lines = []

        if self.loop_type == "while":
            # Generate condition
            last_instr = self.header_block.instructions[-1]
            condition = code_generator._translate_condition(last_instr.mnemonic)

            # Add the while statement
            lines.append(f"{'    ' * indent_level}while ({condition}) {{")

            # Add the loop body
            for block in self.body_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 1)
                )

            # Close the while statement
            lines.append(f"{'    ' * indent_level}}}")

        elif self.loop_type == "do-while":
            # Add the do statement
            lines.append(f"{'    ' * indent_level}do {{")

            # Add the loop body
            for block in self.body_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 1)
                )

            # Generate condition
            last_instr = self.header_block.instructions[-1]
            condition = code_generator._translate_condition(last_instr.mnemonic)

            # Close the do-while statement
            lines.append(f"{'    ' * indent_level}}} while ({condition});")

        elif self.loop_type == "for":
            # Add the for statement
            if self.initialization and self.condition and self.increment:
                lines.append(
                    f"{'    ' * indent_level}for ({self.initialization}; {self.condition}; {self.increment}) {{"
                )
            else:
                # Fallback to while loop if for loop components are not available
                last_instr = self.header_block.instructions[-1]
                condition = code_generator._translate_condition(last_instr.mnemonic)
                lines.append(f"{'    ' * indent_level}while ({condition}) {{")

            # Add the loop body
            for block in self.body_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 1)
                )

            # Close the for statement
            lines.append(f"{'    ' * indent_level}}}")

        return lines


class SwitchStructure(ControlFlowStructure):
    """Represents a switch statement"""

    def __init__(
        self,
        header_block: BasicBlock,
        cases: Dict[int, List[BasicBlock]],
        default_blocks: List[BasicBlock] = None,
    ):
        all_blocks = [header_block]
        for case_blocks in cases.values():
            all_blocks.extend(case_blocks)
        if default_blocks:
            all_blocks.extend(default_blocks)

        super().__init__(all_blocks)
        self.header_block = header_block
        self.cases = cases
        self.default_blocks = default_blocks or []

    def generate_code(self, indent_level: int, code_generator) -> List[str]:
        """Generate code for a switch statement"""
        lines = []

        # Extract the switch variable from the header block
        switch_var = "switch_var"  # Default name
        for instr in self.header_block.instructions:
            if instr.mnemonic == "mov" and "," in instr.operands:
                parts = instr.operands.split(",")
                if len(parts) == 2:
                    switch_var = parts[0].strip()
                    break

        # Add the switch statement
        lines.append(f"{'    ' * indent_level}switch ({switch_var}) {{")

        # Add the cases
        for case_value, case_blocks in self.cases.items():
            lines.append(f"{'    ' * (indent_level + 1)}case {case_value}:")
            for block in case_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 2)
                )
            lines.append(f"{'    ' * (indent_level + 2)}break;")

        # Add the default case if it exists
        if self.default_blocks:
            lines.append(f"{'    ' * (indent_level + 1)}default:")
            for block in self.default_blocks:
                lines.extend(
                    code_generator._generate_block_code(block, set(), indent_level + 2)
                )

        # Close the switch statement
        lines.append(f"{'    ' * indent_level}}}")

        return lines


def identify_loops(cfg: ControlFlowGraph) -> Dict[int, LoopStructure]:
    """
    Identify loops in the control flow graph.

    Args:
        cfg: The control flow graph

    Returns:
        A dictionary mapping loop header addresses to LoopStructure objects
    """
    loops = {}

    # Find back edges (edges from a node to one of its ancestors in the DFS tree)
    # A back edge indicates a loop
    visited = set()
    stack = []

    def dfs(block_addr):
        visited.add(block_addr)
        stack.append(block_addr)

        block = cfg.blocks.get(block_addr)
        if not block:
            stack.pop()
            return

        for succ_addr in block.successors:
            if succ_addr in stack:
                # Found a back edge, which indicates a loop
                # The target of the back edge is the loop header
                header_addr = succ_addr

                # Identify the loop body
                loop_body = []
                for addr in stack[stack.index(header_addr) :]:
                    if addr != header_addr:
                        loop_body.append(cfg.blocks[addr])

                # Create a loop structure
                header_block = cfg.blocks[header_addr]

                # Determine the loop type
                loop_type = "while"

                # Check if it's a do-while loop
                if (
                    len(loop_body) > 0
                    and loop_body[-1].successors
                    and header_addr in loop_body[-1].successors
                ):
                    loop_type = "do-while"

                # Check if it's a for loop
                # This is a simplified heuristic - in a real implementation, you'd need more sophisticated analysis
                if len(header_block.instructions) >= 3:
                    first_instr = header_block.instructions[0]
                    if first_instr.mnemonic == "mov" and "," in first_instr.operands:
                        loop_type = "for"

                loops[header_addr] = LoopStructure(header_block, loop_body, loop_type)
            elif succ_addr not in visited:
                dfs(succ_addr)

        stack.pop()

    # Start DFS from the entry block
    if cfg.entry_block:
        dfs(cfg.entry_block.start_address)

    return loops


def identify_if_statements(cfg: ControlFlowGraph) -> Dict[int, IfStructure]:
    """
    Identify if statements in the control flow graph.

    Args:
        cfg: The control flow graph

    Returns:
        A dictionary mapping condition block addresses to IfStructure objects
    """
    if_statements = {}

    for block_addr, block in cfg.blocks.items():
        if block.is_conditional_branch():
            # This block ends with a conditional branch, which indicates an if statement

            # Get the true branch (target of the conditional jump)
            true_branch = []
            last_instr = block.instructions[-1]
            try:
                target = int(last_instr.operands, 16)
                if target in cfg.blocks:
                    true_branch = [cfg.blocks[target]]
            except ValueError:
                pass

            # Get the false branch (fall-through)
            false_branch = []
            next_addr = block.start_address + sum(
                len(instr.bytes_data) for instr in block.instructions
            )
            if next_addr in cfg.blocks:
                false_branch = [cfg.blocks[next_addr]]

            # Create an if structure
            if_statements[block_addr] = IfStructure(block, true_branch, false_branch)

    return if_statements


def identify_switch_statements(cfg: ControlFlowGraph) -> Dict[int, SwitchStructure]:
    """
    Identify switch statements in the control flow graph.

    Args:
        cfg: The control flow graph

    Returns:
        A dictionary mapping switch header addresses to SwitchStructure objects
    """
    switch_statements = {}

    # Look for patterns that indicate a switch statement
    # This is a simplified heuristic - in a real implementation, you'd need more sophisticated analysis
    for block_addr, block in cfg.blocks.items():
        if len(block.instructions) >= 3:
            # Check for a sequence of CMP and JE instructions, which might indicate a switch statement
            cmp_count = 0
            je_count = 0

            for instr in block.instructions:
                if instr.mnemonic == "cmp":
                    cmp_count += 1
                elif instr.mnemonic == "je":
                    je_count += 1

            if cmp_count >= 2 and je_count >= 2:
                # This might be a switch statement

                # Extract the cases
                cases = {}
                default_blocks = []

                # This is a simplified approach - in a real implementation, you'd need to analyze
                # the control flow more carefully to identify the case blocks

                for i, instr in enumerate(block.instructions):
                    if (
                        instr.mnemonic == "cmp"
                        and i + 1 < len(block.instructions)
                        and block.instructions[i + 1].mnemonic == "je"
                    ):
                        # Found a potential case
                        cmp_instr = instr
                        je_instr = block.instructions[i + 1]

                        # Extract the case value
                        case_value = 0
                        if "," in cmp_instr.operands:
                            parts = cmp_instr.operands.split(",")
                            if len(parts) == 2:
                                try:
                                    case_value = int(parts[1].strip(), 0)
                                except ValueError:
                                    pass

                        # Extract the case block
                        case_blocks = []
                        try:
                            target = int(je_instr.operands, 16)
                            if target in cfg.blocks:
                                case_blocks = [cfg.blocks[target]]
                        except ValueError:
                            pass

                        cases[case_value] = case_blocks

                # The default case is the fall-through from the switch header
                next_addr = block.start_address + sum(
                    len(instr.bytes_data) for instr in block.instructions
                )
                if next_addr in cfg.blocks:
                    default_blocks = [cfg.blocks[next_addr]]

                # Create a switch structure
                switch_statements[block_addr] = SwitchStructure(
                    block, cases, default_blocks
                )

    return switch_statements


def improve_control_flow(
    cfg: ControlFlowGraph,
) -> Dict[str, Dict[int, ControlFlowStructure]]:
    """
    Improve the control flow structure of a function.

    Args:
        cfg: The control flow graph

    Returns:
        A dictionary mapping structure types to dictionaries mapping block addresses to structures
    """
    structures = {
        "loops": identify_loops(cfg),
        "if_statements": identify_if_statements(cfg),
        "switch_statements": identify_switch_statements(cfg),
    }

    return structures
