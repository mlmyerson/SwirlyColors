import pygame
import random
from Blob import Blob

# Constants
WIDTH, HEIGHT = 800, 600
NUM_BLOBS = 100
BLOB_RADIUS = 10
COLOR_SHIFT_STRENGTH = 0.5  # 0 = no color change, 1 = max color change

# Init pygame and window
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Create blobs
blobs = [Blob(BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(NUM_BLOBS)]

# Background color variables
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

def are_attracted(blob1, blob2, threshold=80):
    # If already bonded, always attract
    if id(blob2) in blob1.bonded or id(blob1) in blob2.bonded:
        return True
    # Attract if average colors are similar
    if color_distance(average_color(blob1), average_color(blob2)) < threshold:
        blob1.bonded.add(id(blob2))
        blob2.bonded.add(id(blob1))
        return True
    return False

running = True
while running:
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
            if pygame.K_a <= event.key <= pygame.K_z:
                if blobs:
                    blob = random.choice(blobs)
                    # Change velocity
                    blob.vx = random.uniform(2, 5)
                    blob.vy = random.uniform(2, 5)
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

    # Handle interactions and merging
    merged_indices = set()
    new_blobs = []
    for i, blob in enumerate(blobs):
        if i in merged_indices:
            continue
        for j in range(i + 1, len(blobs)):
            if j in merged_indices:
                continue
            blob2 = blobs[j]
            if blob.is_colliding(blob2):
                attract = are_attracted(blob, blob2)
                merged_blob = blob.interact(blob2, attract=attract, color_shift_strength=COLOR_SHIFT_STRENGTH)
                if merged_blob:
                    merged_indices.add(i)
                    merged_indices.add(j)
                    new_blobs.append(merged_blob)
                    break  # blob i is merged, skip further checks

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

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
