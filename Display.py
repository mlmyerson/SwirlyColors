try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available. Display functionality disabled.")

from Config import config

class Display:
    """Handles all pygame-specific display functionality."""
    
    def __init__(self, width, height):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for display functionality")
        
        pygame.init()
        self.width = width
        self.height = height
        
        # Set up display based on config
        if config.FULLSCREEN:
            self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption("SwirlyColors Simulation")
        self.clock = pygame.time.Clock()
    
    def clear(self):
        """Clear the screen with background color."""
        self.screen.fill(config.BACKGROUND_COLOR)
    
    def draw_blob(self, x, y, radius, color):
        """Draw a single blob."""
        pygame.draw.circle(self.screen, color, (int(x), int(y)), int(radius))
    
    def update(self):
        """Update the display."""
        pygame.display.flip()
        self.clock.tick(config.FPS)
    
    def handle_events(self):
        """Handle pygame events. Returns False if should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def close(self):
        """Clean up pygame."""
        if PYGAME_AVAILABLE:
            pygame.quit()