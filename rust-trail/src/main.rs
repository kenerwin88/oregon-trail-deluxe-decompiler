use macroquad::prelude::*;

mod game;
mod engine;
mod scenes;
mod game_logic;
mod utils;

#[macroquad::main("Oregon Trail Deluxe")]
async fn main() {
    // Initialize game
    let mut game = game::Game::new();
    
    // Load game assets
    game.load_assets().await;
    
    // Main game loop
    loop {
        // Update game state based on delta time
        let delta_time = get_frame_time();
        game.update(delta_time);
        
        // Render current frame
        clear_background(BLACK);
        game.render();
        
        // Check if we should exit
        if game.is_exit_requested() {
            break;
        }
        
        // Wait for next frame
        next_frame().await;
    }
}