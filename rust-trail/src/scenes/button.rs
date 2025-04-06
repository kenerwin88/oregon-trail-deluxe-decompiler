use macroquad::prelude::*;

/// Button state (normal, hover, clicked)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ButtonState {
    Normal,
    Hover,
    Clicked,
}

/// Button action that can be triggered
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ButtonAction {
    Introduction,
    Options,
    Quit,
    TravelTrail,
}

/// A clickable button with different states
pub struct Button {
    /// Position of the button (top-left corner)
    position: Vec2,
    /// Width of the button
    width: f32,
    /// Height of the button
    height: f32,
    /// Current state of the button
    state: ButtonState,
    /// Associated action
    action: ButtonAction,
    /// Button label
    label: String,
    /// Sprite sheet texture
    texture: Option<Texture2D>,
    /// Button row in sprite sheet (0-3)
    sprite_row: usize,
    /// Tracks if this button was pressed down (mouse button pressed while hovering)
    was_pressed: bool,
}

impl Button {
    /// Create a new button
    pub fn new(
        button_type: ButtonAction,
        position: Vec2,
        sprite_sheet: Option<Texture2D>,
        scale_x: f32,
        scale_y: f32,
    ) -> Self {
        // Base dimensions from the sprite sheet
        let base_width = 113.0;
        let base_height = 20.0;
        
        // Scale dimensions based on screen scale factors
        let button_width = base_width * scale_x;
        let button_height = base_height * scale_y;
        
        // Determine sprite row based on button type
        let sprite_row = match button_type {
            ButtonAction::Introduction => 0,
            ButtonAction::Options => 1,
            ButtonAction::Quit => 2,
            ButtonAction::TravelTrail => 3,
        };
        
        // Create label based on button type
        let label = match button_type {
            ButtonAction::Introduction => "Introduction".to_string(),
            ButtonAction::Options => "Options".to_string(),
            ButtonAction::Quit => "Quit".to_string(),
            ButtonAction::TravelTrail => "Travel the Trail".to_string(),
        };
        
        Self {
            position,
            width: button_width,
            height: button_height,
            state: ButtonState::Normal,
            action: button_type,
            label,
            texture: sprite_sheet,
            sprite_row,
            was_pressed: false,
        }
    }
    
    /// Update button state based on mouse position and clicks
    pub fn update(&mut self, _dt: f32) -> Option<ButtonAction> {
        let mouse_pos = mouse_position();
        
        // Check if mouse is over the button
        let is_hovering = 
            mouse_pos.0 >= self.position.x && 
            mouse_pos.0 <= self.position.x + self.width &&
            mouse_pos.1 >= self.position.y && 
            mouse_pos.1 <= self.position.y + self.height;
        
        // Track mouse button state
        let mouse_down = is_mouse_button_down(MouseButton::Left);
        let mouse_released = is_mouse_button_released(MouseButton::Left);
        
        // Handle different cases
        if is_hovering {
            if mouse_down {
                // Mouse is being held down while over the button
                self.state = ButtonState::Clicked;
                if is_mouse_button_pressed(MouseButton::Left) {
                    // Mouse was just pressed down
                    self.was_pressed = true;
                }
            } else {
                // Mouse is over button but not pressed
                self.state = ButtonState::Hover;
            }
        } else {
            // Mouse is not over the button
            self.state = ButtonState::Normal;
        }
        
        // Check for click action (mouse was pressed on this button and now released while hovering)
        if mouse_released && is_hovering && self.was_pressed {
            self.was_pressed = false;
            return Some(self.action);
        }
        
        // Reset was_pressed if mouse is released outside the button
        if mouse_released {
            self.was_pressed = false;
        }
        
        None
    }
    
    /// Draw the button
    pub fn draw(&self) {
        if let Some(texture) = self.texture {
            // Determine source rectangle based on button state and sprite row
            let src_x = match self.state {
                ButtonState::Normal | ButtonState::Hover => 0.0,     // Left column for normal/hover
                ButtonState::Clicked => 113.0,                       // Right column for clicked
            };
            
            // The sprite sheet has each button row at 20px height
            let src_y = (self.sprite_row as f32) * 20.0;  // Row based on button type
            
            // Draw the button using the sprite sheet
            draw_texture_ex(
                texture,
                self.position.x,
                self.position.y,
                WHITE,
                DrawTextureParams {
                    source: Some(Rect::new(src_x, src_y, 113.0, 20.0)),
                    dest_size: Some(Vec2::new(self.width, self.height)),
                    ..Default::default()
                },
            );
        } else {
            // Draw button text
            let font_size = 20.0;
            let text_size = measure_text(&self.label, None, font_size as u16, 1.0);
            
            draw_text(
                &self.label,
                self.position.x + (self.width - text_size.width) / 2.0,
                self.position.y + (self.height + text_size.height) / 2.0,
                font_size,
                BLACK
            );
        }
    }
}