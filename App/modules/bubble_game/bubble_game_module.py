"""
BubbleGameModule — drop-in replacement for the original bubble_game_module.py
==============================================================================
The class name, method signatures, session dict keys, and all data-collection
variable names are kept identical to the original so nothing else in the
project needs to change.

What changed: the GAME only.
  - Bubbles now float upward from the bottom with sine-wave drift
    instead of appearing at fixed random positions.
  - PNG sprites (bubble.png, background.png) are used when available;
    coloured-circle fallbacks are used otherwise.
  - Background music loops for the full session.
  - Coloured particle bursts appear on every pop.
  - A clean HUD shows score (top-left) and countdown timer (top-right).
  - The end screen shows "Time's up!" + final score for 3 s then returns.
  - A bubble that exits the top of the screen is logged as "missed"
    (equivalent to the original lifespan-expiry logic).

Everything OUTSIDE the game (data collection, touch tracking, variable names,
session dict structure, BubbleTouchFeatureExtractor calls) is unchanged.
"""

import pygame
import time
import random
import os
import math
from datetime import datetime

from core.bubble_touch_feature_extractor import BubbleTouchFeatureExtractor
from core.project_paths import app_path

# ---------------------------------------------------------------------------
# Visual / game constants
# ---------------------------------------------------------------------------
FPS            = 60
GAME_DURATION  = 35          # seconds — kept same as original

# Bubble movement
BUBBLE_MIN_DIAMETER = 200    # pixels  (original radius 50–80 → diameter 100–160)
BUBBLE_MAX_DIAMETER = 300
BUBBLE_SPEED_MIN    = 1.5    # pixels per frame upward
BUBBLE_SPEED_MAX    = 3.0
BUBBLE_DRIFT_MAX    = 0.8    # max horizontal sine-wave drift per frame

# Spawn timing (replaces original fixed 1500 ms interval)
SPAWN_INTERVAL_MIN  = 0.4    # seconds
SPAWN_INTERVAL_MAX  = 1.8

# Particle burst on pop
PARTICLE_COUNT      = 18
PARTICLE_SPEED_MAX  = 6
PARTICLE_LIFE       = 40     # frames

# Colours
WHITE      = (255, 255, 255)
YELLOW     = (255, 230,  50)
SOFT_PINK  = (255, 120, 180)
SKY_BLUE   = ( 80, 190, 255)
LIME_GREEN = (100, 240, 100)
ORANGE     = (255, 160,  40)
PURPLE     = (200, 100, 255)

SCORE_COLOR   = YELLOW
TIMER_COLOR   = SOFT_PINK
OVERLAY_COLOR = (20, 20, 60, 200)

PARTICLE_COLORS = [YELLOW, SOFT_PINK, SKY_BLUE, LIME_GREEN, ORANGE, PURPLE, WHITE]


# ---------------------------------------------------------------------------
# Internal helpers (not part of the public API)
# ---------------------------------------------------------------------------
def _load_image(path: str,
                fallback_size: tuple,
                fallback_color: tuple) -> pygame.Surface:
    """Load an image file; return a coloured-circle placeholder on failure."""
    try:
        return pygame.image.load(path).convert_alpha()
    except (FileNotFoundError, pygame.error) as exc:
        print(f"[WARNING] Could not load '{path}': {exc}. Using placeholder.")
    surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
    pygame.draw.circle(
        surf, fallback_color + (200,),
        (fallback_size[0] // 2, fallback_size[1] // 2),
        fallback_size[0] // 2)
    return surf


def _scale_to_fill(image: pygame.Surface,
                   target_w: int, target_h: int) -> pygame.Surface:
    """
    Scale-to-fill (cover) without stretching.
    Scales the image so it completely covers target_w x target_h
    while keeping the original aspect ratio, then centre-crops to fit exactly.
    No black bars, no distortion.
    """
    img_w, img_h = image.get_size()
    scale    = max(target_w / img_w, target_h / img_h)
    scaled_w = int(img_w * scale)
    scaled_h = int(img_h * scale)
    scaled   = pygame.transform.smoothscale(image, (scaled_w, scaled_h))
    crop_x   = (scaled_w - target_w) // 2
    crop_y   = (scaled_h - target_h) // 2
    result   = pygame.Surface((target_w, target_h))
    result.blit(scaled, (0, 0), (crop_x, crop_y, target_w, target_h))
    return result


def _start_music(music_dir: str) -> None:
    """Load and loop background music from the src folder. Silent on failure."""
    for filename in ("music.mp3", "music.ogg", "music.wav"):
        path = os.path.join(music_dir, filename)
        if os.path.isfile(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(loops=-1)
                print(f"[INFO] Background music loaded: '{path}'")
                return
            except pygame.error as exc:
                print(f"[WARNING] Could not play music '{path}': {exc}")
                return
    print("[INFO] No background music file found.")


def _draw_text_with_shadow(screen: pygame.Surface,
                            font: pygame.font.Font,
                            text: str,
                            color: tuple,
                            x: int, y: int,
                            anchor: str = "topleft",
                            shadow_offset: int = 3) -> None:
    """Render text with a black drop shadow for readability."""
    shadow = font.render(text, True, (0, 0, 0))
    surf   = font.render(text, True, color)
    screen.blit(shadow, shadow.get_rect(**{anchor: (x + shadow_offset,
                                                     y + shadow_offset)}))
    screen.blit(surf,   surf.get_rect(**{anchor: (x, y)}))


# ---------------------------------------------------------------------------
# Floating bubble (visual only — data collection stays in BubbleGameModule)
# ---------------------------------------------------------------------------
class _FloatingBubble:
    """
    Replaces the original static Bubble.
    Floats upward from the bottom edge with a gentle sine-wave drift.
    Keeps .x, .y, .radius, and .appear_time so all existing data-collection
    code that references those attributes continues to work unchanged.
    """

    def __init__(self, width: int, height: int,
                 min_radius: int, max_radius: int,
                 raw_image: pygame.Surface):

        # radius kept compatible with original naming
        self.radius = random.randint(min_radius, max_radius)
        diameter    = self.radius * 2

        # Scale sprite to this bubble's size
        self.image = pygame.transform.smoothscale(raw_image, (diameter, diameter))

        # Spawn just below the bottom edge at a random x
        self.x = float(random.randint(self.radius, width  - self.radius))
        self.y = float(height + self.radius)

        # Upward speed
        self.speed_y = -random.uniform(BUBBLE_SPEED_MIN, BUBBLE_SPEED_MAX)

        # Sine-wave horizontal drift parameters
        self._drift_amp  = random.uniform(0.2, BUBBLE_DRIFT_MAX)
        self._drift_freq = random.uniform(0.01, 0.03)
        self._drift_phase = random.uniform(0, 2 * math.pi)
        self._age        = 0

        self.appear_time = time.time()   # identical field name to original
        self.alive       = True

    def update(self, width: int) -> None:
        """Move bubble upward. Mark dead when it exits the top."""
        self._age += 1
        self.y    += self.speed_y
        self.x    += self._drift_amp * math.sin(
            self._drift_freq * self._age + self._drift_phase)

        if self.y + self.radius < 0:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(self.image, rect)

    def is_clicked(self, pos: tuple) -> bool:
        """Circle hit-test — same logic and name as the original."""
        dx = self.x - pos[0]
        dy = self.y - pos[1]
        return math.hypot(dx, dy) <= self.radius


# ---------------------------------------------------------------------------
# Particle (new — not in original)
# ---------------------------------------------------------------------------
class _Particle:
    """Single dot in the pop burst effect."""

    def __init__(self, cx: float, cy: float, color: tuple):
        self.x = cx;  self.y = cy;  self.color = color
        angle      = random.uniform(0, 2 * math.pi)
        speed      = random.uniform(1.5, PARTICLE_SPEED_MAX)
        self.vx    = math.cos(angle) * speed
        self.vy    = math.sin(angle) * speed
        self.life  = PARTICLE_LIFE
        self._max  = PARTICLE_LIFE
        self.r     = random.randint(4, 9)

    def update(self) -> None:
        self.x  += self.vx;  self.y += self.vy
        self.vy += 0.15      # gravity
        self.vx *= 0.97      # air resistance
        self.life -= 1

    def draw(self, screen: pygame.Surface) -> None:
        alpha  = int(255 * self.life / self._max)
        radius = max(1, int(self.r * self.life / self._max))
        surf   = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.color + (alpha,), (radius, radius), radius)
        screen.blit(surf, (int(self.x) - radius, int(self.y) - radius))

    @property
    def alive(self) -> bool:
        return self.life > 0


# ---------------------------------------------------------------------------
# BubbleGameModule — identical public interface to the original
# ---------------------------------------------------------------------------
class BubbleGameModule:
    """
    Drop-in replacement. Public interface is 100% identical to the original:
      - __init__
      - run(session)
      - calculate_behavioral_phenotypes()
      - show_end_screen(screen, background_img, font_large)

    Internal data attributes kept identical:
      self.reaction_data, self.score,
      self.touch_events, self.current_touch_event
    """

    def __init__(self):
        # ---- identical to original ----
        self.reaction_data        = []
        self.score                = 0
        self.touch_events         = []
        self.current_touch_event  = None

    # ------------------------------------------------------------------
    # Touch-event helpers — identical signatures and behaviour to original
    # ------------------------------------------------------------------
    def start_touch_event(self, x, y):
        self.current_touch_event = {
            "touch_id":               len(self.touch_events) + 1,
            "start_time":             time.time(),
            "end_time":               None,
            "duration_seconds":       0,
            "start_x":                x,
            "start_y":                y,
            "end_x":                  x,
            "end_y":                  y,
            "path_points":            [[x, y]],
            "touch_path_length":      0,
            "nearest_bubble_distance": 0,
            "hit":                    False,
            "pressure_value":         0,   # 0 on desktop; use event.pressure on mobile
        }

    def update_touch_event(self, x, y):
        if self.current_touch_event is None:
            return
        self.current_touch_event["path_points"].append([x, y])
        self.current_touch_event["end_x"] = x
        self.current_touch_event["end_y"] = y

    def finish_touch_event(self, x, y, hit, nearest_bubble_distance):
        if self.current_touch_event is None:
            return

        self.current_touch_event["end_time"] = time.time()
        self.current_touch_event["duration_seconds"] = round(
            self.current_touch_event["end_time"]
            - self.current_touch_event["start_time"], 4)
        self.current_touch_event["end_x"] = x
        self.current_touch_event["end_y"] = y
        self.current_touch_event["path_points"].append([x, y])
        self.current_touch_event["touch_path_length"] = round(
            BubbleTouchFeatureExtractor.path_length(
                self.current_touch_event["path_points"]), 4)
        self.current_touch_event["nearest_bubble_distance"] = round(
            nearest_bubble_distance, 4)
        self.current_touch_event["hit"]            = hit
        self.current_touch_event["pressure_value"] = 0

        self.touch_events.append(self.current_touch_event)
        self.current_touch_event = None

    def get_position_from_event(self, event, width, height):
        """Identical to original — normalises mouse and touch coordinates."""
        if event.type in (pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION):
            return pygame.mouse.get_pos()
        if event.type in (pygame.FINGERDOWN,
                          pygame.FINGERUP,
                          pygame.FINGERMOTION):
            return (int(event.x * width), int(event.y * height))
        return (0, 0)

    # ------------------------------------------------------------------
    # Main entry point — same signature: run(session)
    # ------------------------------------------------------------------
    def run(self, session):
        # Reset state (identical field names)
        self.reaction_data       = []
        self.score               = 0
        self.touch_events        = []
        self.current_touch_event = None

        # ---- Audio init (identical to original) ----
        audio_enabled = True
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.init()
            pygame.mixer.init()
            print("Mixer initialized:", pygame.mixer.get_init())
        except Exception as exc:
            print(f"Audio init failed: {exc}")
            audio_enabled = False

        # ---- Screen (identical to original: fullscreen at device resolution) ----
        info   = pygame.display.Info()
        WIDTH  = info.current_w
        HEIGHT = info.current_h

        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Bubble Pop Game")

        # ---- Assets ----
        src_dir = app_path("src")

        # Background — same path as original (GAMEBG.jpg)
        bg_raw = _load_image(
            app_path("src", "GAMEBG.jpg"),
            (WIDTH, HEIGHT), (135, 206, 235))
        background_img = _scale_to_fill(bg_raw, WIDTH, HEIGHT)

        # Bubble sprite — new asset; falls back to a coloured circle
        bubble_raw = _load_image(
            app_path("src", "bubble.png"),
            (160, 160), (100, 180, 255))

        # Pop sound — identical path to original
        pop_sound = None
        if audio_enabled:
            try:
                pop_sound = pygame.mixer.Sound(app_path("src", "pop.wav"))
                print("Pop sound loaded.")
            except Exception as exc:
                print(f"Sound load failed: {exc}")

        # Background music (new feature — silent if file absent)
        if audio_enabled:
            _start_music(src_dir)

        # ---- Fonts ----
        pygame.font.init()
        candidates = ["Comic Sans MS", "Nunito", "Fredoka One",
                      "Arial Rounded MT Bold", "Arial"]
        chosen = None
        for name in candidates:
            if name.lower() in [f.lower() for f in pygame.font.get_fonts()]:
                chosen = name
                break

        font_large  = pygame.font.SysFont(chosen, 56, bold=True)   # HUD
        font_title  = pygame.font.SysFont(chosen, 72, bold=True)   # end screen
        font_speech = pygame.font.SysFont(chosen or "Arial", 28)   # intro bubble

        # ---- Character image for intro (identical to original) ----
        try:
            char_img_raw = pygame.image.load(app_path("src", "character.png"))
            char_w = int(WIDTH // 2.5)
            char_h = int(char_img_raw.get_height()
                         * (char_w / char_img_raw.get_width()))
            char_img = pygame.transform.scale(char_img_raw, (char_w, char_h))
        except Exception as exc:
            print(f"[INFO] character.png not loaded: {exc}")
            char_img = None
            char_w   = 0
            char_h   = 0

        # ---- Show intro (identical call to original) ----
        if char_img is not None:
            show_intro(screen, background_img, char_img,
                       WIDTH, HEIGHT, char_h, char_w, font_speech)

        # ---- Game-loop variables ----
        bubbles:   list[_FloatingBubble] = []
        particles: list[_Particle]       = []

        clock          = pygame.time.Clock()
        game_start     = time.time()
        spawn_timer    = random.uniform(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX)

        # Bubble size — kept in radius units to stay compatible with original
        min_radius = BUBBLE_MIN_DIAMETER // 2   # 50
        max_radius = BUBBLE_MAX_DIAMETER // 2   # 80

        running = True

        # ================================================================
        # Main game loop
        # ================================================================
        while running:
            dt       = clock.tick(FPS) / 1000.0
            now_sec  = time.time()
            elapsed  = now_sec - game_start
            time_left = max(0.0, GAME_DURATION - elapsed)

            if elapsed >= GAME_DURATION:
                break

            # ---- Events ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if (event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE):
                    running = False

                # ---- Press: start tracking + hit test ----
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    if (event.type == pygame.MOUSEBUTTONDOWN
                            and event.button != 1):
                        continue

                    x, y = self.get_position_from_event(event, WIDTH, HEIGHT)
                    self.start_touch_event(x, y)

                    # Nearest-bubble distance at moment of press
                    nearest_bubble_distance = (
                        BubbleTouchFeatureExtractor.nearest_bubble_distance(
                            x, y,
                            [{"x": b.x, "y": b.y} for b in bubbles]
                        )
                    )

                    hit = False
                    for bubble in bubbles[:]:
                        if bubble.is_clicked((x, y)):
                            hit = True

                            # reaction_time_sec: identical field name
                            rt = round(now_sec - bubble.appear_time, 2)
                            self.reaction_data.append({
                                "x":                bubble.x,
                                "y":                bubble.y,
                                "reaction_time_sec": rt,
                                "timestamp":         datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"),
                                "status":            "popped",
                            })

                            self.score += 1

                            # Particle burst
                            for _ in range(PARTICLE_COUNT):
                                particles.append(_Particle(
                                    bubble.x, bubble.y,
                                    random.choice(PARTICLE_COLORS)))

                            if pop_sound:
                                try:
                                    pop_sound.play()
                                except Exception as exc:
                                    print(f"Sound play failed: {exc}")

                            bubble.alive = False
                            break

                    self.finish_touch_event(x, y, hit, nearest_bubble_distance)

                # ---- Move: update path ----
                if event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                    x, y = self.get_position_from_event(event, WIDTH, HEIGHT)
                    self.update_touch_event(x, y)

                # ---- Release: finalise path ----
                if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                    if (event.type == pygame.MOUSEBUTTONUP
                            and event.button != 1):
                        continue
                    x, y = self.get_position_from_event(event, WIDTH, HEIGHT)
                    self.update_touch_event(x, y)

            # ---- Spawn new bubble ----
            spawn_timer -= dt
            if spawn_timer <= 0:
                bubbles.append(_FloatingBubble(
                    WIDTH, HEIGHT, min_radius, max_radius, bubble_raw))
                spawn_timer = random.uniform(SPAWN_INTERVAL_MIN,
                                             SPAWN_INTERVAL_MAX)

            # ---- Update bubbles; log exits as "missed" ----
            for bubble in bubbles:
                bubble.update(WIDTH)

            alive_bubbles, dead_bubbles = [], []
            for b in bubbles:
                (alive_bubbles if b.alive else dead_bubbles).append(b)

            for b in dead_bubbles:
                # Identical "missed" record structure to original
                self.reaction_data.append({
                    "x":                b.x,
                    "y":                b.y,
                    "reaction_time_sec": None,
                    "timestamp":        datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    "status":           "missed",
                })
            bubbles = alive_bubbles

            # ---- Update particles ----
            for p in particles:
                p.update()
            particles = [p for p in particles if p.alive]

            # ---- Draw ----
            screen.blit(background_img, (0, 0))

            for bubble in bubbles:
                bubble.draw(screen)

            for p in particles:
                p.draw(screen)

            # HUD: score top-left, countdown top-right
            pad = 20
            _draw_text_with_shadow(screen, font_large,
                                   f"Score: {self.score}",
                                   SCORE_COLOR, pad, pad, anchor="topleft")

            secs = int(math.ceil(time_left))
            t_color = (ORANGE if int(time_left * 2) % 2 == 0
                       else (255, 60, 60)) if time_left <= 10 else TIMER_COLOR
            _draw_text_with_shadow(screen, font_large,
                                   f"Time: {secs}s",
                                   t_color, WIDTH - pad, pad, anchor="topright")

            pygame.display.flip()

        # ================================================================
        # End screen then clean up
        # ================================================================
        self.show_end_screen(screen, background_img, font_large)

        pygame.quit()

        # ---- Post-game analysis (identical to original) ----
        behavioral_phenotypes = self.calculate_behavioral_phenotypes()

        touch_features = BubbleTouchFeatureExtractor.build_from_touch_events(
            self.touch_events)

        # session dict keys identical to original
        session["game_metrics"] = {
            "score":               self.score,
            "total_reactions":     len(self.reaction_data),
            "reaction_data":       self.reaction_data,
            "behavioral_phenotypes": behavioral_phenotypes,
            "touch_events":        self.touch_events,
            "touch_features":      touch_features,
            "paper_pop_the_bubbles_popping_rate":
                touch_features.get("touch_popping_rate", 0),
            "paper_pop_the_bubbles_accuracy_std":
                touch_features.get("touch_error_std", 0),
            "paper_pop_the_bubbles_average_touch_length":
                touch_features.get("touch_average_length", 0),
            "paper_pop_the_bubbles_average_applied_force":
                touch_features.get("touch_average_applied_force", 0),
            "touch_force_available":
                touch_features.get("touch_force_available", False),
        }

        session_manager = session["session_manager"]
        session_manager.save_json("game_metrics.json",
                                  session["game_metrics"])

    # ------------------------------------------------------------------
    # calculate_behavioral_phenotypes — identical to original
    # ------------------------------------------------------------------
    def calculate_behavioral_phenotypes(self):
        popped = [r for r in self.reaction_data if r["status"] == "popped"]
        missed = [r for r in self.reaction_data if r["status"] == "missed"]
        total_bubbles = len(self.reaction_data)

        avg_reaction = (
            sum(r["reaction_time_sec"] for r in popped) / len(popped)
            if popped else 0
        )

        miss_ratio = (len(missed) / total_bubbles if total_bubbles > 0 else 0)

        reaction_times = [r["reaction_time_sec"] for r in popped]
        if len(reaction_times) > 1:
            mean_rt  = avg_reaction
            variance = sum((rt - mean_rt) ** 2
                           for rt in reaction_times) / len(reaction_times)
        else:
            variance = 0

        return {
            "attention_deficit":  round(min(avg_reaction / 3, 1), 2),
            "disengagement":      round(miss_ratio, 2),
            "motor_irregularity": round(min(variance, 1), 2),
            "responsiveness":     round(min(self.score / 20, 1), 2),
        }

    # ------------------------------------------------------------------
    # show_end_screen — identical signature and visual behaviour to original
    # ------------------------------------------------------------------
    def show_end_screen(self, screen, background_img, font_large):
        screen.blit(background_img, (0, 0))

        # Dark overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        screen.blit(overlay, (0, 0))

        info = pygame.display.Info()
        cx   = info.current_w // 2
        cy   = info.current_h // 2

        # "Time's up!" — identical text to original
        end_msg   = font_large.render("Time's up!", True, WHITE)
        score_msg = font_large.render(f"Final Score: {self.score}", True, WHITE)

        pad = 20
        bw  = max(end_msg.get_width(), score_msg.get_width()) + pad * 2
        bh  = end_msg.get_height() + score_msg.get_height() + pad * 3

        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(box, (0, 0, 0, 200), (0, 0, bw, bh), border_radius=15)
        box.blit(end_msg,
                 ((bw - end_msg.get_width()) // 2, pad))
        box.blit(score_msg,
                 ((bw - score_msg.get_width()) // 2,
                  pad * 2 + end_msg.get_height()))

        screen.blit(box, (cx - bw // 2, cy - bh // 2))
        pygame.display.flip()

        pygame.time.delay(3000)   # identical to original: 3 seconds


# ---------------------------------------------------------------------------
# show_intro — kept as a module-level function (identical to original)
# ---------------------------------------------------------------------------
def show_intro(screen, background_img, char_img,
               width, height, char_h, char_w, font_speech):

    screen.blit(background_img, (0, 0))

    padding = 20
    char_x  = padding
    char_y  = height - char_h - padding
    screen.blit(char_img, (char_x, char_y))

    text      = "Hey! Pop as many bubbles as you can!"
    text_surf = font_speech.render(text, True, (0, 0, 0))

    bubble_w = text_surf.get_width()  + padding * 2
    bubble_h = text_surf.get_height() + padding * 2
    bubble_x = char_x + char_w - 20
    bubble_y = char_y + (char_h - bubble_h) // 2

    bubble_surf = pygame.Surface((bubble_w, bubble_h), pygame.SRCALPHA)
    pygame.draw.rect(bubble_surf, (255, 255, 255, 230),
                     (0, 0, bubble_w, bubble_h), border_radius=15)
    pygame.draw.rect(bubble_surf, (0, 0, 0),
                     (0, 0, bubble_w, bubble_h), 2, border_radius=15)
    bubble_surf.blit(text_surf, (padding, padding))

    screen.blit(bubble_surf, (bubble_x, bubble_y))
    pygame.display.flip()
    pygame.time.delay(2000)