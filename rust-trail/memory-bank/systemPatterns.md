# System Patterns: Oregon Trail Deluxe Rewrite (Rust Trail)

## System Architecture

### High-Level Architecture
Rust Trail follows a modular, state-based architecture organized into the following primary components:

```
[Main Entry] → [Game State Manager] → [Active Scene] → [Game Logic]
     ↓                ↓                     ↓               ↓
[Asset Loading] ← [Engine Services] → [Rendering] → [Player/World State]
```

The architecture separates concerns between:
- Engine functionality (rendering, asset management, input handling)
- Game logic (player, inventory, resources, events)
- Scene management (different screens and transitions)
- State management (overall game state flow)

### Module Structure
The codebase is organized into the following module hierarchy:

```
rust-trail/
├── src/
│   ├── main.rs                 # Application entry point
│   ├── game.rs                 # Game state management
│   ├── engine/                 # Core engine components
│   │   ├── mod.rs              # Module definitions
│   │   ├── asset_loader.rs     # Asset loading and management
│   │   ├── renderer.rs*        # Rendering system (planned)
│   │   ├── audio.rs*           # Audio system (planned)
│   │   ├── input.rs*           # Input handling (planned)
│   │   └── ui.rs*              # UI system (planned)
│   ├── scenes/                 # Game scenes/screens
│   │   ├── mod.rs              # Module definitions
│   │   ├── title_screen.rs     # Title screen
│   │   ├── button.rs           # Reusable button component
│   │   └── (other scenes)      # Additional game screens (planned)
│   ├── game_logic/             # Core game mechanics
│   │   ├── mod.rs              # Module definitions
│   │   ├── player.rs           # Player state management
│   │   ├── inventory.rs        # Inventory system
│   │   └── (other systems)     # Additional game systems (planned)
│   └── utils/                  # Utility functions and helpers
│       └── mod.rs              # Module definitions
```

## Key Design Patterns

### State Machine Pattern
The game uses a state machine pattern through the `GameState` enum and state transitions, managed by the `Game` struct. This pattern encapsulates the varying behaviors and visuals in each game state.

```rust
enum GameState {
    TitleScreen,
    Introduction,
    Options,
    MainMenu,
    Setup,
    Travel,
    // ... other states
}

// Transitions handled through methods like:
pub fn transition_to(&mut self, new_state: GameState) {
    // State transition logic
}
```

### Asset Management System
Resources are loaded and cached through the `AssetManager`, using a repository pattern to abstract asset access:

```rust
// Asset types categorized
enum AssetType {
    Image,
    Sound,
    Music,
    Text,
    Animation,
    Font,
}

// Assets retrieved by name, hiding implementation details
pub async fn load_texture(&mut self, name: &str) -> Result<Texture2D, String> {
    // Loading and caching logic
}
```

### Component Pattern
UI elements like buttons are designed as reusable components:

```rust
struct Button {
    position: Vec2,
    size: Vec2,
    texture: Option<Texture2D>,
    // Additional properties
}

impl Button {
    // Methods for creation, interaction, rendering
}
```

### Scene System
Each game screen is encapsulated as a scene that handles its own:
- Initialization and asset loading
- Input processing  
- Update logic
- Rendering

```rust
struct TitleScreen {
    // Scene-specific state
}

impl TitleScreen {
    pub fn new() -> Self { /* ... */ }
    pub async fn load_assets(&mut self, asset_manager: &mut AssetManager) { /* ... */ }
    pub fn update(&mut self, dt: f32) -> Option<TitleAction> { /* ... */ }
    pub fn draw(&self) { /* ... */ }
}
```

## Critical Implementation Paths

### Game Initialization Flow
1. Program entry (`main.rs`) initializes the game loop
2. `Game::new()` creates initial game state
3. `game.load_assets().await` asynchronously loads required assets
4. Main loop runs update and render cycles

### State Transition Path
1. Input or game event triggers a transition
2. `transition_to(new_state)` method called
3. New state initialization/preparation (if needed)
4. Subsequent update/render cycles use new state logic

### Asset Loading Path
1. `AssetManager` created with base asset path
2. Assets requested by name via specific load methods (textures, text, etc.)
3. File loaded from correct subdirectory based on asset type
4. Loaded asset cached for future access
5. Asset accessed by scenes/systems as needed

### User Input Flow
1. Input events (keyboard, mouse) captured in the game loop
2. Current active state processes relevant inputs in its update method
3. State changes or actions triggered based on input

## Component Relationships

### Game State → Scenes
The active game state determines which scene is currently active. Each scene implementation (e.g., TitleScreen) provides specific behavior for:
- Processing input
- Updating game logic
- Rendering visuals

### Engine Services → Game Components
Engine services provide capabilities to game components:
- `AssetManager` provides assets to scenes and game logic
- (Planned) Rendering system will handle drawing game elements
- (Planned) Input system will provide user interaction detection
- (Planned) Audio system will manage sound effects and music

### Game Logic → World Representation
Game logic components model the game world:
- Player state (party members, health, etc.)
- Inventory (supplies, equipment)
- In-game systems (weather, events, etc.)

## Technical Constraints and Decisions

### Rust + Macroquad Decision
- **Rust** chosen for safety, performance, and modern language features
- **Macroquad** selected for:
  - Cross-platform compatibility
  - WebAssembly support
  - Minimal dependencies
  - Simple API for 2D rendering

### Cross-Platform Architecture
- Asset paths use cross-platform path handling
- Rendering system abstracts platform differences
- Input system normalizes across platforms

### Asset Management Approach
- Assets organized by type in subdirectories
- Original assets converted to modern formats
- Runtime loading and caching to optimize memory use

## Future Architectural Considerations

### Planned Components
- Complete scene implementations for all game screens
- Full implementation of game mechanics (travel, weather, health systems)
- Audio system for sound effects and music
- Saving/loading system for game states
- Advanced UI components for game interface

### Extensibility Points
- Modular scene system allows for new screens
- Asset management system can be extended for new asset types
- Game state design permits adding new states