import pygame
import random
import sys

# Initialize
pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
GRAY = (150, 150, 150)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🚀 Galaxy Defender")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("consolas", 48, bold=True)
font_med   = pygame.font.SysFont("consolas", 28)
font_small = pygame.font.SysFont("consolas", 20)

# --- Stars background ---
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.random()) for _ in range(150)]

def draw_stars():
    for x, y, speed in stars:
        brightness = int(100 + speed * 155)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (int(x), int(y)), 1)

# Move stars (parallax scroll)
def update_stars():
    global stars
    new_stars = []
    for x, y, speed in stars:
        y += speed * 0.8
        if y > HEIGHT:
            y = 0
            x = random.randint(0, WIDTH)
        new_stars.append((x, y, speed))
    stars[:] = new_stars

# --- Particle system ---
particles = []

def spawn_explosion(x, y, color, count=20):
    for _ in range(count):
        vx = random.uniform(-4, 4)
        vy = random.uniform(-4, 4)
        life = random.randint(20, 40)
        particles.append([x, y, vx, vy, life, color])

def update_particles():
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1
        if p[4] <= 0:
            particles.remove(p)

def draw_particles():
    for p in particles:
        alpha = max(0, p[4] * 6)
        r, g, b = p[5]
        color = (min(255, r), min(255, g), min(255, b))
        pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), max(1, p[4] // 10))

# --- Player ---
class Player:
    def __init__(self):
        self.w, self.h = 48, 48
        self.x = WIDTH // 2 - self.w // 2
        self.y = HEIGHT - 80
        self.speed = 5
        self.hp = 3
        self.cooldown = 0
        self.shoot_delay = 15
        self.invincible = 0  # frames of invincibility after hit

    def move(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += self.speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.y += self.speed
        self.x = max(0, min(WIDTH - self.w, self.x))
        self.y = max(HEIGHT // 2, min(HEIGHT - self.h - 10, self.y))

    def shoot(self, bullets, keys):
        if self.cooldown > 0:
            self.cooldown -= 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.cooldown == 0:
            cx = self.x + self.w // 2
            bullets.append(Bullet(cx - 2, self.y, -12, CYAN, "player"))
            self.cooldown = self.shoot_delay

    def take_hit(self):
        if self.invincible == 0:
            self.hp -= 1
            self.invincible = 90
            spawn_explosion(self.x + self.w//2, self.y + self.h//2, RED, 15)

    def update(self):
        if self.invincible > 0:
            self.invincible -= 1

    def draw(self):
        blink = self.invincible > 0 and (self.invincible // 6) % 2 == 0
        if not blink:
            cx = self.x + self.w // 2
            # Engine glow
            pygame.draw.ellipse(screen, ORANGE,
                (cx - 6, self.y + self.h - 10, 12, 16))
            # Body
            body_pts = [
                (cx,          self.y + 4),
                (cx - 18,     self.y + self.h - 10),
                (cx - 10,     self.y + self.h - 4),
                (cx + 10,     self.y + self.h - 4),
                (cx + 18,     self.y + self.h - 10),
            ]
            pygame.draw.polygon(screen, CYAN, body_pts)
            # Wings
            lwing = [(cx - 10, self.y + 28), (cx - 26, self.y + self.h), (cx - 8, self.y + self.h - 6)]
            rwing = [(cx + 10, self.y + 28), (cx + 26, self.y + self.h), (cx + 8, self.y + self.h - 6)]
            pygame.draw.polygon(screen, PURPLE, lwing)
            pygame.draw.polygon(screen, PURPLE, rwing)
            # Cockpit
            pygame.draw.ellipse(screen, WHITE, (cx - 5, self.y + 10, 10, 14))

    def rect(self):
        return pygame.Rect(self.x + 8, self.y + 4, self.w - 16, self.h - 8)

# --- Bullet ---
class Bullet:
    def __init__(self, x, y, vy, color, owner):
        self.x, self.y = x, y
        self.vy = vy
        self.color = color
        self.owner = owner
        self.w, self.h = 4, 14

    def update(self):
        self.y += self.vy

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.w, self.h), border_radius=2)
        # Glow
        glow = pygame.Surface((self.w + 6, self.h + 6), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*self.color, 60), (0, 0, self.w + 6, self.h + 6), border_radius=3)
        screen.blit(glow, (self.x - 3, self.y - 3))

    def off_screen(self):
        return self.y < -20 or self.y > HEIGHT + 20

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

# --- Enemy ---
class Enemy:
    TYPES = {
        "grunt":  {"color": RED,    "hp": 1, "speed": 1.5, "score": 10, "size": 36},
        "tank":   {"color": ORANGE, "hp": 3, "speed": 0.8, "score": 30, "size": 44},
        "speeder":{"color": YELLOW, "hp": 1, "speed": 3.0, "score": 20, "size": 28},
        "elite":  {"color": PURPLE, "hp": 5, "speed": 1.2, "score": 50, "size": 40},
    }

    def __init__(self, kind="grunt"):
        data = self.TYPES[kind]
        self.kind = kind
        self.color = data["color"]
        self.hp = data["hp"]
        self.max_hp = data["hp"]
        self.speed = data["speed"]
        self.score_val = data["score"]
        self.size = data["size"]
        self.x = random.randint(20, WIDTH - 20 - self.size)
        self.y = random.randint(-120, -self.size)
        self.shoot_timer = random.randint(60, 180)
        self.sway = random.uniform(-0.8, 0.8)
        self.sway_timer = 0

    def update(self, bullets):
        self.sway_timer += 1
        self.x += self.sway * (1 + 0.5 * (self.sway_timer % 120 > 60))
        self.x = max(0, min(WIDTH - self.size, self.x))
        self.y += self.speed

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            cx = self.x + self.size // 2
            bullets.append(Bullet(cx - 2, self.y + self.size, 5, RED, "enemy"))
            self.shoot_timer = random.randint(80, 200)

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            spawn_explosion(self.x + self.size//2, self.y + self.size//2, self.color, 25)
            return True
        spawn_explosion(self.x + self.size//2, self.y + self.size//2, WHITE, 8)
        return False

    def draw(self):
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2
        s = self.size
        if self.kind == "grunt":
            pts = [(cx, self.y + 4), (self.x + 4, self.y + s - 4), (self.x + s - 4, self.y + s - 4)]
            pygame.draw.polygon(screen, self.color, pts)
            pygame.draw.circle(screen, WHITE, (cx, cy + 4), 6)
        elif self.kind == "tank":
            pygame.draw.rect(screen, self.color, (self.x, self.y, s, s), border_radius=6)
            pygame.draw.rect(screen, WHITE, (self.x + s//4, self.y + s//4, s//2, s//2), border_radius=3)
        elif self.kind == "speeder":
            pts = [(cx, self.y), (self.x, self.y + s), (cx, self.y + s - 8), (self.x + s, self.y + s)]
            pygame.draw.polygon(screen, self.color, pts)
        elif self.kind == "elite":
            pygame.draw.circle(screen, self.color, (cx, cy), s // 2)
            pygame.draw.circle(screen, WHITE, (cx, cy), s // 4)
            for angle in range(0, 360, 60):
                import math
                ax = cx + int((s//2) * math.cos(math.radians(angle)))
                ay = cy + int((s//2) * math.sin(math.radians(angle)))
                pygame.draw.circle(screen, self.color, (ax, ay), 5)

        # HP bar
        if self.hp < self.max_hp:
            bar_w = s
            filled = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(screen, GRAY, (self.x, self.y - 8, bar_w, 5))
            pygame.draw.rect(screen, GREEN, (self.x, self.y - 8, filled, 5))

    def off_screen(self):
        return self.y > HEIGHT + 20

    def rect(self):
        return pygame.Rect(self.x + 4, self.y + 4, self.size - 8, self.size - 8)

# --- HUD ---
def draw_hud(player, score, wave, kills_left):
    # Score
    txt = font_med.render(f"SCORE: {score}", True, CYAN)
    screen.blit(txt, (10, 10))
    # Wave
    txt2 = font_med.render(f"WAVE {wave}", True, YELLOW)
    screen.blit(txt2, (WIDTH // 2 - txt2.get_width() // 2, 10))
    # Lives
    for i in range(player.hp):
        pygame.draw.polygon(screen, GREEN, [
            (WIDTH - 30 - i * 32, 16),
            (WIDTH - 42 - i * 32, 34),
            (WIDTH - 18 - i * 32, 34),
        ])
    # Kills left
    txt3 = font_small.render(f"Enemies left: {kills_left}", True, GRAY)
    screen.blit(txt3, (10, HEIGHT - 28))

# --- Screens ---
def draw_start_screen():
    screen.fill(BLACK)
    draw_stars()
    t = font_large.render("GALAXY DEFENDER", True, CYAN)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, 160))
    t2 = font_med.render("Arrow Keys / WASD  —  Move", True, WHITE)
    t3 = font_med.render("SPACE  —  Shoot", True, WHITE)
    t4 = font_med.render("Press ENTER to Start", True, YELLOW)
    screen.blit(t2, (WIDTH//2 - t2.get_width()//2, 280))
    screen.blit(t3, (WIDTH//2 - t3.get_width()//2, 320))
    screen.blit(t4, (WIDTH//2 - t4.get_width()//2, 400))

def draw_gameover_screen(score):
    screen.fill(BLACK)
    draw_stars()
    t  = font_large.render("GAME OVER", True, RED)
    t2 = font_med.render(f"Final Score: {score}", True, WHITE)
    t3 = font_med.render("Press ENTER to Restart", True, YELLOW)
    screen.blit(t,  (WIDTH//2 - t.get_width()//2,  180))
    screen.blit(t2, (WIDTH//2 - t2.get_width()//2, 280))
    screen.blit(t3, (WIDTH//2 - t3.get_width()//2, 360))

def draw_wave_banner(wave):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))
    t = font_large.render(f"— WAVE {wave} —", True, YELLOW)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 30))

# --- Wave generator ---
def spawn_wave(wave):
    enemies = []
    count = 5 + wave * 3
    elite_chance = min(0.15, wave * 0.03)
    tank_chance  = min(0.25, wave * 0.05)
    for _ in range(count):
        r = random.random()
        if r < elite_chance:
            kind = "elite"
        elif r < elite_chance + tank_chance:
            kind = "tank"
        elif r < elite_chance + tank_chance + 0.3:
            kind = "speeder"
        else:
            kind = "grunt"
        enemies.append(Enemy(kind))
    return enemies

# ===== MAIN GAME LOOP =====
def main():
    state = "start"  # start | playing | wave_banner | gameover
    player = Player()
    bullets = []
    enemies = []
    score = 0
    wave = 0
    banner_timer = 0

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if state == "start" and event.key == pygame.K_RETURN:
                    state = "wave_banner"
                    wave = 1
                    enemies = spawn_wave(wave)
                    banner_timer = 90
                    player = Player()
                    bullets.clear()
                    score = 0
                    particles.clear()
                if state == "gameover" and event.key == pygame.K_RETURN:
                    state = "start"

        # ---- DRAW ----
        screen.fill((5, 5, 20))
        update_stars()
        draw_stars()

        if state == "start":
            draw_start_screen()

        elif state == "wave_banner":
            # Still draw game elements underneath
            for e in enemies: e.draw()
            for b in bullets: b.draw()
            player.draw()
            draw_particles()
            draw_hud(player, score, wave, len(enemies))
            draw_wave_banner(wave)
            banner_timer -= 1
            if banner_timer <= 0:
                state = "playing"

        elif state == "playing":
            # Update
            player.move(keys)
            player.shoot(bullets, keys)
            player.update()

            for b in bullets[:]:
                b.update()
                if b.off_screen():
                    bullets.remove(b)

            for e in enemies[:]:
                e.update(bullets)
                # Enemy off screen = player takes damage
                if e.off_screen():
                    enemies.remove(e)
                    player.take_hit()
                    continue
                # Bullet hits enemy
                for b in bullets[:]:
                    if b.owner == "player" and b.rect().colliderect(e.rect()):
                        if b in bullets: bullets.remove(b)
                        if e.take_hit():
                            score += e.score_val
                            if e in enemies: enemies.remove(e)
                        break
                # Enemy bullet hits player
            for b in bullets[:]:
                if b.owner == "enemy" and b.rect().colliderect(player.rect()):
                    player.take_hit()
                    if b in bullets: bullets.remove(b)

            update_particles()

            # Next wave?
            if not enemies:
                wave += 1
                enemies = spawn_wave(wave)
                banner_timer = 90
                state = "wave_banner"

            # Game over?
            if player.hp <= 0:
                state = "gameover"

            # Draw
            for e in enemies: e.draw()
            for b in bullets: b.draw()
            draw_particles()
            player.draw()
            draw_hud(player, score, wave, len(enemies))

        elif state == "gameover":
            draw_gameover_screen(score)

        pygame.display.flip()

if __name__ == "__main__":
    main()
