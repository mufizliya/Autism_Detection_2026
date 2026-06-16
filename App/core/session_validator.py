class SessionValidator:

    @staticmethod
    def to_float(value, default=0.0):

        try:

            if value is None:
                return default

            if value == "":
                return default

            return float(value)

        except Exception:

            return default

    @staticmethod
    def section_exists(session, key):

        value = session.get(
            key
        )

        if value is None:
            return False

        if isinstance(value, dict) and len(value) == 0:
            return False

        if isinstance(value, list) and len(value) == 0:
            return False

        return True

    @staticmethod
    def get_quality_level(score):

        if score >= 0.85:
            return "Excellent"

        if score >= 0.70:
            return "Good"

        if score >= 0.50:
            return "Fair"

        return "Poor"

    @staticmethod
    def validate_required_sections(session):

        issues = []
        passed = 0
        total = 0

        required_sections = [
            "questionnaire",
            "video_test",
            "game_metrics",
            "phenotype_vector",
            "paper_timeseries_features",
            "response_to_name_features",
            "attention_to_speech_features",
            "gaze_silhouette_features",
            "paper_aligned_features",
            "paper_feature_coverage"
        ]

        for section in required_sections:

            total += 1

            if SessionValidator.section_exists(
                session,
                section
            ):

                passed += 1

            else:

                issues.append(
                    f"Missing session section: {section}"
                )

        return passed, total, issues

    @staticmethod
    def validate_video_protocol(session):

        issues = []
        warnings = []
        passed = 0
        total = 0

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        protocol_summary = video_test.get(
            "protocol_summary",
            {}
        )

        total += 1

        if len(stimulus_results) > 0:

            passed += 1

        else:

            issues.append(
                "No video stimulus results were recorded."
            )

        total += 1

        uses_tracker_manager = protocol_summary.get(
            "uses_tracker_manager",
            None
        )

        if uses_tracker_manager is False:

            passed += 1

        else:

            issues.append(
                "Video protocol still appears to use TrackerManager or does not report uses_tracker_manager=false."
            )

        total += 1

        measurement_source = protocol_summary.get(
            "measurement_source",
            ""
        )

        if measurement_source in [
            "continuous_framewise_behavior_recorder",
            "framewise_behavior_recorder"
        ]:

            passed += 1

        else:

            issues.append(
                "Video measurement source is not framewise behavior recording."
            )

        total += 1

        if protocol_summary.get(
            "smooth_playlist",
            False
        ) is True:

            passed += 1

        else:

            warnings.append(
                "Stimulus protocol is not marked as smooth_playlist=true."
            )

        scheduled_calls = (
            protocol_summary.get(
                "total_name_call_events",
                0
            )
        )

        triggered_calls = (
            protocol_summary.get(
                "total_triggered_name_call_events",
                0
            )
        )

        total += 1

        if scheduled_calls == 0:

            warnings.append(
                "No scheduled name-call events found."
            )

        elif triggered_calls >= scheduled_calls:

            passed += 1

        else:

            issues.append(
                f"Only {triggered_calls}/{scheduled_calls} scheduled name-call events were triggered."
            )

        return passed, total, issues, warnings

    @staticmethod
    def validate_framewise_quality(session):

        issues = []
        warnings = []
        passed = 0
        total = 0

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        if len(stimulus_results) == 0:

            return passed, total, issues, warnings

        face_ratios = []
        total_frames_all = 0
        weak_stimuli = []

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            stimulus_id = stimulus.get(
                "id",
                "unknown"
            )

            summary = result.get(
                "framewise_summary",
                {}
            )

            total += 1

            total_frames = int(
                SessionValidator.to_float(
                    summary.get(
                        "total_frames",
                        0
                    )
                )
            )

            face_presence_ratio = SessionValidator.to_float(
                summary.get(
                    "face_presence_ratio",
                    0
                )
            )

            total_frames_all += total_frames
            face_ratios.append(
                face_presence_ratio
            )

            if total_frames <= 0:

                issues.append(
                    f"No framewise rows recorded for stimulus: {stimulus_id}"
                )

                continue

            if face_presence_ratio >= 0.50:

                passed += 1

            else:

                weak_stimuli.append(
                    stimulus_id
                )

        total += 1

        if total_frames_all > 0:

            passed += 1

        else:

            issues.append(
                "No framewise video frames were recorded across the stimulus protocol."
            )

        if weak_stimuli:

            warnings.append(
                "Low face presence ratio for stimuli: "
                +
                ", ".join(weak_stimuli)
            )

        if len(face_ratios) > 0:

            average_face_presence = (
                sum(face_ratios) / len(face_ratios)
            )

            if average_face_presence < 0.50:

                issues.append(
                    "Average face presence during stimulus protocol is too low."
                )

        return passed, total, issues, warnings

    @staticmethod
    def validate_bubble_game(session):

        issues = []
        warnings = []
        passed = 0
        total = 0

        game_metrics = session.get(
            "game_metrics",
            {}
        )

        total += 1

        if game_metrics:

            passed += 1

        else:

            issues.append(
                "Bubble game metrics are missing."
            )

            return passed, total, issues, warnings

        touch_features = game_metrics.get(
            "touch_features",
            {}
        )

        total += 1

        if touch_features:

            passed += 1

        else:

            issues.append(
                "Bubble game touch_features are missing."
            )

        total_touches = SessionValidator.to_float(
            touch_features.get(
                "touch_total_count",
                0
            )
        )

        total += 1

        if total_touches > 0:

            passed += 1

        else:

            warnings.append(
                "No bubble-game touches were recorded."
            )

        popping_rate = SessionValidator.to_float(
            touch_features.get(
                "touch_popping_rate",
                0
            )
        )

        total += 1

        if 0 <= popping_rate <= 1:

            passed += 1

        else:

            issues.append(
                "Bubble-game popping rate is outside expected range 0..1."
            )

        force_available = touch_features.get(
            "touch_force_available",
            False
        )

        if force_available is False:

            warnings.append(
                "Touch force is unavailable on desktop/Pygame; this is expected unless running on touch hardware."
            )

        return passed, total, issues, warnings

    @staticmethod
    def validate_paper_features(session):

        issues = []
        warnings = []
        passed = 0
        total = 0

        paper_features = session.get(
            "paper_aligned_features",
            {}
        )

        coverage = session.get(
            "paper_feature_coverage",
            {}
        )

        expected_features = [
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

        for feature in expected_features:

            total += 1

            if feature in paper_features:

                passed += 1

            else:

                issues.append(
                    f"Missing paper-aligned feature: {feature}"
                )

        total += 1

        if coverage:

            passed += 1

        else:

            issues.append(
                "paper_feature_coverage is missing."
            )

        total_features = int(
            SessionValidator.to_float(
                coverage.get(
                    "total_paper_features",
                    0
                )
            )
        )

        total += 1

        if total_features == 23:

            passed += 1

        else:

            issues.append(
                f"Expected 23 paper features, found {total_features}."
            )

        missing_count = int(
            SessionValidator.to_float(
                coverage.get(
                    "missing_count",
                    0
                )
            )
        )

        total += 1

        if missing_count == 0:

            passed += 1

        else:

            warnings.append(
                f"Paper feature mapper reports {missing_count} missing features."
            )

        coverage_score = SessionValidator.to_float(
            coverage.get(
                "coverage_score",
                0
            )
        )

        total += 1

        if coverage_score >= 0.70:

            passed += 1

        else:

            warnings.append(
                f"Paper feature coverage score is low: {coverage_score}"
            )

        return passed, total, issues, warnings

    @staticmethod
    def validate_specialized_extractors(session):

        issues = []
        warnings = []
        passed = 0
        total = 0

        response_to_name = session.get(
            "response_to_name_features",
            {}
        )

        total += 1

        if response_to_name.get(
            "name_call_count",
            0
        ) > 0:

            passed += 1

        else:

            issues.append(
                "Response-to-name extractor found no name-call events."
            )

        total += 1

        if "paper_response_to_name_proportion" in response_to_name:

            passed += 1

        else:

            issues.append(
                "Response-to-name proportion is missing."
            )

        attention_to_speech = session.get(
            "attention_to_speech_features",
            {}
        )

        total += 1

        if attention_to_speech.get(
            "speech_stimulus_count",
            0
        ) > 0:

            passed += 1

        else:

            warnings.append(
                "Attention-to-speech extractor found no speech stimulus."
            )

        gaze_silhouette = session.get(
            "gaze_silhouette_features",
            {}
        )

        total += 1

        if gaze_silhouette.get(
            "gaze_silhouette_stimulus_count",
            0
        ) > 0:

            passed += 1

        else:

            warnings.append(
                "Gaze silhouette extractor found no mixed social/non-social stimulus."
            )

        valid_gaze_points = gaze_silhouette.get(
            "gaze_silhouette_valid_points",
            0
        )

        total += 1

        if valid_gaze_points >= 20:

            passed += 1

        else:

            warnings.append(
                f"Low valid gaze points for silhouette extraction: {valid_gaze_points}"
            )

        return passed, total, issues, warnings

    @staticmethod
    def validate(session):

        issues = []
        warnings = []

        passed_total = 0
        checks_total = 0

        result = SessionValidator.validate_required_sections(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )

        result = SessionValidator.validate_video_protocol(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )
        warnings.extend(
            result[3]
        )

        result = SessionValidator.validate_framewise_quality(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )
        warnings.extend(
            result[3]
        )

        result = SessionValidator.validate_bubble_game(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )
        warnings.extend(
            result[3]
        )

        result = SessionValidator.validate_paper_features(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )
        warnings.extend(
            result[3]
        )

        result = SessionValidator.validate_specialized_extractors(
            session
        )

        passed_total += result[0]
        checks_total += result[1]
        issues.extend(
            result[2]
        )
        warnings.extend(
            result[3]
        )

        if checks_total > 0:

            quality_score = passed_total / checks_total

        else:

            quality_score = 0

        is_valid = (
            len(issues) == 0
            and
            quality_score >= 0.70
        )

        quality_level = SessionValidator.get_quality_level(
            quality_score
        )

        return {
            "is_valid":
                is_valid,

            "quality_score":
                round(
                    quality_score,
                    3
                ),

            "quality_level":
                quality_level,

            "checks_passed":
                passed_total,

            "checks_total":
                checks_total,

            "issues":
                issues,

            "warnings":
                warnings,

            "validator_version":
                "sensetoknow_style_v2",

            "note":
                "Validator checks questionnaire context, continuous video protocol, framewise logs, bubble touch features, and 23 paper-aligned features. It no longer checks removed TrackerManager/name-response standalone modules."
        }