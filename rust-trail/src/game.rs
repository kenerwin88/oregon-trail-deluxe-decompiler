use macroquad::prelude::*;
use crate::engine::asset_loader::AssetManager;
use crate::scenes::title::{TitleScreen, TitleAction};

/// Represents the different states the game can be in
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GameState {
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

/// Main game struct that manages the overall game state
pub struct Game {
    /// Current state of the game
    state: GameState,
    /// Whether the game is requesting to exit
    exit_requested: bool,
    /// Asset manager for loading and caching assets
    asset_manager: AssetManager,
    /// Title screen
    title_screen: Option<TitleScreen>,
    /// Whether assets are loaded
    assets_loaded: bool,
}

impl Game {
    /// Create a new game instance
    pub fn new() -> Self {
        Self {
            state: GameState::TitleScreen,
            exit_requested: false,
            asset_manager: AssetManager::new("assets"),
            title_screen: Some(TitleScreen::new()),
            assets_loaded: false,
        }
    }

    /// Update game state based on delta time
    pub fn update(&mut self, dt: f32) {
        // Load assets if not already loaded
        if !self.assets_loaded {
            return;
        }
        
        // Handle state-specific updates
        match self.state {
            GameState::TitleScreen => {
                // Update title screen
                if let Some(title_screen) = &mut self.title_screen {
                    if let Some(action) = title_screen.update(dt) {
                        match action {
                            TitleAction::StartGame => self.transition_to(GameState::MainMenu),
                            TitleAction::Quit => self.exit_requested = true,
                        }
                    }
                }
            }
            GameState::MainMenu => {
                // Main menu logic
                // Placeholder for menu navigation and selection
            }
            // Other state handling would go here
            _ => {}
        }

        // Check for global exit condition (Escape key)
        if is_key_pressed(KeyCode::Escape) {
            self.exit_requested = true;
        }
    }

    /// Render the current game state
    pub fn render(&self) {
        if !self.assets_loaded {
            // Display loading screen
            let text = "Loading resources...";
            let font_size = 30.0;
            let text_size = measure_text(text, None, font_size as u16, 1.0);
            
            draw_text(
                text,
                screen_width() / 2.0 - text_size.width / 2.0,
                screen_height() / 2.0,
                font_size,
                WHITE,
            );
            return;
        }
        
        match self.state {
            GameState::TitleScreen => {
                // Render title screen
                if let Some(title_screen) = &self.title_screen {
                    title_screen.draw();
                }
            }
            GameState::MainMenu => {
                // Render main menu
                draw_text("Main Menu", 
                    screen_width() / 2.0 - 50.0, 
                    50.0, 
                    30.0, 
                    WHITE);
                
                // Menu options would be rendered here
            }
            // Other state rendering would go here
            _ => {}
        }
    }

    /// Transition to a new game state
    pub fn transition_to(&mut self, new_state: GameState) {
        println!("Transitioning from {:?} to {:?}", self.state, new_state);
        self.state = new_state;
        
        // Additional state transition logic could be added here
        // For example, loading resources, playing transition sounds, etc.
    }

    /// Check if the game is requesting to exit
    pub fn is_exit_requested(&self) -> bool {
        self.exit_requested
    }
    
    /// Load all game assets
    pub async fn load_assets(&mut self) {
        // Load title screen assets
        if let Some(title_screen) = &mut self.title_screen {
            title_screen.load_assets(&mut self.asset_manager).await;
        }
        
        // Mark assets as loaded
        self.assets_loaded = true;
    }
}
