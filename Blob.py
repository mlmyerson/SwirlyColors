# Blob class for position, color, and velocity
import random
import pygame
import math

# === Tunable Simulation Constants ===

SPEED_DAMPING = 0.98
# Factor to reduce velocity each frame (0.98 = 2% reduction per frame)
# Lower values = faster slowdown, higher values = slower slowdown

MAX_SPEED = 12.0
# Maximum speed a blob can have before additional damping kicks in
# Increase for faster maximum speeds, decrease for slower

NORMAL_SPEED = 6.0
# Target speed that blobs try to maintain
# This is the typical starting speed range

MINIMUM_SPEED = 3.0

TARGET_SEARCH_CHANCE = 0.01
# Probability per frame that a blob will search for a target (1% = infrequent searching)
# Lower = less frequent targeting, higher = more frequent targeting

COLOR_ATTRACTION_THRESHOLD = 100
# Maximum color distance for attraction (lower = more selective)
# Decrease for stricter color matching, increase for looser matching

VELOCITY_KICK_STRENGTH = 0.5
# How strong the velocity kick towards target is
# Increase for stronger attraction, decrease for gentler movement

FLOCK_COLOR_THRESHOLD = 50
# Color distance threshold for flocking behavior (should be lower than COLOR_ATTRACTION_THRESHOLD)
# Blobs closer than this in color will move as one unit instead of bouncing

class Blob:
    """A simple colored ball with position, color, and velocity."""
    def __init__(self, radius, width, height, x=None, y=None, vx=None, vy=None, color=None):
        self.width = width
        self.height = height
        self.radius = radius
        
        # Position
        self.x = x if x is not None else random.uniform(radius, width - radius)
        self.y = y if y is not None else random.uniform(radius, height - radius)
        
        # Velocity
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-2, 2)
        
        # Color
        self.color = color if color is not None else [
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        ]
        
        # Collision tracking
        self.collision_memory = {}  # Track recent collisions with other blobs
        self.collision_decay = 0.9  # How fast collision memory fades

    def search_for_target(self, all_blobs):
        """Search for the closest blob with a preferential color match."""
        # Only search occasionally to avoid constant targeting
        if random.random() > TARGET_SEARCH_CHANCE:
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
                dx = dx - self.width * round(dx / self.width)
                dy = dy - self.height * round(dy / self.height)
                
                distance = math.hypot(dx, dy)
                if distance > 0:
                    # Normalize direction and apply velocity kick
                    dx /= distance
                    dy /= distance
                    
                    self.vx += dx * VELOCITY_KICK_STRENGTH
                    self.vy += dy * VELOCITY_KICK_STRENGTH
                
                # Found a target, stop searching
                break

    def is_preferential_match(self, other):
        """Determine if another blob is a preferential match."""
        # Simple color similarity check
        color_distance = sum((self.color[i] - other.color[i]) ** 2 for i in range(3)) ** 0.5
        
        # Prefer blobs with similar colors
        return color_distance < COLOR_ATTRACTION_THRESHOLD

    def move(self):
        """Move the blob and wrap around screen edges."""
    
        # Apply speed damping
        current_speed = math.hypot(self.vx, self.vy)
        
        if current_speed > MAX_SPEED:
            # Strong damping for very high speeds
            damping_factor = SPEED_DAMPING * 0.9  # Extra damping
        elif current_speed > NORMAL_SPEED:
            # Normal damping for above-normal speeds
            damping_factor = SPEED_DAMPING
        else:
            # Light damping for low speeds to prevent stopping completely
            damping_factor = 0.995
        
        self.vx *= damping_factor
        self.vy *= damping_factor
        
        # Prevent speeds from getting too low (add tiny random motion)
        if current_speed < MINIMUM_SPEED:
            self.vx += random.uniform(-0.1, 0.1)
            self.vy += random.uniform(-0.1, 0.1)
        
        # Move
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen
        self.x = self.x % self.width
        self.y = self.y % self.height
        
        # Decay collision memory
            # Blobs that keep colliding bounce off each other more strongly
            # This makes it so that blobs will eventually bounce normally again after some time
        for blob_id in list(self.collision_memory.keys()):
            self.collision_memory[blob_id] *= self.collision_decay
            if self.collision_memory[blob_id] < 0.1:
                del self.collision_memory[blob_id]

    def draw(self, surface):
        """Draw the blob to the given surface."""
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))

    def collides_with(self, other):
        """Check if this blob collides with another blob."""
        dx = self.x - other.x
        dy = self.y - other.y
        
        # Handle toroidal wrapping
        dx = dx - self.width * round(dx / self.width)
        dy = dy - self.height * round(dy / self.height)
        
        distance = math.hypot(dx, dy)
        return distance < (self.radius + other.radius)

    def bounce_off(self, other):
        """Handle collision with another blob - escalating bounce force or flocking."""
        # Calculate collision normal
        dx = self.x - other.x
        dy = self.y - other.y
        
        # Handle toroidal wrapping
        dx = dx - self.width * round(dx / self.width)
        dy = dy - self.height * round(dy / self.height)
        
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
            
        # Check if colors are similar enough for flocking
        color_distance = sum((self.color[i] - other.color[i]) ** 2 for i in range(3)) ** 0.5
        
        if color_distance < FLOCK_COLOR_THRESHOLD:
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
            
            # Add some color mixing on collision (only for bouncing blobs)
            for i in range(3):
                # Instead of averaging colors, make them bounce apart
                diff = self.color[i] - other.color[i]
                
                # Add random variation to the bounce
                bounce_strength = random.randint(10, 30)
                
                if diff > 0:
                    # self has higher value, push it higher and other lower
                    self.color[i] = (self.color[i] + bounce_strength) % 256
                    other.color[i] = (other.color[i] - bounce_strength) % 256
                elif diff < 0:
                    # other has higher value, push it higher and self lower
                    self.color[i] = (self.color[i] - bounce_strength) % 256
                    other.color[i] = (other.color[i] + bounce_strength) % 256
                else:
                    # Colors are the same, push them in random directions
                    if random.choice([True, False]):
                        self.color[i] = (self.color[i] + bounce_strength) % 256
                        other.color[i] = (other.color[i] - bounce_strength) % 256
                    else:
                        self.color[i] = (self.color[i] - bounce_strength) % 256
                        other.color[i] = (other.color[i] + bounce_strength) % 256