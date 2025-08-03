import pygame
from Blob import Blob
from Config import config

# Initialize pygame
pygame.init()

# Get screen dimensions
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Set up display based on config
if config.FULLSCREEN:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()

# Create blobs using config values
blobs = [Blob(config.BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(config.NUM_BLOBS)]

running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Clear screen with config background color
    screen.fill(config.BACKGROUND_COLOR)
    
    # Move blobs
    for blob in blobs:
        blob.search_for_target(blobs)  
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
    clock.tick(config.FPS)

pygame.quit()
