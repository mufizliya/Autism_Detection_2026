class VideoPhenotypeExtractor:

    @staticmethod
    def safe_get(data, key, default=0):

        if data is None:
            return default

        value = data.get(
            key,
            default
        )

        if value is None:
            return default

        return value

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
    def get_video_block(video_test, block_name):

        block = video_test.get(
            block_name,
            {}
        )

        if block is None:
            return {}

        return block

    @staticmethod
    def extract_block_features(prefix, block):

        features = {}

        video_metrics = block.get(
            "video_metrics",
            {}
        )

        gaze_metrics = block.get(
            "gaze_metrics",
            {}
        )

        expression_metrics = block.get(
            "facial_expression_metrics",
            {}
        )

        pose_metrics = block.get(
            "pose_metrics",
            {}
        )

        motor_metrics = block.get(
            "motor_metrics",
            {}
        )

        features[f"{prefix}_video_duration"] = (
            VideoPhenotypeExtractor.to_float(
                video_metrics.get(
                    "duration_seconds",
                    0
                )
            )
        )

        features[f"{prefix}_video_completed"] = (
            1
            if video_metrics.get("completed", False)
            else 0
        )

        # Paper-aligned proxy:
        # facing forward during movie ≈ attention_ratio from gaze tracker
        features[f"{prefix}_facing_forward_proxy"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "attention_ratio",
                    0
                )
            )
        )

        features[f"{prefix}_face_presence_ratio"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "face_presence_ratio",
                    0
                )
            )
        )

        features[f"{prefix}_blink_count"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "blink_count",
                    0
                )
            )
        )

        features[f"{prefix}_blink_rate_per_min"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "blink_rate_per_min",
                    0
                )
            )
        )

        features[f"{prefix}_away_time_sec"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "away_time_sec",
                    0
                )
            )
        )

        features[f"{prefix}_yaw_variability"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "yaw_variability",
                    0
                )
            )
        )

        features[f"{prefix}_pitch_variability"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "pitch_variability",
                    0
                )
            )
        )

        features[f"{prefix}_gaze_variability"] = (
            VideoPhenotypeExtractor.to_float(
                gaze_metrics.get(
                    "gaze_variability",
                    0
                )
            )
        )

        # Paper-aligned proxy:
        # mouth/facial dynamics ≈ smile/facial expression response
        features[f"{prefix}_avg_smile_score"] = (
            VideoPhenotypeExtractor.to_float(
                expression_metrics.get(
                    "avg_smile_score",
                    0
                )
            )
        )

        features[f"{prefix}_smile_ratio"] = (
            VideoPhenotypeExtractor.to_float(
                expression_metrics.get(
                    "smile_ratio",
                    0
                )
            )
        )

        features[f"{prefix}_smiling_frames"] = (
            VideoPhenotypeExtractor.to_float(
                expression_metrics.get(
                    "smiling_frames",
                    0
                )
            )
        )

        # Paper-aligned proxy:
        # head movement / body movement during movie
        features[f"{prefix}_pose_presence_ratio"] = (
            VideoPhenotypeExtractor.to_float(
                pose_metrics.get(
                    "pose_presence_ratio",
                    0
                )
            )
        )

        features[f"{prefix}_head_variability"] = (
            VideoPhenotypeExtractor.to_float(
                pose_metrics.get(
                    "head_variability",
                    0
                )
            )
        )

        features[f"{prefix}_shoulder_variability"] = (
            VideoPhenotypeExtractor.to_float(
                pose_metrics.get(
                    "shoulder_variability",
                    0
                )
            )
        )

        features[f"{prefix}_body_stability_score"] = (
            VideoPhenotypeExtractor.to_float(
                pose_metrics.get(
                    "body_stability_score",
                    0
                )
            )
        )

        features[f"{prefix}_motor_pose_presence_ratio"] = (
            VideoPhenotypeExtractor.to_float(
                motor_metrics.get(
                    "pose_presence_ratio",
                    0
                )
            )
        )

        features[f"{prefix}_arm_stereotypy_score"] = (
            VideoPhenotypeExtractor.to_float(
                motor_metrics.get(
                    "arm_stereotypy_score",
                    0
                )
            )
        )

        features[f"{prefix}_oscillation_frequency_hz"] = (
            VideoPhenotypeExtractor.to_float(
                motor_metrics.get(
                    "oscillation_frequency_hz",
                    0
                )
            )
        )

        features[f"{prefix}_stereotypy_index"] = (
            VideoPhenotypeExtractor.to_float(
                motor_metrics.get(
                    "stereotypy_index",
                    0
                )
            )
        )

        return features

    @staticmethod
    def build(session):

        video_test = session.get(
            "video_test",
            {}
        )

        if not video_test:

            return {
                "video_test_available": 0
            }

        social_block = (
            VideoPhenotypeExtractor.get_video_block(
                video_test,
                "social_video"
            )
        )

        nonsocial_block = (
            VideoPhenotypeExtractor.get_video_block(
                video_test,
                "nonsocial_video"
            )
        )

        features = {
            "video_test_available": 1
        }

        social_features = (
            VideoPhenotypeExtractor.extract_block_features(
                "video_social",
                social_block
            )
        )

        nonsocial_features = (
            VideoPhenotypeExtractor.extract_block_features(
                "video_nonsocial",
                nonsocial_block
            )
        )

        features.update(
            social_features
        )

        features.update(
            nonsocial_features
        )

        social_attention = features.get(
            "video_social_facing_forward_proxy",
            0
        )

        nonsocial_attention = features.get(
            "video_nonsocial_facing_forward_proxy",
            0
        )

        social_smile = features.get(
            "video_social_smile_ratio",
            0
        )

        nonsocial_smile = features.get(
            "video_nonsocial_smile_ratio",
            0
        )

        social_motor = features.get(
            "video_social_stereotypy_index",
            0
        )

        nonsocial_motor = features.get(
            "video_nonsocial_stereotypy_index",
            0
        )

        social_head = features.get(
            "video_social_head_variability",
            0
        )

        nonsocial_head = features.get(
            "video_nonsocial_head_variability",
            0
        )

        # Key paper-inspired contrast feature
        features["video_social_preference_score"] = round(
            social_attention - nonsocial_attention,
            3
        )

        features["video_nonsocial_preference_score"] = round(
            nonsocial_attention - social_attention,
            3
        )

        features["video_smile_response_difference"] = round(
            social_smile - nonsocial_smile,
            3
        )

        features["video_motor_difference"] = round(
            social_motor - nonsocial_motor,
            3
        )

        features["video_head_movement_difference"] = round(
            social_head - nonsocial_head,
            3
        )

        if features["video_social_preference_score"] > 0.1:

            features["video_attention_pattern"] = (
                "social_preference"
            )

        elif features["video_social_preference_score"] < -0.1:

            features["video_attention_pattern"] = (
                "nonsocial_preference"
            )

        else:

            features["video_attention_pattern"] = (
                "balanced"
            )

        return features