"""
C code generator for the Oregon Trail decompiler.
"""

import re
from typing import Dict, List, Tuple

from .models import DOSFunction, X86Instruction
from .oregon_trail_specific import (
    MEMORY_ADDRESSES,
    GRAPHICS_ADDRESSES,
    SOUND_ADDRESSES,
    INPUT_ADDRESSES,
    GAME_STATES,
    PROFESSIONS,
    WEATHER_CONDITIONS,
    PACE_SETTINGS,
    RATION_SETTINGS,
    RIVER_CROSSING_METHODS,
    LANDMARKS,
    EVENTS,
    ILLNESSES,
    MONTHS,
    ITEM_TYPES,
)


class CCodeGenerator:
    """
    Generates readable C code from decompiled functions.
    """

    def __init__(self, functions: List[DOSFunction]):
        """
        Initialize the C code generator.

        Args:
            functions: List of functions to generate code for
        """
        self.functions = functions
        self.global_variables = set()
        self.structs = {}
        self.enums = self._generate_enums()
        self.function_prototypes = []
        self.function_implementations = []

    def _generate_enums(self) -> Dict[str, Dict[int, str]]:
        """
        Generate enum definitions for game constants.

        Returns:
            Dictionary of enum names to enum values
        """
        enums = {
            "GameState": GAME_STATES,
            "Profession": PROFESSIONS,
            "Weather": WEATHER_CONDITIONS,
            "Pace": PACE_SETTINGS,
            "Rations": RATION_SETTINGS,
            "RiverCrossing": RIVER_CROSSING_METHODS,
            "Landmark": LANDMARKS,
            "Event": EVENTS,
            "Illness": ILLNESSES,
            "Month": MONTHS,
            "ItemType": ITEM_TYPES,
        }
        return enums

    def _generate_struct_definitions(self) -> str:
        """
        Generate struct definitions for game data structures.

        Returns:
            String containing struct definitions
        """
        structs = []

        # Player struct
        structs.append("""
typedef struct {
    char name[16];
    int health;
    int age;
    int is_alive;
    int illness;
    int illness_days_remaining;
} Player;
""")

        # Game state struct
        structs.append("""
typedef struct {
    int current_state;
    int current_month;
    int current_day;
    int current_year;
    int total_miles_traveled;
    int miles_to_next_landmark;
    int current_weather;
    int current_health;
    int current_pace;
    int current_rations;
    int food_remaining;
    int money_remaining;
    int oxen_count;
    int clothing_count;
    int ammunition_count;
    int spare_parts_count;
    int medical_kits_count;
    int player_count;
    Player players[5];
    int current_landmark_index;
    int river_depth;
    int river_width;
    int next_event_miles;
    int next_event_type;
    int random_seed;
    int profession_type;
    int starting_month;
} GameState;
""")

        # Graphics state struct
        structs.append("""
typedef struct {
    int screen_mode;
    int current_palette;
    int text_color;
    int background_color;
} GraphicsState;
""")

        # Sound state struct
        structs.append("""
typedef struct {
    int sound_enabled;
    int current_music;
    int sound_effect_playing;
    int music_tempo;
} SoundState;
""")

        # Input state struct
        structs.append("""
typedef struct {
    int key_pressed;
    int mouse_x;
    int mouse_y;
    int mouse_buttons;
} InputState;
""")

        return "\n".join(structs)

    def _generate_enum_definitions(self) -> str:
        """
        Generate enum definitions for game constants.

        Returns:
            String containing enum definitions
        """
        enum_defs = []

        for enum_name, enum_values in self.enums.items():
            enum_def = "typedef enum {\n"
            for value, name in sorted(enum_values.items()):
                enum_def += f"    {name} = {value},\n"
            enum_def += f"}} {enum_name};\n"
            enum_defs.append(enum_def)

        return "\n".join(enum_defs)

    def _generate_global_variables(self) -> str:
        """
        Generate global variable declarations.

        Returns:
            String containing global variable declarations
        """
        globals_decl = []

        # Game state
        globals_decl.append("// Game state variables")
        globals_decl.append("GameState game_state;")

        # Graphics state
        globals_decl.append("\n// Graphics state variables")
        globals_decl.append("GraphicsState graphics_state;")

        # Sound state
        globals_decl.append("\n// Sound state variables")
        globals_decl.append("SoundState sound_state;")

        # Input state
        globals_decl.append("\n// Input state variables")
        globals_decl.append("InputState input_state;")

        return "\n".join(globals_decl)

    def _generate_function_prototypes(self) -> str:
        """
        Generate function prototypes.

        Returns:
            String containing function prototypes
        """
        prototypes = []

        for func in self.functions:
            # Skip functions without instructions
            if not func.instructions:
                continue

            # Generate function prototype
            return_type = "void"
            if hasattr(func, "return_type") and func.return_type:
                return_type = func.return_type

            params = []
            if hasattr(func, "variables"):
                for var in func.variables.values():
                    if hasattr(var, "is_parameter") and var.is_parameter:
                        param_type = (
                            var.type if hasattr(var, "type") and var.type else "int"
                        )
                        params.append(f"{param_type} {var.name}")

            if not params:
                params = ["void"]

            prototype = f"{return_type} {func.name}({', '.join(params)});"
            prototypes.append(prototype)

        return "\n".join(prototypes)

    def _generate_function_implementations(self) -> str:
        """
        Generate function implementations.

        Returns:
            String containing function implementations
        """
        implementations = []

        for func in self.functions:
            # Skip functions without instructions
            if not func.instructions:
                continue

            # Generate function implementation
            return_type = "void"
            if hasattr(func, "return_type") and func.return_type:
                return_type = func.return_type

            params = []
            if hasattr(func, "variables"):
                for var in func.variables.values():
                    if hasattr(var, "is_parameter") and var.is_parameter:
                        param_type = (
                            var.type if hasattr(var, "type") and var.type else "int"
                        )
                        params.append(f"{param_type} {var.name}")

            if not params:
                params = ["void"]

            implementation = f"{return_type} {func.name}({', '.join(params)}) {{\n"

            # Add function purpose comment
            if hasattr(func, "purpose") and func.purpose:
                implementation = f"/**\n * {func.purpose}\n */\n{implementation}"

            # Add local variable declarations
            if hasattr(func, "variables"):
                local_vars = []
                for var in func.variables.values():
                    if not hasattr(var, "is_parameter") or not var.is_parameter:
                        if (
                            not hasattr(var, "is_return_value")
                            or not var.is_return_value
                        ):
                            var_type = (
                                var.type if hasattr(var, "type") and var.type else "int"
                            )
                            local_vars.append(f"    {var_type} {var.name};")

                if local_vars:
                    implementation += "\n    // Local variables\n"
                    implementation += "\n".join(local_vars) + "\n"

            # Add function body
            if hasattr(func, "cfg") and func.cfg:
                implementation += self._generate_function_body(func)
            else:
                implementation += "    // Function body not available\n"

            implementation += "}\n"
            implementations.append(implementation)

        return "\n\n".join(implementations)

    def _generate_function_body(self, func: DOSFunction) -> str:
        """
        Generate function body from control flow graph.

        Args:
            func: Function to generate body for

        Returns:
            String containing function body
        """
        body = "\n"

        # If we have a control flow graph, use it to generate structured code
        if hasattr(func, "cfg") and func.cfg:
            # Generate code for each basic block
            visited_blocks = set()
            if hasattr(func.cfg, "entry_block") and func.cfg.entry_block:
                body += self._generate_block_code(
                    func.cfg, func.cfg.entry_block, visited_blocks, 1
                )
        else:
            # Otherwise, just list the instructions
            for instr in func.instructions:
                body += f"    // {instr.mnemonic} {instr.operands}\n"

        return body

    def _generate_block_code(self, cfg, block, visited, indent_level):
        """
        Generate code for a basic block and its successors.

        Args:
            cfg: Control flow graph
            block: Basic block to generate code for
            visited: Set of visited block addresses
            indent_level: Current indentation level

        Returns:
            String containing block code
        """
        if not block:
            return f"{'    ' * indent_level}// Missing block\n"

        if block.start_address in visited:
            # Already visited this block, likely a loop or jump target
            return f"{'    ' * indent_level}// Jump to already visited block\n{'    ' * indent_level}goto block_{block.start_address:X};\n"

        visited.add(block.start_address)
        lines = []

        # Add block label
        lines.append(f"{'    ' * (indent_level - 1)}block_{block.start_address:X}:")

        # Add block instructions
        prev_instr = None
        for instr in block.instructions:
            # Convert instruction to C code, passing previous instruction for context
            c_code = self._instruction_to_c(instr, prev_instr)
            if c_code:
                lines.append(f"{'    ' * indent_level}{c_code}")
            prev_instr = instr # Update previous instruction for next iteration

        # Handle successors based on control flow
        if len(block.successors) == 0:
            # No successors - return or end of function
            if any(instr.mnemonic.startswith("ret") for instr in block.instructions):
                lines.append(f"{'    ' * indent_level}return;")
        elif len(block.successors) == 1:
            # One successor - unconditional jump or fall-through
            target_addr = block.successors[0]
            next_block = cfg.blocks.get(target_addr) # Use dict.get for safety

            # Check if the last instruction is an explicit JMP
            last_instr = block.instructions[-1] if block.instructions else None
            is_explicit_jmp = last_instr and last_instr.mnemonic.lower() == "jmp"

            if is_explicit_jmp:
                 # Generate a goto for explicit jumps
                 lines.append(f"{'    ' * indent_level}goto block_{target_addr:X};")
                 # Don't generate code for the target block here if it's an explicit jump
                 # to avoid duplicating code or infinite recursion in simple loops.
                 # The target block will be generated when encountered naturally.
            elif next_block:
                 # If it's a fall-through, generate the next block's code inline
                 # This avoids unnecessary labels for simple sequential code.
                 # However, ensure we don't infinitely recurse if the next block loops back immediately.
                 if next_block.start_address not in visited:
                     lines.append(
                         self._generate_block_code(cfg, next_block, visited, indent_level)
                     )
                 else:
                      # If the fall-through target was already visited, generate a goto
                      lines.append(f"{'    ' * indent_level}// Fall-through to visited block\n{'    ' * indent_level}goto block_{next_block.start_address:X};")
            else:
                 lines.append(f"{'    ' * indent_level}// Successor block 0x{target_addr:X} not found in CFG")
        elif len(block.successors) == 2:
            # Two successors - conditional jump
            # Find the condition
            condition = "true"  # Default condition
            for instr in reversed(block.instructions):
                if instr.mnemonic.startswith("j") and not instr.mnemonic == "jmp":
                    condition = self._get_jump_condition(instr)
                    break

            # Generate if-else structure
            true_block = None
            false_block = None

            # Find the blocks for the successors
            for blk in cfg.blocks:
                if (
                    hasattr(blk, "start_address")
                    and hasattr(block, "successors")
                    and block.successors
                ):
                    if blk.start_address == block.successors[0]:
                        true_block = blk
                    elif (
                        len(block.successors) > 1
                        and blk.start_address == block.successors[1]
                    ):
                        false_block = blk

            if true_block:
                lines.append(f"{'    ' * indent_level}if ({condition}) {{")
                lines.append(
                    self._generate_block_code(
                        cfg, true_block, visited.copy(), indent_level + 1
                    )
                )

                if false_block:
                    lines.append(f"{'    ' * indent_level}}} else {{")
                    lines.append(
                        self._generate_block_code(
                            cfg, false_block, visited, indent_level + 1
                        )
                    )

                lines.append(f"{'    ' * indent_level}}}")

        return "\n".join(lines) + "\n"

    def _instruction_to_c(self, instr: X86Instruction, prev_instr = None) -> str:
        """
        Convert an x86 instruction to C code.

        Args:
            instr: Instruction to convert

        Returns:
            String containing C code, or an empty string if handled by control flow logic
        """
        mnemonic = instr.mnemonic.lower()

        # Handle different instruction types
        if mnemonic == "mov":
            dest, src = self._parse_operands(instr.operands)
            if dest == "bp" and src == "sp":
                 return "// Standard function prologue: set up stack frame pointer"
            elif dest and src:
                 return f"{dest} = {src};"
        elif mnemonic == "add":
            dest, src = self._parse_operands(instr.operands)
            if dest == "sp" and src.isdigit():
                 return f"// Deallocate {src} bytes from stack"
            elif dest and src:
                 return f"{dest} += {src};"
        elif mnemonic == "sub":
            dest, src = self._parse_operands(instr.operands)
            if dest == "sp" and src.isdigit():
                 return f"// Allocate {src} bytes on stack for local variables"
            elif dest and src:
                 return f"{dest} -= {src};"
        elif mnemonic.startswith("mul"):
            src = self._parse_operands(instr.operands)[0]
            if src: return f"ax = al * {src}; // Assuming 8-bit multiply"
        elif mnemonic.startswith("imul"):
             # Handle different forms of imul
            parts = instr.operands.split(',')
            if len(parts) == 1:
                src = self._parse_operands(parts[0])[0]
                if src: return f"ax = al * {src}; // Signed multiply"
            elif len(parts) == 2:
                dest, src = self._parse_operands(instr.operands)
                if dest and src: return f"{dest} *= {src}; // Signed multiply"
            elif len(parts) == 3:
                dest, src1, src2 = [self._parse_operands(p)[0] for p in parts]
                if dest and src1 and src2: return f"{dest} = {src1} * {src2}; // Signed multiply"
        elif mnemonic.startswith("div"):
            src = self._parse_operands(instr.operands)[0]
            if src: return f"ax = ax / {src}; dx = ax % {src}; // Unsigned divide"
        elif mnemonic.startswith("idiv"):
            src = self._parse_operands(instr.operands)[0]
            if src: return f"ax = ax / {src}; dx = ax % {src}; // Signed divide"
        elif mnemonic.startswith("inc"):
            dest = self._parse_operands(instr.operands)[0]
            if dest: return f"{dest}++;"
        elif mnemonic.startswith("dec"):
            dest = self._parse_operands(instr.operands)[0]
            if dest: return f"{dest}--;"
        elif mnemonic.startswith("and"):
            dest, src = self._parse_operands(instr.operands)
            if dest and src: return f"{dest} &= {src};"
        elif mnemonic.startswith("or"):
            dest, src = self._parse_operands(instr.operands)
            if dest and src: return f"{dest} |= {src};"
        elif mnemonic.startswith("xor"):
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                # Check for common XOR to zero register pattern
                if dest == src:
                    return f"{dest} = 0;"
                else:
                    return f"{dest} ^= {src};"
        elif mnemonic.startswith("shl") or mnemonic.startswith("sal"):
            dest, src = self._parse_operands(instr.operands)
            if dest and src: return f"{dest} <<= {src};"
        elif mnemonic.startswith("shr"): # Logical shift right
            dest, src = self._parse_operands(instr.operands)
            if dest and src: return f"{dest} = (uint16_t){dest} >> {src}; // Logical shift right" # Cast to unsigned for logical shift
        elif mnemonic.startswith("sar"):
            dest, src = self._parse_operands(instr.operands)
            if dest and src: return f"{dest} >>= {src}; // Signed shift right"
        elif mnemonic == "push":
             src = self._parse_operands(instr.operands)[0]
             if src == "bp":
                 return "// Standard function prologue: save old base pointer"
             elif src:
                 # Assuming push decrements SP by 2 (for 16-bit)
                 return f"sp -= 2; *(uint16_t*)sp = {src}; // push {src}"
        elif mnemonic == "pop":
             dest = self._parse_operands(instr.operands)[0]
             if dest == "bp":
                 return "// Standard function epilogue: restore old base pointer"
             elif dest:
                 # Assuming pop increments SP by 2 (for 16-bit)
                 return f"{dest} = *(uint16_t*)sp; sp += 2; // pop {dest}"
        elif mnemonic.startswith("lea"): # Load Effective Address
            dest, src_mem = self._parse_operands(instr.operands)
            # LEA calculates an address, so we remove the dereference (*) added by _convert_memory_reference
            if dest and src_mem and src_mem.startswith("*("):
                 # LEA calculates an address, treat src_mem as the address calculation itself
                 # Need to handle different forms potentially generated by _convert_memory_reference
                 if src_mem.startswith("*("): # If it looks like a pointer dereference, remove it
                     address_calculation = src_mem[2:-1]
                 else: # Otherwise assume it's already the address expression
                     address_calculation = src_mem
                 return f"{dest} = ({address_calculation}); // Calculate address"
            elif dest and src_mem:
                 # Fallback if src_mem wasn't parsed as expected
                 return f"{dest} = &({src_mem}); // Calculate address (fallback)"
        elif mnemonic == "xchg":
             op1, op2 = self._parse_operands(instr.operands)
             if op1 and op2: return f"swap({op1}, {op2}); // Exchange values"
        elif mnemonic == "cmp":
            op1, op2 = self._parse_operands(instr.operands)
            if op1 and op2: return f"compare({op1}, {op2}); // Sets flags"
        elif mnemonic.startswith("test"):
            op1, op2 = self._parse_operands(instr.operands)
            if op1 and op2: return f"test_bits({op1}, {op2}); // Sets flags"
        elif mnemonic == "call":
            func_target = self._parse_operands(instr.operands)[0]
            if func_target:
                 # Resolve function name if it's an address
                 if func_target.startswith("0x"):
                     try:
                         target_addr = int(func_target, 16)
                         # Find function by address - requires self.functions to be available
                         func_name = next((f.name for f in self.functions if f.start_address == target_addr), func_target)
                         func_target = func_name
                     except ValueError: pass # Keep original target if not a valid address
                 return f"{func_target}();"
        elif mnemonic == "int":
            interrupt_str = instr.operands.strip()
            interrupt_num = -1
            try:
                interrupt_num = int(interrupt_str, 16)
            except ValueError:
                pass

            func_code = None
            func_reg = None
            # Check previous instruction for mov ah/al, value
            if prev_instr and prev_instr.mnemonic.lower() == "mov":
                 dest, src = self._parse_operands(prev_instr.operands)
                 # Check if dest is ah/al and src is a number
                 if dest in ["ah", "al"] and (src.startswith("0x") or src.isdigit()):
                     try:
                         func_code = int(src, 0)
                         func_reg = dest
                     except ValueError: pass

            # Look up specific interrupt function using dos_api helper
            from .dos_api import recognize_interrupt # Ensure import is available
            dos_interrupt = recognize_interrupt(interrupt_num, func_code)

            if dos_interrupt:
                 # Generate a detailed comment
                 comment = f"// {dos_interrupt.name}"
                 if func_reg:
                     comment += f" ({func_reg}=0x{func_code:X})" if func_code is not None else ""
                 comment += f" - {dos_interrupt.description}"
                 return comment
            else:
                 # Fallback comment if specific function not found
                 comment = f"// Interrupt {interrupt_str}"
                 if func_reg:
                     comment += f" ({func_reg}=0x{func_code:X})" if func_code is not None else ""
                 return comment
        elif mnemonic.startswith("j") or mnemonic.startswith("loop") or mnemonic == "ret" or mnemonic == "retf":
             # Jumps, loops, and returns are handled by the block generation logic
             return "" # Return empty string, don't generate separate C code for these
        elif mnemonic == "nop":
             return "// No operation" # Common instruction, translate to comment

        # Default - return the instruction as a comment, indicating it needs translation
        # Include address for context
        return f"// 0x{instr.address:X}: TODO: Translate: {instr.mnemonic} {instr.operands}"

    def _parse_operands(self, operands: str) -> Tuple[str, str]:
        """
        Parse instruction operands.

        Args:
            operands: Instruction operands

        Returns:
            Tuple of destination and source operands
        """
        if "," in operands:
            dest, src = operands.split(",", 1)
            dest = dest.strip()
            src = src.strip()

            # Convert memory references
            dest = self._convert_memory_reference(dest)
            src = self._convert_memory_reference(src)

            return dest, src
        else:
            operand = operands.strip()
            operand = self._convert_memory_reference(operand)
            return operand, None

    def _convert_memory_reference(self, operand: str) -> str:
        """
        Convert an assembly memory reference operand to a C-like expression.

        Args:
            operand: Memory reference operand string (e.g., "word ptr [bx+si+4]", "[0x5C00]", "byte ptr [bp-2]")

        Returns:
            C-like expression (e.g., "*(uint16_t*)(bx + si + 4)", "game_state.current_month", "*(uint8_t*)(bp - 2)")
        """
        operand = operand.strip()
        
        # Regex to capture size specifier (byte, word, dword) and the content inside brackets []
        mem_match = re.match(r"(?:(byte|word|dword)\s+ptr\s+)?\[(.+)\]", operand, re.IGNORECASE)

        if mem_match:
            size_spec = mem_match.group(1)
            content = mem_match.group(2).strip().lower() # Normalize content
            
            # Determine C type based on size specifier
            c_type = "uint16_t" # Default to word for 16-bit arch
            if size_spec:
                if size_spec.lower() == "byte":
                    c_type = "uint8_t"
                elif size_spec.lower() == "dword":
                    c_type = "uint32_t"
            
            # Try to resolve known absolute addresses first
            if content.startswith("0x"):
                 try:
                     addr_val = int(content, 16)
                     # Check known global structs
                     for addr, name in MEMORY_ADDRESSES.items():
                         if addr_val == addr: return f"game_state.{name}" # Assumes word access for simplicity
                     for addr, name in GRAPHICS_ADDRESSES.items():
                         if addr_val == addr: return f"graphics_state.{name}"
                     for addr, name in SOUND_ADDRESSES.items():
                         if addr_val == addr: return f"sound_state.{name}"
                     for addr, name in INPUT_ADDRESSES.items():
                         if addr_val == addr: return f"input_state.{name}"
                     # If not a known named address, treat as direct memory access pointer
                     return f"*({c_type}*)({content})"
                 except ValueError:
                     pass # Fall through if not a valid hex number

            # Handle register-based addressing (e.g., [bx+si], [bp-4], [di+var+2])
            # Replace register names and handle basic arithmetic within brackets
            # This is a simplified parser for common cases like [reg+reg], [reg+offset], [reg-offset]
            content = content.replace('bp', 'bp_reg') # Use temp names to avoid conflicts if var names exist
            content = content.replace('bx', 'bx_reg')
            content = content.replace('si', 'si_reg')
            content = content.replace('di', 'di_reg')
            # Convert arithmetic operations
            content = re.sub(r'\s*\+\s*', ' + ', content)
            content = re.sub(r'\s*-\s*', ' - ', content)
            
            # Assume registers used in addressing hold addresses (pointers)
            # A more sophisticated analysis would track register types
            return f"*({c_type}*)({content})"

        # Handle simple register operands (e.g., "ax", "al")
        if operand.lower() in ["ax", "bx", "cx", "dx", "si", "di", "bp", "sp", "al", "ah", "bl", "bh", "cl", "ch", "dl", "dh"]:
            return operand.lower()

        # Handle immediate values (hex or decimal)
        if operand.startswith("0x") or operand.isdigit():
            return operand
            
        # Handle segment registers (comment them out as they are implicit in C)
        if operand.lower() in ["cs", "ds", "es", "ss", "fs", "gs"]:
             return f"/* {operand} */"

        # Default: return operand as is (might be a label, variable name, or unrecognized)
        # Could potentially look up labels/variables here if available
        return operand

    def _get_jump_condition(self, instr: X86Instruction) -> str:
        """
        Get the condition for a conditional jump.

        Args:
            instr: Jump instruction

        Returns:
            C condition expression
        """
        mnemonic = instr.mnemonic.lower()

        if mnemonic == "je" or mnemonic == "jz":
            return "a == b"
        elif mnemonic == "jne" or mnemonic == "jnz":
            return "a != b"
        elif mnemonic == "jg" or mnemonic == "jnle":
            return "a > b"
        elif mnemonic == "jge" or mnemonic == "jnl":
            return "a >= b"
        elif mnemonic == "jl" or mnemonic == "jnge":
            return "a < b"
        elif mnemonic == "jle" or mnemonic == "jng":
            return "a <= b"
        elif mnemonic == "ja" or mnemonic == "jnbe":
            return "a > b (unsigned)"
        elif mnemonic == "jae" or mnemonic == "jnb":
            return "a >= b (unsigned)"
        elif mnemonic == "jb" or mnemonic == "jnae":
            return "a < b (unsigned)"
        elif mnemonic == "jbe" or mnemonic == "jna":
            return "a <= b (unsigned)"

        # Default condition
        return "condition"

    def generate_c_code(self) -> str:
        """
        Generate complete C code.

        Returns:
            String containing C code
        """
        # Generate code sections
        includes = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n"
        struct_defs = self._generate_struct_definitions()
        enum_defs = self._generate_enum_definitions()
        globals = self._generate_global_variables()
        prototypes = self._generate_function_prototypes()
        implementations = self._generate_function_implementations()

        # Combine sections
        c_code = f"""/**
 * Oregon Trail Decompiled Code
 * Generated by Oregon Trail Decompiler
 */

{includes}
// Struct definitions
{struct_defs}

// Enum definitions
{enum_defs}

// Global variables
{globals}

// Function prototypes
{prototypes}

// Function implementations
{implementations}
"""

        return c_code


def generate_c_code(functions: List[DOSFunction]) -> str:
    """
    Generate C code from decompiled functions.

    Args:
        functions: List of functions to generate code for

    Returns:
        String containing C code
    """
    generator = CCodeGenerator(functions)
    return generator.generate_c_code()
