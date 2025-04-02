# Oregon Trail Decompiler

A set of tools to extract, convert, and decompile the classic Oregon Trail game.

## Project Structure

The project is organized as follows:

```
oregon-trail-decompiler/
├── main.py                     # Main CLI entry point
├── README.md                   # This file
├── tools/                      # Tool modules
│   ├── decompiler/             # Decompiler modules
│   │   ├── analyzers/          # Analysis modules
│   │   │   ├── __init__.py     # Analyzer package
│   │   │   ├── call_graph.py   # Call graph analysis
│   │   │   ├── data_structures.py # Data structure recognition
│   │   │   ├── resources.py    # Resource reference analysis
│   │   │   └── state_machine.py # State machine analysis
│   │   ├── __init__.py         # Decompiler package
│   │   ├── constants.py        # Game-specific constants
│   │   ├── enhanced_output.py  # Output enhancement
│   │   ├── main.py             # Decompiler entry point
│   │   ├── models.py           # Data models
│   │   └── utils.py            # Utility functions
│   ├── gxl_extractor.py        # GXL archive extractor
│   └── convert.py              # File format converter
└── original_game/              # Original game files
    └── OREGON.GXL              # Oregon Trail GXL archive
```

## Usage

The decompiler tools provide several commands:

### Extract Files from GXL Archives

```bash
python main.py extract original_game/OREGON.GXL --output raw_extracted
```

### Convert Game Files to Modern Formats

```bash
python main.py convert raw_extracted --output modern
```

### Decompile the Game Executable

```bash
python main.py decompile original_game/OREGON.EXE --output decompiled_output
```

By default, the decompiler enables all analyzers for the best results. You can disable specific features with options like `--no-enhanced`, `--no-data-flow`, etc.

### Process Everything (Extract, Convert, and Decompile)

```bash
python main.py
```

## Analyzer Modules

The decompiler includes several analyzer modules that provide different types of analysis:

### Call Graph Analyzer

Analyzes function call relationships and builds a call graph to identify function hierarchies, entry points, and related functions.

### Resource Analyzer

Analyzes references to resource files in the game code, identifying which functions load or use specific resource files.

### State Machine Analyzer

Analyzes state machines in the decompiled code, identifying state transitions and visualizing the state flow.

### Data Structure Recognizer

Identifies and recognizes data structures like arrays and structs in the decompiled code to improve variable identification and code readability.

## Development

To contribute to this project:

1. Make sure you understand the project structure and the role of each module
2. Follow the existing code style and patterns
3. Add proper docstrings and comments to your code
4. Use the logging system for informational and error messages
5. Add appropriate error handling
6. Test your changes thoroughly

## Oregon Trail-Specific Features

The decompiler includes special features for The Oregon Trail:

- Recognition of game states, professions, weather conditions, etc.
- Mapping of memory addresses to meaningful names
- Identification of key game functions
- Analysis of game resources (images, sounds, etc.)
- State machine analysis for game flow
