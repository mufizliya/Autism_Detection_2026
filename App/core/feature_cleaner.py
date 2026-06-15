import os
import csv


class FeatureCleaner:

    DATASET_DIR = os.path.join(
        "logs",
        "dataset"
    )

    RAW_DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset.csv"
    )

    CLEANED_DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset_cleaned.csv"
    )

    DROP_COLUMNS = [
        "session_id",
        "risk_level_rule_based",
        "risk_score_rule_based",

        # Keep this for now as low confidence, but remove from ML input
        # because we already noticed it is only a proxy.
        "gaze_eye_contact_ratio",
    ]

    FEATURE_COLUMNS = [
        "child_age",
        "child_gender_encoded",

        # SCQ
        "scq_score",
        "scq_social_communication_raw",
        "scq_social_communication_severity",
        "scq_sensory_sensitivity_raw",
        "scq_sensory_sensitivity_severity",
        "scq_repetitive_behavior_raw",
        "scq_repetitive_behavior_severity",
        "scq_emotional_regulation_raw",
        "scq_emotional_regulation_severity",
        "scq_motor_behavior_raw",
        "scq_motor_behavior_severity",

        # Name response
        "name_response_time",
        "name_response_good",
        "name_response_not_good",
        "emotion_emotional_distress",
        "emotion_social_hesitation",
        "emotion_interaction_engagement",
        "emotion_emotional_responsiveness",

        # Game
        "game_score",
        "game_total_reactions",
        "game_avg_reaction_time",
        "game_min_reaction_time",
        "game_max_reaction_time",
        "game_popped_count",
        "game_missed_count",
        "game_miss_ratio",
        "game_attention_deficit",
        "game_disengagement",
        "game_motor_irregularity",
        "game_responsiveness",

        # Gaze / attention
        "gaze_face_presence_ratio",
        "gaze_blink_count",
        "gaze_blink_rate_per_min",
        "gaze_away_time_sec",
        "gaze_attention_ratio",
        "gaze_yaw_variability",
        "gaze_pitch_variability",
        "gaze_gaze_variability",

        # Facial expression
        "expression_avg_smile_score",
        "expression_baseline_smile",
        "expression_smile_threshold",
        "expression_smiling_frames",
        "expression_smile_ratio",

        # Pose
        "pose_pose_presence_ratio",
        "pose_head_variability",
        "pose_shoulder_variability",
        "pose_body_stability_score",

        # Motor
        "motor_pose_presence_ratio",
        "motor_left_arm_variability",
        "motor_right_arm_variability",
        "motor_arm_stereotypy_score",
        "motor_left_frequency_hz",
        "motor_right_frequency_hz",
        "motor_oscillation_frequency_hz",
        "motor_stereotypy_index",

        # Label stays last
        "label"
    ]

    @staticmethod
    def encode_gender(gender):

        gender = str(gender).strip().lower()

        if gender == "male":
            return 1

        if gender == "female":
            return 2

        if gender == "other":
            return 3

        return 0

    @staticmethod
    def to_float(value):

        try:
            if value is None:
                return 0

            if value == "":
                return 0

            return float(value)

        except Exception:
            return 0

    @staticmethod
    def clean_row(row):

        cleaned = {}

        cleaned["child_gender_encoded"] = (
            FeatureCleaner.encode_gender(
                row.get("child_gender", "")
            )
        )

        for column in FeatureCleaner.FEATURE_COLUMNS:

            if column == "label":

                cleaned[column] = row.get(
                    "label",
                    ""
                )

            elif column == "child_gender_encoded":

                continue

            else:

                cleaned[column] = FeatureCleaner.to_float(
                    row.get(column, 0)
                )

        final_row = {}

        for column in FeatureCleaner.FEATURE_COLUMNS:

            if column == "child_gender_encoded":

                final_row[column] = cleaned.get(
                    column,
                    0
                )

            else:

                final_row[column] = cleaned.get(
                    column,
                    ""
                    if column == "label"
                    else 0
                )

        return final_row

    @staticmethod
    def clean_dataset():

        if not os.path.exists(
            FeatureCleaner.RAW_DATASET_FILE
        ):

            print(
                "❌ Raw dataset not found:",
                FeatureCleaner.RAW_DATASET_FILE
            )

            return

        os.makedirs(
            FeatureCleaner.DATASET_DIR,
            exist_ok=True
        )

        cleaned_rows = []

        with open(
            FeatureCleaner.RAW_DATASET_FILE,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                cleaned_rows.append(
                    FeatureCleaner.clean_row(row)
                )

        with open(
            FeatureCleaner.CLEANED_DATASET_FILE,
            "w",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=FeatureCleaner.FEATURE_COLUMNS
            )

            writer.writeheader()

            for row in cleaned_rows:

                writer.writerow(row)

        print(
            "✅ Cleaned dataset saved to:",
            FeatureCleaner.CLEANED_DATASET_FILE
        )

        print(
            "Rows:",
            len(cleaned_rows)
        )


if __name__ == "__main__":

    FeatureCleaner.clean_dataset()