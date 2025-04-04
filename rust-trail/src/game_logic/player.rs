use serde::{Serialize, Deserialize};

/// Represents the health status of a party member
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HealthStatus {
    Good,
    Fair,
    Poor,
    VeryPoor,
    Deceased,
}

/// Represents a specific disease or ailment
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Disease {
    Cholera,
    Dysentery,
    Measles,
    Typhoid,
    Fever,
    BrokenLeg,
    BrokenArm,
    Exhaustion,
    SnakeBite,
}

/// Represents a single party member
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartyMember {
    /// Name of the party member
    pub name: String,
    /// Current health status
    pub health: HealthStatus,
    /// Any diseases the party member has
    pub diseases: Vec<Disease>,
    /// Whether this member is the party leader
    pub is_leader: bool,
    /// Age of the party member
    pub age: u8,
}

impl PartyMember {
    /// Create a new party member
    pub fn new(name: &str, age: u8, is_leader: bool) -> Self {
        Self {
            name: name.to_string(),
            health: HealthStatus::Good,
            diseases: Vec::new(),
            is_leader,
            age,
        }
    }
    
    /// Check if the party member is alive
    pub fn is_alive(&self) -> bool {
        self.health != HealthStatus::Deceased
    }
    
    /// Contract a disease
    pub fn contract_disease(&mut self, disease: Disease) {
        if !self.diseases.contains(&disease) {
            self.diseases.push(disease);
            // Worsen health when contracting a disease
            self.degrade_health();
        }
    }
    
    /// Recover from a disease
    pub fn recover_from_disease(&mut self, disease: Disease) {
        self.diseases.retain(|&d| d != disease);
    }
    
    /// Degrade health by one level
    pub fn degrade_health(&mut self) {
        self.health = match self.health {
            HealthStatus::Good => HealthStatus::Fair,
            HealthStatus::Fair => HealthStatus::Poor,
            HealthStatus::Poor => HealthStatus::VeryPoor,
            HealthStatus::VeryPoor => HealthStatus::Deceased,
            HealthStatus::Deceased => HealthStatus::Deceased,
        };
    }
    
    /// Improve health by one level
    pub fn improve_health(&mut self) {
        self.health = match self.health {
            HealthStatus::Good => HealthStatus::Good,
            HealthStatus::Fair => HealthStatus::Good,
            HealthStatus::Poor => HealthStatus::Fair,
            HealthStatus::VeryPoor => HealthStatus::Poor,
            HealthStatus::Deceased => HealthStatus::Deceased,
        };
    }
}

/// Represents the pace of travel
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Pace {
    Steady,
    Strenuous,
    Grueling,
    Resting,
}

/// Represents the food ration level
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Rations {
    Filling,
    Meager,
    BareBones,
}

/// Manages the player's party and game state
#[derive(Debug, Serialize, Deserialize)]
pub struct PlayerState {
    /// Party members
    pub party: Vec<PartyMember>,
    /// Money (in dollars)
    pub money: u32,
    /// Current pace of travel
    pub pace: Pace,
    /// Current food ration level
    pub rations: Rations,
    /// Miles traveled so far
    pub miles_traveled: f32,
    /// Current location name
    pub location: String,
    /// Day of the journey
    pub day: u32,
    /// Month (1-12)
    pub month: u8,
    /// Year
    pub year: u16,
}

impl PlayerState {
    /// Create a new player state with default values
    pub fn new() -> Self {
        Self {
            party: Vec::new(),
            money: 1600, // Default starting money
            pace: Pace::Steady,
            rations: Rations::Filling,
            miles_traveled: 0.0,
            location: "Independence, Missouri".to_string(),
            day: 1,
            month: 3, // March
            year: 1848,
        }
    }
    
    /// Set up the initial party with the given leader name
    pub fn setup_party(&mut self, leader_name: &str, party_names: &[&str]) {
        // Create leader
        let leader = PartyMember::new(leader_name, 30, true);
        self.party.push(leader);
        
        // Create other party members
        for name in party_names {
            let member = PartyMember::new(name, 25, false);
            self.party.push(member);
        }
    }
    
    /// Get the number of living party members
    pub fn living_party_members(&self) -> usize {
        self.party.iter().filter(|m| m.is_alive()).count()
    }
    
    /// Advance the date by the specified number of days
    pub fn advance_date(&mut self, days: u32) {
        let mut remaining_days = days;
        
        while remaining_days > 0 {
            // Days in the current month
            let days_in_month = match self.month {
                1 => 31,  // January
                2 => if self.year % 4 == 0 { 29 } else { 28 },  // February
                3 => 31,  // March
                4 => 30,  // April
                5 => 31,  // May
                6 => 30,  // June
                7 => 31,  // July
                8 => 31,  // August
                9 => 30,  // September
                10 => 31, // October
                11 => 30, // November
                12 => 31, // December
                _ => 30,  // Default
            };
            
            // Calculate how many days to advance in the current month
            let days_to_advance = remaining_days.min(days_in_month - self.day + 1);
            
            // Advance the day
            self.day += days_to_advance;
            remaining_days -= days_to_advance;
            
            // Check if we need to move to the next month
            if self.day > days_in_month {
                self.day = 1;
                self.month += 1;
                
                // Check if we need to move to the next year
                if self.month > 12 {
                    self.month = 1;
                    self.year += 1;
                }
            }
        }
    }
}