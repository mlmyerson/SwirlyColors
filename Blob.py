# Blob class for position, color, and velocity
import random
import pygame
import math

# === Tunable Simulation Constants ===

MERGE_COOLDOWN_FRAMES = 0
# Minimum number of frames a merged blob must wait before merging again.
# Increase to reduce rapid-fire merging (helps at high speeds), decrease for more organic growth.

MAX_SUBBLOBS_PER_BLOB = 50
# Maximum number of sub-blobs allowed in a single blob before it is split.
# Lower for better performance and more fragmentation, higher for larger blobs.

SPREAD_EXTRA = 1.05  # Lower than default 1.15
# Multiplier for minimum separation between sub-blobs after a merge.
# Increase to reduce immediate overlaps after merging (but may make blobs less cohesive).
# Decrease for more compact, irregular blobs.

SPREAD_JITTER = 3.0
# Amount of random jitter added to sub-blob positions after merging.
# Increase for more irregular, organic shapes; decrease for smoother merges.

BASE_REPULSION = 0.002  # Lower than default 0.008
# Base strength of repulsion between sub-blobs.
# Increase to keep blobs from overlapping, decrease for more compact blobs.

GRID_CELL_SIZE = 24
# Size of the spatial grid cells for repulsion and collision checks.
# Lower for more accurate but slower physics, higher for faster but less accurate.

MAX_STEP_FRACTION = 0.5
# Maximum fraction of a sub-blob's radius it can move in a single physics substep.
# Lower to prevent "teleporting" and tunneling, higher for faster movement.

PHYSICS_SUBSTEPS = 1
# Number of physics substeps per frame.
# Increase for more stable physics at high speeds, decrease for better performance.

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

    def move(self):
        """Move the blob and wrap around screen edges."""
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen
        self.x = self.x % self.width
        self.y = self.y % self.height

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
        """Handle collision with another blob - simple bounce."""
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
        
        # Simple velocity swap along collision normal
        v1_normal = self.vx * dx + self.vy * dy
        v2_normal = other.vx * dx + other.vy * dy
        
        self.vx += (v2_normal - v1_normal) * dx
        self.vy += (v2_normal - v1_normal) * dy
        other.vx += (v1_normal - v2_normal) * dx
        other.vy += (v1_normal - v2_normal) * dy
        
        # Add some color mixing on collision
        for i in range(3):
            avg = (self.color[i] + other.color[i]) // 2
            self.color[i] = min(255, max(0, avg + random.randint(-20, 20)))
            other.color[i] = min(255, max(0, avg + random.randint(-20, 20)))