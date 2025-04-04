use macroquad::prelude::*;
use crate::engine::asset_loader::AssetManager;

/// Represents the title screen state
pub struct TitleScreen {
    /// Title background texture
    background: Option<Texture2D>,
    /// Time counter for animations
    time: f32,
    /// Whether assets are loaded
    assets_loaded: bool,
}

impl TitleScreen {
    /// Create a new title screen
    pub fn new() -> Self {
        Self {
            background: None,
            time: 0.0,
            assets_loaded: false,
        }
    }
    
    /// Load assets for the title screen
    pub async fn load_assets(&mut self, asset_manager: &mut AssetManager) {
        // Load the title screen background
        match asset_manager.load_texture("TITLE.png").await {
            Ok(texture) => {
                self.background = Some(texture);
                self.assets_loaded = true;
            },
            Err(error) => {
                println!("Failed to load title screen assets: {}", error);
                // Fall back to a simple text-based title screen
                self.assets_loaded = true;
            }
        }
    }
    
    /// Update the title screen
    pub fn update(&mut self, dt: f32) -> Option<TitleAction> {
        // Update time counter for animations
        self.time += dt;
        
        // Check for input to continue
        if is_key_pressed(KeyCode::Space) || 
           is_key_pressed(KeyCode::Enter) ||
           is_mouse_button_pressed(MouseButton::Left) {
            return Some(TitleAction::StartGame);
        }
        
        // Check for quit
        if is_key_pressed(KeyCode::Escape) {
            return Some(TitleAction::Quit);
        }
        
        None
    }
    
    /// Draw the title screen
    pub fn draw(&self) {
        clear_background(BLACK);
        
        if let Some(texture) = self.background {
            // Draw background texture
            let screen_width = screen_width();
            let screen_height = screen_height();
            
            // Center the texture on screen
            let dest_size = Vec2::new(screen_width, screen_height);
            draw_texture_ex(
                texture,
                0.0,
                0.0,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(dest_size),
                    ..Default::default()
                },
            );
        } else {
            // Fallback to text-based title
            let title_text = "THE OREGON TRAIL";
            let title_font_size = 40.0;
            let title_size = measure_text(title_text, None, title_font_size as u16, 1.0);
            
            draw_text(
                title_text,
                screen_width() / 2.0 - title_size.width / 2.0,
                screen_height() / 3.0,
                title_font_size,
                WHITE,
            );
            
            // Draw subtitle
            let subtitle_text = "DELUXE EDITION";
            let subtitle_font_size = 20.0;
            let subtitle_size = measure_text(subtitle_text, None, subtitle_font_size as u16, 1.0);
            
            draw_text(
                subtitle_text,
                screen_width() / 2.0 - subtitle_size.width / 2.0,
                screen_height() / 3.0 + 50.0,
                subtitle_font_size,
                WHITE,
            );
        }
        
        // Draw prompt text with pulsing effect
        let prompt_text = "Press SPACE or CLICK to begin";
        let prompt_font_size = 20.0;
        let prompt_size = measure_text(prompt_text, None, prompt_font_size as u16, 1.0);
        
        // Make text pulse by changing alpha
        let alpha = (self.time * 2.0).sin() * 0.5 + 0.5;
        let prompt_color = Color::new(1.0, 1.0, 1.0, alpha);
        
        draw_text(
            prompt_text,
            screen_width() / 2.0 - prompt_size.width / 2.0,
            screen_height() * 0.75,
            prompt_font_size,
            prompt_color,
        );
        
        // Draw copyright
        let copyright_text = "© 2025 Oregon Trail Rewrite Project";
        let copyright_font_size = 16.0;
        let copyright_size = measure_text(copyright_text, None, copyright_font_size as u16, 1.0);
        
        draw_text(
            copyright_text,
            screen_width() / 2.0 - copyright_size.width / 2.0,
            screen_height() - 30.0,
            copyright_font_size,
            GRAY,
        );
    }
    
    /// Check if the title screen assets are loaded
    pub fn is_loaded(&self) -> bool {
        self.assets_loaded
    }
}

/// Actions that can be triggered from the title screen
pub enum TitleAction {
    /// Start the game (go to main menu)
    StartGame,
    /// Quit the game
    Quit,
}