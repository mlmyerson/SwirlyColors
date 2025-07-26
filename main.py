import pygame
import random
from Blob import Blob

# Constants
WIDTH, HEIGHT = 800, 600
NUM_BLOBS = 100
BLOB_RADIUS = 10

# Init pygame and window
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Create blobs
blobs = [Blob(BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(NUM_BLOBS)]

def are_attracted(blob1, blob2, threshold=80):
    # If already bonded, always attract
    if id(blob2) in blob1.bonded or id(blob1) in blob2.bonded:
        return True
    # Attract if colors are similar
    if color_distance(blob1.color, blob2.color) < threshold:
        blob1.bonded.add(id(blob2))
        blob2.bonded.add(id(blob1))
        return True
    return False

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

running = True
while running:
    screen.fill((20, 20, 30))  # dark background
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

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
                merged_blob = blob.interact(blob2, attract=attract)
                if merged_blob:
                    merged_indices.add(i)
                    merged_indices.add(j)
                    new_blobs.append(merged_blob)
                    break  # blob i is merged, skip further checks

    # Remove merged blobs and add new ones
    blobs = [b for idx, b in enumerate(blobs) if idx not in merged_indices]
    blobs.extend(new_blobs)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
