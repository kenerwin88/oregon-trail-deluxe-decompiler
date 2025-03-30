# Active Context: Oregon Trail Decompilation

## Current Work Focus

### Project Reorganization (March 28, 2025)
- Moved all original game files to `/original_game/` subfolder for better organization
- Kept raw extracted assets at top level (`/raw_extracted/`) for backward compatibility
- Updated README.md, extract.sh, and memory-bank files to reflect new directory structure
- Modified dosbox-x.conf to automatically navigate to the original_game directory
- Project now has cleaner separation between:
  - Original game files (`/original_game/`)
  - Raw extracted assets (`/raw_extracted/`)
  - Conversion tools (`/tools/`)
  - Converted modern assets (`/modern/`)
  - Documentation (`/docs/`)

This reorganization preserves all functionality while making the project structure more intuitive and maintainable.
