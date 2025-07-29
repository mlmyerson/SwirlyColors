import pygame
import random
import math
import numpy as np
from Blob import Blob, any_subblob_collision

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# === Tunable Simulation Constants ===

NUM_BLOBS = 100
# Number of initial blobs in the simulation.
# Increase for more activity, decrease for performance.

BLOB_RADIUS = 10
# Radius of each initial blob's sub-blob.
# Increase for larger blobs, decrease for more granular blobs.

COLOR_SHIFT_STRENGTH = 0.1
# How much color shifts on collision/merge.
# Increase for more dramatic color changes.

COLOR_SIMILARITY = 1
# Color similarity threshold for attraction/merging.
# Lower for stricter merging, higher for more frequent merges.

GRID_SIZE = 10
# Size of the grid cells for blob group collision checks.
# Lower for more accurate but slower checks.

MAX_COLLISIONS_PER_FRAME = 1000
# Maximum number of blob merges/collisions processed per frame.
# Lower to throttle merging, higher for more dynamic merging.

MERGE_COOLDOWN_FRAMES = 1
# Minimum number of frames a merged blob must wait before merging again.
# Increase to reduce rapid-fire merging (helps at high speeds), decrease for more organic growth.

STAGGER_DIV = 1
# Only check every nth blob per frame (for performance).
# Increase for less frequent checks, decrease for more frequent.

MAX_SUBBLOBS_PER_BLOB = 50
# Maximum number of sub-blobs allowed in a single blob before it is split.
# Lower for better performance and more fragmentation, higher for larger blobs.

speed_multiplier = 1.0
# Global speed multiplier for all blobs.
# Use up/down arrow keys to adjust at runtime.

blobs = [Blob(BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(NUM_BLOBS)]

background_color = [20, 20, 30]
background_shift = [random.choice([-1, 1]) for _ in range(3)]

def average_color(blob):
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
            elif event.key == pygame.K_UP:
                speed_multiplier *= 1.1
            elif event.key == pygame.K_DOWN:
                speed_multiplier /= 1.1
            elif pygame.K_a <= event.key <= pygame.K_z:
                if blobs:
                    blob = random.choice(blobs)
                    blob.vx = random.uniform(-10, 10)
                    blob.vy = random.uniform(-10, 10)
                    new_sub_blobs = []
                    for x, y, r, _ in blob.sub_blobs:
                        new_color = [
                            random.randint(50, 255),
                            random.randint(50, 255),
                            random.randint(50, 255)
                        ]
                        new_sub_blobs.append((x, y, r, new_color))
                    blob.sub_blobs = new_sub_blobs

    for blob in blobs:
        orig_vx, orig_vy = blob.vx, blob.vy
        blob.vx *= speed_multiplier
        blob.vy *= speed_multiplier
        blob.move()
        blob.vx, blob.vy = orig_vx, orig_vy
        blob.draw(screen)

    for blob in blobs:
        if hasattr(blob, 'merge_cooldown') and blob.merge_cooldown > 0:
            blob.merge_cooldown -= 1

    grid = {}
    for idx, blob in enumerate(blobs):
        for x, y, r, _ in blob.sub_blobs:
            gx, gy = get_grid_pos(x, y)
            grid.setdefault((gx, gy), set()).add(idx)

    used_indices = set()
    merged_indices = set()
    new_blobs = []
    collisions_this_frame = 0

    for i, blob in enumerate(blobs):
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
                            checked.add(j)
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
                        checked.add(j)
            if collisions_this_frame >= MAX_COLLISIONS_PER_FRAME:
                break

    blobs = [b for idx, b in enumerate(blobs) if idx not in merged_indices]
    blobs.extend(new_blobs)

    ejected_blobs = []
    for blob in blobs:
        ejected_blobs.extend(blob.eject_outlier_subblobs(color_threshold=100, color_shift_strength=COLOR_SHIFT_STRENGTH))
    blobs.extend(ejected_blobs)

    split_blobs = []
    for blob in blobs:
        split_blobs.extend(blob.split_if_disconnected())
    blobs = split_blobs

    final_blobs = []
    for blob in blobs:
        if len(blob.sub_blobs) > MAX_SUBBLOBS_PER_BLOB:
            for i in range(0, len(blob.sub_blobs), MAX_SUBBLOBS_PER_BLOB):
                chunk = blob.sub_blobs[i:i+MAX_SUBBLOBS_PER_BLOB]
                final_blobs.append(Blob(
                    radius=0,
                    width=blob.width,
                    height=blob.height,
                    sub_blobs=chunk,
                    vx=blob.vx + random.uniform(-1, 1),
                    vy=blob.vy + random.uniform(-1, 1),
                    bonded=set(blob.bonded)
                ))
        else:
            final_blobs.append(blob)
    blobs = final_blobs

    blobs = [b for b in blobs if len(b.sub_blobs) > 0]

    for i, blob1 in enumerate(blobs):
        for j in range(i + 1, len(blobs)):
            blob2 = blobs[j]
            x1, y1, r1, _ = blob1.sub_blobs[0]
            x2, y2, r2, _ = blob2.sub_blobs[0]
            dx = x2 - x1
            dy = y2 - y1
            dx = dx - WIDTH * round(dx / WIDTH)
            dy = dy - HEIGHT * round(dy / HEIGHT)
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

    for blob1 in blobs:
        if len(blob1.sub_blobs) == 1:
            x1, y1, r1, _ = blob1.sub_blobs[0]
            for blob2 in blobs:
                if blob1 is blob2 or len(blob2.sub_blobs) < 2:
                    continue
                for x2, y2, r2, _ in blob2.sub_blobs:
                    dx = x1 - x2
                    dy = y1 - y2
                    dx = dx - WIDTH * round(dx / WIDTH)
                    dy = dy - HEIGHT * round(dy / HEIGHT)
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    min_dist = r1 + r2
                    if dist < min_dist and dist > 0:
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
