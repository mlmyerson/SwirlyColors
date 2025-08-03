import os
import datetime
from Blob import Blob
from Config import config

def run_simulation():
    """Run the simulation with optional display."""
    
    # Get dimensions from config
    WIDTH, HEIGHT = config.WIDTH, config.HEIGHT
    
    # Initialize display only if enabled
    display = None
    if config.ENABLE_DISPLAY:
        try:
            print("Attempting to import Display...")
            from Display import Display
            print("Display imported successfully")
            print("Creating Display instance...")
            display = Display(WIDTH, HEIGHT)
            print(f"Display enabled - running with pygame visualization ({WIDTH}x{HEIGHT})")
        except ImportError as e:
            print(f"ImportError: {e}")
            print("pygame not available - running headless")
            display = None
        except Exception as e:
            print(f"Unexpected error initializing display: {e}")
            print("Running headless")
            display = None
    else:
        print(f"Display disabled - running headless simulation ({WIDTH}x{HEIGHT})")
    
    # Create blobs
    blobs = [Blob(config.BLOB_RADIUS, WIDTH, HEIGHT) for _ in range(config.NUM_BLOBS)]
    
    # Set up logging
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    mode = "visual" if display else "headless"
    log_filename = os.path.join(logs_dir, f"{mode}-{timestamp}.log")
    
    # Initialize frame counter
    frame_count = 0
    
    # Determine when to stop
    max_frames = config.MAX_FRAMES if config.MAX_FRAMES > 0 else float('inf')
    
    # Open log file
    with open(log_filename, 'w') as log_file:
        # Write header
        log_file.write(f"SwirlyColors {mode.title()} Simulation Log\n")
        log_file.write(f"Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Configuration: {config.NUM_BLOBS} blobs, radius {config.BLOB_RADIUS}\n")
        log_file.write(f"World size: {WIDTH}x{HEIGHT}\n")
        log_file.write(f"Mode: {mode}\n")
        if config.MAX_FRAMES > 0:
            log_file.write(f"Max frames: {config.MAX_FRAMES}\n")
        log_file.write("="*80 + "\n\n")
        
        running = True
        
        try:
            while running and frame_count < max_frames:
                # Handle events (only if display exists)
                if display:
                    running = display.handle_events()
                    display.clear()
                
                # Core simulation logic
                for blob in blobs:
                    blob.search_for_target(blobs)  
                    blob.move()
                
                # Check collisions
                for i, blob1 in enumerate(blobs):
                    for j in range(i + 1, len(blobs)):
                        blob2 = blobs[j]
                        if blob1.collides_with(blob2):
                            blob1.bounce_off(blob2)
                
                # Draw blobs (only if display exists)
                if display:
                    for blob in blobs:
                        display.draw_blob(blob.x, blob.y, blob.radius, blob.color)
                    display.update()
                
                # Log data
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
                    log_file.flush()
                
                frame_count += 1
                
                # Print progress for headless mode
                if not display and frame_count % 100 == 0:
                    print(f"Frame: {frame_count}")
        
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        
        # Write closing information
        log_file.write("="*80 + "\n")
        log_file.write(f"Simulation ended at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Total frames: {frame_count}\n")
    
    # Clean up display
    if display:
        display.close()
    
    print(f"Simulation complete. Log saved to {log_filename}")
    print(f"Total frames: {frame_count}")

if __name__ == "__main__":
    run_simulation()
