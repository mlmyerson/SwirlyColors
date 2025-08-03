import pygame
import os
import datetime
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

# Set up logging
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create log filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
log_filename = os.path.join(logs_dir, f"{timestamp}.log")

# Initialize frame counter
frame_count = 0

# Open log file
with open(log_filename, 'w') as log_file:
    # Write header
    log_file.write("SwirlyColors Simulation Log\n")
    log_file.write(f"Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Configuration: {config.NUM_BLOBS} blobs, radius {config.BLOB_RADIUS}\n")
    log_file.write("="*80 + "\n\n")
    
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
        
        # Log data every LOG_INTERVAL_FRAMES frames
        if frame_count % config.LOG_INTERVAL_FRAMES == 0:
            log_file.write(f"Frame: {frame_count}\n")
            for i, blob in enumerate(blobs):
                log_file.write(
                    f"Blob {i:2d}: "
                    f"pos=({blob.x:7.2f},{blob.y:7.2f}) "
                    f"vel=({blob.vx:6.3f},{blob.vy:6.3f}) "
                    f"color=({blob.color[0]:3d},{blob.color[1]:3d},{blob.color[2]:3d})\n"
                )
            log_file.write("\n")
            log_file.flush()  # Ensure data is written to disk
        
        frame_count += 1
        
        pygame.display.flip()
        clock.tick(config.FPS)
    
    # Write closing information
    log_file.write("="*80 + "\n")
    log_file.write(f"Simulation ended at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Total frames: {frame_count}\n")

pygame.quit()
