import pygame
import sys
import numpy as np
import random

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.font.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Paddle settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10

# Ball settings
BALL_RADIUS = 10
BALL_SPEED_X = 5
BALL_SPEED_Y = 5

# Brick settings
BRICK_WIDTH = 75
BRICK_HEIGHT = 30
BRICK_ROWS = 5
BRICK_COLUMNS = 10
BRICK_GAP = 5

# Fonts
font = pygame.font.SysFont(None, 50)
small_font = pygame.font.SysFont(None, 30)

# Function to generate beep sound using NumPy
def generate_beep(freq=880, duration=0.1):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(freq * t * 2 * np.pi)
    audio = np.hstack((tone, tone))  # Stereo
    audio = (audio * 32767).astype(np.int16)  # Scale to int16
    return pygame.mixer.Sound(buffer=audio.tobytes())

# Function to generate boop sound using NumPy
def generate_boop(freq=440, duration=0.1):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(freq * t * 2 * np.pi)
    audio = np.hstack((tone, tone))  # Stereo
    audio = (audio * 32767).astype(np.int16)  # Scale to int16
    return pygame.mixer.Sound(buffer=audio.tobytes())

# Sounds
beep_sound = generate_beep()  # For brick collision
boop_sound = generate_boop()  # For paddle/wall collision

# Game setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout Game")

clock = pygame.time.Clock()

# Paddle class
class Paddle:
    def __init__(self):
        self.rect = pygame.Rect((SCREEN_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 10, PADDLE_WIDTH, PADDLE_HEIGHT)

    def update(self):
        mouse_x = pygame.mouse.get_pos()[0]
        self.rect.centerx = max(PADDLE_WIDTH // 2, min(SCREEN_WIDTH - PADDLE_WIDTH // 2, mouse_x))

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

# Ball class
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - BALL_RADIUS, SCREEN_HEIGHT // 2 - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.dx = random.choice([-BALL_SPEED_X, BALL_SPEED_X])
        self.dy = -BALL_SPEED_Y

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

    def draw(self):
        pygame.draw.circle(screen, RED, self.rect.center, BALL_RADIUS)

    def bounce_x(self):
        self.dx = -self.dx
        boop_sound.play()  # Boop on wall bounce

    def bounce_y(self):
        self.dy = -self.dy

# Brick class
class Brick:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

# Function to create bricks
def create_bricks():
    bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLUMNS):
            x = col * (BRICK_WIDTH + BRICK_GAP) + BRICK_GAP
            y = row * (BRICK_HEIGHT + BRICK_GAP) + BRICK_GAP + 50
            bricks.append(Brick(x, y))
    return bricks

# Initial game objects (placeholders)
bricks = []
paddle = Paddle()
ball = Ball()

# PS1-inspired features: achievements, session tracking
total_bricks_broken = 0
lost_balls = 0
has_won = False
achievements = {
    "Brick Buster": {"desc": "Break 10 bricks", "condition": lambda: total_bricks_broken >= 10, "unlocked": False},
    "Butterfingers": {"desc": "Lose 5 balls", "condition": lambda: lost_balls >= 5, "unlocked": False},
    "Champion": {"desc": "Win the game", "condition": lambda: has_won, "unlocked": False},
    # Add more PS1-style unlocks (e.g., survival, score-based)
    "Survivor": {"desc": "Lose 10 balls without winning", "condition": lambda: lost_balls >= 10 and not has_won, "unlocked": False},
    "Brick Master": {"desc": "Break 50 bricks", "condition": lambda: total_bricks_broken >= 50, "unlocked": False},
}

# Menu setup (PS1 main menu style: simple navigation)
game_state = "menu"
options = ["Start Game", "Trophies", "Exit"]
selected_option = 0

# Game loop
running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        bricks = create_bricks()
                        paddle = Paddle()
                        ball = Ball()
                        game_state = "game"
                    elif selected_option == 1:
                        game_state = "trophies"
                    elif selected_option == 2:
                        running = False
            elif game_state == "trophies":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    game_state = "menu"
            elif game_state == "game":
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"

    if game_state == "menu":
        # Draw PS1-style main menu
        title = font.render("Breakout PS1", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        for i, opt in enumerate(options):
            color = RED if i == selected_option else WHITE
            text = small_font.render(opt, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 50))

    elif game_state == "trophies":
        # Update and draw trophies
        title = font.render("Trophies", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        y = 150
        for name, info in achievements.items():
            if info["condition"]():
                info["unlocked"] = True
            status = "Unlocked" if info["unlocked"] else "Locked"
            text = small_font.render(f"{name}: {info['desc']} - {status}", True, WHITE)
            screen.blit(text, (100, y))
            y += 40
        back_text = small_font.render("Press ESC or ENTER to return", True, WHITE)
        screen.blit(back_text, (100, y + 50))

    elif game_state == "game":
        # Paddle movement via mouse
        paddle.update()

        # Ball movement
        ball.move()

        # Ball collisions with walls
        if ball.rect.left <= 0 or ball.rect.right >= SCREEN_WIDTH:
            ball.bounce_x()
        if ball.rect.top <= 0:
            ball.bounce_y()
            boop_sound.play()  # Boop on top wall

        # Respawn ball if it hits bottom
        if ball.rect.bottom >= SCREEN_HEIGHT:
            lost_balls += 1
            ball.rect.centerx = SCREEN_WIDTH // 2
            ball.rect.centery = SCREEN_HEIGHT // 2
            ball.dx = random.choice([-BALL_SPEED_X, BALL_SPEED_X])
            ball.dy = -BALL_SPEED_Y

        # Ball collision with paddle
        if ball.rect.colliderect(paddle.rect):
            ball.bounce_y()
            boop_sound.play()  # Boop on paddle

        # Ball collision with bricks
        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.bounce_y()
                bricks.remove(brick)
                total_bricks_broken += 1
                beep_sound.play()  # Beep on brick hit
                break

        # Check win condition
        if not bricks:
            print("You Win!")
            has_won = True
            game_state = "menu"

        # Draw everything
        paddle.draw()
        ball.draw()
        for brick in bricks:
            brick.draw()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
