# Blob class for position, color, and velocity
import random
import pygame
import math

class Blob:
    def __init__(self, radius, width, height, sub_blobs=None, vx=None, vy=None, color=None, bonded=None):
        self.width = width
        self.height = height
        if sub_blobs is None:
            # Each sub-blob is (x, y, radius)
            self.sub_blobs = [
                (
                    random.uniform(radius, width - radius),
                    random.uniform(radius, height - radius),
                    radius
                )
            ]
        else:
            self.sub_blobs = sub_blobs
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-2, 2)
        self.color = color if color is not None else [
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        ]
        # Track which blobs this blob is bonded to (by id)
        self.bonded = set() if bonded is None else set(bonded)

    def move(self):
        # Move all sub-blobs by the same velocity
        self.sub_blobs = [
            (x + self.vx, y + self.vy, r) for (x, y, r) in self.sub_blobs
        ]
        # Bounce if any sub-blob hits a wall
        for x, y, r in self.sub_blobs:
            if x < r or x > self.width - r:
                self.vx *= -1
                break
            if y < r or y > self.height - r:
                self.vy *= -1
                break

    def draw(self, surface):
        for x, y, r in self.sub_blobs:
            pygame.draw.circle(surface, self.color, (int(x), int(y)), int(r))

    def is_colliding(self, other):
        for x1, y1, r1 in self.sub_blobs:
            for x2, y2, r2 in other.sub_blobs:
                if math.hypot(x1 - x2, y1 - y2) < r1 + r2:
                    return True
        return False

    def interact(self, other, attract=True):
        if self.is_colliding(other):
            if attract:
                # Record the bond
                self.bonded.add(id(other))
                other.bonded.add(id(self))
                # Merge: combine sub-blobs, average velocity and color
                new_sub_blobs = self.sub_blobs + other.sub_blobs
                avg_vx = (self.vx + other.vx) / 2
                avg_vy = (self.vy + other.vy) / 2
                avg_color = [
                    (c1 + c2) // 2 for c1, c2 in zip(self.color, other.color)
                ]
                new_bonded = self.bonded.union(other.bonded)
                return Blob(
                    radius=0,  # Not used for merged blobs
                    width=self.width,
                    height=self.height,
                    sub_blobs=new_sub_blobs,
                    vx=avg_vx,
                    vy=avg_vy,
                    color=avg_color,
                    bonded=new_bonded
                )
            else:
                # Bounce: reverse velocities for both blobs
                self.vx *= -1
                self.vy *= -1
                other.vx *= -1
                other.vy *= -1
                return None
        return None