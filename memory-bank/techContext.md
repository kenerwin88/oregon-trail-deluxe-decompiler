# Technical Context: Oregon Trail Decompilation

## Technologies Used

### Core Technologies
- **Python 3**: Primary development language for conversion tools
- **DOSBox-X**: Emulator for running the original DOS version
- **argparse**: Command-line interface framework
- **logging**: Structured logging system

### File Formats
- **GXL**: Archive format containing all game assets
- **PC8/PC4/PCX**: Image formats for graphics (256/16 color)
- **XMI**: Miles Sound System music format
- **SND**: Raw PCM audio format for sound effects
- **CTR/TXT**: Text files for game content and dialog
- **ANI**: Animation format for sprite sequences
- **GBT/GFT**: Game-specific data formats (guide and font)
- **LST**: High score data format

### Modern Output Formats
- **PNG**: Modern image format for converted graphics
- **MIDI**: Standard format for converted music
- **WAV**: Standard audio format for converted sounds
- **UTF-8 Text**: Modern text encoding
- **JSON**: For structured data (analysis output, high scores)

## Development Setup

### Required Software
- Python 3.6+ (with pip for package management)
- DOSBox-X for testing original game

### Project Structure
```
/
├── original_game/        # Original DOS game files
│   ├── OREGON.EXE        # Main game executable 
│   ├── OREGON.GXL        # Game asset archive
│   ├── *.COM             # DOS sound drivers
│   ├── *.ADV             # Sound driver data
│   └── ...               # Other original files
│
├── raw_extracted/        # Extracted original assets (from GXL)
│
├── tools/                # Asset conversion tools
│   ├── main.py          # Main CLI entry point
│   ├── gxl_extractor.py # GXL archive extractor
│   ├── convert.py       # Main conversion script
│   ├── convert_pc8.py   # PC8/PC4 image converter
│   ├── convert_snd.py   # Sound converter
│   ├── convert_xmi.py   # Music converter
│   ├── convert_text.py  # Text converter
│   ├── convert_ani.py   # Animation converter
│   ├── convert_gbt.py   # Guide data converter
│   └── convert_gft.py   # Font converter
│   
├── docs/                 # Technical documentation
│   ├── executable_analysis.md  # OREGON.EXE analysis
│   ├── ctr_format_analysis.md  # Control file format
│   └── XMI_format.md          # Music file format
│   
├── modern/               # Converted modern assets
│   ├── images/           # Converted PNG images
│   ├── music/            # Converted MIDI files
│   ├── sounds/           # Converted WAV files
│   ├── text/             # Converted text files
│   ├── animations/       # Converted animations
│   ├── scores/           # Converted high scores
│   └── fonts/            # Converted fonts
│   
├── tests/                # Test cases
└── memory-bank/          # Project documentation and memory
```

### Development Workflow
1. **Extract**: Run GXL extractor to get raw game assets
2. **Convert**: Process raw assets to modern formats
3. **Verify**: Check file integrity and conversion accuracy
4. **Test**: Verify against original game behavior
5. **Document**: Record format specifications and implementation details

## Technical Constraints

### Original Game Constraints
- **DOS Platform**: Original game designed for MS-DOS
- **16-bit Architecture**: Original executable is 16-bit
- **256-Color VGA**: Graphics designed for 256-color palette
- **Limited Sound**: PC Speaker, Sound Blaster, or AdLib audio
- **Low Resolution**: 640x480 or lower resolution graphics
- **Memory Limitations**: Designed for systems with limited RAM

### Modern Implementation Constraints
- **Format Conversion Challenges**:
  - Proprietary formats require reverse engineering
  - Some formats lack complete documentation
  - Potential loss of fidelity in conversion process
- **Asset Completeness**:
  - Not all original assets may be extractable
  - Some assets may require manual reconstruction
- **Performance Considerations**:
  - Large file processing efficiency
  - Memory usage during conversion
  - Batch processing optimization

## Dependencies

### Core Dependencies
- **Python 3.6+**: For all conversion tools and modern game
- **DOSBox-X**: For running original game

### Python Package Dependencies
- **numpy**: Used for efficient binary data processing
- **Pillow**: Used for image processing and conversion
- **pygame**: Used for game implementation
- **argparse**: Used for command-line interface
- **logging**: Used for structured logging
- **json**: Used for structured data output
- **shutil**: Used for directory operations

### File Dependencies
- Original game files (located in `/original_game/` directory)
- Supporting DOS driver files (also in `/original_game/` directory)

## Command Line Interface

### Main Commands
```bash
# Process everything (extract and convert)
python3 main.py

# Extract specific files
python3 main.py extract original_game/OREGON.GXL --output raw_extracted [options]
  --debug            Enable debug logging
  --analyze         Only analyze without extracting
  --format          Output format (text/json)
  --no-verify       Disable integrity verification

# Convert specific formats
python3 main.py convert raw_extracted --output modern [options]
  --type            Specific format to convert
  --debug           Enable debug logging
```

### Analysis Features
```bash
# Analyze GXL archive
python3 main.py extract original_game/OREGON.GXL --analyze --format json

# Enable debug logging
python3 main.py extract original_game/OREGON.GXL --debug
```

## Build and Run Instructions

### Quick Start
```bash
# Process everything
python3 main.py
```

### Detailed Commands
```bash
# Extract with analysis
python3 main.py extract original_game/OREGON.GXL --analyze --format json

# Convert specific formats
python3 main.py convert raw_extracted --output modern --type pc8
python3 main.py convert raw_extracted --output modern --type xmi
python3 main.py convert raw_extracted --output modern --type snd
python3 main.py convert raw_extracted --output modern --type text
python3 main.py convert raw_extracted --output modern --type ani
python3 main.py convert raw_extracted --output modern --type lst

# Run the decompiler
python main.py decompile --output decompiled
```

### Running the Original Game
```bash
# Run the original game in DOSBox-X
dosbox-x -conf dosbox-x.conf
