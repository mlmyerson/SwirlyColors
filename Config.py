import json
import os

class Config:
    """Configuration class that loads constants from a JSON file."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.json file."""
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Using default values.")
            config_data = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}. Using default values.")
            config_data = self._get_default_config()
        
        # Assign configuration values to explicit class variables
        self._assign_config_values(config_data)
    
    def _get_default_config(self):
        """Return default configuration values."""
        return {
            "simulation": {
                "num_blobs": 20,
                "blob_radius": 15,
                "fps": 60,
                "fullscreen": True
            },
            "display": {
                "background_color": [20, 20, 30]
            },
            "physics": {
                "speed_damping": 0.98,
                "max_speed": 2.0,
                "normal_speed": 0.5,
                "velocity_kick_strength": 0.1
            },
            "appearance": {
                "minimum_color": 100,
                "maximum_color": 200
            },
            "behavior": {
                "collision_memory_decay": 0.9,
                "target_search_chance": 1.01,
                "flock_color_threshold": 50
            }
        }
    
    def _assign_config_values(self, config_data):
        """Assign configuration values to explicit class variables."""
        # Simulation constants
        self.NUM_BLOBS = config_data.get("simulation", {}).get("num_blobs", 20)
        self.BLOB_RADIUS = config_data.get("simulation", {}).get("blob_radius", 15)
        self.FPS = config_data.get("simulation", {}).get("fps", 60)
        self.FULLSCREEN = config_data.get("simulation", {}).get("fullscreen", True)
        
        # Display constants
        bg_color = config_data.get("display", {}).get("background_color", [20, 20, 30])
        self.BACKGROUND_COLOR = tuple(bg_color)
        
        # Physics constants
        self.SPEED_DAMPING = config_data.get("physics", {}).get("speed_damping", 0.98)
        self.MAX_SPEED = config_data.get("physics", {}).get("max_speed", 2.0)
        self.NORMAL_SPEED = config_data.get("physics", {}).get("normal_speed", 0.5)
        self.VELOCITY_KICK_STRENGTH = config_data.get("physics", {}).get("velocity_kick_strength", 0.1)
        
        # Appearance constants
        self.MINIMUM_COLOR = config_data.get("appearance", {}).get("minimum_color", 100)
        self.MAXIMUM_COLOR = config_data.get("appearance", {}).get("maximum_color", 200)
        
        # Behavior constants
        self.COLLISION_MEMORY_DECAY = config_data.get("behavior", {}).get("collision_memory_decay", 0.9)
        self.TARGET_SEARCH_CHANCE = config_data.get("behavior", {}).get("target_search_chance", 1.01)
        self.FLOCK_COLOR_THRESHOLD = config_data.get("behavior", {}).get("flock_color_threshold", 50)
        
        # Derived constants (computed from other values)
        self.COLOR_ATTRACTION_THRESHOLD = self.FLOCK_COLOR_THRESHOLD  # Keep attraction and flocking in sync
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
    
    def __str__(self):
        """Return a string representation of all configuration values."""
        return f"""Config Values:
Simulation:
  NUM_BLOBS = {self.NUM_BLOBS}
  BLOB_RADIUS = {self.BLOB_RADIUS}
  FPS = {self.FPS}
  FULLSCREEN = {self.FULLSCREEN}

Display:
  BACKGROUND_COLOR = {self.BACKGROUND_COLOR}

Physics:
  SPEED_DAMPING = {self.SPEED_DAMPING}
  MAX_SPEED = {self.MAX_SPEED}
  NORMAL_SPEED = {self.NORMAL_SPEED}
  VELOCITY_KICK_STRENGTH = {self.VELOCITY_KICK_STRENGTH}

Appearance:
  MINIMUM_COLOR = {self.MINIMUM_COLOR}
  MAXIMUM_COLOR = {self.MAXIMUM_COLOR}

Behavior:
  COLLISION_MEMORY_DECAY = {self.COLLISION_MEMORY_DECAY}
  TARGET_SEARCH_CHANCE = {self.TARGET_SEARCH_CHANCE}
  FLOCK_COLOR_THRESHOLD = {self.FLOCK_COLOR_THRESHOLD}
  COLOR_ATTRACTION_THRESHOLD = {self.COLOR_ATTRACTION_THRESHOLD}
"""

# Static instance for easy access
config = Config()