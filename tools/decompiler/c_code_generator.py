"""
C code generator for the Oregon Trail decompiler.
"""

import re
from typing import Dict, List, Set, Optional, Tuple, Any

from .models import DOSFunction, X86Instruction, Variable
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
    ITEM_TYPES
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
            "ItemType": ITEM_TYPES
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
            enum_def = f"typedef enum {{\n"
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
                        param_type = var.type if hasattr(var, "type") and var.type else "int"
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
                        param_type = var.type if hasattr(var, "type") and var.type else "int"
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
                        if not hasattr(var, "is_return_value") or not var.is_return_value:
                            var_type = var.type if hasattr(var, "type") and var.type else "int"
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
                body += self._generate_block_code(func.cfg, func.cfg.entry_block, visited_blocks, 1)
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
            return f"{'    ' * indent_level}goto block_{block.start_address:X};\n"
        
        visited.add(block.start_address)
        lines = []
        
        # Add block label
        lines.append(f"{'    ' * (indent_level-1)}block_{block.start_address:X}:")
        
        # Add block instructions
        for instr in block.instructions:
            # Convert instruction to C code
            c_code = self._instruction_to_c(instr)
            if c_code:
                lines.append(f"{'    ' * indent_level}{c_code}")
        
        # Handle successors based on control flow
        if len(block.successors) == 0:
            # No successors - return or end of function
            if any(instr.mnemonic.startswith("ret") for instr in block.instructions):
                lines.append(f"{'    ' * indent_level}return;")
        elif len(block.successors) == 1:
            # One successor - unconditional jump or fall-through
            next_block = None
            # Find the block for the successor
            for blk in cfg.blocks:
                if hasattr(blk, 'start_address') and hasattr(block, 'successors') and block.successors and blk.start_address == block.successors[0]:
                    next_block = blk
                    break
                    
            if next_block:
                lines.append(self._generate_block_code(cfg, next_block, visited, indent_level))
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
                if hasattr(blk, 'start_address') and hasattr(block, 'successors') and block.successors:
                    if blk.start_address == block.successors[0]:
                        true_block = blk
                    elif len(block.successors) > 1 and blk.start_address == block.successors[1]:
                        false_block = blk
            
            if true_block:
                lines.append(f"{'    ' * indent_level}if ({condition}) {{")
                lines.append(self._generate_block_code(cfg, true_block, visited.copy(), indent_level + 1))
                
                if false_block:
                    lines.append(f"{'    ' * indent_level}}} else {{")
                    lines.append(self._generate_block_code(cfg, false_block, visited, indent_level + 1))
                
                lines.append(f"{'    ' * indent_level}}}")
        
        return "\n".join(lines) + "\n"
    
    def _instruction_to_c(self, instr: X86Instruction) -> str:
        """
        Convert an x86 instruction to C code.
        
        Args:
            instr: Instruction to convert
            
        Returns:
            String containing C code
        """
        # Handle different instruction types
        if instr.mnemonic.startswith("mov"):
            # Move instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} = {src};"
        elif instr.mnemonic.startswith("add"):
            # Add instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} += {src};"
        elif instr.mnemonic.startswith("sub"):
            # Subtract instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} -= {src};"
        elif instr.mnemonic.startswith("mul"):
            # Multiply instruction
            src = self._parse_operands(instr.operands)[0]
            if src:
                return f"ax = al * {src};"
        elif instr.mnemonic.startswith("div"):
            # Divide instruction
            src = self._parse_operands(instr.operands)[0]
            if src:
                return f"ax = ax / {src}; dx = ax % {src};"
        elif instr.mnemonic.startswith("inc"):
            # Increment instruction
            dest = self._parse_operands(instr.operands)[0]
            if dest:
                return f"{dest}++;"
        elif instr.mnemonic.startswith("dec"):
            # Decrement instruction
            dest = self._parse_operands(instr.operands)[0]
            if dest:
                return f"{dest}--;"
        elif instr.mnemonic.startswith("and"):
            # Bitwise AND instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} &= {src};"
        elif instr.mnemonic.startswith("or"):
            # Bitwise OR instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} |= {src};"
        elif instr.mnemonic.startswith("xor"):
            # Bitwise XOR instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} ^= {src};"
        elif instr.mnemonic.startswith("shl"):
            # Shift left instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} <<= {src};"
        elif instr.mnemonic.startswith("shr"):
            # Shift right instruction
            dest, src = self._parse_operands(instr.operands)
            if dest and src:
                return f"{dest} >>= {src};"
        elif instr.mnemonic.startswith("call"):
            # Function call instruction
            func_name = instr.operands.strip()
            if func_name.startswith("0x"):
                # Convert address to function name
                for func in self.functions:
                    if hex(func.start_address) == func_name:
                        func_name = func.name
                        break
            
            return f"{func_name}();"
        elif instr.mnemonic.startswith("int"):
            # Interrupt instruction
            interrupt = instr.operands.strip()
            if interrupt == "0x21":
                return "// DOS API call"
            elif interrupt == "0x10":
                return "// Video BIOS call"
            elif interrupt == "0x16":
                return "// Keyboard BIOS call"
            else:
                return f"// Interrupt {interrupt}"
        
        # Default - return the instruction as a comment
        return f"// {instr.mnemonic} {instr.operands}"
    
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
        Convert a memory reference to a C variable.
        
        Args:
            operand: Memory reference
            
        Returns:
            C variable name
        """
        # Check for memory references
        if operand.startswith("[") and operand.endswith("]"):
            # Extract address
            address = operand[1:-1]
            
            # Check for known memory addresses
            if address.startswith("0x"):
                try:
                    addr_val = int(address, 16)
                    
                    # Check game state variables
                    for addr, name in MEMORY_ADDRESSES.items():
                        if addr_val == addr:
                            return f"game_state.{name}"
                    
                    # Check graphics variables
                    for addr, name in GRAPHICS_ADDRESSES.items():
                        if addr_val == addr:
                            return f"graphics_state.{name}"
                    
                    # Check sound variables
                    for addr, name in SOUND_ADDRESSES.items():
                        if addr_val == addr:
                            return f"sound_state.{name}"
                    
                    # Check input variables
                    for addr, name in INPUT_ADDRESSES.items():
                        if addr_val == addr:
                            return f"input_state.{name}"
                except ValueError:
                    pass
            
            # Default - return as memory reference
            return f"memory[{address}]"
        
        # Check for register references
        if operand.lower() in ["ax", "bx", "cx", "dx", "si", "di", "bp", "sp"]:
            return operand.lower()
        
        # Check for immediate values
        if operand.startswith("0x") or operand.isdigit():
            return operand
        
        # Default - return as is
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