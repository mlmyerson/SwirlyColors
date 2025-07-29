# Blob class for position, color, and velocity
import random
import pygame
import math
import numpy as np

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
    """A blob composed of one or more sub-blobs, with position, color, and velocity."""
    def __init__(self, radius, width, height, sub_blobs=None, vx=None, vy=None, bonded=None):
        self.width = width
        self.height = height
        if sub_blobs is None:
            self.sub_blobs = [(
                random.uniform(radius, width - radius),
                random.uniform(radius, height - radius),
                radius,
                [
                    random.randint(50, 255),
                    random.randint(50, 255),
                    random.randint(50, 255)
                ]
            )]
        else:
            self.sub_blobs = sub_blobs
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-2, 2)
        self.bonded = set() if bonded is None else set(bonded)
        self.merge_cooldown = 0

    def move(self):
        """Move all sub-blobs, apply repulsion (using spatial grid), and wrap toroidally, with substeps and clamped step size."""
        if len(self.sub_blobs) == 0:
            return
        arr = np.array([[x, y, r] for x, y, r, _ in self.sub_blobs])
        for _ in range(PHYSICS_SUBSTEPS):
            dx = np.full(len(arr), self.vx / PHYSICS_SUBSTEPS)
            dy = np.full(len(arr), self.vy / PHYSICS_SUBSTEPS)

            # --- Spatial grid for repulsion ---
            grid = {}
            for idx, (x, y, r) in enumerate(arr):
                gx, gy = int(x // GRID_CELL_SIZE), int(y // GRID_CELL_SIZE)
                grid.setdefault((gx, gy), []).append(idx)

            # Adaptive repulsion: scale with speed
            speed = np.hypot(self.vx, self.vy)
            repulsion_strength = BASE_REPULSION / max(1, len(arr) ** 0.5)
            repulsion_strength *= (1 + speed / 5)

            for i, (x, y, r) in enumerate(arr):
                gx, gy = int(x // GRID_CELL_SIZE), int(y // GRID_CELL_SIZE)
                neighbors = []
                for dxg in [-1, 0, 1]:
                    for dyg in [-1, 0, 1]:
                        cell = ((gx + dxg) % (self.width // GRID_CELL_SIZE),
                                (gy + dyg) % (self.height // GRID_CELL_SIZE))
                        neighbors.extend(grid.get(cell, []))
                for j in neighbors:
                    if i == j:
                        continue
                    x2, y2, r2 = arr[j]
                    ddx, ddy = toroidal_distance(x - x2, y - y2, self.width, self.height)
                    dist = math.hypot(ddx, ddy)
                    buffer_zone = 1.2
                    repel_zone = (r + r2) * buffer_zone
                    if dist < repel_zone and dist > 0:
                        overlap = repel_zone - dist
                        repel = overlap / repel_zone
                        dx[i] += ddx * repel * repulsion_strength
                        dy[i] += ddy * repel * repulsion_strength

            # Clamp step size for each sub-blob
            for i, (x, y, r) in enumerate(arr):
                step = math.hypot(dx[i], dy[i])
                max_step = r * MAX_STEP_FRACTION
                if step > max_step:
                    scale = max_step / step
                    dx[i] *= scale
                    dy[i] *= scale

            # Add random jiggle
            arr[:, 0] += dx + np.random.uniform(-0.1, 0.1, size=len(arr))
            arr[:, 1] += dy + np.random.uniform(-0.1, 0.1, size=len(arr))
            arr[:, 0] = np.mod(arr[:, 0], self.width)
            arr[:, 1] = np.mod(arr[:, 1], self.height)
        self.sub_blobs = [(arr[i, 0], arr[i, 1], arr[i, 2], self.sub_blobs[i][3]) for i in range(len(arr))]

    def draw(self, surface):
        """Draw all sub-blobs to the given surface."""
        for x, y, r, color in self.sub_blobs:
            pygame.draw.circle(surface, color, (int(x), int(y)), int(r))

    def interact(self, other, attract=True, color_shift_strength=0.5):
        """Handle collision and merging/bouncing with another blob."""
        collided = False
        new_self_sub_blobs = list(self.sub_blobs)
        new_other_sub_blobs = list(other.sub_blobs)
        for i, (x1, y1, r1, color1) in enumerate(self.sub_blobs):
            for j, (x2, y2, r2, color2) in enumerate(other.sub_blobs):
                dx = x1 - x2
                dy = y1 - y2
                dx, dy = toroidal_distance(dx, dy, self.width, self.height)
                if math.hypot(dx, dy) < r1 + r2:
                    collided = True
                    def shift_color(color, vx, vy):
                        base_shift = (abs(vx) + abs(vy)) * 2
                        shift = max(1, int(base_shift * color_shift_strength))
                        return [
                            (c + random.choice([-shift, shift])) % 256
                            for c in color
                        ]
                    if attract:
                        new_self_sub_blobs[i] = (x1, y1, r1, shift_color(color1, self.vx, self.vy))
                        new_other_sub_blobs[j] = (x2, y2, r2, shift_color(color2, other.vx, other.vy))
                    else:
                        def bounce_color(c1, c2, vx, vy):
                            base_shift = (abs(vx) + abs(vy)) * 2
                            shift = max(1, int(base_shift * color_shift_strength))
                            return [
                                (c1[k] + shift) % 256 if c1[k] > c2[k] else (c1[k] - shift) % 256
                                for k in range(3)
                            ]
                        new_self_sub_blobs[i] = (x1, y1, r1, bounce_color(color1, color2, self.vx, self.vy))
                        new_other_sub_blobs[j] = (x2, y2, r2, bounce_color(color2, color1, other.vx, other.vy))
                    break
            if collided:
                break

        if collided:
            if attract:
                self.bonded.add(id(other))
                other.bonded.add(id(self))
                new_sub_blobs = new_self_sub_blobs + new_other_sub_blobs
                radii = sorted([r for _, _, r, _ in new_sub_blobs], reverse=True)
                if len(radii) >= 2:
                    base_dist = (radii[0] + radii[1])
                else:
                    base_dist = radii[0]
                speed = math.hypot(self.vx, self.vy) + math.hypot(other.vx, other.vy)
                min_dist = base_dist * (SPREAD_EXTRA + 0.1 * min(1, speed / 10))
                new_sub_blobs = nonuniform_spread(new_sub_blobs, min_dist, jitter=SPREAD_JITTER)
                avg_vx = (self.vx + other.vx) / 2
                avg_vy = (self.vy + other.vy) / 2
                new_bonded = self.bonded.union(other.bonded)
                merged_blob = Blob(
                    radius=0,
                    width=self.width,
                    height=self.height,
                    sub_blobs=new_sub_blobs,
                    vx=avg_vx,
                    vy=avg_vy,
                    bonded=new_bonded
                )
                merged_blob.merge_cooldown = int(MERGE_COOLDOWN_FRAMES * (1 + speed / 10))
                return merged_blob
            else:
                self.vx *= -1
                self.vy *= -1
                other.vx *= -1
                other.vy *= -1
                self.sub_blobs = new_self_sub_blobs
                other.sub_blobs = new_other_sub_blobs
                return None
        return None

    def eject_outlier_subblobs(self, color_threshold=100, color_shift_strength=0.5):
        """Return a list of new Blobs for ejected sub-blobs, and update self.sub_blobs."""
        if len(self.sub_blobs) <= 1:
            return []
        n = len(self.sub_blobs)
        avg = [0, 0, 0]
        for _, _, _, color in self.sub_blobs:
            for i in range(3):
                avg[i] += color[i]
        avg = [int(x / n) for x in avg]
        keep = []
        ejected = []
        for sub in self.sub_blobs:
            _, _, _, color = sub
            if color_distance(color, avg) > color_threshold:
                ejected.append(sub)
            else:
                keep.append(sub)
        self.sub_blobs = keep
        new_blobs = []
        for x, y, r, color in ejected:
            new_blobs.append(
                Blob(
                    radius=r,
                    width=self.width,
                    height=self.height,
                    sub_blobs=[(x, y, r, color)],
                    vx=self.vx + random.uniform(-2, 2),
                    vy=self.vy + random.uniform(-2, 2)
                )
            )
        return new_blobs

    def _find_connected_components(self):
        """Return a list of lists of sub-blobs, each list is a connected component."""
        if not self.sub_blobs:
            return []
        visited = set()
        components = []

        def are_connected(sub1, sub2):
            x1, y1, r1, _ = sub1
            x2, y2, r2, _ = sub2
            dx = x1 - x2
            dy = y1 - y2
            dx, dy = toroidal_distance(dx, dy, self.width, self.height)
            return math.hypot(dx, dy) < r1 + r2

        for idx, sub in enumerate(self.sub_blobs):
            if idx in visited:
                continue
            queue = [idx]
            group = []
            while queue:
                i = queue.pop()
                if i in visited:
                    continue
                visited.add(i)
                group.append(self.sub_blobs[i])
                for j, other_sub in enumerate(self.sub_blobs):
                    if j not in visited and are_connected(self.sub_blobs[i], other_sub):
                        queue.append(j)
            components.append(group)
        return components

    def split_if_disconnected(self):
        """If the blob is disconnected, return a list of new Blobs (including self if still valid)."""
        components = self._find_connected_components()
        if len(components) <= 1:
            return [self]
        new_blobs = []
        for sub_blobs in components:
            new_blobs.append(
                Blob(
                    radius=0,
                    width=self.width,
                    height=self.height,
                    sub_blobs=sub_blobs,
                    vx=self.vx + random.uniform(-1, 1),
                    vy=self.vy + random.uniform(-1, 1),
                    bonded=set(self.bonded)
                )
            )
        return new_blobs

    def bounding_circle(self):
        """Return (cx, cy, radius) for a circle that bounds all sub-blobs (toroidal-aware)."""
        if not self.sub_blobs:
            return (0, 0, 0)
        arr = np.array([[x, y, r] for x, y, r, _ in self.sub_blobs])
        cx = np.mean(arr[:, 0])
        cy = np.mean(arr[:, 1])
        dx = arr[:, 0] - cx
        dy = arr[:, 1] - cy
        dx, dy = toroidal_distance(dx, dy, self.width, self.height)
        dists = np.sqrt(dx ** 2 + dy ** 2) + arr[:, 2]
        max_r = np.max(dists)
        cx = np.mod(cx, self.width)
        cy = np.mod(cy, self.height)
        return (cx, cy, max_r)

def color_distance(c1, c2):
    """Euclidean distance between two RGB colors."""
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def any_subblob_collision(blob1, blob2):
    """Return True if any sub-blobs in blob1 and blob2 overlap (NumPy version, toroidal)."""
    if not blob1.sub_blobs or not blob2.sub_blobs:
        return False
    arr1 = np.array([[x, y, r] for x, y, r, _ in blob1.sub_blobs])
    arr2 = np.array([[x, y, r] for x, y, r, _ in blob2.sub_blobs])
    dx = arr1[:, None, 0] - arr2[None, :, 0]
    dy = arr1[:, None, 1] - arr2[None, :, 1]
    dx, dy = toroidal_distance(dx, dy, blob1.width, blob1.height)
    dist = np.sqrt(dx ** 2 + dy ** 2)
    min_dist = arr1[:, None, 2] + arr2[None, :, 2]
    return np.any(dist < min_dist)

def toroidal_distance(dx, dy, width, height):
    """Return the minimum toroidal (wrapped) distance for dx, dy arrays or scalars."""
    dx = dx - width * np.round(dx / width)
    dy = dy - height * np.round(dy / height)
    return dx, dy

def nonuniform_spread(sub_blobs, min_dist, jitter=2.0):
    """Spread sub-blobs with random offsets, not just around centroid."""
    n = len(sub_blobs)
    if n == 1:
        return sub_blobs
    spread = []
    for x, y, r, color in sub_blobs:
        angle = random.uniform(0, 2 * math.pi)
        dist = min_dist * (0.9 + 0.2 * random.random())
        nx = x + math.cos(angle) * dist + random.uniform(-jitter, jitter)
        ny = y + math.sin(angle) * dist + random.uniform(-jitter, jitter)
        spread.append((nx, ny, r, color))
    return spread