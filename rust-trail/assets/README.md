# Assets Directory

This directory contains all game assets used by Rust Trail. The assets should be converted from the original Oregon Trail Deluxe game files using the conversion tools from the Oregon Trail Decompilation project.

## Directory Structure

- `images/` - PNG image files converted from PC8/PC4/PCX formats
- `audio/`
  - `sounds/` - WAV sound files converted from SND format
  - `music/` - MIDI music files converted from XMI format
- `text/` - Text files converted from CTR/TXT formats
- `animations/` - Animation files converted from ANI format
- `fonts/` - Font files converted from GFT format

## Asset Conversion

Original game assets are not included in this repository due to copyright considerations. You'll need to convert assets from a legitimately owned copy of the game using the conversion tools from the Oregon Trail Decompilation project.

The conversion process can be run with:

```bash
python main.py convert raw_extracted --output rust-trail/assets
```

Please refer to the Oregon Trail Decompilation project for detailed instructions on extracting and converting game assets.