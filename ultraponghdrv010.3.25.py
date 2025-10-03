import pygame, sys, random, math

# Optional NumPy (for procedural audio)
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False
    print("NumPy not found – running silent mode.")

# Initialize
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
BALL_RADIUS = 5
PADDLE_SPEED = 5
BALL_SPEED = 3
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GLOW_COLOR = (100, 255, 100)
GLOW_ALPHA = 50
AI_SPEED = 4  # Slightly slower than player for fairness

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Atari Pong - PS5 Edition")
clock = pygame.time.Clock()

# Enhanced Procedural Sound Generator with ADSR Envelope
def generate_sound(freq=440, duration=0.1, volume=0.05, wave_type='sine', attack=0.01, decay=0.05, sustain_level=0.5, release=0.01):
    if not HAVE_NUMPY:
        return pygame.mixer.Sound(buffer=b'\x00'*100)  # silent dummy sound
    sample_rate = pygame.mixer.get_init()[0]
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    # Generate base wave
    if wave_type == 'sine':
        wave = np.sin(2 * np.pi * freq * t)
    elif wave_type == 'square':
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == 'saw':
        wave = 2 * (t * freq - np.floor(0.5 + t * freq)) - 1  # Normalized to [-1,1]
    else:
        wave = np.sin(2 * np.pi * freq * t)
    
    # ADSR Envelope
    envelope = np.ones(num_samples)
    
    # Attack
    attack_samples = min(int(sample_rate * attack), num_samples)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Decay
    decay_start = attack_samples
    decay_samples = int(sample_rate * decay)
    decay_end = min(decay_start + decay_samples, num_samples)
    if decay_end > decay_start:
        envelope[decay_start:decay_end] = np.linspace(1, sustain_level, decay_end - decay_start)
    
    # Sustain (flat at sustain_level until release)
    sustain_end = max(decay_end, num_samples - int(sample_rate * release))
    if sustain_end > decay_end:
        envelope[decay_end:sustain_end] = sustain_level
    
    # Release
    release_start = max(0, num_samples - int(sample_rate * release))
    if release_start < num_samples:
        envelope[release_start:] = np.linspace(sustain_level, 0, num_samples - release_start)
    
    wave *= envelope * volume
    audio = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((audio, audio)))  # stereo

# Pre-generate base sounds (will be overridden for dynamic ones)
wall_bounce_sound = generate_sound(300, 0.05, wave_type='square', attack=0.001, decay=0.03, sustain_level=0.3, release=0.01)
score_sound = generate_sound(659.25, 0.2, wave_type='saw', attack=0.01, decay=0.1, sustain_level=0.4, release=0.05)

# Classes (unchanged)
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)

    def move(self, dy):
        self.rect.y += dy
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH//2 - BALL_RADIUS, SCREEN_HEIGHT//2 - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)
        self.speed = BALL_SPEED
        self.hit_count = 0
        self.reset()

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

    def bounce_wall(self):
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.dy = -self.dy
            if HAVE_NUMPY: wall_bounce_sound.play()

    def bounce_paddle(self, paddle):
        if self.rect.colliderect(paddle.rect):
            self.hit_count += 1

            hit_pos = self.rect.centery - paddle.rect.top
            segment = int(hit_pos // (PADDLE_HEIGHT / 8))

            if self.hit_count >= 12:
                max_angle_deg = 60
                self.speed += 2
            elif self.hit_count >= 4:
                max_angle_deg = 45
                self.speed += 1
            else:
                max_angle_deg = 30

            angles = [
                -max_angle_deg,
                -round(max_angle_deg * 2 / 3),
                -round(max_angle_deg / 3),
                0,
                0,
                round(max_angle_deg / 3),
                round(max_angle_deg * 2 / 3),
                max_angle_deg
            ]
            angle_deg = angles[segment % 8]
            angle = math.radians(angle_deg)

            if paddle.rect.left < SCREEN_WIDTH // 2:
                self.dx = self.speed * math.cos(angle)
                self.dy = self.speed * math.sin(angle)
            else:
                self.dx = -self.speed * math.cos(angle)
                self.dy = self.speed * math.sin(angle)
            
            # Dynamic beep based on segment (higher pitch for center hits)
            dynamic_freq = 400 + (segment * 30)  # Range ~400-640 Hz
            if HAVE_NUMPY:
                dynamic_bounce = generate_sound(dynamic_freq, 0.05, wave_type='square', attack=0.005, decay=0.02, sustain_level=0.2, release=0.01)
                dynamic_bounce.play()
            return True
        return False

    def check_score(self, left_score, right_score):
        scored = False
        if self.rect.left <= 0:
            right_score += 1
            self.reset()
            scored = True
        elif self.rect.right >= SCREEN_WIDTH:
            left_score += 1
            self.reset()
            scored = True
        if scored and HAVE_NUMPY:
            score_sound.play()
        return left_score, right_score

    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        direction = random.choice([-1, 1])
        self.dx = direction * self.speed
        self.dy = 0
        self.hit_count = 0
        self.speed = BALL_SPEED

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.lifetime = random.randint(20, 40)
        self.color = GLOW_COLOR

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 2)

# Procedural Starfield
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.1, 0.5)
        self.brightness = random.randint(100, 255)

    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = SCREEN_WIDTH
            self.y = random.randint(0, SCREEN_HEIGHT)

    def draw(self, surface):
        pygame.draw.circle(surface, (self.brightness, self.brightness, self.brightness), (int(self.x), int(self.y)), 1)

# Generate starfield layers
stars = [Star() for _ in range(200)]

# Gradient background function
def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    if rect is None: rect = surface.get_rect()
    x1, x2 = rect.left, rect.right
    y1, y2 = rect.top, rect.bottom
    if vertical:
        h = y2 - y1
    else:
        h = x2 - x1
    if forward:
        a, b = color, gradient
    else:
        b, a = color, gradient
    rate = (
        float(b[0] - a[0]) / h,
        float(b[1] - a[1]) / h,
        float(b[2] - a[2]) / h
    )
    fn_line = pygame.draw.line if vertical else pygame.draw.line
    for line in range(h):
        color = (
            min(max(a[0] + (rate[0] * line), 0), 255),
            min(max(a[1] + (rate[1] * line), 0), 255),
            min(max(a[2] + (rate[2] * line), 0), 255)
        )
        if vertical:
            fn_line(surface, color, (x1, y1 + line), (x2, y1 + line))
        else:
            fn_line(surface, color, (x1 + line, y1), (x1 + line, y2))

# Game objects
left_paddle = Paddle(20, SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2)
right_paddle = Paddle(SCREEN_WIDTH - 30, SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2)
ball = Ball()
left_score = 0
right_score = 0
font = pygame.font.Font(None, 74)
title_font = pygame.font.Font(None, 120)
small_font = pygame.font.Font(None, 50)
particles = []

# Background surface for gradient
bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
fill_gradient(bg_surface, (0, 0, 50), (0, 0, 0), vertical=True)

# Game state
game_state = "menu"
flash_timer = 0
flash_interval = 30  # Frames for flashing effect
winner = ""

# Main loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_SPACE:
                    game_state = "playing"
                    left_score = 0
                    right_score = 0
                    ball.reset()
                    left_paddle.rect.centery = SCREEN_HEIGHT // 2
                    right_paddle.rect.centery = SCREEN_HEIGHT // 2
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif game_state == "playing":
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
            elif game_state == "game_over":
                if event.key == pygame.K_y:
                    game_state = "playing"
                    left_score = 0
                    right_score = 0
                    ball.reset()
                    left_paddle.rect.centery = SCREEN_HEIGHT // 2
                    right_paddle.rect.centery = SCREEN_HEIGHT // 2
                elif event.key == pygame.K_n:
                    running = False

    # Get controls for playing state
    if game_state == "playing":
        # Left paddle: Mouse control
        mouse_y = pygame.mouse.get_pos()[1]
        left_paddle.rect.centery = mouse_y
        if left_paddle.rect.top < 0:
            left_paddle.rect.top = 0
        if left_paddle.rect.bottom > SCREEN_HEIGHT:
            left_paddle.rect.bottom = SCREEN_HEIGHT

        # Right paddle: AI control (track ball y)
        if right_paddle.rect.centery < ball.rect.centery:
            right_paddle.move(AI_SPEED)
        elif right_paddle.rect.centery > ball.rect.centery:
            right_paddle.move(-AI_SPEED)

        ball.move()
        ball.bounce_wall()
        bounced = ball.bounce_paddle(left_paddle) or ball.bounce_paddle(right_paddle)
        if bounced:
            for _ in range(20):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery))
        left_score, right_score = ball.check_score(left_score, right_score)

        # Check win condition
        if left_score >= 5 or right_score >= 5:
            game_state = "game_over"
            winner = "Player" if left_score >= 5 else "AI"

        for p in particles[:]:
            p.update()
            if p.lifetime <= 0:
                particles.remove(p)

    # Draw background and starfield (common to all states)
    screen.blit(bg_surface, (0, 0))
    for star in stars:
        star.update()
        star.draw(screen)

    if game_state == "menu":
        # Draw title
        title_text = title_font.render("PONG", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//4))

        # Flashing start text
        flash_timer += 1
        if flash_timer % flash_interval < flash_interval // 2:
            start_text = small_font.render("Press SPACE to Start", True, WHITE)
            screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))

        quit_text = small_font.render("Press ESC to Quit", True, WHITE)
        screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 60))

    elif game_state == "playing":
        # Dashed middle line with glow
        mid_x = SCREEN_WIDTH // 2
        dash_height = 10
        space = 10
        y = 0
        glow_surf = pygame.Surface((3, dash_height), pygame.SRCALPHA)
        glow_surf.fill((*GLOW_COLOR, GLOW_ALPHA))
        while y < SCREEN_HEIGHT:
            # Glow
            screen.blit(glow_surf, (mid_x - 1, y))
            # Line
            pygame.draw.line(screen, WHITE, (mid_x, y), (mid_x, y + dash_height), 1)
            y += dash_height + space

        # Draw paddles with glow
        for paddle in [left_paddle, right_paddle]:
            # Glow
            glow_rect = paddle.rect.inflate(10, 10)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GLOW_COLOR, GLOW_ALPHA), (0, 0, glow_rect.width, glow_rect.height))
            screen.blit(glow_surf, glow_rect.topleft)
            # Paddle
            pygame.draw.rect(screen, WHITE, paddle.rect)

        # Draw ball with glow
        # Outer glow
        pygame.draw.circle(screen, (*GLOW_COLOR, GLOW_ALPHA), ball.rect.center, BALL_RADIUS + 5)
        pygame.draw.circle(screen, (*GLOW_COLOR, GLOW_ALPHA // 2), ball.rect.center, BALL_RADIUS + 10)
        # Ball
        pygame.draw.circle(screen, WHITE, ball.rect.center, BALL_RADIUS)

        # Scores
        left_text = font.render(str(left_score), True, WHITE)
        right_text = font.render(str(right_score), True, WHITE)
        screen.blit(left_text, (SCREEN_WIDTH//4, 10))
        screen.blit(right_text, (3*SCREEN_WIDTH//4, 10))

        # Particles
        for p in particles:
            p.draw(screen)

    elif game_state == "game_over":
        # Draw game over prompt
        over_text = title_font.render("Game Over!", True, WHITE)
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//4))

        winner_text = small_font.render(f"{winner} Wins!", True, WHITE)
        screen.blit(winner_text, (SCREEN_WIDTH//2 - winner_text.get_width()//2, SCREEN_HEIGHT//2 - 30))

        restart_text = small_font.render("Restart? (Y/N)", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit(0)
