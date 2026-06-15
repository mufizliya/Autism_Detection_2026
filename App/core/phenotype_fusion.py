class PhenotypeFusion:

    @staticmethod
    def safe_get(data, key, default=0):

        if data is None:
            return default

        return data.get(key, default)

    @staticmethod
    def extract_scq_phenotypes(questionnaire):

        features = {}

        if questionnaire is None:
            return features

        features["scq_score"] = questionnaire.get(
            "score",
            0
        )

        features["scq_outcome"] = questionnaire.get(
            "outcome",
            "Unknown"
        )

        phenotypes = questionnaire.get(
            "phenotypes",
            {}
        )

        for phenotype_name, phenotype_data in phenotypes.items():

            if isinstance(phenotype_data, dict):

                features[
                    f"scq_{phenotype_name}_raw"
                ] = phenotype_data.get(
                    "raw_score",
                    0
                )

                features[
                    f"scq_{phenotype_name}_severity"
                ] = phenotype_data.get(
                    "severity",
                    0
                )

            else:

                features[
                    f"scq_{phenotype_name}_raw"
                ] = phenotype_data

        return features

    @staticmethod
    def extract_name_response_features(name_response):

        features = {}

        if name_response is None:
            return features

        features["name_response_time"] = (
            name_response.get(
                "response_time",
                0
            )
        )

        response = name_response.get(
            "response",
            "unknown"
        )

        features["name_response_good"] = (
            1 if response == "good" else 0
        )

        features["name_response_not_good"] = (
            1 if response == "not_good" else 0
        )

        emotional_phenotypes = name_response.get(
            "emotional_phenotypes",
            {}
        )

        for key, value in emotional_phenotypes.items():

            features[
                f"emotion_{key}"
            ] = value

        return features

    @staticmethod
    def extract_game_features(game_metrics):

        features = {}

        if game_metrics is None:
            return features

        features["game_score"] = game_metrics.get(
            "score",
            0
        )

        features["game_total_reactions"] = (
            game_metrics.get(
                "total_reactions",
                0
            )
        )

        reaction_data = game_metrics.get(
            "reaction_data",
            []
        )

        popped = [
            r for r in reaction_data
            if r.get("status") == "popped"
        ]

        missed = [
            r for r in reaction_data
            if r.get("status") == "missed"
        ]

        reaction_times = [
            r.get("reaction_time_sec")
            for r in popped
            if r.get("reaction_time_sec") is not None
        ]

        if reaction_times:

            features["game_avg_reaction_time"] = (
                sum(reaction_times) /
                len(reaction_times)
            )

            features["game_min_reaction_time"] = (
                min(reaction_times)
            )

            features["game_max_reaction_time"] = (
                max(reaction_times)
            )

        else:

            features["game_avg_reaction_time"] = 0
            features["game_min_reaction_time"] = 0
            features["game_max_reaction_time"] = 0

        total = len(reaction_data)

        features["game_popped_count"] = len(popped)

        features["game_missed_count"] = len(missed)

        features["game_miss_ratio"] = (
            len(missed) / total
            if total > 0
            else 0
        )

        behavioral_phenotypes = game_metrics.get(
            "behavioral_phenotypes",
            {}
        )

        for key, value in behavioral_phenotypes.items():

            features[
                f"game_{key}"
            ] = value

        return features

    @staticmethod
    def extract_gaze_features(gaze_metrics):

        features = {}

        if gaze_metrics is None:
            return features

        keys = [
            "face_presence_ratio",
            "blink_count",
            "blink_rate_per_min",
            "away_time_sec",
            "attention_ratio",
            "yaw_variability",
            "pitch_variability",
            "eye_contact_ratio",
            "gaze_variability"
        ]

        for key in keys:

            features[
                f"gaze_{key}"
            ] = gaze_metrics.get(
                key,
                0
            )

        return features

    @staticmethod
    def extract_expression_features(expression_metrics):

        features = {}

        if expression_metrics is None:
            return features

        keys = [
            "avg_smile_score",
            "baseline_smile",
            "smile_threshold",
            "smiling_frames",
            "smile_ratio"
        ]

        for key in keys:

            features[
                f"expression_{key}"
            ] = expression_metrics.get(
                key,
                0
            )

        return features

    @staticmethod
    def extract_pose_features(pose_metrics):

        features = {}

        if pose_metrics is None:
            return features

        keys = [
            "pose_presence_ratio",
            "head_variability",
            "shoulder_variability",
            "body_stability_score"
        ]

        for key in keys:

            features[
                f"pose_{key}"
            ] = pose_metrics.get(
                key,
                0
            )

        return features

    @staticmethod
    def extract_motor_features(motor_metrics):

        features = {}

        if motor_metrics is None:
            return features

        keys = [
            "pose_presence_ratio",
            "left_arm_variability",
            "right_arm_variability",
            "arm_stereotypy_score",
            "left_frequency_hz",
            "right_frequency_hz",
            "oscillation_frequency_hz",
            "stereotypy_index"
        ]

        for key in keys:

            features[
                f"motor_{key}"
            ] = motor_metrics.get(
                key,
                0
            )

        return features

    @staticmethod
    def build(session):

        phenotype_vector = {}

        phenotype_vector.update(
            PhenotypeFusion.extract_scq_phenotypes(
                session.get("questionnaire")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_name_response_features(
                session.get("name_response")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_game_features(
                session.get("game_metrics")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_gaze_features(
                session.get("gaze_metrics")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_expression_features(
                session.get("facial_expression_metrics")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_pose_features(
                session.get("pose_metrics")
            )
        )

        phenotype_vector.update(
            PhenotypeFusion.extract_motor_features(
                session.get("motor_metrics")
            )
        )

        return phenotype_vector