// Game Logic module - handles core game mechanics and rules

// Export modules
pub mod player;
pub mod inventory;
// Submodules will be declared here as they're created
// pub mod resources;
// pub mod time;
// pub mod weather;
// pub mod health;
// pub mod events;

/// Core game mechanics constants
pub mod constants {
    /// Default starting money
    pub const DEFAULT_STARTING_MONEY: u32 = 1600;
    
    /// Food consumption per person per day (in pounds)
    pub const FOOD_CONSUMPTION_PER_DAY: f32 = 2.0;
    
    /// Miles per day at normal pace
    pub const MILES_PER_DAY_NORMAL: f32 = 20.0;
    
    /// Wagon capacity in pounds
    pub const WAGON_CAPACITY: f32 = 2000.0;
}

/// Initializes game logic components
pub fn initialize() {
    println!("Game logic system initialized");
}
