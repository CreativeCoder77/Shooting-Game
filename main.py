import pygame
import random
import os
import json

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Configuration
WIDTH, HEIGHT = 1024, 768
FPS = 60
PLAYER_SPEED = 8
BULLET_SPEED = 10
ENEMY_BASE_SPEED = 3
MAX_ENEMY_SPEED = 8
ENEMY_SPAWN_RATE = 45
SHIELD_MAX = 100
PARTICLE_LIFETIME = 15

# Colors
COLORS = {
    "bg": (5, 5, 25),
    "player": (50, 200, 255),
    "enemy": (255, 50, 100),
    "bullet": (255, 255, 200),
    "ui": (255, 255, 255),
    "shield": (100, 200, 255),
    "particle": (255, 150, 50)
}

# Initialize window
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Defender")
clock = pygame.time.Clock()

# Load assets
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(current_dir, 'assets')

try:
    player_img = pygame.image.load(os.path.join(assets_dir, 'player_ship.png')).convert_alpha()
    bullet_img = pygame.image.load(os.path.join(assets_dir, 'bullet.png')).convert_alpha()
    enemy_img = pygame.image.load(os.path.join(assets_dir, 'enemy_ship.png')).convert_alpha()
except FileNotFoundError:
    # Fallback shapes
    player_img = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(player_img, COLORS["player"], [(20,0), (40,40), (20,30), (0,40)])
    bullet_img = pygame.Surface((4, 12), pygame.SRCALPHA)
    pygame.draw.rect(bullet_img, COLORS["bullet"], (0, 0, 4, 12))
    enemy_img = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(enemy_img, COLORS["enemy"], [(20,40), (40,0), (20,10), (0,0)])

# Load sounds
shoot_sound = pygame.mixer.Sound(os.path.join(assets_dir, 'shoot.wav')) if os.path.exists(os.path.join(assets_dir, 'shoot.wav')) else None
explosion_sound = pygame.mixer.Sound(os.path.join(assets_dir, 'explosion.wav')) if os.path.exists(os.path.join(assets_dir, 'explosion.wav')) else None

# High score system
HIGH_SCORE_FILE = "highscore.json"

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return json.load(f).get('high_score', 0)
    except:
        return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, 'w') as f:
        json.dump({"high_score": score}, f)

# Particle system
particles = []

def add_particles(pos):
    for _ in range(20):
        particles.append({
            "pos": list(pos),
            "vel": [random.uniform(-3, 3), random.uniform(-3, 3)],
            "lifetime": PARTICLE_LIFETIME
        })

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2

current_state = STATE_MENU
high_score = load_high_score()
score = 0
shield = SHIELD_MAX

# Game objects
player = pygame.Rect(WIDTH//2 - 20, HEIGHT - 100, 40, 40)
bullets = []
enemies = []

# UI Elements
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)

def game_menu():
    global current_state, high_score
    
    while True:
        window.fill(COLORS["bg"])
        draw_text("GALAXY DEFENDER", font_large, COLORS["ui"], window, WIDTH//2, HEIGHT//3)
        
        mx, my = pygame.mouse.get_pos()
        button_play = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
        button_quit = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50)
        
        # Draw buttons
        pygame.draw.rect(window, COLORS["ui"], button_play, 2)
        pygame.draw.rect(window, COLORS["ui"], button_quit, 2)
        draw_text("PLAY", font_medium, COLORS["ui"], window, WIDTH//2, HEIGHT//2 + 25)
        draw_text("QUIT", font_medium, COLORS["ui"], window, WIDTH//2, HEIGHT//2 + 105)
        draw_text(f"HIGH SCORE: {high_score}", font_small, COLORS["ui"], window, WIDTH//2, HEIGHT - 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_play.collidepoint(event.pos):
                    current_state = STATE_PLAYING
                    return
                elif button_quit.collidepoint(event.pos):
                    pygame.quit()
                    return

        pygame.display.update()
        clock.tick(FPS)

def game_loop():
    global current_state, score, shield, high_score, particles
    
    player.x = WIDTH//2 - 20
    player.y = HEIGHT - 100
    bullets.clear()
    enemies.clear()
    particles.clear()
    score = 0
    shield = SHIELD_MAX
    enemy_speed = ENEMY_BASE_SPEED
    
    while current_state == STATE_PLAYING:
        window.fill(COLORS["bg"])
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullets.append(pygame.Rect(player.x + 18, player.y - 20, 4, 12))
                    if shoot_sound: shoot_sound.play()

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x > 0:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and player.x < WIDTH - player.width:
            player.x += PLAYER_SPEED

        # Bullet movement
        bullets[:] = [b for b in bullets if b.y > -20]
        for b in bullets:
            b.y -= BULLET_SPEED

        # Enemy spawning
        if random.randint(1, ENEMY_SPAWN_RATE) == 1:
            enemies.append(pygame.Rect(random.randint(0, WIDTH-40), -40, 40, 40))

        # Enemy movement and collision
        enemies[:] = [e for e in enemies if e.y < HEIGHT]
        for e in enemies:
            e.y += enemy_speed
            if e.colliderect(player):
                shield = max(0, shield - 40)
                if shield <= 0:
                    current_state = STATE_GAME_OVER
                    if explosion_sound: explosion_sound.play()
            
            for b in bullets[:]:
                if e.colliderect(b):
                    add_particles((e.x + 20, e.y + 20))
                    enemies.remove(e)
                    bullets.remove(b)
                    score += 1
                    enemy_speed = min(ENEMY_BASE_SPEED + score//20, MAX_ENEMY_SPEED)
                    if explosion_sound: explosion_sound.play()
                    break

        # Update particles
        particles[:] = [p for p in particles if p["lifetime"] > 0]
        for p in particles:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["lifetime"] -= 1

        # Draw everything
        window.blit(player_img, player)
        
        for b in bullets:
            window.blit(bullet_img, b)
        
        for e in enemies:
            window.blit(enemy_img, e)
        
        for p in particles:
            alpha = int(255 * p["lifetime"]/PARTICLE_LIFETIME)
            pygame.draw.circle(window, COLORS["particle"] + (alpha,), (int(p["pos"][0]), int(p["pos"][1])), 3)

        # UI Elements
        pygame.draw.rect(window, COLORS["shield"], (10, 10, 200 * (shield/SHIELD_MAX), 20))
        pygame.draw.rect(window, COLORS["ui"], (10, 10, 200, 20), 2)
        draw_text(f"SCORE: {score}", font_small, COLORS["ui"], window, WIDTH - 100, 20)
        draw_text(f"HIGH SCORE: {high_score}", font_small, COLORS["ui"], window, WIDTH//2, 20)

        pygame.display.update()
        clock.tick(FPS)

def game_over():
    global current_state, high_score
    
    if score > high_score:
        high_score = score
        save_high_score(high_score)
    
    while current_state == STATE_GAME_OVER:
        window.fill(COLORS["bg"])
        draw_text("GAME OVER", font_large, COLORS["ui"], window, WIDTH//2, HEIGHT//3)
        draw_text(f"FINAL SCORE: {score}", font_medium, COLORS["ui"], window, WIDTH//2, HEIGHT//2)
        draw_text("CLICK TO RETURN TO MENU", font_small, COLORS["ui"], window, WIDTH//2, HEIGHT - 100)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_state = STATE_MENU
                return

        pygame.display.update()
        clock.tick(FPS)

# Main game flow
while True:
    if current_state == STATE_MENU:
        game_menu()
    elif current_state == STATE_PLAYING:
        game_loop()
    elif current_state == STATE_GAME_OVER:
        game_over()
    else:
        break

pygame.quit()