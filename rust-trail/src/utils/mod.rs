// Utilities module - contains helper functions and utility code

// Submodules will be declared here as they're created
// pub mod math;
// pub mod rng;
// pub mod format_converters;

/// Get a percentage value between 0.0 and 1.0
pub fn get_percentage(value: f32, max: f32) -> f32 {
    if max <= 0.0 {
        return 0.0;
    }
    (value / max).clamp(0.0, 1.0)
}

/// Format money as a string with $ sign and commas
pub fn format_money(amount: u32) -> String {
    format!("${}", amount)
}

/// Linearly interpolate between two values
pub fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t.clamp(0.0, 1.0)
}

/// Convert a date (month, day, year) to a string
pub fn format_date(month: u8, day: u8, year: u16) -> String {
    // Month names
    let months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    
    // Ensure month index is valid (1-12 converted to 0-11)
    let month_idx = (month.saturating_sub(1) % 12) as usize;
    
    format!("{} {}, {}", months[month_idx], day, year)
}