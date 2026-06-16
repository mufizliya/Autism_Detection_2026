import pygame
import time
import random
import os
from datetime import datetime

from core.bubble_touch_feature_extractor import BubbleTouchFeatureExtractor
from core.project_paths import app_path

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

BUBBLE_COLORS = [
    (135, 206, 250),
    (100, 149, 237),
    (173, 216, 230),
    (176, 224, 230)
]


class Bubble:

    def __init__(
        self,
        width,
        height,
        min_radius,
        max_radius
    ):

        self.radius = random.randint(
            min_radius,
            max_radius
        )

        self.color = random.choice(
            BUBBLE_COLORS
        )

        self.x = random.randint(
            self.radius,
            width - self.radius
        )

        self.y = random.randint(
            self.radius,
            height - self.radius
        )

        self.appear_time = time.time()

    def draw(
        self,
        screen
    ):

        elapsed = time.time() - self.appear_time

        alpha = int(
            255 * min(
                elapsed / 0.5,
                1
            )
        )

        surf = pygame.Surface(
            (
                self.radius * 2,
                self.radius * 2
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            surf,
            (
                *self.color,
                alpha
            ),
            (
                self.radius,
                self.radius
            ),
            self.radius
        )

        shadow = pygame.Surface(
            (
                self.radius * 2,
                self.radius * 2
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            shadow,
            (
                0,
                0,
                0,
                int(alpha * 0.3)
            ),
            (
                self.radius + 2,
                self.radius + 2
            ),
            self.radius
        )

        screen.blit(
            shadow,
            (
                self.x - self.radius,
                self.y - self.radius
            )
        )

        screen.blit(
            surf,
            (
                self.x - self.radius,
                self.y - self.radius
            )
        )

    def is_clicked(
        self,
        pos
    ):

        return (
            (
                self.x - pos[0]
            ) ** 2
            +
            (
                self.y - pos[1]
            ) ** 2
        ) ** 0.5 <= self.radius


def show_intro(
    screen,
    background_img,
    char_img,
    width,
    height,
    char_h,
    char_w,
    font_speech
):

    screen.blit(
        background_img,
        (0, 0)
    )

    padding = 20

    char_x = padding
    char_y = height - char_h - padding

    screen.blit(
        char_img,
        (
            char_x,
            char_y
        )
    )

    text = "Hey! Pop as many bubbles as you can!"

    text_surf = font_speech.render(
        text,
        True,
        (0, 0, 0)
    )

    bubble_w = (
        text_surf.get_width()
        +
        padding * 2
    )

    bubble_h = (
        text_surf.get_height()
        +
        padding * 2
    )

    bubble_x = char_x + char_w - 20

    bubble_y = (
        char_y
        +
        (
            char_h - bubble_h
        ) // 2
    )

    bubble = pygame.Surface(
        (
            bubble_w,
            bubble_h
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        bubble,
        (
            255,
            255,
            255,
            230
        ),
        (
            0,
            0,
            bubble_w,
            bubble_h
        ),
        border_radius=15
    )

    pygame.draw.rect(
        bubble,
        (0, 0, 0),
        (
            0,
            0,
            bubble_w,
            bubble_h
        ),
        2,
        border_radius=15
    )

    bubble.blit(
        text_surf,
        (
            padding,
            padding
        )
    )

    screen.blit(
        bubble,
        (
            bubble_x,
            bubble_y
        )
    )

    pygame.display.flip()

    pygame.time.delay(
        2000
    )


class BubbleGameModule:

    def __init__(self):

        self.reaction_data = []
        self.score = 0

        # New paper-style touch logs
        self.touch_events = []
        self.current_touch_event = None

    def start_touch_event(
        self,
        x,
        y
    ):

        self.current_touch_event = {
            "touch_id":
                len(self.touch_events) + 1,

            "start_time":
                time.time(),

            "end_time":
                None,

            "duration_seconds":
                0,

            "start_x":
                x,

            "start_y":
                y,

            "end_x":
                x,

            "end_y":
                y,

            "path_points":
                [
                    [
                        x,
                        y
                    ]
                ],

            "touch_path_length":
                0,

            "nearest_bubble_distance":
                0,

            "hit":
                False,

            # Desktop mouse has no force.
            # Android/iOS can later replace this with pressure.
            "pressure_value":
                0
        }

    def update_touch_event(
        self,
        x,
        y
    ):

        if self.current_touch_event is None:
            return

        self.current_touch_event["path_points"].append(
            [
                x,
                y
            ]
        )

        self.current_touch_event["end_x"] = x
        self.current_touch_event["end_y"] = y

    def finish_touch_event(
        self,
        x,
        y,
        hit,
        nearest_bubble_distance
    ):

        if self.current_touch_event is None:
            return

        self.current_touch_event["end_time"] = time.time()

        self.current_touch_event["duration_seconds"] = round(
            self.current_touch_event["end_time"]
            -
            self.current_touch_event["start_time"],
            4
        )

        self.current_touch_event["end_x"] = x
        self.current_touch_event["end_y"] = y

        self.current_touch_event["path_points"].append(
            [
                x,
                y
            ]
        )

        self.current_touch_event["touch_path_length"] = round(
            BubbleTouchFeatureExtractor.path_length(
                self.current_touch_event["path_points"]
            ),
            4
        )

        self.current_touch_event["nearest_bubble_distance"] = round(
            nearest_bubble_distance,
            4
        )

        self.current_touch_event["hit"] = hit

        self.current_touch_event["pressure_value"] = 0

        self.touch_events.append(
            self.current_touch_event
        )

        self.current_touch_event = None

    def get_position_from_event(
        self,
        event,
        width,
        height
    ):

        if event.type in [
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION
        ]:

            return pygame.mouse.get_pos()

        if event.type in [
            pygame.FINGERDOWN,
            pygame.FINGERUP,
            pygame.FINGERMOTION
        ]:

            return (
                int(event.x * width),
                int(event.y * height)
            )

        return (
            0,
            0
        )

    def run(
        self,
        session
    ):

        self.reaction_data = []
        self.score = 0
        self.touch_events = []
        self.current_touch_event = None

        audio_enabled = True

        try:

            pygame.mixer.pre_init(
                44100,
                -16,
                2,
                512
            )

            pygame.init()

            pygame.mixer.init()

            print(
                "Mixer initialized:",
                pygame.mixer.get_init()
            )

        except Exception as e:

            print(
                f"Audio init failed: {e}"
            )

            audio_enabled = False

        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h

        screen = pygame.display.set_mode(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.FULLSCREEN
        )

        pygame.display.set_caption(
            "Bubble Pop Game"
        )

        background_img = pygame.image.load(
            app_path(
                "src",
                "GAMEBG.jpg"
            )
        )

        background_img = pygame.transform.scale(
            background_img,
            (
                WIDTH,
                HEIGHT
            )
        )

        char_img = pygame.image.load(
            app_path(
                "src",
                "character.png"
            )
        )

        char_w = WIDTH // 2.5

        char_h = int(
            char_img.get_height()
            *
            (
                char_w
                /
                char_img.get_width()
            )
        )

        char_img = pygame.transform.scale(
            char_img,
            (
                char_w,
                char_h
            )
        )

        pop_sound = None

        if audio_enabled:

            try:

                pop_sound = pygame.mixer.Sound(
                    app_path(
                        "src",
                        "pop.wav"
                    )
                )

                print(
                    "Pop sound loaded."
                )

            except Exception as e:

                print(
                    f"Sound load failed: {e}"
                )

        pygame.font.init()

        font_large = pygame.font.SysFont(
            "Arial",
            36,
            bold=True
        )

        font_speech = pygame.font.SysFont(
            "Arial",
            28
        )

        bubbles = []

        clock = pygame.time.Clock()

        game_duration = 35
        bubble_interval = 1500
        bubble_lifespan = 3

        max_radius = 80
        min_radius = 50

        show_intro(
            screen,
            background_img,
            char_img,
            WIDTH,
            HEIGHT,
            char_h,
            char_w,
            font_speech
        )

        game_start_time = time.time()

        running = True

        last_bubble_time = pygame.time.get_ticks()

        while running:

            if time.time() - game_start_time > game_duration:
                break

            screen.blit(
                background_img,
                (
                    0,
                    0
                )
            )

            now_sec = time.time()

            if (
                pygame.time.get_ticks()
                -
                last_bubble_time
                >
                bubble_interval
            ):

                bubbles.append(
                    Bubble(
                        WIDTH,
                        HEIGHT,
                        min_radius,
                        max_radius
                    )
                )

                last_bubble_time = pygame.time.get_ticks()

            for bubble in bubbles[:]:

                bubble.draw(
                    screen
                )

                if now_sec - bubble.appear_time > bubble_lifespan:

                    self.reaction_data.append(
                        {
                            "x":
                                bubble.x,

                            "y":
                                bubble.y,

                            "reaction_time_sec":
                                None,

                            "timestamp":
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),

                            "status":
                                "missed"
                        }
                    )

                    bubbles.remove(
                        bubble
                    )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                if (
                    event.type == pygame.KEYDOWN
                    and
                    event.key == pygame.K_ESCAPE
                ):

                    running = False

                if event.type in [
                    pygame.MOUSEBUTTONDOWN,
                    pygame.FINGERDOWN
                ]:

                    x, y = self.get_position_from_event(
                        event,
                        WIDTH,
                        HEIGHT
                    )

                    self.start_touch_event(
                        x,
                        y
                    )

                    active_bubbles_for_distance = []

                    for bubble in bubbles:

                        active_bubbles_for_distance.append(
                            {
                                "x":
                                    bubble.x,

                                "y":
                                    bubble.y
                            }
                        )

                    nearest_bubble_distance = (
                        BubbleTouchFeatureExtractor.nearest_bubble_distance(
                            x,
                            y,
                            active_bubbles_for_distance
                        )
                    )

                    hit = False

                    for bubble in bubbles[:]:

                        if bubble.is_clicked(
                            (
                                x,
                                y
                            )
                        ):

                            hit = True

                            rt = now_sec - bubble.appear_time

                            self.reaction_data.append(
                                {
                                    "x":
                                        bubble.x,

                                    "y":
                                        bubble.y,

                                    "reaction_time_sec":
                                        round(
                                            rt,
                                            2
                                        ),

                                    "timestamp":
                                        datetime.now().strftime(
                                            "%Y-%m-%d %H:%M:%S"
                                        ),

                                    "status":
                                        "popped"
                                }
                            )

                            self.score += 1

                            if pop_sound:

                                try:

                                    pop_sound.play()

                                except Exception as e:

                                    print(
                                        f"Sound play failed: {e}"
                                    )

                            bubbles.remove(
                                bubble
                            )

                            break

                    self.finish_touch_event(
                        x,
                        y,
                        hit,
                        nearest_bubble_distance
                    )

                if event.type in [
                    pygame.MOUSEMOTION,
                    pygame.FINGERMOTION
                ]:

                    x, y = self.get_position_from_event(
                        event,
                        WIDTH,
                        HEIGHT
                    )

                    self.update_touch_event(
                        x,
                        y
                    )

                if event.type in [
                    pygame.MOUSEBUTTONUP,
                    pygame.FINGERUP
                ]:

                    x, y = self.get_position_from_event(
                        event,
                        WIDTH,
                        HEIGHT
                    )

                    self.update_touch_event(
                        x,
                        y
                    )

            score_surf = font_large.render(
                f"Score: {self.score}",
                True,
                (
                    255,
                    255,
                    255
                )
            )

            box = pygame.Surface(
                (
                    score_surf.get_width() + 20,
                    score_surf.get_height() + 10
                ),
                pygame.SRCALPHA
            )

            pygame.draw.rect(
                box,
                (
                    0,
                    0,
                    0,
                    150
                ),
                box.get_rect(),
                border_radius=10
            )

            box.blit(
                score_surf,
                (
                    10,
                    5
                )
            )

            screen.blit(
                box,
                (
                    10,
                    10
                )
            )

            pygame.display.flip()

            clock.tick(
                60
            )

        self.show_end_screen(
            screen,
            background_img,
            font_large
        )

        pygame.quit()

        behavioral_phenotypes = (
            self.calculate_behavioral_phenotypes()
        )

        touch_features = (
            BubbleTouchFeatureExtractor.build_from_touch_events(
                self.touch_events
            )
        )

        session["game_metrics"] = {
            "score":
                self.score,

            "total_reactions":
                len(self.reaction_data),

            "reaction_data":
                self.reaction_data,

            "behavioral_phenotypes":
                behavioral_phenotypes,

            # New paper-style touch logs
            "touch_events":
                self.touch_events,

            "touch_features":
                touch_features,

            "paper_pop_the_bubbles_popping_rate":
                touch_features.get(
                    "touch_popping_rate",
                    0
                ),

            "paper_pop_the_bubbles_accuracy_std":
                touch_features.get(
                    "touch_error_std",
                    0
                ),

            "paper_pop_the_bubbles_average_touch_length":
                touch_features.get(
                    "touch_average_length",
                    0
                ),

            "paper_pop_the_bubbles_average_applied_force":
                touch_features.get(
                    "touch_average_applied_force",
                    0
                ),

            "touch_force_available":
                touch_features.get(
                    "touch_force_available",
                    False
                )
        }

        session_manager = session["session_manager"]

        session_manager.save_json(
            "game_metrics.json",
            session["game_metrics"]
        )

    def calculate_behavioral_phenotypes(self):

        popped = [
            r for r in self.reaction_data
            if r["status"] == "popped"
        ]

        missed = [
            r for r in self.reaction_data
            if r["status"] == "missed"
        ]

        total_bubbles = len(
            self.reaction_data
        )

        if len(popped) > 0:

            avg_reaction = sum(
                r["reaction_time_sec"]
                for r in popped
            ) / len(popped)

        else:

            avg_reaction = 0

        miss_ratio = (
            len(missed) / total_bubbles
            if total_bubbles > 0
            else 0
        )

        reaction_times = [
            r["reaction_time_sec"]
            for r in popped
        ]

        if len(reaction_times) > 1:

            mean_rt = avg_reaction

            variance = sum(
                (
                    rt - mean_rt
                ) ** 2
                for rt in reaction_times
            ) / len(reaction_times)

        else:

            variance = 0

        phenotypes = {
            "attention_deficit":
                round(
                    min(
                        avg_reaction / 3,
                        1
                    ),
                    2
                ),

            "disengagement":
                round(
                    miss_ratio,
                    2
                ),

            "motor_irregularity":
                round(
                    min(
                        variance,
                        1
                    ),
                    2
                ),

            "responsiveness":
                round(
                    min(
                        self.score / 20,
                        1
                    ),
                    2
                )
        }

        return phenotypes

    def show_end_screen(
        self,
        screen,
        background_img,
        font_large
    ):

        screen.blit(
            background_img,
            (
                0,
                0
            )
        )

        end_msg = font_large.render(
            "Time's up!",
            True,
            (
                255,
                255,
                255
            )
        )

        score_msg = font_large.render(
            f"Final Score: {self.score}",
            True,
            (
                255,
                255,
                255
            )
        )

        pad = 20

        bw = max(
            end_msg.get_width(),
            score_msg.get_width()
        ) + pad * 2

        bh = (
            end_msg.get_height()
            +
            score_msg.get_height()
            +
            pad * 3
        )

        info = pygame.display.Info()

        bx = (
            info.current_w - bw
        ) // 2

        by = (
            info.current_h - bh
        ) // 2

        box_e = pygame.Surface(
            (
                bw,
                bh
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            box_e,
            (
                0,
                0,
                0,
                200
            ),
            (
                0,
                0,
                bw,
                bh
            ),
            border_radius=15
        )

        box_e.blit(
            end_msg,
            (
                (
                    bw - end_msg.get_width()
                ) // 2,
                pad
            )
        )

        box_e.blit(
            score_msg,
            (
                (
                    bw - score_msg.get_width()
                ) // 2,
                pad * 2 + end_msg.get_height()
            )
        )

        screen.blit(
            box_e,
            (
                bx,
                by
            )
        )

        pygame.display.flip()

        pygame.time.delay(
            3000
        )