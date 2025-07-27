# Blob class for position, color, and velocity
import random
import pygame
import math

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

    def move(self):
        # Move all sub-blobs by the same velocity
        self.sub_blobs = [
            (x + self.vx, y + self.vy, r, color) for (x, y, r, color) in self.sub_blobs
        ]
        # Bounce if any sub-blob hits a wall
        for x, y, r, color in self.sub_blobs:
            if x < r or x > self.width - r:
                self.vx *= -1
                break
            if y < r or y > self.height - r:
                self.vy *= -1
                break

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
                avg_vx = (self.vx + other.vx) / 2
                avg_vy = (self.vy + other.vy) / 2
                new_bonded = self.bonded.union(other.bonded)
                return Blob(
                    radius=0,
                    width=self.width,
                    height=self.height,
                    sub_blobs=new_sub_blobs,
                    vx=avg_vx,
                    vy=avg_vy,
                    bonded=new_bonded
                )
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
        """Return (cx, cy, radius) for a circle that bounds all sub-blobs."""
        if not self.sub_blobs:
            return (0, 0, 0)
        xs = [x for x, y, r, c in self.sub_blobs]
        ys = [y for x, y, r, c in self.sub_blobs]
        rs = [r for x, y, r, c in self.sub_blobs]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        max_r = max(math.hypot(x - cx, y - cy) + r for x, y, r, c in self.sub_blobs)
        return (cx, cy, max_r)

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5