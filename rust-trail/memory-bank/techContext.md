# Technical Context: Oregon Trail Deluxe Rewrite (Rust Trail)

## Technologies Used

### Core Technologies
- **Rust Programming Language**
  - Version: Latest stable (2021 edition)
  - Purpose: Main development language providing memory safety, performance, and modern language features
  - Benefits: Performance comparable to C/C++ with memory safety guarantees without garbage collection

- **Macroquad Game Framework**
  - Version: 0.3
  - Purpose: Cross-platform 2D game framework with minimal dependencies
  - Benefits: 
    - Simple API for 2D rendering
    - WebAssembly support
    - Cross-platform compatibility
    - Good performance for 2D games

### Supporting Technologies
- **Cargo**
  - Purpose: Rust's package manager and build system
  - Usage: Dependency management, building, testing, and documentation

- **Serde/Serde JSON**
  - Purpose: Serialization/deserialization framework
  - Usage: Configuration files, save game data, game data structures

- **Rand**
  - Purpose: Random number generation
  - Usage: Game events, procedural content, and simulations

## Development Setup

### Build Environment
- **Local Development**
  ```bash
  # Development build with debug information
  cargo run
  
  # Optimized release build
  cargo run --release
  ```

- **Web Build**
  ```bash
  # Build for WebAssembly target
  cargo build --target wasm32-unknown-unknown --release
  ```

### Directory Structure
```
rust-trail/
├── Cargo.toml          # Dependencies and project configuration
├── src/                # Rust source code
├── assets/             # Game assets (converted from original)
│   ├── images/         # PNG images
│   ├── audio/          # Sound and music files
│   ├── text/           # Text assets
│   ├── fonts/          # Font assets
│   └── animations/     # Animation assets
├── tests/              # Integration tests
└── memory-bank/        # Project documentation
```

### Asset Pipeline
1. **Original Assets**: Original MECC Oregon Trail assets (not included in repository)
2. **Conversion Tools**: Existing Python tools from decompilation project
3. **Converted Assets**: Modern formats used by the Rust application
   - Images: PNG format (converted from PC8/PC4/PCX)
   - Audio: WAV format (converted from SND) and MIDI (from XMI)
   - Text: UTF-8 (from proprietary formats)
   - Animations: Sprite sheets with metadata

## Technical Constraints

### Performance Targets
- **Desktop**: 60+ FPS on modern systems
- **Web**: 30+ FPS on average browsers/hardware
- **Memory Usage**: <100MB memory footprint
- **Loading Time**: <5 seconds on typical systems

### Compatibility Requirements
- **Desktop**: Windows 10+, macOS 10.14+, Linux (major distributions)
- **Web Browsers**: Chrome, Firefox, Safari, Edge (latest 2 versions)
- **WebAssembly Support**: Required for web deployment
- **Input Methods**: Mouse, keyboard, touch (for web)

### Original Game Constraints
- **Visual Fidelity**: Must match original game's visual style and aesthetic
- **Game Logic**: Must faithfully recreate original game mechanics
- **Educational Content**: Must preserve historical accuracy and educational value

### Copyright Considerations
- Original game assets are property of their respective copyright holders
- New code is available under MIT License
- Users must own a legitimate copy of the original game to use its assets

## Dependencies

### Runtime Dependencies
```toml
[dependencies]
macroquad = "0.3"       # 2D game framework
serde = { version = "1.0", features = ["derive"] }  # Serialization
serde_json = "1.0"      # JSON support
rand = "0.8"            # Random number generation
```

### Planned Additional Dependencies
- Audio processing library (TBD)
- Additional UI components (TBD)
- Resource compression/decompression (TBD)

### Developer Dependencies (Potential)
- Test frameworks
- Benchmarking tools
- Documentation generators
- Asset processing tools

## Tool Usage Patterns

### Asset Management
- Assets are loaded through the `AssetManager` class
- Resources are organized by type (image, sound, etc.)
- Assets are referenced by name rather than direct file paths
- Textures are cached in memory after first load

```rust
// Asset loading pattern
async fn load_game_assets(asset_manager: &mut AssetManager) {
    // Preload commonly used assets
    asset_manager.preload_textures(&["TITLE.png", "BANNER.png"]).await.unwrap();
    
    // Load individual assets as needed
    let texture = asset_manager.load_texture("SPRITE.png").await.unwrap();
}
```

### Game State Management
- State transitions managed through explicit methods
- Current state determines update and render behavior
- Scene-specific initialization on state changes

```rust
// State transition pattern
game.transition_to(GameState::MainMenu);
```

### Input Handling
- Input captured at the game loop level
- Dispatched to current active state
- State determines specific response to input events

### Rendering Pattern
- Render calls flow from game state to active scene
- Active scene manages layer order and composition
- UI elements draw on top of base scene elements

### Error Handling
- Results and Options for error propagation
- Structured error handling with specific error types
- Error logging for debugging

## Development Workflow

### Feature Implementation Process
1. Design feature interface and integration points
2. Implement minimal viable version
3. Integration with existing systems
4. Testing against original game behavior
5. Optimization and polish

### Testing Strategy
- Unit tests for game logic components
- Integration tests for system interactions
- Manual testing against original game behavior
- Cross-platform testing for compatibility

### Version Control Practices
- Feature branches for new development
- Pull requests for code review
- Semantic versioning for releases
- Comprehensive documentation in code