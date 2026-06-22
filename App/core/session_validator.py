import os
import json


class SessionValidator:

    REQUIRED_JSON_FILES = [
        "video_test.json",
        "stimulus_events.json",
        "response_to_name_features.json",
        "attention_to_speech_features.json",
        "gaze_silhouette_features.json",
        "paper_aligned_features.json",
        "paper_feature_coverage.json",
        "phenotype_vector.json"
    ]

    EXPECTED_VIDEO_STIMULI = 9
    EXPECTED_NAME_CALLS = 3
    EXPECTED_PAPER_FEATURES = 23

    MIN_GAZE_VALID_POINTS = 100
    MIN_SPEECH_VALID_FRAMES = 50
    MIN_FRAMEWISE_STIMULI_WITH_FACE = 5

    @staticmethod
    def load_json(path):

        if not os.path.exists(path):
            return None

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:

            return None

    @staticmethod
    def add_issue(
        issues,
        severity,
        code,
        message
    ):

        issues.append(
            {
                "severity": severity,
                "code": code,
                "message": message
            }
        )

    @staticmethod
    def get_session_path(session):

        session_manager = session.get(
            "session_manager"
        )

        if session_manager is None:
            return None

        return session_manager.get_session_path()

    @staticmethod
    def check_required_files(
        session_path,
        issues
    ):

        missing = []

        unreadable = []

        for filename in SessionValidator.REQUIRED_JSON_FILES:

            path = os.path.join(
                session_path,
                filename
            )

            if not os.path.exists(path):

                missing.append(
                    filename
                )

                continue

            data = SessionValidator.load_json(
                path
            )

            if data is None:

                unreadable.append(
                    filename
                )

        if missing:

            SessionValidator.add_issue(
                issues,
                "error",
                "missing_required_json",
                f"Missing required JSON files: {missing}"
            )

        if unreadable:

            SessionValidator.add_issue(
                issues,
                "error",
                "unreadable_required_json",
                f"Unreadable/corrupt JSON files: {unreadable}"
            )

    @staticmethod
    def check_video_protocol(
        session_path,
        issues
    ):

        video_test = SessionValidator.load_json(
            os.path.join(
                session_path,
                "video_test.json"
            )
        )

        stimulus_events = SessionValidator.load_json(
            os.path.join(
                session_path,
                "stimulus_events.json"
            )
        )

        if video_test is None:

            SessionValidator.add_issue(
                issues,
                "error",
                "video_test_missing",
                "video_test.json could not be loaded."
            )

            return

        protocol_summary = video_test.get(
            "protocol_summary",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        triggered = video_test.get(
            "triggered_name_call_events",
            []
        )

        total_video_stimuli = protocol_summary.get(
            "total_video_stimuli",
            len(stimulus_results)
        )

        smooth_playlist = protocol_summary.get(
            "smooth_playlist",
            False
        )

        uses_tracker_manager = protocol_summary.get(
            "uses_tracker_manager",
            None
        )

        if total_video_stimuli != SessionValidator.EXPECTED_VIDEO_STIMULI:

            SessionValidator.add_issue(
                issues,
                "error",
                "wrong_video_stimulus_count",
                f"Expected {SessionValidator.EXPECTED_VIDEO_STIMULI} video stimuli, found {total_video_stimuli}."
            )

        if not smooth_playlist:

            SessionValidator.add_issue(
                issues,
                "warning",
                "not_smooth_playlist",
                "Protocol summary does not report smooth_playlist=true."
            )

        if uses_tracker_manager is not False:

            SessionValidator.add_issue(
                issues,
                "warning",
                "legacy_tracker_manager_possible",
                "uses_tracker_manager is not false. Check that old TrackerManager pipeline is inactive."
            )

        if len(triggered) != SessionValidator.EXPECTED_NAME_CALLS:

            SessionValidator.add_issue(
                issues,
                "error",
                "wrong_triggered_name_call_count",
                f"Expected {SessionValidator.EXPECTED_NAME_CALLS} triggered name calls, found {len(triggered)}."
            )

        if stimulus_events is not None:

            triggered_events = stimulus_events.get(
                "triggered_name_call_events",
                []
            )

            if len(triggered_events) != SessionValidator.EXPECTED_NAME_CALLS:

                SessionValidator.add_issue(
                    issues,
                    "error",
                    "stimulus_events_name_call_mismatch",
                    f"stimulus_events.json has {len(triggered_events)} triggered name calls."
                )

    @staticmethod
    def check_response_to_name(
        session_path,
        issues
    ):

        data = SessionValidator.load_json(
            os.path.join(
                session_path,
                "response_to_name_features.json"
            )
        )

        if data is None:

            SessionValidator.add_issue(
                issues,
                "error",
                "response_to_name_missing",
                "response_to_name_features.json could not be loaded."
            )

            return

        call_count = data.get(
            "name_call_count",
            0
        )

        response_count = data.get(
            "name_response_count",
            0
        )

        call_results = data.get(
            "name_call_results",
            []
        )

        if call_count != SessionValidator.EXPECTED_NAME_CALLS:

            SessionValidator.add_issue(
                issues,
                "error",
                "wrong_name_call_count",
                f"Expected {SessionValidator.EXPECTED_NAME_CALLS} name calls, found {call_count}."
            )

        for result in call_results:

            call_index = result.get(
                "call_index"
            )

            reason = result.get(
                "reason",
                ""
            )

            window_rows = result.get(
                "response_window_rows",
                0
            )

            if reason == "no_response_window_rows":

                SessionValidator.add_issue(
                    issues,
                    "error",
                    "name_call_no_response_window",
                    f"Name call {call_index} has no response-window rows. Likely timing mismatch."
                )

            if reason == "no_face_rows":

                SessionValidator.add_issue(
                    issues,
                    "warning",
                    "name_call_no_face_rows",
                    f"Name call {call_index} has no face rows."
                )

            if window_rows == 0:

                SessionValidator.add_issue(
                    issues,
                    "warning",
                    "name_call_zero_window_rows",
                    f"Name call {call_index} has zero response-window rows."
                )

        if response_count == 0 and call_count > 0:

            SessionValidator.add_issue(
                issues,
                "warning",
                "no_name_responses_detected",
                "No response-to-name events detected. This may be valid behavior, but verify tracking quality."
            )

    @staticmethod
    def check_attention_to_speech(
        session_path,
        issues
    ):

        data = SessionValidator.load_json(
            os.path.join(
                session_path,
                "attention_to_speech_features.json"
            )
        )

        if data is None:

            SessionValidator.add_issue(
                issues,
                "error",
                "attention_to_speech_missing",
                "attention_to_speech_features.json could not be loaded."
            )

            return

        stimulus_count = data.get(
            "speech_stimulus_count",
            0
        )

        valid_frames = data.get(
            "speech_valid_frames",
            0
        )

        matched_frames = data.get(
            "speech_matched_frames",
            0
        )

        if stimulus_count < 2:

            SessionValidator.add_issue(
                issues,
                "warning",
                "low_speech_stimulus_count",
                f"Expected 2 speech stimuli, found {stimulus_count}."
            )

        if valid_frames < SessionValidator.MIN_SPEECH_VALID_FRAMES:

            SessionValidator.add_issue(
                issues,
                "warning",
                "low_speech_valid_frames",
                f"Speech valid frames are low: {valid_frames}."
            )

        if valid_frames > 0 and matched_frames == 0:

            SessionValidator.add_issue(
                issues,
                "warning",
                "zero_attention_to_speech_matches",
                "Speech frames exist but no gaze matched speaker AOI."
            )

    @staticmethod
    def check_gaze_silhouette(
        session_path,
        issues
    ):

        data = SessionValidator.load_json(
            os.path.join(
                session_path,
                "gaze_silhouette_features.json"
            )
        )

        if data is None:

            SessionValidator.add_issue(
                issues,
                "error",
                "gaze_silhouette_missing",
                "gaze_silhouette_features.json could not be loaded."
            )

            return

        valid_points = data.get(
            "gaze_silhouette_valid_points",
            0
        )

        stimulus_count = data.get(
            "gaze_silhouette_stimulus_count",
            0
        )

        results = data.get(
            "gaze_silhouette_stimulus_results",
            []
        )

        if valid_points < SessionValidator.MIN_GAZE_VALID_POINTS:

            SessionValidator.add_issue(
                issues,
                "warning",
                "low_gaze_valid_points",
                f"Gaze silhouette valid points are low: {valid_points}."
            )

        if stimulus_count == 0:

            SessionValidator.add_issue(
                issues,
                "warning",
                "zero_gaze_silhouette_stimuli",
                "No gaze silhouette stimuli were analyzed."
            )

        no_aoi_hits = []

        one_sided = []

        for result in results:

            stimulus_id = result.get(
                "stimulus_id",
                "unknown"
            )

            gaze_quality = result.get(
                "gaze_quality",
                ""
            )

            if gaze_quality == "no_aoi_hits":

                no_aoi_hits.append(
                    stimulus_id
                )

            if gaze_quality == "one_sided_aoi_attention":

                one_sided.append(
                    stimulus_id
                )

        if no_aoi_hits:

            SessionValidator.add_issue(
                issues,
                "warning",
                "gaze_no_aoi_hits",
                f"No AOI hits for stimuli: {no_aoi_hits}"
            )

        if one_sided:

            SessionValidator.add_issue(
                issues,
                "info",
                "gaze_one_sided_attention",
                f"Only one AOI side was attended for stimuli: {one_sided}"
            )

    @staticmethod
    def check_paper_feature_coverage(
        session_path,
        issues
    ):

        coverage_path = os.path.join(
            session_path,
            "paper_feature_coverage.json"
        )

        aligned_path = os.path.join(
            session_path,
            "paper_aligned_features.json"
        )

        phenotype_path = os.path.join(
            session_path,
            "phenotype_vector.json"
        )

        coverage_data = SessionValidator.load_json(
            coverage_path
        )

        aligned_data = SessionValidator.load_json(
            aligned_path
        )

        phenotype_data = SessionValidator.load_json(
            phenotype_path
        )

        if coverage_data is None:

            SessionValidator.add_issue(
                issues,
                "error",
                "paper_feature_coverage_missing",
                "paper_feature_coverage.json could not be loaded."
            )

            return

        # Different versions of our coverage exporter used different names.
        possible_count_keys = [
            "present_feature_count",
            "paper_feature_count",
            "covered_feature_count",
            "available_feature_count",
            "matched_feature_count",
            "total_present_features",
            "features_present_count",
            "feature_count"
        ]

        present_count = None

        for key in possible_count_keys:

            if key in coverage_data:

                try:

                    present_count = int(
                        coverage_data.get(
                            key,
                            0
                        )
                    )

                    break

                except Exception:

                    pass

        # Some coverage files store lists instead of direct counts.
        if present_count is None:

            possible_present_list_keys = [
                "present_features",
                "covered_features",
                "available_features",
                "matched_features"
            ]

            for key in possible_present_list_keys:

                value = coverage_data.get(
                    key
                )

                if isinstance(
                    value,
                    list
                ):

                    present_count = len(
                        value
                    )

                    break

        # Fallback 1: count usable paper-aligned feature keys.
        if present_count is None and isinstance(
            aligned_data,
            dict
        ):

            ignored_keys = [
                "metadata",
                "notes",
                "feature_sources",
                "coverage",
                "missing_features",
                "present_features"
            ]

            usable_keys = []

            for key, value in aligned_data.items():

                if key in ignored_keys:
                    continue

                if isinstance(
                    value,
                    (int, float, bool)
                ):

                    usable_keys.append(
                        key
                    )

                elif isinstance(
                    value,
                    str
                ) and value != "":

                    usable_keys.append(
                        key
                    )

            present_count = len(
                usable_keys
            )

        # Fallback 2: count phenotype vector feature keys.
        if present_count is None and isinstance(
            phenotype_data,
            dict
        ):

            ignored_keys = [
                "session_id",
                "label",
                "child_age",
                "child_gender",
                "session_quality_score",
                "session_quality_grade",
                "session_is_valid",
                "validator_version"
            ]

            usable_keys = []

            for key, value in phenotype_data.items():

                if key in ignored_keys:
                    continue

                if isinstance(
                    value,
                    (int, float, bool)
                ):

                    usable_keys.append(
                        key
                    )

                elif isinstance(
                    value,
                    str
                ) and value != "":

                    usable_keys.append(
                        key
                    )

            present_count = len(
                usable_keys
            )

        if present_count is None:

            present_count = 0

        missing = coverage_data.get(
            "missing_features",
            []
        )

        if not isinstance(
            missing,
            list
        ):

            missing = []

        if present_count < SessionValidator.EXPECTED_PAPER_FEATURES:

            SessionValidator.add_issue(
                issues,
                "error",
                "paper_feature_coverage_low",
                f"Expected {SessionValidator.EXPECTED_PAPER_FEATURES} paper features, found {present_count}."
            )

        if missing:

            SessionValidator.add_issue(
                issues,
                "error",
                "paper_features_missing",
                f"Missing paper features: {missing}"
            )

    @staticmethod
    def check_framewise_logs(
        session_path,
        issues
    ):

        framewise_files = [
            file
            for file in os.listdir(
                session_path
            )
            if file.endswith(
                "_framewise_log.csv"
            )
        ]

        if len(framewise_files) < SessionValidator.EXPECTED_VIDEO_STIMULI:

            SessionValidator.add_issue(
                issues,
                "warning",
                "low_framewise_log_count",
                f"Expected at least {SessionValidator.EXPECTED_VIDEO_STIMULI} framewise logs, found {len(framewise_files)}."
            )

        usable_face_logs = 0

        for filename in framewise_files:

            path = os.path.join(
                session_path,
                filename
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read()

                if "face_detected" in content and ",1" in content:

                    usable_face_logs += 1

            except Exception:

                pass

        if usable_face_logs < SessionValidator.MIN_FRAMEWISE_STIMULI_WITH_FACE:

            SessionValidator.add_issue(
                issues,
                "warning",
                "low_face_usable_framewise_logs",
                f"Only {usable_face_logs} framewise logs appear to contain face-detected rows."
            )

    @staticmethod
    def compute_quality_score(issues):

        score = 1.0

        for issue in issues:

            severity = issue.get(
                "severity",
                "info"
            )

            if severity == "error":

                score -= 0.25

            elif severity == "warning":

                score -= 0.08

            elif severity == "info":

                score -= 0.02

        if score < 0:
            score = 0.0

        return round(
            score,
            4
        )

    @staticmethod
    def validate(
        session,
        *args,
        **kwargs
    ):

        return SessionValidator.build(
            session
        )
    @staticmethod
    def build(session):

        session_path = SessionValidator.get_session_path(
            session
        )

        issues = []

        if session_path is None:

            return {
                "is_valid": False,
                "quality_score": 0.0,
                "quality_grade": "Failed",
                "issues": [
                    {
                        "severity": "error",
                        "code": "missing_session_manager",
                        "message": "Session manager missing from session."
                    }
                ]
            }

        SessionValidator.check_required_files(
            session_path,
            issues
        )

        SessionValidator.check_video_protocol(
            session_path,
            issues
        )

        SessionValidator.check_response_to_name(
            session_path,
            issues
        )

        SessionValidator.check_attention_to_speech(
            session_path,
            issues
        )

        SessionValidator.check_gaze_silhouette(
            session_path,
            issues
        )

        SessionValidator.check_paper_feature_coverage(
            session_path,
            issues
        )

        SessionValidator.check_framewise_logs(
            session_path,
            issues
        )

        quality_score = SessionValidator.compute_quality_score(
            issues
        )

        has_error = any(
            issue.get(
                "severity"
            )
            ==
            "error"
            for issue in issues
        )

        if has_error:

            quality_grade = "Failed"

        elif quality_score >= 0.9:

            quality_grade = "Excellent"

        elif quality_score >= 0.75:

            quality_grade = "Good"

        elif quality_score >= 0.6:

            quality_grade = "Usable with caution"

        else:

            quality_grade = "Poor"

        return {
            "is_valid":
                not has_error,

            "quality_score":
                quality_score,

            "quality_grade":
                quality_grade,

            "issues":
                issues,

            "validator_version":
                "paper_aligned_strict_v2",

            "checks":
                {
                    "expected_video_stimuli":
                        SessionValidator.EXPECTED_VIDEO_STIMULI,

                    "expected_name_calls":
                        SessionValidator.EXPECTED_NAME_CALLS,

                    "expected_paper_features":
                        SessionValidator.EXPECTED_PAPER_FEATURES,

                    "min_gaze_valid_points":
                        SessionValidator.MIN_GAZE_VALID_POINTS,

                    "min_speech_valid_frames":
                        SessionValidator.MIN_SPEECH_VALID_FRAMES
                }
        }