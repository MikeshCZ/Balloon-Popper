import pygame
import random
import sys
import math
import os
import base64
import hashlib
import json

pygame.init()

# --- Promenne ---
VERSION = "0.3.1"
RESOLUTIONS = {
    "HD": (1280, 720),
    "FullHD": (1920, 1080),
    "2K": (2560, 1440),
    "4K": (3840, 2160),
}
DEFAULT_RES = "FullHD"
WIDTH, HEIGHT = RESOLUTIONS[DEFAULT_RES]
FPS = 60
BALLOON_SPAWN_TIME = 400  # ms
INITIAL_BALLOON_GROWTH = 0.3
MAX_LIVES = 5
FONT = pygame.font.SysFont("arial", 24)
TITLE_FONT = pygame.font.SysFont("arial", 48, bold=True)
HIGH_SCORE_FILE = "config/.highscore"
SETTINGS_FILE = "config/settings.json"
BUTTON_WIDTH = 220
BUTTON_HEIGHT = 30

# --- Barvy ---
WHITE = (235, 235, 235)
BLACK = (30, 30, 30)
RED = (235, 0, 0)
GREY = (180, 180, 180)

# --- Zvuky ---
CLICK_SOUND_FILE = "assets/click.mp3"
if os.path.exists(CLICK_SOUND_FILE):
    click_sound = pygame.mixer.Sound(CLICK_SOUND_FILE)
else:
    click_sound = None

BALLOON_POP_SOUND_FILE = "assets/balloon-pop.mp3"
if os.path.exists(BALLOON_POP_SOUND_FILE):
    balloon_pop_sound = pygame.mixer.Sound(BALLOON_POP_SOUND_FILE)
else:
    balloon_pop_sound = None


# --- Inicializace ---
dark_mode = False
screen_flags = 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
pygame.display.set_caption("Balloon Popper")
clock = pygame.time.Clock()

# --- Stavy hry ---
MENU, PLAYING, GAME_OVER, SETTINGS = "menu", "playing", "game_over", "settings"


# --- Castice ---
class Particle:
    def __init__(self, pos, color):
        self.x, self.y = pos
        self.radius = random.randint(2, 4)
        self.color = color
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.life = random.randint(20, 40)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(
                surface, self.color, (int(self.x), int(self.y)), self.radius
            )


# --- Balonek ---
class Balloon:
    def __init__(self):
        scale = WIDTH / 1920
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.radius = int(10 * scale)
        self.max_radius = int(60 * scale)
        self.growth = INITIAL_BALLOON_GROWTH
        self.alive = True
        self.color = (
            random.randint(100, 200),
            random.randint(100, 200),
            random.randint(100, 200),
        )
        self.pulsing = False
        self.pulse_timer = 0
        self.pulse_duration = 2000  # ms
        self.blink_timer = 0

    def update(self, dt):
        if not self.pulsing:
            self.radius += self.growth * dt / 16
            if self.radius >= self.max_radius:
                self.pulsing = True
                self.pulse_timer = self.pulse_duration
        else:
            self.pulse_timer -= dt
            pulse_scale = 1 + 0.05 * math.sin(pygame.time.get_ticks() / 100.0)
            self.radius = int(self.max_radius * pulse_scale)
            self.blink_timer += dt
            if self.blink_timer >= 100:
                self.color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255),
                )
                self.blink_timer = 0
            if self.pulse_timer <= 0:
                self.alive = False

    def is_clicked(self, pos):
        return math.hypot(pos[0] - self.x, pos[1] - self.y) <= self.radius

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), int(self.radius))


# --- Hra ---
class Game:
    def __init__(self, scale=1.0, antialias=False):
        self.scale = scale
        self.antialias = antialias
        self.reset()
        self.load_high_score()

    # Inicializace a reset herního stavu
    def reset(self):
        self.balloons = []
        self.particles = []
        self.spawn_timer = 0
        self.score = 0
        self.lives = MAX_LIVES
        self.growth_multiplier = 1.0
        self.high_score = 0

    def save_high_score(self, score):
        self.load_high_score()  # načteme aktuální high score
        if score > self.high_score:
            self.high_score = score
            key = hashlib.sha256(b"secret-key").digest()
            encoded = base64.b64encode(f"{self.high_score}:{key.hex()}".encode("utf-8"))
            with open(HIGH_SCORE_FILE, "wb") as f:
                f.write(encoded)

    def load_high_score(self):
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, "rb") as f:
                try:
                    decoded = base64.b64decode(f.read()).decode("utf-8")
                    score_str, key_hash = decoded.split(":")
                    expected_key = hashlib.sha256(b"secret-key").hexdigest()
                    if key_hash == expected_key:
                        self.high_score = int(score_str)
                    else:
                        self.high_score = 0
                except Exception:
                    self.high_score = 0
        else:
            self.high_score = 0

    # Aktualizace stavu hry – spawn balonku, pohyb partiklu, ztraty zivotu
    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer >= BALLOON_SPAWN_TIME + random.uniform(0, 800):
            self.spawn_timer = 0
            if len(self.balloons) < 10:  # max 10 balonku na obrazovce
                b = Balloon()
                b.growth *= self.growth_multiplier
                self.balloons.append(b)

        for b in self.balloons[:]:
            b.update(dt)
            if not b.alive:
                self.balloons.remove(b)
                self.lives -= 1
                if balloon_pop_sound:
                    balloon_pop_sound.play()
                for _ in range(20):
                    self.particles.append(
                        Particle((b.x, b.y), b.color)
                    )  # animace i pri ztrate

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        self.growth_multiplier += 0.0001  # postupne zrychlujeme rust

    # Zpracovani kliknuti mysi – pokud je kliknuto na balonek, odebrat a vytvorit particles
    def handle_click(self, pos):
        for b in self.balloons[:]:
            if b.is_clicked(pos):
                self.balloons.remove(b)
                self.score += 1
                if click_sound:
                    click_sound.play()
                # Zkontrolujeme, zda je skore delitelne 100 a prida zivot
                if self.score % 100 == 0:
                    self.lives += 1
                    # Zaskoruje všechny balonky na obrazovce
                    for balloon in self.balloons[:]:
                        self.balloons.remove(balloon)
                        self.score += 1
                        for _ in range(20):
                            self.particles.append(
                                Particle((balloon.x, balloon.y), balloon.color)
                            )
                for _ in range(20):
                    self.particles.append(Particle((b.x, b.y), b.color))
                break

    # Vykresleni vsech objektu – balonky, partikly, HUD
    def draw(self, surface):
        surface.fill((30, 30, 30) if dark_mode else WHITE)
        for b in self.balloons:
            b.draw(surface)
        for p in self.particles:
            p.draw(surface)
        self.draw_hud(surface)

    # Vykresleni skore a poctu zivotu
    def draw_hud(self, surface):
        score_text = FONT.render(
            f"Skóre: {self.score}", True, (BLACK if not dark_mode else WHITE)
        )
        lives_text = FONT.render(f"Životy: {self.lives}", True, RED)
        surface.blit(score_text, (10, 10))
        surface.blit(lives_text, (10, 40))


# --- Menu ---
def draw_menu(surface, high_score, last_score):

    # Vykresleni pozadi
    surface.fill((30, 30, 30) if dark_mode else WHITE)

    # Vytvoreni textu
    title = TITLE_FONT.render(
        "BALLOON POPPER", True, (BLACK if not dark_mode else WHITE)
    )
    play = FONT.render("Nová hra", True, (BLACK if not dark_mode else WHITE))
    settings = FONT.render("Nastavení", True, (BLACK if not dark_mode else WHITE))
    quit = FONT.render("Konec", True, (BLACK if not dark_mode else WHITE))
    hs = FONT.render(
        f"Nejvyšší skóre: {high_score}", True, (BLACK if not dark_mode else WHITE)
    )
    ls = FONT.render(
        f"Skóre poslední hry: {last_score}", True, (BLACK if not dark_mode else WHITE)
    )

    # Vykresleni textu
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    play_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, 250, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    settings_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, 300, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    quit_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, 350, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    ls_rect = ls.get_rect(center=(WIDTH // 2, 450))
    hs_rect = hs.get_rect(center=(WIDTH // 2, 500))

    # Vykresleni pozadi tlacitek
    pygame.draw.rect(surface, GREY, play_rect.inflate(20, 10))
    pygame.draw.rect(surface, GREY, settings_rect.inflate(20, 10))
    pygame.draw.rect(surface, GREY, quit_rect.inflate(20, 10))

    # Vykresleni textu
    surface.blit(play, play_rect)
    surface.blit(settings, settings_rect)
    surface.blit(quit, quit_rect)
    surface.blit(ls, ls_rect)
    surface.blit(hs, hs_rect)

    # Verze aplikace vpravo dole
    version_text = FONT.render(f"Verze: {VERSION}", True, GREY)
    surface.blit(
        version_text,
        (
            WIDTH - version_text.get_width() - 20,
            HEIGHT - version_text.get_height() - 20,
        ),
    )

    # Vytvoreni obdelniku pro tlacitka
    return (
        play_rect.inflate(20, 10),
        quit_rect.inflate(20, 10),
        settings_rect.inflate(20, 10),
    )


def draw_settings_menu(surface):
    # Vykresleni pozadi
    surface.fill((30, 30, 30) if dark_mode else WHITE)

    # Vytvoreni textu pro rozliseni
    y = 150
    options = ["HD", "FullHD", "2K", "4K"]
    res_buttons = []
    for res in options:
        txt = FONT.render(res, True, (BLACK if not dark_mode else WHITE))
        rect = pygame.Rect(
            WIDTH // 2 - BUTTON_WIDTH // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
        )
        pygame.draw.rect(surface, GREY, rect.inflate(20, 10))
        surface.blit(txt, rect)
        res_buttons.append((res, rect.inflate(20, 10)))
        y += 50

    # fullscreen toggle
    fs_state = "[X] " if bool(screen_flags & pygame.FULLSCREEN) else "[ ] "
    fs_txt = FONT.render(
        fs_state + "Fullscreen", True, (BLACK if not dark_mode else WHITE)
    )
    fs_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    pygame.draw.rect(surface, GREY, fs_rect.inflate(20, 10))
    surface.blit(fs_txt, fs_rect)

    # antialias toggle
    y += 50
    aa_state = "[X] " if game.antialias else "[ ] "
    aa_txt = FONT.render(
        aa_state + "Antialiasing", True, (BLACK if not dark_mode else WHITE)
    )
    aa_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    pygame.draw.rect(surface, GREY, aa_rect.inflate(20, 10))
    surface.blit(aa_txt, aa_rect)

    # dark mode toggle
    y += 50
    dm_state = "[X] " if dark_mode else "[ ] "
    dm_txt = FONT.render(
        dm_state + "Dark Mode", True, (BLACK if not dark_mode else WHITE)
    )
    dm_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    pygame.draw.rect(surface, GREY, dm_rect.inflate(20, 10))
    surface.blit(dm_txt, dm_rect)

    # Zpet tlacitko
    y += 50
    back_txt = FONT.render("Zpět", True, (BLACK if not dark_mode else WHITE))
    back_rect = pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    pygame.draw.rect(surface, GREY, back_rect.inflate(20, 10))
    surface.blit(back_txt, back_rect)

    return (
        res_buttons,
        fs_rect.inflate(20, 10),
        aa_rect.inflate(20, 10),
        dm_rect.inflate(20, 10),
        back_rect.inflate(20, 10),
    )


def save_settings(res, fullscreen, antialias, dark_mode):
    data = {
        "resolution": res,
        "fullscreen": fullscreen,
        "antialias": antialias,
        "dark_mode": dark_mode,
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                data = json.load(f)
                return (
                    data.get("resolution", DEFAULT_RES),
                    data.get("fullscreen", False),
                    data.get("antialias", False),
                    data.get("dark_mode", False),
                )
            except Exception:
                pass
    return DEFAULT_RES, False, False, False


# --- Inicializace nastavení ---
res, fullscreen, antialias, dark_mode = load_settings()
WIDTH, HEIGHT = RESOLUTIONS[res]
screen_flags = pygame.FULLSCREEN if fullscreen else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
game = Game(antialias=antialias)

# --- Main Loop ---
state = MENU
play_button = None
quit_button = None
settings_button = None
res_buttons = []
fs_button = None
aa_button = None
dm_button = None
back_button = None
last_score = 0

while True:
    dt = clock.tick(FPS)

    # Zpracovani udalosti
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_settings(
                res, bool(screen_flags & pygame.FULLSCREEN), game.antialias, dark_mode
            )
            pygame.quit()
            sys.exit()
        if state == MENU:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button and play_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    game.reset()
                    state = PLAYING
                elif quit_button and quit_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    pygame.quit()
                    sys.exit()
                elif settings_button and settings_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    state = "settings"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        elif state == PLAYING:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game.lives = 0
        elif state == SETTINGS:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for r, btn in res_buttons:
                    if btn.collidepoint(event.pos):
                        if click_sound:
                            click_sound.play()
                        res = r
                        WIDTH, HEIGHT = RESOLUTIONS[res]
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
                if fs_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    screen_flags ^= pygame.FULLSCREEN
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
                if aa_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    game.antialias = not game.antialias
                elif dm_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    dark_mode = not dark_mode
                if back_button.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    save_settings(
                        res,
                        bool(screen_flags & pygame.FULLSCREEN),
                        game.antialias,
                        dark_mode,
                    )
                    state = MENU

    if state == MENU:
        play_button, quit_button, settings_button = draw_menu(
            screen, game.high_score, last_score
        )
    elif state == PLAYING:
        game.update(dt)
        game.draw(screen)
        if game.lives <= 0:
            last_score = game.score
            game.save_high_score(last_score)
            state = MENU
    elif state == SETTINGS:
        res_buttons, fs_button, aa_button, dm_button, back_button = draw_settings_menu(
            screen
        )

    pygame.display.flip()  # Aktualizace obrazovky
