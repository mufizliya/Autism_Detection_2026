import os
import csv
import math


class GazeSilhouetteExtractor:

    @staticmethod
    def to_float(value):

        try:

            if value is None:
                return 0.0

            if value == "":
                return 0.0

            return float(value)

        except Exception:

            return 0.0

    @staticmethod
    def read_csv_rows(file_path):

        if not os.path.exists(file_path):
            return []

        rows = []

        with open(
            file_path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                rows.append(row)

        return rows

    @staticmethod
    def get_session_path(session):

        return session[
            "session_manager"
        ].get_session_path()

    @staticmethod
    def find_mixed_stimuli(session):

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        mixed_stimuli = []

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            if stimulus.get("type") == "mixed_social_nonsocial_movie":

                mixed_stimuli.append(
                    stimulus
                )

        return mixed_stimuli

    @staticmethod
    def find_framewise_log(
        session,
        stimulus_id
    ):

        session_path = (
            GazeSilhouetteExtractor.get_session_path(
                session
            )
        )

        expected_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        if os.path.exists(expected_path):
            return expected_path

        for filename in os.listdir(session_path):

            if (
                filename.startswith(stimulus_id)
                and
                filename.endswith("_framewise_log.csv")
            ):

                return os.path.join(
                    session_path,
                    filename
                )

        return None

    @staticmethod
    def extract_gaze_points(rows):

        points = []

        for row in rows:

            face_detected = int(
                GazeSilhouetteExtractor.to_float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            eye_open = int(
                GazeSilhouetteExtractor.to_float(
                    row.get(
                        "eye_open",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            if eye_open != 1:
                continue

            gaze_x = GazeSilhouetteExtractor.to_float(
                row.get(
                    "gaze_x",
                    0
                )
            )

            gaze_y = GazeSilhouetteExtractor.to_float(
                row.get(
                    "gaze_y",
                    0
                )
            )

            if gaze_x <= 0 or gaze_y <= 0:
                continue

            if gaze_x > 1 or gaze_y > 1:
                continue

            points.append(
                [
                    gaze_x,
                    gaze_y
                ]
            )

        return points

    @staticmethod
    def basic_left_right_counts(points):

        left_count = 0
        right_count = 0

        for point in points:

            gaze_x = point[0]

            if gaze_x < 0.5:
                left_count += 1
            else:
                right_count += 1

        return left_count, right_count

    @staticmethod
    def fallback_separation_score(points, labels):

        if len(points) < 4:
            return 0.0

        cluster_0 = [
            points[i]
            for i in range(len(points))
            if labels[i] == 0
        ]

        cluster_1 = [
            points[i]
            for i in range(len(points))
            if labels[i] == 1
        ]

        if len(cluster_0) < 2 or len(cluster_1) < 2:
            return 0.0

        def mean_point(items):

            return [
                sum(p[0] for p in items) / len(items),
                sum(p[1] for p in items) / len(items)
            ]

        def distance(p1, p2):

            return math.sqrt(
                (p1[0] - p2[0]) ** 2
                +
                (p1[1] - p2[1]) ** 2
            )

        center_0 = mean_point(
            cluster_0
        )

        center_1 = mean_point(
            cluster_1
        )

        center_distance = distance(
            center_0,
            center_1
        )

        spreads = []

        for p in cluster_0:

            spreads.append(
                distance(
                    p,
                    center_0
                )
            )

        for p in cluster_1:

            spreads.append(
                distance(
                    p,
                    center_1
                )
            )

        avg_spread = (
            sum(spreads) / len(spreads)
            if len(spreads) > 0
            else 0
        )

        score = center_distance / (
            center_distance
            +
            avg_spread
            +
            1e-6
        )

        return max(
            0.0,
            min(
                1.0,
                score
            )
        )

    @staticmethod
    def compute_kmeans_silhouette(points):

        if len(points) < 8:

            return {
                "score":
                    0.0,

                "labels":
                    [],

                "method":
                    "not_enough_points",

                "note":
                    "Need more valid gaze points for reliable clustering."
            }

        try:

            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score

            kmeans = KMeans(
                n_clusters=2,
                random_state=42,
                n_init=10
            )

            labels = kmeans.fit_predict(
                points
            )

            unique_labels = set(
                labels
            )

            if len(unique_labels) < 2:

                return {
                    "score":
                        0.0,

                    "labels":
                        labels.tolist(),

                    "method":
                        "kmeans_failed_one_cluster",

                    "note":
                        "KMeans produced only one usable cluster."
                }

            raw_score = silhouette_score(
                points,
                labels
            )

            normalized_score = (
                raw_score + 1
            ) / 2

            return {
                "score":
                    round(
                        max(
                            0.0,
                            min(
                                1.0,
                                normalized_score
                            )
                        ),
                        4
                    ),

                "labels":
                    labels.tolist(),

                "method":
                    "kmeans_silhouette",

                "note":
                    "Silhouette computed using KMeans clusters over frame-wise gaze points."
            }

        except Exception as e:

            # Fallback: split using median x, then compute separation score.
            xs = [
                point[0]
                for point in points
            ]

            sorted_xs = sorted(
                xs
            )

            median_x = sorted_xs[
                len(sorted_xs) // 2
            ]

            labels = [
                0 if point[0] < median_x else 1
                for point in points
            ]

            score = (
                GazeSilhouetteExtractor.fallback_separation_score(
                    points,
                    labels
                )
            )

            return {
                "score":
                    round(
                        score,
                        4
                    ),

                "labels":
                    labels,

                "method":
                    "fallback_median_split",

                "note":
                    f"sklearn unavailable or failed: {e}"
            }

    @staticmethod
    def compute_for_stimulus(
        rows,
        stimulus
    ):

        points = (
            GazeSilhouetteExtractor.extract_gaze_points(
                rows
            )
        )

        valid_points = len(
            points
        )

        left_count, right_count = (
            GazeSilhouetteExtractor.basic_left_right_counts(
                points
            )
        )

        if valid_points > 0:

            left_ratio = left_count / valid_points
            right_ratio = right_count / valid_points

        else:

            left_ratio = 0.0
            right_ratio = 0.0

        social_aoi = stimulus.get(
            "social_aoi",
            {}
        )

        social_side = social_aoi.get(
            "side",
            "left"
        )

        if social_side == "left":

            gaze_percent_social = left_ratio

        elif social_side == "right":

            gaze_percent_social = right_ratio

        else:

            gaze_percent_social = 0.0

        silhouette_result = (
            GazeSilhouetteExtractor.compute_kmeans_silhouette(
                points
            )
        )

        gaze_quality = "usable"

        if valid_points < 30:

            gaze_quality = "weak_low_valid_points"

        if left_count == 0 or right_count == 0:

            gaze_quality = "weak_one_sided_gaze"

        return {
            "stimulus_id":
                stimulus.get(
                    "id",
                    ""
                ),

            "valid_gaze_points":
                valid_points,

            "left_gaze_count":
                left_count,

            "right_gaze_count":
                right_count,

            "left_gaze_ratio":
                round(
                    left_ratio,
                    4
                ),

            "right_gaze_ratio":
                round(
                    right_ratio,
                    4
                ),

            "social_aoi_side":
                social_side,

            "paper_gaze_percent_social":
                round(
                    gaze_percent_social,
                    4
                ),

            "paper_gaze_silhouette_score":
                silhouette_result.get(
                    "score",
                    0
                ),

            "silhouette_method":
                silhouette_result.get(
                    "method",
                    ""
                ),

            "silhouette_note":
                silhouette_result.get(
                    "note",
                    ""
                ),

            "gaze_quality":
                gaze_quality
        }

    @staticmethod
    def build(session):

        mixed_stimuli = (
            GazeSilhouetteExtractor.find_mixed_stimuli(
                session
            )
        )

        stimulus_results = []

        total_valid_points = 0
        weighted_silhouette_sum = 0.0
        weighted_social_sum = 0.0

        for stimulus in mixed_stimuli:

            stimulus_id = stimulus.get(
                "id",
                ""
            )

            log_path = (
                GazeSilhouetteExtractor.find_framewise_log(
                    session,
                    stimulus_id
                )
            )

            if log_path is None:

                stimulus_results.append(
                    {
                        "stimulus_id":
                            stimulus_id,

                        "error":
                            "framewise_log_not_found",

                        "paper_gaze_silhouette_score":
                            0,

                        "paper_gaze_percent_social":
                            0,

                        "gaze_quality":
                            "missing_log"
                    }
                )

                continue

            rows = (
                GazeSilhouetteExtractor.read_csv_rows(
                    log_path
                )
            )

            result = (
                GazeSilhouetteExtractor.compute_for_stimulus(
                    rows,
                    stimulus
                )
            )

            result["framewise_log"] = log_path

            stimulus_results.append(
                result
            )

            valid_points = result.get(
                "valid_gaze_points",
                0
            )

            total_valid_points += valid_points

            weighted_silhouette_sum += (
                result.get(
                    "paper_gaze_silhouette_score",
                    0
                )
                *
                valid_points
            )

            weighted_social_sum += (
                result.get(
                    "paper_gaze_percent_social",
                    0
                )
                *
                valid_points
            )

        if total_valid_points > 0:

            overall_silhouette = (
                weighted_silhouette_sum /
                total_valid_points
            )

            overall_gaze_percent_social = (
                weighted_social_sum /
                total_valid_points
            )

        else:

            overall_silhouette = 0.0
            overall_gaze_percent_social = 0.0

        return {
            "paper_gaze_silhouette_score":
                round(
                    overall_silhouette,
                    4
                ),

            "paper_gaze_percent_social":
                round(
                    overall_gaze_percent_social,
                    4
                ),

            "gaze_silhouette_valid_points":
                total_valid_points,

            "gaze_silhouette_stimulus_count":
                len(
                    mixed_stimuli
                ),

            "gaze_silhouette_stimulus_results":
                stimulus_results
        }