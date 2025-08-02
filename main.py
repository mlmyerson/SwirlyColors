import pygame
import random
from Blob import Blob

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Simple constants
NUM_BLOBS = 50
BLOB_RADIUS = 15

# Create blobs
blobs = [Blob(BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(NUM_BLOBS)]

running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Clear screen
    screen.fill((20, 20, 30))
    
    # Move blobs
    for blob in blobs:
        blob.search_for_target(blobs)  # Pass the full blob list
        blob.move()
    
    # Check collisions
    for i, blob1 in enumerate(blobs):
        for j in range(i + 1, len(blobs)):
            blob2 = blobs[j]
            if blob1.collides_with(blob2):
                blob1.bounce_off(blob2)
    
    # Draw blobs
    for blob in blobs:
        blob.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
