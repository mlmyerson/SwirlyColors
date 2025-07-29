# Blob class for position, color, and velocity
import random
import pygame
import math
import numpy as np

# Constants
MERGE_COOLDOWN_FRAMES = 1  # Adjust this value to change the merge cooldown duration

class Blob:
    def __init__(self, radius, width, height, sub_blobs=None, vx=None, vy=None, bonded=None):
        self.width = width
        self.height = height
        if sub_blobs is None:
            # Each sub-blob is (x, y, radius, color)
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
        # Track which blobs this blob is bonded to (by id)
        self.bonded = set() if bonded is None else set(bonded)
        self.merge_cooldown = 0  # <-- Add this line

    def move(self):
        if len(self.sub_blobs) == 0:
            return
        arr = np.array([[x, y, r] for x, y, r, _ in self.sub_blobs])
        dx = np.full(len(arr), self.vx)
        dy = np.full(len(arr), self.vy)
        # Repulsion
        for i in range(len(arr)):
            diff = arr[i, :2] - arr[:, :2]
            diff[:, 0], diff[:, 1] = toroidal_distance(diff[:, 0], diff[:, 1], self.width, self.height)
            dist = np.linalg.norm(diff, axis=1)
            overlap = (arr[i, 2] + arr[:, 2]) - dist
            mask = (overlap > 0) & (dist > 0)
            if np.any(mask):
                repel = diff[mask] / dist[mask][:, None]
                repel_sum = np.sum(repel * overlap[mask][:, None], axis=0)
                dx[i] += repel_sum[0] * 0.01  # Reduced from 0.05 to 0.01
                dy[i] += repel_sum[1] * 0.01
        # Add random jiggle
        arr[:, 0] += dx + np.random.uniform(-0.1, 0.1, size=len(arr))
        arr[:, 1] += dy + np.random.uniform(-0.1, 0.1, size=len(arr))
        # Toroidal wrapping
        arr[:, 0] = np.mod(arr[:, 0], self.width)
        arr[:, 1] = np.mod(arr[:, 1], self.height)
        # Update sub_blobs
        self.sub_blobs = [(arr[i, 0], arr[i, 1], arr[i, 2], self.sub_blobs[i][3]) for i in range(len(arr))]

    def draw(self, surface):
        for x, y, r, color in self.sub_blobs:
            pygame.draw.circle(surface, color, (int(x), int(y)), int(r))

    def is_colliding(self, other):
        for x1, y1, r1, _ in self.sub_blobs:
            for x2, y2, r2, _ in other.sub_blobs:
                if math.hypot(x1 - x2, y1 - y2) < r1 + r2:
                    return True
        return False

    def interact(self, other, attract=True, color_shift_strength=0.5):
        collided = False
        new_self_sub_blobs = list(self.sub_blobs)
        new_other_sub_blobs = list(other.sub_blobs)
        for i, (x1, y1, r1, color1) in enumerate(self.sub_blobs):
            for j, (x2, y2, r2, color2) in enumerate(other.sub_blobs):
                if math.hypot(x1 - x2, y1 - y2) < r1 + r2:
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
                # Use a larger min_dist based on sub-blob radii
                max_r = max(r for _, _, r, _ in new_sub_blobs)
                min_dist = max_r * 2
                new_sub_blobs = self._spread_subblobs(new_sub_blobs, min_dist=min_dist)
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
                merged_blob.merge_cooldown = MERGE_COOLDOWN_FRAMES
                return merged_blob
            else:
                # Bounce: reverse velocities for both blobs
                self.vx *= -1
                self.vy *= -1
                other.vx *= -1
                other.vy *= -1
                # Update sub-blobs with bounced colors
                self.sub_blobs = new_self_sub_blobs
                other.sub_blobs = new_other_sub_blobs
                return None
        return None

    def eject_outlier_subblobs(self, color_threshold=100, color_shift_strength=0.5):
        """Return a list of new Blobs for ejected sub-blobs, and update self.sub_blobs."""
        if len(self.sub_blobs) <= 1:
            return []
        # Compute average color of all sub-blobs
        n = len(self.sub_blobs)
        avg = [0, 0, 0]
        for _, _, _, color in self.sub_blobs:
            for i in range(3):
                avg[i] += color[i]
        avg = [int(x / n) for x in avg]
        # Find outliers
        keep = []
        ejected = []
        for sub in self.sub_blobs:
            _, _, _, color = sub
            if color_distance(color, avg) > color_threshold:
                ejected.append(sub)
            else:
                keep.append(sub)
        self.sub_blobs = keep
        # Create new blobs for ejected sub-blobs
        new_blobs = []
        for x, y, r, color in ejected:
            new_blobs.append(
                Blob(
                    radius=r,
                    width=self.width,
                    height=self.height,
                    sub_blobs=[(x, y, r, color)],
                    vx=self.vx + random.uniform(-2, 2),  # Give it a little kick
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
            return math.hypot(x1 - x2, y1 - y2) < r1 + r2

        for idx, sub in enumerate(self.sub_blobs):
            if idx in visited:
                continue
            # BFS to find all connected sub-blobs
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
        # Otherwise, make a new Blob for each component
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
        """Return (cx, cy, radius) for a circle that bounds all sub-blobs (NumPy version)."""
        if not self.sub_blobs:
            return (0, 0, 0)
        arr = np.array([[x, y, r] for x, y, r, _ in self.sub_blobs])
        cx = np.mean(arr[:, 0])
        cy = np.mean(arr[:, 1])
        dists = np.sqrt((arr[:, 0] - cx) ** 2 + (arr[:, 1] - cy) ** 2) + arr[:, 2]
        max_r = np.max(dists)
        return (cx, cy, max_r)

    @staticmethod
    def _spread_subblobs(sub_blobs, min_dist=5):
        """Spread sub-blobs in a small circle to avoid overlap after merging."""
        n = len(sub_blobs)
        if n == 1:
            return sub_blobs
        angle_step = 2 * math.pi / n
        cx = sum(x for x, y, r, c in sub_blobs) / n
        cy = sum(y for x, y, r, c in sub_blobs) / n
        spread = []
        for i, (x, y, r, color) in enumerate(sub_blobs):
            angle = i * angle_step
            nx = cx + math.cos(angle) * min_dist
            ny = cy + math.sin(angle) * min_dist
            spread.append((nx, ny, r, color))
        return spread

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def any_subblob_collision(blob1, blob2):
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
    dx = dx - width * np.round(dx / width)
    dy = dy - height * np.round(dy / height)
    return dx, dy