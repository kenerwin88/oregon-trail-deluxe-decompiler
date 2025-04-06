use macroquad::prelude::*;
use crate::engine::asset_loader::AssetManager;

/// Actions that can be triggered from the title screen
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TitleAction {
    StartGame,
    Introduction,
    Options,
    Quit,
}

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
                println!("Failed to load title screen background: {}", error);
                // We'll still mark assets as loaded so the game can proceed
                self.assets_loaded = true;
            }
        }
    }
    
    /// Update the title screen
    pub fn update(&mut self, dt: f32) -> Option<TitleAction> {
        // Update time counter for animations
        self.time += dt;
        
        // Process keyboard input
        if is_key_pressed(KeyCode::Space) || is_key_pressed(KeyCode::Enter) {
            return Some(TitleAction::StartGame);
        }
        
        if is_key_pressed(KeyCode::I) {
            return Some(TitleAction::Introduction);
        }
        
        if is_key_pressed(KeyCode::O) {
            return Some(TitleAction::Options);
        }
        
        if is_key_pressed(KeyCode::Escape) || is_key_pressed(KeyCode::Q) {
            return Some(TitleAction::Quit);
        }
        
        // Process mouse input
        if is_mouse_button_pressed(MouseButton::Left) {
            let mouse_pos = mouse_position();
            let screen_width = screen_width();
            let screen_height = screen_height();
            
            // Bottom center - Travel Trail
            if mouse_pos.1 > screen_height - 100.0 && 
               mouse_pos.0 > screen_width / 2.0 - 75.0 && 
               mouse_pos.0 < screen_width / 2.0 + 75.0 {
                return Some(TitleAction::StartGame);
            }
            
            // Left buttons area
            if mouse_pos.0 < 200.0 {
                // Introduction button
                if mouse_pos.1 > 200.0 && mouse_pos.1 < 240.0 {
                    return Some(TitleAction::Introduction);
                }
                
                // Options button
                if mouse_pos.1 > 260.0 && mouse_pos.1 < 300.0 {
                    return Some(TitleAction::Options);
                }
                
                // Quit button
                if mouse_pos.1 > 320.0 && mouse_pos.1 < 360.0 {
                    return Some(TitleAction::Quit);
                }
            }
        }
        
        None
    }
    
    /// Draw the title screen
    pub fn draw(&self) {
        clear_background(BLACK);
        
        if let Some(texture) = self.background {
            // Draw the background centered on screen
            let screen_width = screen_width();
            let screen_height = screen_height();
            
            draw_texture_ex(
                texture,
                0.0,
                0.0,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(Vec2::new(screen_width, screen_height)),
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
        
        // Draw buttons as colored rectangles
        let screen_width = screen_width();
        let screen_height = screen_height();
        
        // Travel the Trail button
        draw_rectangle(screen_width / 2.0 - 75.0, screen_height - 100.0, 150.0, 40.0, GREEN);
        draw_rectangle_lines(screen_width / 2.0 - 75.0, screen_height - 100.0, 150.0, 40.0, 2.0, DARKGREEN);
        let travel_text = "Travel the Trail";
        let text_dim = measure_text(travel_text, None, 20.0 as u16, 1.0);
        draw_text(
            travel_text,
            screen_width / 2.0 - text_dim.width / 2.0,
            screen_height - 80.0,
            20.0,
            WHITE
        );
        
        // Introduction button
        draw_rectangle(50.0, 200.0, 150.0, 40.0, BLUE);
        draw_rectangle_lines(50.0, 200.0, 150.0, 40.0, 2.0, DARKBLUE);
        draw_text("Introduction", 75.0, 225.0, 20.0, WHITE);
        
        // Options button
        draw_rectangle(50.0, 260.0, 150.0, 40.0, PURPLE);
        draw_rectangle_lines(50.0, 260.0, 150.0, 40.0, 2.0, DARKPURPLE);
        draw_text("Options", 95.0, 285.0, 20.0, WHITE);
        
        // Quit button
        draw_rectangle(50.0, 320.0, 150.0, 40.0, RED);
        draw_rectangle_lines(50.0, 320.0, 150.0, 40.0, 2.0, MAROON);
        draw_text("Quit", 110.0, 345.0, 20.0, WHITE);
        
        // Draw copyright
        let copyright_text = "© 2025 Oregon Trail Rewrite Project";
        let copyright_font_size = 16.0;
        let copyright_size = measure_text(copyright_text, None, copyright_font_size as u16, 1.0);
        
        draw_text(
            copyright_text,
            screen_width / 2.0 - copyright_size.width / 2.0,
            screen_height - 30.0,
            copyright_font_size,
            GRAY,
        );
    }
    
    /// Check if the title screen assets are loaded
    pub fn is_loaded(&self) -> bool {
        self.assets_loaded
    }
}
