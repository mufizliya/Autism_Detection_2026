import os
import csv
import json
import math


class GazeSilhouetteExtractor:

    MIN_VALID_GAZE_POINTS = 20

    @staticmethod
    def to_float(value, default=None):

        try:

            if value is None:
                return default

            if value == "":
                return default

            return float(value)

        except Exception:

            return default

    @staticmethod
    def load_csv_rows(path):

        if not os.path.exists(path):
            return []

        rows = []

        with open(
            path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                rows.append(row)

        return rows

    @staticmethod
    def point_inside_aoi(x, y, aoi):

        if aoi is None:
            return False

        if x is None or y is None:
            return False

        return (
            x >= float(aoi.get("x_min", 0))
            and
            x <= float(aoi.get("x_max", 1))
            and
            y >= float(aoi.get("y_min", 0))
            and
            y <= float(aoi.get("y_max", 1))
        )

    @staticmethod
    def aoi_center(aoi):

        if aoi is None:
            return None

        x_min = float(aoi.get("x_min", 0))
        y_min = float(aoi.get("y_min", 0))
        x_max = float(aoi.get("x_max", 1))
        y_max = float(aoi.get("y_max", 1))

        return (
            (x_min + x_max) / 2.0,
            (y_min + y_max) / 2.0
        )

    @staticmethod
    def distance(point_a, point_b):

        if point_a is None or point_b is None:
            return None

        return math.sqrt(
            (
                point_a[0]
                -
                point_b[0]
            ) ** 2
            +
            (
                point_a[1]
                -
                point_b[1]
            ) ** 2
        )

    @staticmethod
    def compute_aoi_preference_score(
        social_count,
        nonsocial_count
    ):

        total = (
            social_count
            +
            nonsocial_count
        )

        if total == 0:
            return 0.0

        return (
            social_count
            -
            nonsocial_count
        ) / total

    @staticmethod
    def compute_simple_separation_score(
        gaze_points,
        social_aoi,
        nonsocial_aoi
    ):

        social_center = GazeSilhouetteExtractor.aoi_center(
            social_aoi
        )

        nonsocial_center = GazeSilhouetteExtractor.aoi_center(
            nonsocial_aoi
        )

        if social_center is None or nonsocial_center is None:
            return 0.0

        if len(gaze_points) < GazeSilhouetteExtractor.MIN_VALID_GAZE_POINTS:
            return 0.0

        social_distances = []
        nonsocial_distances = []

        for point in gaze_points:

            social_distance = GazeSilhouetteExtractor.distance(
                point,
                social_center
            )

            nonsocial_distance = GazeSilhouetteExtractor.distance(
                point,
                nonsocial_center
            )

            if social_distance is not None:
                social_distances.append(
                    social_distance
                )

            if nonsocial_distance is not None:
                nonsocial_distances.append(
                    nonsocial_distance
                )

        if len(social_distances) == 0 or len(nonsocial_distances) == 0:
            return 0.0

        avg_social_distance = sum(
            social_distances
        ) / len(
            social_distances
        )

        avg_nonsocial_distance = sum(
            nonsocial_distances
        ) / len(
            nonsocial_distances
        )

        denominator = (
            avg_social_distance
            +
            avg_nonsocial_distance
        )

        if denominator == 0:
            return 0.0

        # Positive score means gaze points are closer to social AOI.
        # Negative score means gaze points are closer to nonsocial AOI.
        return (
            avg_nonsocial_distance
            -
            avg_social_distance
        ) / denominator

    @staticmethod
    def analyze_stimulus(
        session,
        stimulus
    ):

        session_manager = session.get(
            "session_manager"
        )

        session_path = session_manager.get_session_path()

        stimulus_id = stimulus.get(
            "id",
            ""
        )

        social_aoi = stimulus.get(
            "social_aoi"
        )

        nonsocial_aoi = stimulus.get(
            "nonsocial_aoi"
        )

        framewise_log_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        rows = GazeSilhouetteExtractor.load_csv_rows(
            framewise_log_path
        )

        valid_gaze_points = []

        social_look_count = 0
        nonsocial_look_count = 0
        other_look_count = 0
        face_valid_count = 0

        for row in rows:

            face_detected = GazeSilhouetteExtractor.to_float(
                row.get(
                    "face_detected",
                    0
                ),
                0
            )

            if face_detected != 1:
                continue

            gaze_x = GazeSilhouetteExtractor.to_float(
                row.get(
                    "gaze_x"
                )
            )

            gaze_y = GazeSilhouetteExtractor.to_float(
                row.get(
                    "gaze_y"
                )
            )

            if gaze_x is None or gaze_y is None:
                continue

            if gaze_x < 0 or gaze_x > 1 or gaze_y < 0 or gaze_y > 1:
                continue

            face_valid_count += 1

            valid_gaze_points.append(
                (
                    gaze_x,
                    gaze_y
                )
            )

            in_social = GazeSilhouetteExtractor.point_inside_aoi(
                gaze_x,
                gaze_y,
                social_aoi
            )

            in_nonsocial = GazeSilhouetteExtractor.point_inside_aoi(
                gaze_x,
                gaze_y,
                nonsocial_aoi
            )

            if in_social and not in_nonsocial:

                social_look_count += 1

            elif in_nonsocial and not in_social:

                nonsocial_look_count += 1

            elif in_social and in_nonsocial:

                # Some AOIs overlap slightly.
                # Assign to whichever AOI center is closer.
                social_distance = GazeSilhouetteExtractor.distance(
                    (
                        gaze_x,
                        gaze_y
                    ),
                    GazeSilhouetteExtractor.aoi_center(
                        social_aoi
                    )
                )

                nonsocial_distance = GazeSilhouetteExtractor.distance(
                    (
                        gaze_x,
                        gaze_y
                    ),
                    GazeSilhouetteExtractor.aoi_center(
                        nonsocial_aoi
                    )
                )

                if (
                    social_distance is not None
                    and
                    nonsocial_distance is not None
                    and
                    social_distance <= nonsocial_distance
                ):

                    social_look_count += 1

                else:

                    nonsocial_look_count += 1

            else:

                other_look_count += 1

        valid_count = len(
            valid_gaze_points
        )

        social_nonsocial_total = (
            social_look_count
            +
            nonsocial_look_count
        )

        if social_nonsocial_total > 0:

            percent_social = (
                social_look_count
                /
                social_nonsocial_total
            )

        else:

            percent_social = 0.0

        preference_score = GazeSilhouetteExtractor.compute_aoi_preference_score(
            social_look_count,
            nonsocial_look_count
        )

        separation_score = GazeSilhouetteExtractor.compute_simple_separation_score(
            valid_gaze_points,
            social_aoi,
            nonsocial_aoi
        )

        if valid_count < GazeSilhouetteExtractor.MIN_VALID_GAZE_POINTS:

            gaze_quality = "too_few_valid_points"

        elif social_nonsocial_total == 0:

            gaze_quality = "no_aoi_hits"

        elif social_look_count == 0 or nonsocial_look_count == 0:

            gaze_quality = "one_sided_aoi_attention"

        else:

            gaze_quality = "usable"

        return {
            "stimulus_id":
                stimulus_id,

            "valid_gaze_points":
                valid_count,

            "face_valid_gaze_points":
                face_valid_count,

            "social_look_count":
                social_look_count,

            "nonsocial_look_count":
                nonsocial_look_count,

            "other_look_count":
                other_look_count,

            "social_nonsocial_aoi_total":
                social_nonsocial_total,

            "paper_gaze_percent_social":
                round(
                    percent_social,
                    4
                ),

            "paper_gaze_silhouette_score":
                round(
                    separation_score,
                    4
                ),

            "aoi_preference_score":
                round(
                    preference_score,
                    4
                ),

            "social_aoi":
                social_aoi,

            "nonsocial_aoi":
                nonsocial_aoi,

            "gaze_quality":
                gaze_quality,

            "silhouette_method":
                "aoi_rectangle_distance_proxy",

            "silhouette_note":
                "Uses actual social/nonsocial AOI rectangles from stimulus_schedule/video_test instead of coarse left/right gaze split.",

            "framewise_log":
                framewise_log_path
        }

    @staticmethod
    def get_video_stimuli(session):

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        stimuli = []

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            if not isinstance(
                stimulus,
                dict
            ):

                continue

            social_aoi = stimulus.get(
                "social_aoi"
            )

            nonsocial_aoi = stimulus.get(
                "nonsocial_aoi"
            )

            measurements = stimulus.get(
                "measurements",
                []
            )

            # For gaze silhouette, use only mixed social-vs-nonsocial stimuli.
            if (
                social_aoi is not None
                and
                nonsocial_aoi is not None
                and
                (
                    "gaze_percent_social" in measurements
                    or
                    "gaze_silhouette" in measurements
                )
            ):

                stimuli.append(
                    stimulus
                )

        return stimuli

    @staticmethod
    def build(session):

        stimuli = GazeSilhouetteExtractor.get_video_stimuli(
            session
        )

        stimulus_results = []

        total_valid_points = 0
        weighted_social_sum = 0.0
        weighted_silhouette_sum = 0.0
        weighted_preference_sum = 0.0

        for stimulus in stimuli:

            result = GazeSilhouetteExtractor.analyze_stimulus(
                session,
                stimulus
            )

            stimulus_results.append(
                result
            )

            valid_points = result.get(
                "valid_gaze_points",
                0
            )

            total_valid_points += valid_points

            weighted_social_sum += (
                result.get(
                    "paper_gaze_percent_social",
                    0
                )
                *
                valid_points
            )

            weighted_silhouette_sum += (
                result.get(
                    "paper_gaze_silhouette_score",
                    0
                )
                *
                valid_points
            )

            weighted_preference_sum += (
                result.get(
                    "aoi_preference_score",
                    0
                )
                *
                valid_points
            )

        if total_valid_points > 0:

            overall_percent_social = (
                weighted_social_sum
                /
                total_valid_points
            )

            overall_silhouette = (
                weighted_silhouette_sum
                /
                total_valid_points
            )

            overall_preference = (
                weighted_preference_sum
                /
                total_valid_points
            )

        else:

            overall_percent_social = 0.0
            overall_silhouette = 0.0
            overall_preference = 0.0

        return {
            "paper_gaze_silhouette_score":
                round(
                    overall_silhouette,
                    4
                ),

            "paper_gaze_percent_social":
                round(
                    overall_percent_social,
                    4
                ),

            "paper_gaze_aoi_preference_score":
                round(
                    overall_preference,
                    4
                ),

            "gaze_silhouette_valid_points":
                total_valid_points,

            "gaze_silhouette_stimulus_count":
                len(
                    stimulus_results
                ),

            "gaze_silhouette_stimulus_results":
                stimulus_results
        }