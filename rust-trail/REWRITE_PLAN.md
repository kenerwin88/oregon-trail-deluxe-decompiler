# Oregon Trail Deluxe Rewrite Plan - Rust + Macroquad

## Project Overview

This document outlines the plan for rewriting "The Oregon Trail Deluxe" (1995 MECC version) using Rust programming language and the Macroquad game engine. The goal is to create a faithful reproduction of the original game with modern technology, ensuring proper preservation while making it accessible on current platforms.

## Technology Stack

- **Primary Language**: Rust
- **Game Engine**: Macroquad
  - Cross-platform 2D game framework
  - Minimal dependencies
  - Good performance
  - WebAssembly support
- **Asset Management**: Custom asset loaders for original game formats
- **Build System**: Cargo (Rust's package manager)
- **Testing**: Rust's built-in testing framework

## Project Structure

```
rust-trail/
├── Cargo.toml                  # Rust package configuration
├── assets/                     # Converted game assets
│   ├── images/                 # PNG images converted from PC8/PC4
│   ├── audio/                  # WAV sounds and MIDI music
│   ├── text/                   # Text assets
│   ├── fonts/                  # Font assets
│   └── animations/             # Animation assets
├── src/
│   ├── main.rs                 # Application entry point
│   ├── game.rs                 # Game state management
│   ├── engine/                 # Core engine components
│   │   ├── mod.rs              # Module definitions
│   │   ├── asset_loader.rs     # Asset loading and management
│   │   ├── renderer.rs         # Rendering system
│   │   ├── audio.rs            # Audio system
│   │   ├── input.rs            # Input handling
│   │   └── ui.rs               # UI system
│   ├── scenes/                 # Game scenes/screens
│   │   ├── mod.rs              # Module definitions
│   │   ├── title.rs            # Title screen
│   │   ├── main_menu.rs        # Main menu
│   │   ├── setup.rs            # Game setup (character creation, etc.)
│   │   ├── travel.rs           # Travel gameplay
│   │   ├── hunting.rs          # Hunting mini-game
│   │   ├── river_crossing.rs   # River crossing scenes
│   │   ├── landmarks.rs        # Historical landmarks
│   │   ├── trading.rs          # Trading post interactions
│   │   └── events.rs           # Random events
│   ├── game_logic/             # Core game mechanics
│   │   ├── mod.rs              # Module definitions
│   │   ├── player.rs           # Player state and management
│   │   ├── party.rs            # Party members management
│   │   ├── inventory.rs        # Inventory system
│   │   ├── resources.rs        # Resource management (food, bullets, etc.)
│   │   ├── time.rs             # In-game time system
│   │   ├── weather.rs          # Weather system
│   │   ├── health.rs           # Health and disease system
│   │   └── events.rs           # Event generation and handling
│   └── utils/                  # Utility functions and helpers
│       ├── mod.rs              # Module definitions
│       ├── math.rs             # Math utilities
│       ├── rng.rs              # Random number generation
│       └── format_converters.rs # Utilities for loading original formats
└── tests/                      # Integration tests
```

## Asset Conversion Strategy

The rewrite will leverage the existing conversion tools from the decompilation project to transform the original assets into formats that can be easily consumed by the Rust application:

1. **Images**: Convert PC8/PC4/PCX files to PNG format
2. **Audio**: 
   - Convert SND files to WAV format
   - Convert XMI music to MIDI format (with potential MP3 fallback)
3. **Text**: Convert CTR/TXT files to UTF-8 text files
4. **Animations**: Convert ANI files to sprite sheet PNGs with JSON metadata
5. **Game Data**: Convert GBT/GFT files to JSON or structured text formats

The asset conversion pipeline will be:
1. Extract all assets from original game (using existing Python tools)
2. Convert to modern formats (using existing Python tools)
3. Package converted assets with the Rust application

## Core Systems Design

### 1. Game State Management

The game state will be managed using a Rust-based state machine, similar to the original game's architecture:

```rust
enum GameState {
    TitleScreen,
    MainMenu,
    Setup,
    Travel,
    Hunting,
    RiverCrossing,
    Trading,
    Event,
    Landmark,
    GameOver,
}

struct Game {
    state: GameState,
    party: Party,
    inventory: Inventory,
    resources: Resources,
    game_time: GameTime,
    weather: Weather,
    // Other state data
}
```

### 2. Rendering System

Macroquad will handle the core rendering, with a custom layer for managing the UI elements and scene transitions:

- Sprite-based rendering for characters and objects
- Layered background rendering for environments
- Text rendering with custom fonts
- Animation system for character and environment animations
- UI rendering for menus, dialogs, and HUD elements

### 3. Audio System

A custom audio system built on Macroquad's audio capabilities:

- Sound effect playback (converted from SND files)
- Background music playback (converted from XMI files)
- Volume control and settings

### 4. Input Handling

Adaptive input system supporting multiple input methods:

- Mouse and keyboard (primary)
- Touch (for mobile platforms)
- Gamepad support (for console-like experience)

### 5. UI System

A faithful recreation of the original UI with modern usability improvements:

- Menu system matching original layouts
- Dialog system for in-game conversations
- HUD elements for displaying game status

## Game Mechanics Implementation

### 1. Travel System

- Path-based travel along the Oregon Trail
- Speed calculation based on party health, weather, terrain
- Resource consumption during travel (food, supplies)
- Random event generation during travel

### 2. Hunting Mini-Game

- First-person shooting mechanics
- Animal spawning and movement patterns
- Bullet management and scoring
- Meat calculation based on animals shot

### 3. River Crossing

- Multiple crossing methods (ford, ferry, etc.)
- Risk calculation based on river depth, weather
- Resource consumption for paid crossings
- Consequence handling for failed crossings

### 4. Health and Disease System

- Party member health tracking
- Disease contraction and progression
- Treatment options and effectiveness
- Death handling and consequences

### 5. Resource Management

- Food, ammunition, clothing, spare parts tracking
- Purchase and consumption mechanics
- Trading system with dynamic pricing
- Resource allocation decisions

### 6. Weather and Time System

- Season and weather progression
- Weather effects on travel and health
- Time-based event scheduling
- Day/night cycle effects

## Development Roadmap

### Phase 1: Foundation (Months 1-2)

- Project setup and structure
- Core engine components
- Asset loading systems
- Basic rendering and UI framework
- Scene management system

### Phase 2: Core Mechanics (Months 3-4)

- Travel system implementation
- Resource management
- Party and health systems
- Basic UI screens (main menu, setup)
- Time and weather systems

### Phase 3: Gameplay Features (Months 5-6)

- Hunting mini-game
- River crossing mechanics
- Trading post interactions
- Landmark visits
- Random events system

### Phase 4: Polish and Completion (Months 7-8)

- Full game flow integration
- Audio implementation
- UI polish and refinement
- Bug fixing and optimization
- Platform-specific adjustments

### Phase 5: Testing and Release (Months 9-10)

- Comprehensive testing
- Performance optimization
- Documentation
- Packaging and distribution
- Release management

## Technical Challenges

1. **Asset Conversion**: Ensuring accurate conversion of original assets to maintain game feel
2. **Game Logic Recreation**: Accurately recreating game mechanics without original source code
3. **Cross-Platform Compatibility**: Ensuring consistent experience across desktop, web, and mobile
4. **Performance Optimization**: Balancing authentic experience with modern performance expectations
5. **Original Format Support**: Potentially supporting direct loading of original file formats

## Preservation Considerations

1. **Authentic Experience**: Maintain the look, feel, and gameplay of the original
2. **Historical Accuracy**: Preserve educational content and historical information
3. **Accessibility**: Make the game accessible on modern platforms while respecting original design

## Initial Implementation Steps

1. Set up Rust + Macroquad project structure
2. Create basic window and game loop
3. Implement asset loading for converted PNG images
4. Build simple scene transition system
5. Create title screen and main menu mockups
6. Test rendering of background images and UI elements

## Cargo.toml Initial Configuration

```toml
[package]
name = "rust-trail"
version = "0.1.0"
edition = "2021"
authors = ["Oregon Trail Decompilation Project"]
description = "A Rust rewrite of Oregon Trail Deluxe using Macroquad"

[dependencies]
macroquad = "0.3"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rand = "0.8"
```

## Initial Main.rs Implementation

```rust
use macroquad::prelude::*;

mod game;
mod engine;
mod scenes;
mod game_logic;
mod utils;

#[macroquad::main("Oregon Trail Deluxe")]
async fn main() {
    let mut game = game::Game::new();
    
    loop {
        game.update();
        game.render();
        
        next_frame().await;
    }
}
```

This document provides a comprehensive plan for rewriting The Oregon Trail Deluxe using Rust and Macroquad, with a focus on authentic recreation while making the game accessible on modern platforms.