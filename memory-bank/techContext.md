# Technical Context: Oregon Trail Decompilation

## Technologies Used

### Core Technologies
- **Python 3**: Primary development language for conversion tools
- **DOSBox-X**: Emulator for running the original DOS version

### File Formats
- **GXL**: Archive format containing all game assets
- **PC8/PC4/PCX**: Image formats for graphics (256/16 color)
- **XMI**: Miles Sound System music format
- **SND**: Raw PCM audio format for sound effects
- **CTR/TXT**: Text files for game content and dialog
- **ANI**: Animation format for sprite sequences
- **GBT/GFT**: Game-specific data formats (guide and font)

### Modern Output Formats
- **PNG**: Modern image format for converted graphics
- **MIDI**: Standard format for converted music
- **WAV**: Standard audio format for converted sounds
- **UTF-8 Text**: Modern text encoding

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
│   ├── convert.py        # Main conversion script
│   ├── convert_pc8.py    # PC8/PC4 image converter
│   ├── convert_snd.py    # Sound converter
│   ├── convert_xmi.py    # Music converter
│   ├── convert_text.py   # Text converter
│   ├── convert_ani.py    # Animation converter
│   ├── convert_gbt.py    # Guide data converter
│   ├── convert_gft.py    # Font converter
│   └── gxl_extractor.py  # GXL archive extractor
│   
├── docs/                 # Technical documentation
│   ├── xmi_debug.md      # XMI format debugging notes
│   └── image_format_analysis.md # Image format documentation
│   
├── modern/               # Converted modern assets
│   ├── images/           # Converted PNG images
│   ├── music/            # Converted MIDI files
│   ├── sounds/           # Converted WAV files
│   ├── text/             # Converted text files
│   ├── animations/       # Converted animations
│   └── fonts/            # Converted fonts
│   
├── src/                  # Source code for additional components
├── tests/                # Test cases
└── memory-bank/          # Project documentation and memory
```

### Development Workflow
1. **Extract**: Run GXL extractor to get raw game assets
2. **Convert**: Process raw assets to modern formats
3. **Implement**: Build modern game features using converted assets
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

## Dependencies

### Core Dependencies
- **Python 3.6+**: For all conversion tools and modern game
- **DOSBox-X**: For running original game

### Python Package Dependencies
- **numpy**: Used for efficient binary data processing
- **Pillow**: Used for image processing and conversion
- **pygame**: Used for game implementation
- **argparse**: Used for command-line argument parsing

### File Dependencies
- Original game files (located in `/original_game/` directory)
- Supporting DOS driver files (also in `/original_game/` directory)

## Build and Run Instructions

### Extracting and Converting Assets
```bash
# Extract all files from GXL archive
python3 tools/gxl_extractor.py original_game/OREGON.GXL --output raw_extracted --debug

# Convert all assets to modern formats
python3 tools/convert.py raw_extracted --output modern

# Or convert specific asset types
python3 tools/convert_pc8.py raw_extracted modern --debug
python3 tools/convert_snd.py raw_extracted modern --debug
python3 tools/convert_xmi.py raw_extracted modern --debug
python3 tools/convert_text.py raw_extracted modern --debug
python3 tools/convert_gbt.py raw_extracted/GUIDE.GBT modern --debug
python3 tools/convert_ani.py raw_extracted/BANKS.ANI modern --debug
```

### Running the Modern Implementation
```bash
# Run the modern game implementation
python3 modern/game.py
```

### Running the Original Game
```bash
# Run the original game in DOSBox-X (dosbox-x.conf handles directory navigation)
dosbox-x -conf dosbox-x.conf
```
