import pygame
import random
import math
import numpy as np
from Blob import Blob, any_subblob_collision  # <-- Import the function!

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Constants
NUM_BLOBS = 200
BLOB_RADIUS = 10
COLOR_SHIFT_STRENGTH = 0.3
COLOR_SIMILARITY = 1
GRID_SIZE = 10
MAX_COLLISIONS_PER_FRAME = 20
MERGE_COOLDOWN_FRAMES = 5
STAGGER_DIV = 2  # Only check every Nth blob per frame (set to 1 for no staggering)

# Create blobs
blobs = [Blob(BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(NUM_BLOBS)]

background_color = [20, 20, 30]
background_shift = [random.choice([-1, 1]) for _ in range(3)]

def average_color(blob):
    """Return the average color (as a list of 3 ints) of all sub-blobs in a blob."""
    n = len(blob.sub_blobs)
    if n == 0:
        return [0, 0, 0]
    sums = [0, 0, 0]
    for _, _, _, color in blob.sub_blobs:
        for i in range(3):
            sums[i] += color[i]
    return [int(s / n) for s in sums]

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def are_attracted(blob1, blob2, similarity=COLOR_SIMILARITY):
    # Max possible color distance in RGB is sqrt(3*255^2) ≈ 441.67
    max_dist = (3 * 255 ** 2) ** 0.5
    threshold = similarity * max_dist
    if getattr(blob2, 'merge_cooldown', 0) > 0 or getattr(blob1, 'merge_cooldown', 0) > 0:
        return False
    if id(blob2) in blob1.bonded or id(blob1) in blob2.bonded:
        return True
    if color_distance(average_color(blob1), average_color(blob2)) < threshold:
        blob1.bonded.add(id(blob2))
        blob2.bonded.add(id(blob1))
        return True
    return False

def get_grid_pos(x, y):
    return int(x // GRID_SIZE), int(y // GRID_SIZE)

frame_count = 0
running = True
while running:
    frame_count += 1
    # Slowly shift background color
    for i in range(3):
        background_color[i] += background_shift[i] * random.uniform(0.1, 0.5)
        if background_color[i] < 10 or background_color[i] > 80:
            background_shift[i] *= -1
        background_color[i] = max(10, min(80, background_color[i]))
    screen.fill(tuple(int(c) for c in background_color))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif pygame.K_a <= event.key <= pygame.K_z:
                if blobs:
                    blob = random.choice(blobs)
                    # Change velocity
                    blob.vx = random.uniform(2, 20)
                    blob.vy = random.uniform(2, 20)
                    # Change color of all sub-blobs
                    new_sub_blobs = []
                    for x, y, r, _ in blob.sub_blobs:
                        new_color = [
                            random.randint(50, 255),
                            random.randint(50, 255),
                            random.randint(50, 255)
                        ]
                        new_sub_blobs.append((x, y, r, new_color))
                    blob.sub_blobs = new_sub_blobs

    # Move and draw all blobs
    for blob in blobs:
        blob.move()
        blob.draw(screen)

    # Decrement merge cooldowns
    for blob in blobs:
        if hasattr(blob, 'merge_cooldown') and blob.merge_cooldown > 0:
            blob.merge_cooldown -= 1

    # --- Build grid for this frame ---
    grid = {}
    for idx, blob in enumerate(blobs):
        for x, y, r, _ in blob.sub_blobs:
            gx, gy = get_grid_pos(x, y)
            grid.setdefault((gx, gy), set()).add(idx)
    # ---------------------------------

    # Only handle collisions/merging and splitting every 10 frames
    if True:
        used_indices = set()
        merged_indices = set()
        new_blobs = []
        collisions_this_frame = 0

        for i, blob in enumerate(blobs):
            # Stagger: only check every Nth blob per frame
            if i % STAGGER_DIV != frame_count % STAGGER_DIV:
                continue
            if i in used_indices or i in merged_indices:
                continue
            if getattr(blob, 'merge_cooldown', 0) > 0:
                continue
            checked = set()
            cx1, cy1, br1 = blob.bounding_circle()
            for x, y, r, _ in blob.sub_blobs:
                gx, gy = get_grid_pos(x, y)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        for j in grid.get((gx + dx, gy + dy), []):
                            if collisions_this_frame >= MAX_COLLISIONS_PER_FRAME:
                                break
                            if j <= i or j in used_indices or j in merged_indices or j in checked:
                                continue
                            if j >= len(blobs):
                                continue
                            blob2 = blobs[j]
                            if getattr(blob2, 'merge_cooldown', 0) > 0:
                                continue
                            cx2, cy2, br2 = blob2.bounding_circle()
                            if math.hypot(cx1 - cx2, cy1 - cy2) > br1 + br2:
                                checked.add(j)
                                continue
                            if any_subblob_collision(blob, blob2):
                                attract = are_attracted(blob, blob2)
                                if not attract:
                                    checked.add(j)
                                    continue
                                merged_blob = blob.interact(blob2, attract=attract, color_shift_strength=COLOR_SHIFT_STRENGTH)
                                if merged_blob:
                                    merged_blob.merge_cooldown = MERGE_COOLDOWN_FRAMES
                                    merged_indices.add(i)
                                    merged_indices.add(j)
                                    used_indices.add(i)
                                    used_indices.add(j)
                                    new_blobs.append(merged_blob)
                                    collisions_this_frame += 1
                                    checked.add(j)
                                    break
                            checked.add(j)  # <-- This is safe, as j is always defined here
            if collisions_this_frame >= MAX_COLLISIONS_PER_FRAME:
                break

        # Remove merged blobs and add new ones
        blobs = [b for idx, b in enumerate(blobs) if idx not in merged_indices]
        blobs.extend(new_blobs)

        # After handling merges, eject outlier sub-blobs
        ejected_blobs = []
        for blob in blobs:
            ejected_blobs.extend(blob.eject_outlier_subblobs(color_threshold=100, color_shift_strength=COLOR_SHIFT_STRENGTH))
        blobs.extend(ejected_blobs)

        # Now split blobs if they're disconnected
        split_blobs = []
        for blob in blobs:
            split_blobs.extend(blob.split_if_disconnected())
        blobs = split_blobs

    # Remove blobs with no sub-blobs
    blobs = [b for b in blobs if len(b.sub_blobs) > 0]

    # After all merging/splitting logic, separate overlapping blobs
    for i, blob1 in enumerate(blobs):
        for j in range(i + 1, len(blobs)):
            blob2 = blobs[j]
            x1, y1, r1, _ = blob1.sub_blobs[0]
            x2, y2, r2, _ = blob2.sub_blobs[0]
            dx = x2 - x1
            dy = y2 - y1
            dist = (dx ** 2 + dy ** 2) ** 0.5
            min_dist = r1 + r2
            if dist < min_dist and dist > 0:
                overlap = min_dist - dist
                move_x = (dx / dist) * (overlap / 2)
                move_y = (dy / dist) * (overlap / 2)
                blob1.sub_blobs = [
                    (x - move_x, y - move_y, r, color)
                    for (x, y, r, color) in blob1.sub_blobs
                ]
                blob2.sub_blobs = [
                    (x + move_x, y + move_y, r, color)
                    for (x, y, r, color) in blob2.sub_blobs
                ]

    # Only separate single-sub-blob blobs from larger blobs to prevent them getting stuck
    for blob1 in blobs:
        if len(blob1.sub_blobs) == 1:
            x1, y1, r1, _ = blob1.sub_blobs[0]
            for blob2 in blobs:
                if blob1 is blob2 or len(blob2.sub_blobs) < 2:
                    continue
                # Check if single blob is inside any sub-blob of the larger blob
                for x2, y2, r2, _ in blob2.sub_blobs:
                    dx = x1 - x2
                    dy = y1 - y2
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    min_dist = r1 + r2
                    if dist < min_dist and dist > 0:
                        # Move the single-sub-blob blob out of the larger blob
                        overlap = min_dist - dist
                        move_x = (dx / dist) * overlap if dist != 0 else overlap
                        move_y = (dy / dist) * overlap if dist != 0 else overlap
                        blob1.sub_blobs = [(
                            x1 + move_x,
                            y1 + move_y,
                            r1,
                            blob1.sub_blobs[0][3]
                        )]
                        break

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
