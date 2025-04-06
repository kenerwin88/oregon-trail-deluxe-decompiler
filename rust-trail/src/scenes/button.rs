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
    /// Click timer (for showing clicked state briefly)
    click_timer: f32,
    /// Button label
    label: String,
}

impl Button {
    /// Create a new button
    pub fn new(
        button_type: ButtonAction,
        position: Vec2,
        _sprite_sheet: Texture2D, // Not used for now
    ) -> Self {
        // Button dimensions
        let button_width = 150.0;
        let button_height = 40.0;
        
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
            click_timer: 0.0,
            label,
        }
    }
    
    /// Update button state based on mouse position and clicks
    pub fn update(&mut self, dt: f32) -> Option<ButtonAction> {
        let mouse_pos = mouse_position();
        let was_clicked = self.state == ButtonState::Clicked;
        
        // Check if mouse is over the button
        let is_hovering = 
            mouse_pos.0 >= self.position.x && 
            mouse_pos.0 <= self.position.x + self.width &&
            mouse_pos.1 >= self.position.y && 
            mouse_pos.1 <= self.position.y + self.height;
        
        // Update click timer if button is in clicked state
        if self.state == ButtonState::Clicked {
            self.click_timer += dt;
            if self.click_timer >= 0.1 {
                self.state = ButtonState::Normal;
                self.click_timer = 0.0;
            }
        } else if is_hovering {
            // Check for mouse click when hovering
            if is_mouse_button_pressed(MouseButton::Left) {
                self.state = ButtonState::Clicked;
                self.click_timer = 0.0;
            } else {
                self.state = ButtonState::Hover;
            }
        } else {
            self.state = ButtonState::Normal;
        }
        
        // Return action if button was clicked and now released
        if was_clicked && self.state != ButtonState::Clicked {
            Some(self.action)
        } else {
            None
        }
    }
    
    /// Draw the button
    pub fn draw(&self) {
        // Choose colors based on button type and state
        let (bg_color, border_color, text_color) = match self.action {
            ButtonAction::Introduction => {
                match self.state {
                    ButtonState::Normal => (BLUE, DARKBLUE, WHITE),
                    ButtonState::Hover => (Color::new(0.3, 0.3, 0.9, 1.0), BLUE, WHITE),
                    ButtonState::Clicked => (DARKBLUE, WHITE, YELLOW),
                }
            },
            ButtonAction::Options => {
                match self.state {
                    ButtonState::Normal => (PURPLE, Color::new(0.3, 0.0, 0.3, 1.0), WHITE),
                    ButtonState::Hover => (Color::new(0.7, 0.3, 0.7, 1.0), PURPLE, WHITE),
                    ButtonState::Clicked => (DARKPURPLE, WHITE, YELLOW),
                }
            },
            ButtonAction::Quit => {
                match self.state {
                    ButtonState::Normal => (RED, DARKRED, WHITE),
                    ButtonState::Hover => (Color::new(1.0, 0.3, 0.3, 1.0), RED, WHITE),
                    ButtonState::Clicked => (DARKRED, WHITE, YELLOW),
                }
            },
            ButtonAction::TravelTrail => {
                match self.state {
                    ButtonState::Normal => (GREEN, DARKGREEN, WHITE),
                    ButtonState::Hover => (Color::new(0.3, 0.9, 0.3, 1.0), GREEN, WHITE),
                    ButtonState::Clicked => (DARKGREEN, WHITE, YELLOW),
                }
            },
        };
        
        // Draw button background
        draw_rectangle(
            self.position.x,
            self.position.y,
            self.width,
            self.height,
            bg_color
        );
        
        // Draw border
        draw_rectangle_lines(
            self.position.x,
            self.position.y,
            self.width,
            self.height,
            3.0,
            border_color
        );
        
        // Draw button text
        let font_size = 20.0;
        let text_size = measure_text(&self.label, None, font_size as u16, 1.0);
        
        draw_text(
            &self.label,
            self.position.x + (self.width - text_size.width) / 2.0,
            self.position.y + (self.height + text_size.height) / 2.0,
            font_size,
            text_color
        );
        
        // Print debug info
        let debug_info = format!(
            "{:?} Button at ({:.1}, {:.1}), size: {:.1}x{:.1}, state: {:?}",
            self.action, self.position.x, self.position.y, self.width, self.height, self.state
        );
        
        // Draw debug text below the button
        draw_text(
            &debug_info,
            self.position.x,
            self.position.y + self.height + 15.0,
            10.0,
            GRAY
        );
    }
}