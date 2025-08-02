# Blob class for position, color, and velocity
import random
import pygame
import math

# === Tunable Simulation Constants ===

SPEED_DAMPING = 0.98
# Factor to reduce velocity each frame (0.98 = 2% reduction per frame)
# Lower values = faster slowdown, higher values = slower slowdown

MAX_SPEED = 8.0
# Maximum speed a blob can have before additional damping kicks in
# Increase for faster maximum speeds, decrease for slower

NORMAL_SPEED = 2.0
# Target speed that blobs try to maintain
# This is the typical starting speed range

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
        if current_speed < 0.5:
            self.vx += random.uniform(-0.1, 0.1)
            self.vy += random.uniform(-0.1, 0.1)
        
        # Move
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen
        self.x = self.x % self.width
        self.y = self.y % self.height
        
        # Decay collision memory
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
        """Handle collision with another blob - escalating bounce force."""
        # Calculate collision normal
        dx = self.x - other.x
        dy = self.y - other.y
        
        # Handle toroidal wrapping
        dx = dx - self.width * round(dx / self.width)
        dy = dy - self.height * round(dy / self.height)
        
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
            
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
        
        # Add some color mixing on collision
        for i in range(3):
            avg = (self.color[i] + other.color[i]) // 2
            self.color[i] = min(255, max(0, avg + random.randint(-20, 20)))
            other.color[i] = min(255, max(0, avg + random.randint(-20, 20)))