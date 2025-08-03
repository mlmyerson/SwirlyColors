# Blob class for position, color, and velocity
import random
import math
from Config import config

class Blob:
    """A simple colored ball with position, color, and velocity."""
    
    def __init__(self, radius, window_width, window_height, x=None, y=None, vx=None, vy=None, color=None):
        self.window_width = window_width
        self.window_height = window_height
        self.radius = radius
        
        # Position
        self.x = random.uniform(radius, window_width - radius)
        self.y = random.uniform(radius, window_height - radius)
        
        # Velocity
        self.vx = random.uniform(-config.NORMAL_SPEED, config.NORMAL_SPEED)
        self.vy = random.uniform(-config.NORMAL_SPEED, config.NORMAL_SPEED)
        
        # Color
        self.color = [
            random.randint(config.MINIMUM_COLOR, config.MAXIMUM_COLOR),
            random.randint(config.MINIMUM_COLOR, config.MAXIMUM_COLOR),
            random.randint(config.MINIMUM_COLOR, config.MAXIMUM_COLOR)
        ]
        
        # Collision tracking
        self.collision_memory = {}  
        self.collision_decay = config.COLLISION_MEMORY_DECAY

    def search_for_target(self, all_blobs):
        """Search for the closest blob with a preferential color match."""
        # Only search occasionally to avoid constant targeting
        if random.random() > config.TARGET_SEARCH_CHANCE:
            return
        
        # Shuffle the blob list to get random iteration order
        blob_candidates = list(all_blobs)
        random.shuffle(blob_candidates)
        
        for target_blob in blob_candidates:
            # Don't target yourself
            if target_blob is self:
                continue
                
            # Check if this blob is a preferential match
            if self.is_preferential_match(target_blob):
                # Calculate direction to target (with toroidal wrapping)
                dx = target_blob.x - self.x
                dy = target_blob.y - self.y
                
                # Handle toroidal wrapping
                dx = dx - self.window_width * round(dx / self.window_width)
                dy = dy - self.window_height * round(dy / self.window_height)
                
                distance = math.hypot(dx, dy)
                if distance > 0:
                    # Normalize direction and apply velocity kick
                    dx /= distance
                    dy /= distance
                    
                    self.vx += dx * config.VELOCITY_KICK_STRENGTH
                    self.vy += dy * config.VELOCITY_KICK_STRENGTH
                
                # Found a target, stop searching
                break

    def is_preferential_match(self, other):
        """Determine if another blob is a preferential match."""
        # Check for color similarity
        color_distance = sum((self.color[i] - other.color[i]) ** 2 for i in range(3)) ** 0.5
        
        # Prefer blobs with similar colors
        return color_distance < config.FLOCK_COLOR_THRESHOLD

    def move(self):
        """Move the blob and wrap around screen edges."""
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > config.MAX_SPEED:
            # Apply speed damping
            self.vx *= config.SPEED_DAMPING
            self.vy *= config.SPEED_DAMPING
        elif current_speed < config.NORMAL_SPEED:
            # Apply normal speed to maintain typical movement
            self.vx += config.NORMAL_SPEED
            self.vy += config.NORMAL_SPEED
        
        # Move
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen
        self.x = self.x % self.window_width
        self.y = self.y % self.window_height
        
        # Decay collision memory
        # Blobs that keep colliding bounce off each other more strongly
        # This makes it so that blobs will eventually bounce normally again after some time
        for blob_id in list(self.collision_memory.keys()):
            self.collision_memory[blob_id] *= self.collision_decay
            if self.collision_memory[blob_id] < 0.1:
                del self.collision_memory[blob_id]

    def collides_with(self, other):
        if not self.is_preferential_match(other):
            """Check if this blob collides with another blob."""
            dx = self.x - other.x
            dy = self.y - other.y
            
            # Handle toroidal wrapping
            dx = dx - self.window_width * round(dx / self.window_width)
            dy = dy - self.window_height * round(dy / self.window_height)
            
            distance = math.hypot(dx, dy)
            return distance < (self.radius + other.radius)

    def bounce_off(self, other):
        """Handle collision with another blob - escalating bounce force or flocking."""
        # Calculate collision normal
        dx = self.x - other.x
        dy = self.y - other.y
        
        # Handle toroidal wrapping
        dx = dx - self.window_width * round(dx / self.window_width)
        dy = dy - self.window_height * round(dy / self.window_height)
        
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
            
        # Check if colors are similar enough for flocking
        color_distance = sum((self.color[i] - other.color[i]) ** 2 for i in range(3)) ** 0.5
        
        if color_distance < config.FLOCK_COLOR_THRESHOLD:
            # FLOCKING BEHAVIOR: Move as one unit
            # Average the velocities so they move together
            avg_vx = (self.vx + other.vx) / 2
            avg_vy = (self.vy + other.vy) / 2
            
            self.vx = avg_vx
            self.vy = avg_vy
            other.vx = avg_vx
            other.vy = avg_vy
            
            # No color change for flocking blobs
            # They maintain their similar colors
            
            # Reset collision memory since they're now moving together
            other_id = id(other)
            self_id = id(self)
            if other_id in self.collision_memory:
                del self.collision_memory[other_id]
            if self_id in other.collision_memory:
                del other.collision_memory[self_id]
                
        else:
            # NORMAL BOUNCING BEHAVIOR: Different colors bounce off each other
            # Normalize
            dx /= distance
            dy /= distance
            
            # Track collision intensity
            other_id = id(other)
            if other_id not in self.collision_memory:
                self.collision_memory[other_id] = 1.0
            else:
                self.collision_memory[other_id] = min(10.0, self.collision_memory[other_id] + 1.0)
            
            # Do the same for the other blob
            self_id = id(self)
            if self_id not in other.collision_memory:
                other.collision_memory[self_id] = 1.0
            else:
                other.collision_memory[self_id] = min(10.0, other.collision_memory[self_id] + 1.0)
            
            # Calculate bounce intensity based on collision history
            bounce_multiplier = max(1.0, self.collision_memory[other_id])
            
            # Simple velocity swap along collision normal with escalating force
            v1_normal = self.vx * dx + self.vy * dy
            v2_normal = other.vx * dx + other.vy * dy
            
            force = (v2_normal - v1_normal) * bounce_multiplier
            self.vx += force * dx
            self.vy += force * dy
            
            force = (v1_normal - v2_normal) * bounce_multiplier
            other.vx += force * dx
            other.vy += force * dy
            
            # Add separation force to prevent overlap
            separation_force = bounce_multiplier * 0.5
            self.vx += dx * separation_force
            self.vy += dy * separation_force
            other.vx -= dx * separation_force
            other.vy -= dy * separation_force

            self.color_bounce(other)
            
    def color_bounce(self, other):
        # Add some color mixing on collision (only for bouncing blobs)
        for i in range(3):
            # Instead of averaging colors, make them bounce apart
            diff = self.color[i] - other.color[i]
            
            # Add random variation to the bounce
            bounce_strength = random.randint(10, 30)
            
            if diff > 0:
                # self has higher value, push it higher and other lower
                self.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, self.color[i] + bounce_strength))
                other.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, other.color[i] - bounce_strength))
            elif diff < 0:
                # other has higher value, push it higher and self lower
                self.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, self.color[i] - bounce_strength))
                other.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, other.color[i] + bounce_strength))
            else:
                # Colors are the same, push them in random directions
                if random.choice([True, False]):
                    self.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, self.color[i] + bounce_strength))
                    other.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, other.color[i] - bounce_strength))
                else:
                    self.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, self.color[i] - bounce_strength))
                    other.color[i] = max(config.MINIMUM_COLOR, min(config.MAXIMUM_COLOR, other.color[i] + bounce_strength))