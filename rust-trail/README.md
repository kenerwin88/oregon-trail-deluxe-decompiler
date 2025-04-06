# Rust Trail - Oregon Trail Deluxe Rewrite

A faithful rewrite of the 1995 MECC classic "The Oregon Trail Deluxe" using Rust and the Macroquad game framework.

## Project Description

This project aims to rewrite the classic educational game "The Oregon Trail Deluxe" (1995 MECC version) using modern technology while preserving the authentic gameplay experience. The rewrite uses the Rust programming language for performance and safety, and the Macroquad game framework for cross-platform compatibility including web deployment.

## Features

- Faithful reproduction of the original game mechanics and experience
- Cross-platform compatibility (Windows, macOS, Linux, Web)
- Asset conversion from original formats to modern standards
- Improved UI and accessibility features while maintaining original aesthetic
- Clean, modular Rust code following modern practices

## Getting Started

### Prerequisites

- Rust (latest stable version)
- Cargo (included with Rust)

### Building and Running

1. Clone the repository
2. Navigate to the project directory
3. Run the game:

```bash
cargo run --release
```

For development:

```bash
cargo run
```

### Building for Web

```bash
cargo build --target wasm32-unknown-unknown --release
```

## Project Structure

- `src/` - Rust source code
  - `main.rs` - Application entry point
  - `game.rs` - Game state management
  - `engine/` - Core engine components (rendering, assets, etc.)
  - `scenes/` - Game screens/scenes (title, menu, travel, etc.)
  - `game_logic/` - Core game mechanics (player, inventory, etc.)
  - `utils/` - Utility functions and helpers
- `assets/` - Game assets (converted from original formats)
- `docs/` - Project documentation

## Asset Conversion

This project utilizes converted assets from the original game. The conversion process preserves the authentic look and feel while making the assets compatible with modern systems.

**Note:** Original game assets are not included in this repository due to copyright considerations. A separate asset conversion tool from the Oregon Trail Decompilation project is used to convert assets from a legitimately owned copy of the game.

## License

This project's code is available under the MIT License. Original game assets and content are property of their respective copyright holders.

## Acknowledgments

- MECC for creating the original Oregon Trail
- The Oregon Trail Decompilation Project for research and asset conversion tools
- The Macroquad framework developers