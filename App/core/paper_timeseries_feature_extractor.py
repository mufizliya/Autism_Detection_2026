import os
import csv
import math
import statistics


class PaperTimeSeriesFeatureExtractor:

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
    def zero_crossing_rate(values):

        if len(values) <= 1:
            return 0.0

        mean_value = PaperTimeSeriesFeatureExtractor.mean(
            values
        )

        centered = [
            value - mean_value
            for value in values
        ]

        crossings = 0

        for i in range(
            1,
            len(centered)
        ):

            if (
                centered[i - 1] <= 0 < centered[i]
                or
                centered[i - 1] >= 0 > centered[i]
            ):

                crossings += 1

        return crossings / max(
            len(values) - 1,
            1
        )

    @staticmethod
    def approximate_entropy(values):

        """
        Lightweight complexity approximation.

        The paper uses multiscale entropy for facial/head dynamics.
        For our prototype, this gives a time-series complexity score
        without adding heavy dependencies.
        """

        if len(values) < 5:
            return 0.0

        value_std = PaperTimeSeriesFeatureExtractor.std(
            values
        )

        zcr = PaperTimeSeriesFeatureExtractor.zero_crossing_rate(
            values
        )

        return value_std * (
            1.0 + zcr
        )

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
    def get_values(rows, key, face_only=True):

        values = []

        for row in rows:

            if face_only:

                face_detected = int(
                    PaperTimeSeriesFeatureExtractor.to_float(
                        row.get(
                            "face_detected",
                            0
                        )
                    )
                )

                if face_detected != 1:
                    continue

            values.append(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        key,
                        0
                    )
                )
            )

        return values

    @staticmethod
    def compute_facing_forward(rows):

        """
        Paper definition:
        eyes open + gaze at/near screen + face relatively steady.

        Our implementation:
        eye_open == 1
        face_detected == 1
        yaw/pitch within threshold
        head movement not too high
        """

        if len(rows) == 0:
            return 0.0

        valid_frames = 0
        forward_frames = 0

        for row in rows:

            face_detected = int(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            valid_frames += 1

            eye_open = int(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "eye_open",
                        0
                    )
                )
            )

            yaw = abs(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "yaw_proxy",
                        0
                    )
                )
            )

            pitch = abs(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "pitch_proxy",
                        0
                    )
                )
            )

            head_movement = abs(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "head_movement",
                        0
                    )
                )
            )

            if (
                eye_open == 1
                and yaw <= 0.18
                and pitch <= 0.35
                and head_movement <= 0.05
            ):

                forward_frames += 1

        if valid_frames == 0:
            return 0.0

        return forward_frames / valid_frames

    @staticmethod
    def compute_blink_rate(rows):

        if len(rows) == 0:
            return 0.0

        blink_count = 0
        previous_state = 0

        timestamps = []

        for row in rows:

            face_detected = int(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            timestamps.append(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "elapsed_time",
                        0
                    )
                )
            )

            blink_state = int(
                PaperTimeSeriesFeatureExtractor.to_float(
                    row.get(
                        "blink_state",
                        0
                    )
                )
            )

            if (
                blink_state == 1
                and previous_state == 0
            ):

                blink_count += 1

            previous_state = blink_state

        if len(timestamps) <= 1:
            return 0.0

        duration = max(
            timestamps[-1] - timestamps[0],
            1e-6
        )

        return blink_count / duration * 60.0

    @staticmethod
    def compute_head_movement(rows):

        head_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                rows,
                "head_movement"
            )
        )

        return PaperTimeSeriesFeatureExtractor.mean(
            head_values
        )

    @staticmethod
    def compute_head_complexity(rows):

        head_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                rows,
                "head_movement"
            )
        )

        return PaperTimeSeriesFeatureExtractor.approximate_entropy(
            head_values
        )

    @staticmethod
    def compute_head_acceleration(rows):

        acceleration_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                rows,
                "head_acceleration"
            )
        )

        return PaperTimeSeriesFeatureExtractor.mean(
            acceleration_values
        )

    @staticmethod
    def compute_mouth_complexity(rows):

        mouth_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                rows,
                "mouth_open"
            )
        )

        return PaperTimeSeriesFeatureExtractor.approximate_entropy(
            mouth_values
        )

    @staticmethod
    def compute_eyebrow_complexity(rows):

        eyebrow_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                rows,
                "eyebrow_signal"
            )
        )

        return PaperTimeSeriesFeatureExtractor.approximate_entropy(
            eyebrow_values
        )

    @staticmethod
    def collect_framewise_logs(session):

        session_path = session[
            "session_manager"
        ].get_session_path()

        logs = []

        for filename in os.listdir(session_path):

            if filename.endswith(
                "_framewise_log.csv"
            ):

                file_path = os.path.join(
                    session_path,
                    filename
                )

                rows = (
                    PaperTimeSeriesFeatureExtractor.read_csv_rows(
                        file_path
                    )
                )

                if len(rows) == 0:
                    continue

                stimulus_id = rows[0].get(
                    "stimulus_id",
                    filename.replace(
                        "_framewise_log.csv",
                        ""
                    )
                )

                stimulus_type = rows[0].get(
                    "stimulus_type",
                    ""
                )

                paper_category = rows[0].get(
                    "paper_category",
                    ""
                )

                logs.append(
                    {
                        "stimulus_id":
                            stimulus_id,

                        "stimulus_type":
                            stimulus_type,

                        "paper_category":
                            paper_category,

                        "file_path":
                            file_path,

                        "rows":
                            rows
                    }
                )

        return logs

    @staticmethod
    def aggregate_by_category(logs, category):

        selected_rows = []

        for log in logs:

            if log.get("paper_category") == category:

                selected_rows.extend(
                    log.get(
                        "rows",
                        []
                    )
                )

        return selected_rows

    @staticmethod
    def build(session):

        logs = (
            PaperTimeSeriesFeatureExtractor.collect_framewise_logs(
                session
            )
        )

        social_rows = (
            PaperTimeSeriesFeatureExtractor.aggregate_by_category(
                logs,
                "social"
            )
        )

        nonsocial_rows = (
            PaperTimeSeriesFeatureExtractor.aggregate_by_category(
                logs,
                "non_social"
            )
        )

        mixed_rows = (
            PaperTimeSeriesFeatureExtractor.aggregate_by_category(
                logs,
                "mixed_social_non_social"
            )
        )

        speech_rows = (
            PaperTimeSeriesFeatureExtractor.aggregate_by_category(
                logs,
                "speech_social"
            )
        )

        features = {}

        features["paper_ts_framewise_logs_found"] = len(
            logs
        )

        # -----------------------------
        # Facing forward
        # -----------------------------

        features["paper_facing_forward_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_facing_forward(
                social_rows
            ),
            4
        )

        features["paper_facing_forward_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_facing_forward(
                nonsocial_rows
            ),
            4
        )

        # -----------------------------
        # Blink rate
        # -----------------------------

        features["paper_blink_rate_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_blink_rate(
                social_rows
            ),
            4
        )

        features["paper_blink_rate_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_blink_rate(
                nonsocial_rows
            ),
            4
        )

        # -----------------------------
        # Facial dynamics complexity
        # -----------------------------

        features["paper_eyebrows_complexity_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_eyebrow_complexity(
                social_rows
            ),
            4
        )

        features["paper_eyebrows_complexity_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_eyebrow_complexity(
                nonsocial_rows
            ),
            4
        )

        features["paper_mouth_complexity_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_mouth_complexity(
                social_rows
            ),
            4
        )

        features["paper_mouth_complexity_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_mouth_complexity(
                nonsocial_rows
            ),
            4
        )

        # -----------------------------
        # Head movement
        # -----------------------------

        features["paper_head_movement_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_movement(
                social_rows
            ),
            4
        )

        features["paper_head_movement_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_movement(
                nonsocial_rows
            ),
            4
        )

        features["paper_head_movement_complexity_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_complexity(
                social_rows
            ),
            4
        )

        features["paper_head_movement_complexity_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_complexity(
                nonsocial_rows
            ),
            4
        )

        features["paper_head_movement_acceleration_social_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_acceleration(
                social_rows
            ),
            4
        )

        features["paper_head_movement_acceleration_nonsocial_movies"] = round(
            PaperTimeSeriesFeatureExtractor.compute_head_acceleration(
                nonsocial_rows
            ),
            4
        )

        # -----------------------------
        # Gaze social / speech placeholders
        # will become better once AOI gaze is implemented.
        # -----------------------------

        features["paper_gaze_percent_social"] = 0.0

        if len(mixed_rows) > 0:

            social_like = 0
            valid_gaze = 0

            for row in mixed_rows:

                face_detected = int(
                    PaperTimeSeriesFeatureExtractor.to_float(
                        row.get(
                            "face_detected",
                            0
                        )
                    )
                )

                if face_detected != 1:
                    continue

                gaze_x = (
                    PaperTimeSeriesFeatureExtractor.to_float(
                        row.get(
                            "gaze_x",
                            0
                        )
                    )
                )

                if gaze_x <= 0:
                    continue

                valid_gaze += 1

                # Placeholder schedule says social AOI is left side.
                if gaze_x < 0.5:
                    social_like += 1

            if valid_gaze > 0:

                features["paper_gaze_percent_social"] = round(
                    social_like / valid_gaze,
                    4
                )

        gaze_x_values = (
            PaperTimeSeriesFeatureExtractor.get_values(
                mixed_rows,
                "gaze_x"
            )
        )

        features["paper_gaze_silhouette_score"] = round(
            1.0 / (
                1.0
                +
                PaperTimeSeriesFeatureExtractor.std(
                    gaze_x_values
                )
            ),
            4
        )

        features["paper_attention_to_speech"] = 0.0

        if len(speech_rows) > 0:

            # Temporary placeholder:
            # use gaze stability during speech clip.
            speech_gaze_values = (
                PaperTimeSeriesFeatureExtractor.get_values(
                    speech_rows,
                    "gaze_x"
                )
            )

            features["paper_attention_to_speech"] = round(
                1.0 / (
                    1.0
                    +
                    PaperTimeSeriesFeatureExtractor.std(
                        speech_gaze_values
                    )
                ),
                4
            )

        return features