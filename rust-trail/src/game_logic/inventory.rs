use serde::{Serialize, Deserialize};
use std::collections::HashMap;

/// Represents the different types of items in the game
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ItemType {
    Food,           // Food for the party
    Clothing,       // Clothing for protection
    Ammunition,     // Bullets for hunting and protection
    OxenPair,       // Pairs of oxen for pulling the wagon
    SpareWheel,     // Spare wagon wheels
    SpareAxle,      // Spare wagon axles
    SpareTongue,    // Spare wagon tongues
    MedicalSupply,  // Medicine for treating illnesses
}

/// A single type of item with quantity and properties
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Item {
    /// The type of item
    pub item_type: ItemType,
    /// Quantity of the item
    pub quantity: u32,
    /// Weight per unit in pounds
    pub weight_per_unit: f32,
    /// Cost per unit in dollars
    pub cost_per_unit: u32,
}

impl Item {
    /// Create a new item
    pub fn new(item_type: ItemType, quantity: u32, weight_per_unit: f32, cost_per_unit: u32) -> Self {
        Self {
            item_type,
            quantity,
            weight_per_unit,
            cost_per_unit,
        }
    }

    /// Get the total weight of this item
    pub fn total_weight(&self) -> f32 {
        self.quantity as f32 * self.weight_per_unit
    }

    /// Get the total cost of this item
    pub fn total_cost(&self) -> u32 {
        self.quantity * self.cost_per_unit
    }
}

/// Manages all inventory items
#[derive(Debug, Serialize, Deserialize)]
pub struct Inventory {
    /// Map of items by type
    items: HashMap<ItemType, Item>,
    /// Maximum weight capacity in pounds
    max_capacity: f32,
}

impl Inventory {
    /// Create a new, empty inventory
    pub fn new(max_capacity: f32) -> Self {
        Self {
            items: HashMap::new(),
            max_capacity,
        }
    }

    /// Add an item to the inventory
    pub fn add_item(&mut self, item_type: ItemType, quantity: u32) {
        if let Some(item) = self.items.get_mut(&item_type) {
            // Item already exists, update quantity
            item.quantity += quantity;
        } else {
            // Create new item with default properties
            let item = match item_type {
                ItemType::Food => Item::new(item_type, quantity, 1.0, 2),
                ItemType::Clothing => Item::new(item_type, quantity, 2.0, 10),
                ItemType::Ammunition => Item::new(item_type, quantity, 0.1, 2),
                ItemType::OxenPair => Item::new(item_type, quantity, 500.0, 40),
                ItemType::SpareWheel => Item::new(item_type, quantity, 15.0, 10),
                ItemType::SpareAxle => Item::new(item_type, quantity, 10.0, 8),
                ItemType::SpareTongue => Item::new(item_type, quantity, 8.0, 6),
                ItemType::MedicalSupply => Item::new(item_type, quantity, 0.5, 15),
            };
            self.items.insert(item_type, item);
        }
    }

    /// Remove an item from the inventory
    /// Returns true if successful, false if not enough items
    pub fn remove_item(&mut self, item_type: ItemType, quantity: u32) -> bool {
        if let Some(item) = self.items.get_mut(&item_type) {
            if item.quantity >= quantity {
                item.quantity -= quantity;
                
                // Remove the entry if quantity is zero
                if item.quantity == 0 {
                    self.items.remove(&item_type);
                }
                
                return true;
            }
        }
        false
    }

    /// Get the quantity of a specific item
    pub fn get_quantity(&self, item_type: ItemType) -> u32 {
        self.items.get(&item_type).map_or(0, |item| item.quantity)
    }

    /// Calculate the total weight of all inventory items
    pub fn total_weight(&self) -> f32 {
        self.items.values().map(|item| item.total_weight()).sum()
    }

    /// Check if adding an item would exceed capacity
    pub fn can_add(&self, item_type: ItemType, quantity: u32) -> bool {
        let weight_per_unit = match self.items.get(&item_type) {
            Some(item) => item.weight_per_unit,
            None => match item_type {
                ItemType::Food => 1.0,
                ItemType::Clothing => 2.0,
                ItemType::Ammunition => 0.1,
                ItemType::OxenPair => 500.0,
                ItemType::SpareWheel => 15.0,
                ItemType::SpareAxle => 10.0,
                ItemType::SpareTongue => 8.0,
                ItemType::MedicalSupply => 0.5,
            },
        };

        let additional_weight = weight_per_unit * quantity as f32;
        self.total_weight() + additional_weight <= self.max_capacity
    }

    /// Get a list of all items
    pub fn get_all_items(&self) -> Vec<&Item> {
        self.items.values().collect()
    }

    /// Use food from inventory
    /// Returns true if successful, false if not enough food
    pub fn use_food(&mut self, pounds: f32) -> bool {
        let pounds_int = pounds.ceil() as u32;
        self.remove_item(ItemType::Food, pounds_int)
    }

    /// Use ammunition for hunting or defense
    /// Returns true if successful, false if not enough ammunition
    pub fn use_ammunition(&mut self, quantity: u32) -> bool {
        self.remove_item(ItemType::Ammunition, quantity)
    }

    /// Use medical supplies for treating illness
    /// Returns true if successful, false if not enough supplies
    pub fn use_medical_supply(&mut self) -> bool {
        self.remove_item(ItemType::MedicalSupply, 1)
    }

    /// Get the capacity information
    pub fn capacity_info(&self) -> (f32, f32, f32) {
        let current_weight = self.total_weight();
        let percent_full = (current_weight / self.max_capacity) * 100.0;
        (current_weight, self.max_capacity, percent_full)
    }
}