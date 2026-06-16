import math
import statistics


class BubbleTouchFeatureExtractor:

    @staticmethod
    def distance(p1, p2):

        return math.sqrt(
            (p1[0] - p2[0]) ** 2
            +
            (p1[1] - p2[1]) ** 2
        )

    @staticmethod
    def path_length(points):

        if len(points) <= 1:
            return 0.0

        total = 0.0

        for i in range(1, len(points)):

            total += BubbleTouchFeatureExtractor.distance(
                points[i - 1],
                points[i]
            )

        return total

    @staticmethod
    def mean(values):

        if len(values) == 0:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def std(values):

        if len(values) <= 1:
            return 0.0

        return statistics.stdev(values)

    @staticmethod
    def nearest_bubble_distance(
        touch_x,
        touch_y,
        bubbles
    ):

        if bubbles is None:
            return 0.0

        if len(bubbles) == 0:
            return 0.0

        distances = []

        for bubble in bubbles:

            bubble_x = bubble.get(
                "x",
                0
            )

            bubble_y = bubble.get(
                "y",
                0
            )

            distances.append(
                BubbleTouchFeatureExtractor.distance(
                    (touch_x, touch_y),
                    (bubble_x, bubble_y)
                )
            )

        return min(distances)

    @staticmethod
    def build_from_touch_events(touch_events):

        if touch_events is None:
            touch_events = []

        total_touches = len(touch_events)

        popped_count = 0
        touch_errors = []
        touch_lengths = []
        touch_durations = []
        force_values = []

        for event in touch_events:

            if event.get("hit", False):
                popped_count += 1

            touch_errors.append(
                float(
                    event.get(
                        "nearest_bubble_distance",
                        0
                    )
                )
            )

            touch_lengths.append(
                float(
                    event.get(
                        "touch_path_length",
                        0
                    )
                )
            )

            touch_durations.append(
                float(
                    event.get(
                        "duration_seconds",
                        0
                    )
                )
            )

            force_values.append(
                float(
                    event.get(
                        "pressure_value",
                        0
                    )
                )
            )

        if total_touches > 0:

            popping_rate = (
                popped_count /
                total_touches
            )

        else:

            popping_rate = 0.0

        return {
            "touch_total_count":
                total_touches,

            "touch_popped_count":
                popped_count,

            "touch_popping_rate":
                round(
                    popping_rate,
                    4
                ),

            "touch_error_std":
                round(
                    BubbleTouchFeatureExtractor.std(
                        touch_errors
                    ),
                    4
                ),

            "touch_error_mean":
                round(
                    BubbleTouchFeatureExtractor.mean(
                        touch_errors
                    ),
                    4
                ),

            "touch_average_length":
                round(
                    BubbleTouchFeatureExtractor.mean(
                        touch_lengths
                    ),
                    4
                ),

            "touch_average_duration":
                round(
                    BubbleTouchFeatureExtractor.mean(
                        touch_durations
                    ),
                    4
                ),

            "touch_average_applied_force":
                round(
                    BubbleTouchFeatureExtractor.mean(
                        force_values
                    ),
                    4
                ),

            "touch_force_available":
                False,

            "touch_force_note":
                "Laptop/Pygame mouse input does not provide real touch force. On Android/iOS/tablet, replace pressure_value with device touch pressure if available."
        }