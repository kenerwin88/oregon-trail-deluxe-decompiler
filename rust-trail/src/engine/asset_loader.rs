use macroquad::prelude::*;
use std::collections::HashMap;
use std::path::Path;

/// Represents the different types of assets
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AssetType {
    Image,
    Sound,
    Music,
    Text,
    Animation,
    Font,
}

/// Asset manager for loading and caching game assets
pub struct AssetManager {
    /// Cache of loaded textures
    textures: HashMap<String, Texture2D>,
    /// Base path for assets
    asset_base_path: String,
}

impl AssetManager {
    /// Create a new asset manager
    pub fn new(base_path: &str) -> Self {
        Self {
            textures: HashMap::new(),
            asset_base_path: base_path.to_string(),
        }
    }

    /// Get the full path for an asset
    pub fn get_asset_path(&self, asset_type: AssetType, asset_name: &str) -> String {
        let type_folder = match asset_type {
            AssetType::Image => "images",
            AssetType::Sound => "audio/sounds",
            AssetType::Music => "audio/music",
            AssetType::Text => "text",
            AssetType::Animation => "animations",
            AssetType::Font => "fonts",
        };

        format!("{}/{}/{}", self.asset_base_path, type_folder, asset_name)
    }

    /// Load a texture from file
    pub async fn load_texture(&mut self, name: &str) -> Result<Texture2D, String> {
        // Check if texture is already loaded
        if let Some(texture) = self.textures.get(name) {
            return Ok(*texture);
        }

        // Get path for the image
        let path = self.get_asset_path(AssetType::Image, name);
        
        // Attempt to load the texture
        let texture = load_texture(&path).await.map_err(|e| {
            format!("Failed to load texture '{}': {}", path, e)
        })?;

        // Store in cache
        self.textures.insert(name.to_string(), texture);
        
        Ok(texture)
    }

    /// Load a text file
    pub async fn load_text(&self, name: &str) -> Result<String, String> {
        let path = self.get_asset_path(AssetType::Text, name);
        
        // Use load_string to load text content
        load_string(&path).await.map_err(|e| {
            format!("Failed to load text '{}': {}", path, e)
        })
    }

    /// Check if an asset file exists
    pub fn asset_exists(&self, asset_type: AssetType, name: &str) -> bool {
        let path = self.get_asset_path(asset_type, name);
        Path::new(&path).exists()
    }

    /// Preload a list of textures
    pub async fn preload_textures(&mut self, names: &[&str]) -> Result<(), String> {
        for name in names {
            self.load_texture(name).await?;
        }
        Ok(())
    }

    /// Get a loaded texture by name
    pub fn get_texture(&self, name: &str) -> Option<Texture2D> {
        self.textures.get(name).copied()
    }
}