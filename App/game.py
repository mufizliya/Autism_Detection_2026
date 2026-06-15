import pygame
import time
import random
import csv
import os
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Initialize Pygame
pygame.init()

# Fullscreen settings
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bubble Pop Game")

# Load background and character
BACKGROUND_IMG = pygame.image.load('src/GAMEBG.jpg')
BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (WIDTH, HEIGHT))
CHAR_IMG = pygame.image.load('src/character.png')  # ensure this file exists
# Scale character to ~1/3 screen width
CHAR_W = WIDTH // 2.5
CHAR_H = int(CHAR_IMG.get_height() * (CHAR_W / CHAR_IMG.get_width()))
CHAR_IMG = pygame.transform.scale(CHAR_IMG, (CHAR_W, CHAR_H))

# Load assets
BUBBLE_COLORS = [(135, 206, 250), (100, 149, 237), (173, 216, 230), (176, 224, 230)]
POP_SOUND = pygame.mixer.Sound(file='src/pop.mp3')

# Fonts
pygame.font.init()
font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_speech = pygame.font.SysFont("Arial", 28)

# Game variables
bubbles = []
reaction_data = []
score = 0
clock = pygame.time.Clock()

game_duration = 35  # seconds
BUBBLE_INTERVAL = 1500  # ms
BUBBLE_LIFESPAN = 3     # seconds
MAX_RADIUS = 80
MIN_RADIUS = 50

class Bubble:
    def __init__(self):
        self.radius = random.randint(MIN_RADIUS, MAX_RADIUS)
        self.color = random.choice(BUBBLE_COLORS)
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.appear_time = time.time()

    def draw(self):
        elapsed = time.time() - self.appear_time
        alpha = int(255 * min(elapsed / 0.5, 1))
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.radius, self.radius), self.radius)
        shadow = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0,0,0,int(alpha*0.3)), (self.radius+2, self.radius+2), self.radius)
        screen.blit(shadow, (self.x-self.radius, self.y-self.radius))
        screen.blit(surf, (self.x-self.radius, self.y-self.radius))

    def is_clicked(self, pos):
        return ((self.x-pos[0])**2 + (self.y-pos[1])**2)**0.5 <= self.radius

# Intro screen before starting the timer
# Modified to position character bottom-left and bring text closer to character

def show_intro():
    screen.blit(BACKGROUND_IMG, (0, 0))
    padding = 20
    # Position character at bottom-left
    char_x = padding
    char_y = HEIGHT - CHAR_H - padding
    screen.blit(CHAR_IMG, (char_x, char_y))

    # Speech bubble next to character
    text = "Hey! Pop as many bubbles as you can!"
    text_surf = font_speech.render(text, True, (0, 0, 0))
    bubble_w = text_surf.get_width() + padding*2
    bubble_h = text_surf.get_height() + padding*2
    # Reduce horizontal gap, bring bubble closer to character
    bubble_x = char_x + CHAR_W - 20
    bubble_y = char_y + (CHAR_H - bubble_h) // 2

    bubble = pygame.Surface((bubble_w, bubble_h), pygame.SRCALPHA)
    pygame.draw.rect(bubble, (255,255,255,230), (0,0,bubble_w,bubble_h), border_radius=15)
    pygame.draw.rect(bubble, (0,0,0), (0,0,bubble_w,bubble_h), 2, border_radius=15)
    bubble.blit(text_surf, (padding, padding))
    screen.blit(bubble, (bubble_x, bubble_y))

    pygame.display.flip()
    pygame.time.delay(2000)

# Display intro
show_intro()

# Start the game timer
game_start_time = time.time()

# Main game loop
running = True
last_bubble_time = pygame.time.get_ticks()

while running:
    if time.time() - game_start_time > game_duration:
        break

    screen.blit(BACKGROUND_IMG, (0, 0))
    now_sec = time.time()

    if pygame.time.get_ticks() - last_bubble_time > BUBBLE_INTERVAL:
        bubbles.append(Bubble())
        last_bubble_time = pygame.time.get_ticks()

    for bubble in bubbles[:]:
        bubble.draw()
        if now_sec - bubble.appear_time > BUBBLE_LIFESPAN:
            reaction_data.append({
                "x": bubble.x,
                "y": bubble.y,
                "reaction_time_sec": None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "missed"
            })
            bubbles.remove(bubble)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            pos = pygame.mouse.get_pos() if event.type == pygame.MOUSEBUTTONDOWN else (int(event.x*WIDTH), int(event.y*HEIGHT))
            for bubble in bubbles[:]:
                if bubble.is_clicked(pos):
                    rt = now_sec - bubble.appear_time
                    reaction_data.append({
                        "x": bubble.x,
                        "y": bubble.y,
                        "reaction_time_sec": round(rt, 2),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "popped"
                    })
                    score += 1
                    try:
                        POP_SOUND.play()
                    except:
                        pass
                    bubbles.remove(bubble)
                    break

    score_surf = font_large.render(f"Score: {score}", True, (255,255,255))
    box = pygame.Surface((score_surf.get_width()+20, score_surf.get_height()+10), pygame.SRCALPHA)
    pygame.draw.rect(box, (0,0,0,150), box.get_rect(), border_radius=10)
    box.blit(score_surf, (10,5))
    screen.blit(box, (10,10))

    pygame.display.flip()
    clock.tick(60)

# End screen
screen.blit(BACKGROUND_IMG, (0, 0))
end_msg = font_large.render("Time's up!", True, (255,255,255))
score_msg = font_large.render(f"Final Score: {score}", True, (255,255,255))
pad = 20
bw = max(end_msg.get_width(), score_msg.get_width()) + pad*2
bh = end_msg.get_height() + score_msg.get_height() + pad*3
bx, by = (WIDTH-bw)//2, (HEIGHT-bh)//2
box_e = pygame.Surface((bw,bh), pygame.SRCALPHA)
pygame.draw.rect(box_e, (0,0,0,200), (0,0,bw,bh), border_radius=15)
box_e.blit(end_msg, ((bw-end_msg.get_width())//2, pad))
box_e.blit(score_msg, ((bw-score_msg.get_width())//2, pad*2+end_msg.get_height()))
screen.blit(box_e, (bx,by))
pygame.display.flip()
pygame.time.delay(3000)
pygame.quit()

# Save CSV inside logs folder
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = os.path.join(LOG_DIR, f"reaction_times_{ts}.csv")
with open(filename, "w", newline='') as f:
    w = csv.DictWriter(f, ["x","y","reaction_time_sec","timestamp","status"])
    w.writeheader()
    w.writerows(reaction_data)

print(f"Saved {len(reaction_data)} reactions to {filename}.")
