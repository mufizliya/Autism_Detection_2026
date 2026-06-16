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

    TRAIN_READY_DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset_train_ready.csv"
    )

    # Missing values are not forced to 0 anymore.
    # 0 can be a real behavioral value, so missing should stay distinguishable.
    MISSING_VALUE = -999

    QUESTIONNAIRE_CONTEXT_COLUMNS = [
        "child_age",
        "child_gender_encoded",

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
        "scq_motor_behavior_severity"
    ]

    SESSION_QUALITY_COLUMNS = [
        "session_quality_score",
        "session_is_valid"
    ]

    PAPER_FEATURE_COLUMNS = [
        "paper_facing_forward_social_movies",
        "paper_facing_forward_nonsocial_movies",

        "paper_gaze_percent_social",
        "paper_gaze_silhouette_score",
        "paper_attention_to_speech",

        "paper_response_to_name_delay",
        "paper_response_to_name_proportion",

        "paper_blink_rate_social_movies",
        "paper_blink_rate_nonsocial_movies",

        "paper_eyebrows_complexity_social_movies",
        "paper_eyebrows_complexity_nonsocial_movies",

        "paper_mouth_complexity_social_movies",
        "paper_mouth_complexity_nonsocial_movies",

        "paper_head_movement_social_movies",
        "paper_head_movement_nonsocial_movies",

        "paper_head_movement_complexity_social_movies",
        "paper_head_movement_complexity_nonsocial_movies",

        "paper_head_movement_acceleration_social_movies",
        "paper_head_movement_acceleration_nonsocial_movies",

        "paper_pop_the_bubbles_popping_rate",
        "paper_pop_the_bubbles_accuracy_std",
        "paper_pop_the_bubbles_average_touch_length",
        "paper_pop_the_bubbles_average_applied_force"
    ]

    FEATURE_COLUMNS = (
        QUESTIONNAIRE_CONTEXT_COLUMNS
        +
        SESSION_QUALITY_COLUMNS
        +
        PAPER_FEATURE_COLUMNS
        +
        [
            "paper_feature_coverage_score",
            "include_for_training",
            "label"
        ]
    )

    @staticmethod
    def encode_gender(gender):

        gender = str(
            gender
        ).strip().lower()

        if gender == "male":
            return 1

        if gender == "female":
            return 2

        if gender == "other":
            return 3

        return 0

    @staticmethod
    def is_missing(value):

        if value is None:
            return True

        if value == "":
            return True

        if str(value).strip().lower() in [
            "none",
            "nan",
            "null"
        ]:
            return True

        return False

    @staticmethod
    def to_float(
        value,
        missing_value=None
    ):

        if missing_value is None:

            missing_value = FeatureCleaner.MISSING_VALUE

        try:

            if FeatureCleaner.is_missing(
                value
            ):

                return missing_value

            return float(
                value
            )

        except Exception:

            return missing_value

    @staticmethod
    def to_bool_flag(value):

        if isinstance(value, bool):

            return 1 if value else 0

        text = str(
            value
        ).strip().lower()

        if text in [
            "true",
            "1",
            "yes",
            "valid"
        ]:

            return 1

        return 0

    @staticmethod
    def get_coverage_score(row):

        possible_keys = [
            "coverage_score",
            "paper_feature_coverage_score",
            "paper_feature_coverage_coverage_score"
        ]

        for key in possible_keys:

            if key in row and not FeatureCleaner.is_missing(
                row.get(key)
            ):

                return FeatureCleaner.to_float(
                    row.get(key)
                )

        return FeatureCleaner.MISSING_VALUE

    @staticmethod
    def get_session_quality_score(row):

        possible_keys = [
            "session_quality_score",
            "quality_score"
        ]

        for key in possible_keys:

            if key in row and not FeatureCleaner.is_missing(
                row.get(key)
            ):

                return FeatureCleaner.to_float(
                    row.get(key)
                )

        return FeatureCleaner.MISSING_VALUE

    @staticmethod
    def get_session_is_valid(row):

        possible_keys = [
            "session_is_valid",
            "is_valid"
        ]

        for key in possible_keys:

            if key in row:

                return FeatureCleaner.to_bool_flag(
                    row.get(key)
                )

        return 0

    @staticmethod
    def normalize_label(label):

        label_text = str(
            label
        ).strip()

        if label_text == "":
            return ""

        if label_text.lower() in [
            "skip",
            "skipped",
            "none",
            "unknown"
        ]:

            return ""

        return label_text

    @staticmethod
    def compute_include_for_training(cleaned):

        label = FeatureCleaner.normalize_label(
            cleaned.get(
                "label",
                ""
            )
        )

        if label == "":
            return 0

        session_is_valid = int(
            FeatureCleaner.to_float(
                cleaned.get(
                    "session_is_valid",
                    0
                ),
                missing_value=0
            )
        )

        if session_is_valid != 1:
            return 0

        critical_features = [
            "paper_facing_forward_social_movies",
            "paper_facing_forward_nonsocial_movies",
            "paper_gaze_percent_social",
            "paper_attention_to_speech",
            "paper_response_to_name_delay",
            "paper_response_to_name_proportion",
            "paper_pop_the_bubbles_popping_rate"
        ]

        for feature in critical_features:

            if cleaned.get(
                feature
            ) == FeatureCleaner.MISSING_VALUE:

                return 0

        return 1

    @staticmethod
    def clean_row(row):

        cleaned = {}

        cleaned["child_age"] = FeatureCleaner.to_float(
            row.get(
                "child_age",
                ""
            )
        )

        cleaned["child_gender_encoded"] = (
            FeatureCleaner.encode_gender(
                row.get(
                    "child_gender",
                    ""
                )
            )
        )

        for column in FeatureCleaner.QUESTIONNAIRE_CONTEXT_COLUMNS:

            if column in [
                "child_age",
                "child_gender_encoded"
            ]:

                continue

            cleaned[column] = FeatureCleaner.to_float(
                row.get(
                    column,
                    ""
                )
            )

        cleaned["session_quality_score"] = (
            FeatureCleaner.get_session_quality_score(
                row
            )
        )

        cleaned["session_is_valid"] = (
            FeatureCleaner.get_session_is_valid(
                row
            )
        )

        for column in FeatureCleaner.PAPER_FEATURE_COLUMNS:

            cleaned[column] = FeatureCleaner.to_float(
                row.get(
                    column,
                    ""
                )
            )

        cleaned["paper_feature_coverage_score"] = (
            FeatureCleaner.get_coverage_score(
                row
            )
        )

        cleaned["label"] = FeatureCleaner.normalize_label(
            row.get(
                "label",
                ""
            )
        )

        cleaned["include_for_training"] = (
            FeatureCleaner.compute_include_for_training(
                cleaned
            )
        )

        final_row = {}

        for column in FeatureCleaner.FEATURE_COLUMNS:

            final_row[column] = cleaned.get(
                column,
                ""
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

            reader = csv.DictReader(
                f
            )

            for row in reader:

                cleaned_rows.append(
                    FeatureCleaner.clean_row(
                        row
                    )
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

                writer.writerow(
                    row
                )

        train_ready_rows = [
            row
            for row in cleaned_rows
            if int(
                row.get(
                    "include_for_training",
                    0
                )
            ) == 1
        ]

        with open(
            FeatureCleaner.TRAIN_READY_DATASET_FILE,
            "w",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=FeatureCleaner.FEATURE_COLUMNS
            )

            writer.writeheader()

            for row in train_ready_rows:

                writer.writerow(
                    row
                )

        print(
            "✅ Cleaned dataset saved to:",
            FeatureCleaner.CLEANED_DATASET_FILE
        )

        print(
            "Rows:",
            len(cleaned_rows)
        )

        print(
            "✅ Train-ready dataset saved to:",
            FeatureCleaner.TRAIN_READY_DATASET_FILE
        )

        print(
            "Train-ready rows:",
            len(train_ready_rows)
        )


if __name__ == "__main__":

    FeatureCleaner.clean_dataset()