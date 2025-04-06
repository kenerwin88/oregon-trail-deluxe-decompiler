use macroquad::prelude::*;
use crate::engine::asset_loader::AssetManager;
use crate::scenes::button::{Button, ButtonAction};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TitleAction {
    StartGame,
    Introduction,
    Options,
    Quit,
}

pub struct TitleScreen {
    background: Option<Texture2D>,
    button_texture: Option<Texture2D>,
    time: f32,
    assets_loaded: bool,
    buttons: Vec<Button>,
}

impl TitleScreen {
    pub fn new() -> Self {
        Self {
            background: None,
            button_texture: None,
            time: 0.0,
            assets_loaded: false,
            buttons: Vec::new(),
        }
    }
    
    pub async fn load_assets(&mut self, asset_manager: &mut AssetManager) {
        // Load background
        if let Ok(texture) = asset_manager.load_texture("TITLE.png").await {
            self.background = Some(texture);
        }
        
        // Load button texture
        if let Ok(texture) = asset_manager.load_texture("TITLEBTN.png").await {
            self.button_texture = Some(texture);
            self.init_buttons();
        }
        
        self.assets_loaded = true;
    }
    
    fn init_buttons(&mut self) {
        self.buttons.clear();
        
        // Get screen dimensions
        let screen_w = screen_width();
        let screen_h = screen_height();
        
        // Calculate scaling based on original TITLE.png dimensions (577 x 418)
        let screen_scale_x = screen_w / 577.0;
        let screen_scale_y = screen_h / 418.0;
        

        
        // Button Y position
        let button_y = 370.0 * screen_scale_y; // Options
        
        // Create Introduction button
        let intro_button = Button::new(
            ButtonAction::Introduction,
            Vec2::new(34.0 * screen_scale_x,  button_y),
            self.button_texture,
            screen_scale_x,
            screen_scale_y
        );
        self.buttons.push(intro_button);
        
        // Create Options button
        let options_button = Button::new(
            ButtonAction::Options,
            Vec2::new(165.0 * screen_scale_x, button_y),
            self.button_texture,
            screen_scale_x,
            screen_scale_y
        );
        self.buttons.push(options_button);
        
        // Create Quit button
        let quit_button = Button::new(
            ButtonAction::Quit,
            Vec2::new(298.0 * screen_scale_x, button_y),
            self.button_texture,
            screen_scale_x,
            screen_scale_y
        );
        self.buttons.push(quit_button);
        
        // Create Travel Trail button
        let travel_button = Button::new(
            ButtonAction::TravelTrail,
            Vec2::new(428.0 * screen_scale_x, button_y),
            self.button_texture,
            screen_scale_x,
            screen_scale_y
        );
        self.buttons.push(travel_button);
    }
    
    pub fn update(&mut self, dt: f32) -> Option<TitleAction> {
        self.time += dt;
        
        // Keyboard shortcuts
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
        
        // Button interactions
        for button in &mut self.buttons {
            if let Some(action) = button.update(dt) {
                match action {
                    ButtonAction::Introduction => return Some(TitleAction::Introduction),
                    ButtonAction::Options => return Some(TitleAction::Options),
                    ButtonAction::Quit => return Some(TitleAction::Quit),
                    ButtonAction::TravelTrail => return Some(TitleAction::StartGame),
                }
            }
        }
        
        None
    }
    
    pub fn draw(&self) {
        clear_background(BLACK);
        
        let screen_w = screen_width();
        let screen_h = screen_height();
        
        // Draw background
        if let Some(texture) = self.background {
            draw_texture_ex(
                texture,
                0.0,
                0.0,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(Vec2::new(screen_w, screen_h)),
                    ..Default::default()
                }
            );
        } else {
            // Fallback title
            let title_text = "THE OREGON TRAIL";
            let font_size = 40.0;
            let text_size = measure_text(title_text, None, font_size as u16, 1.0);
            draw_text(
                title_text,
                screen_w / 2.0 - text_size.width / 2.0,
                screen_h / 3.0,
                font_size,
                WHITE
            );
        }
        
        // Draw buttons
        for button in &self.buttons {
            button.draw();
        }
        
        // Draw copyright
        let copyright = "© 2025 Oregon Trail Rewrite Project";
        let font_size = 16.0;
        let text_size = measure_text(copyright, None, font_size as u16, 1.0);
        draw_text(
            copyright,
            screen_w / 2.0 - text_size.width / 2.0,
            screen_h - 30.0,
            font_size,
            GRAY
        );
    }
    
    pub fn is_loaded(&self) -> bool {
        self.assets_loaded
    }
}
