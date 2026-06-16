class PaperFeatureMapper:

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
    def clamp(value, min_value=0.0, max_value=1.0):

        return max(
            min_value,
            min(
                max_value,
                value
            )
        )

    @staticmethod
    def add_feature(
        features,
        report,
        paper_name,
        value,
        app_source,
        match_type,
        note
    ):

        features[paper_name] = round(
            PaperFeatureMapper.to_float(value),
            4
        )

        report[paper_name] = {
            "paper_feature":
                paper_name,

            "our_app_source":
                app_source,

            "match_type":
                match_type,

            "note":
                note
        }

    @staticmethod
    def build(session):

        phenotype_vector = session.get(
            "phenotype_vector",
            {}
        )

        features = {}
        report = {}

        # -----------------------------
        # 1. Facing forward
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_facing_forward_social_movies",
            phenotype_vector.get(
                "video_social_facing_forward_proxy",
                0
            ),
            "video_social_facing_forward_proxy",
            "proxy",
            "Paper uses eyes open + gaze near screen + steady face. Our app uses webcam attention ratio proxy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_facing_forward_nonsocial_movies",
            phenotype_vector.get(
                "video_nonsocial_facing_forward_proxy",
                0
            ),
            "video_nonsocial_facing_forward_proxy",
            "proxy",
            "Paper uses eyes open + gaze near screen + steady face. Our app uses webcam attention ratio proxy."
        )

        # -----------------------------
        # 2. Social attention
        # -----------------------------

        social_attention = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "video_social_facing_forward_proxy",
                0
            )
        )

        nonsocial_attention = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "video_nonsocial_facing_forward_proxy",
                0
            )
        )

        attention_total = social_attention + nonsocial_attention

        if attention_total > 0:

            gaze_percent_social_proxy = (
                social_attention /
                attention_total
            )

        else:

            gaze_percent_social_proxy = 0

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_gaze_percent_social",
            gaze_percent_social_proxy,
            "video_social_facing_forward_proxy / social+nonsocial attention",
            "proxy",
            "Paper uses gaze AOI to social half of screen. Our app estimates relative attention to social vs nonsocial video blocks."
        )

        avg_gaze_variability = (
            PaperFeatureMapper.to_float(
                phenotype_vector.get(
                    "video_social_gaze_variability",
                    0
                )
            )
            +
            PaperFeatureMapper.to_float(
                phenotype_vector.get(
                    "video_nonsocial_gaze_variability",
                    0
                )
            )
        ) / 2

        gaze_silhouette_proxy = 1 / (
            1 + avg_gaze_variability
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_gaze_silhouette_score",
            gaze_silhouette_proxy,
            "video_social_gaze_variability + video_nonsocial_gaze_variability",
            "proxy",
            "Paper uses gaze clustering on person/toy AOIs. Our app uses inverse gaze variability as weak proxy."
        )

        # -----------------------------
        # 3. Attention to speech
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_attention_to_speech",
            0,
            "not_implemented",
            "missing",
            "Paper uses gaze correlation with alternating conversation. Our app needs a dedicated speech-turn video task for this."
        )

        # -----------------------------
        # 4. Response to name
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_response_to_name_delay",
            phenotype_vector.get(
                "name_response_time",
                0
            ),
            "name_response_time",
            "proxy",
            "Paper calls name three times during movies and measures head-turn delay. Our app measures response time during name response task."
        )

        name_good = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "name_response_good",
                0
            )
        )

        name_not_good = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "name_response_not_good",
                0
            )
        )

        if name_good > 0 or name_not_good > 0:

            response_proportion_proxy = 1

        else:

            response_proportion_proxy = 0

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_response_to_name_proportion",
            response_proportion_proxy,
            "name_response_good/name_response_not_good",
            "proxy",
            "Paper uses three examiner name calls. Our app currently has one response event."
        )

        # -----------------------------
        # 5. Blink rate
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_blink_rate_social_movies",
            phenotype_vector.get(
                "video_social_blink_rate_per_min",
                0
            ),
            "video_social_blink_rate_per_min",
            "proxy",
            "Paper extracts blink rate during social movies. Our app extracts webcam blink rate during social video."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_blink_rate_nonsocial_movies",
            phenotype_vector.get(
                "video_nonsocial_blink_rate_per_min",
                0
            ),
            "video_nonsocial_blink_rate_per_min",
            "proxy",
            "Paper extracts blink rate during nonsocial movies. Our app extracts webcam blink rate during nonsocial video."
        )

        # -----------------------------
        # 6. Facial dynamics complexity
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_eyebrows_complexity_social_movies",
            0,
            "not_implemented",
            "missing",
            "Paper uses multiscale entropy of eyebrow landmarks. Our app does not yet calculate eyebrow dynamics complexity."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_eyebrows_complexity_nonsocial_movies",
            0,
            "not_implemented",
            "missing",
            "Paper uses multiscale entropy of eyebrow landmarks. Our app does not yet calculate eyebrow dynamics complexity."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_mouth_complexity_social_movies",
            phenotype_vector.get(
                "video_social_avg_smile_score",
                0
            ),
            "video_social_avg_smile_score",
            "proxy",
            "Paper uses multiscale entropy of mouth landmarks. Our app uses smile/mouth score as proxy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_mouth_complexity_nonsocial_movies",
            phenotype_vector.get(
                "video_nonsocial_avg_smile_score",
                0
            ),
            "video_nonsocial_avg_smile_score",
            "proxy",
            "Paper uses multiscale entropy of mouth landmarks. Our app uses smile/mouth score as proxy."
        )

        # -----------------------------
        # 7. Head movement
        # -----------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_social_movies",
            phenotype_vector.get(
                "video_social_head_variability",
                0
            ),
            "video_social_head_variability",
            "proxy",
            "Paper uses head movement from facial landmark time series. Our app uses head position variability."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_nonsocial_movies",
            phenotype_vector.get(
                "video_nonsocial_head_variability",
                0
            ),
            "video_nonsocial_head_variability",
            "proxy",
            "Paper uses head movement from facial landmark time series. Our app uses head position variability."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_complexity_social_movies",
            phenotype_vector.get(
                "video_social_head_variability",
                0
            ),
            "video_social_head_variability",
            "proxy",
            "Paper uses multiscale entropy. Our app currently uses variability as a simple proxy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_complexity_nonsocial_movies",
            phenotype_vector.get(
                "video_nonsocial_head_variability",
                0
            ),
            "video_nonsocial_head_variability",
            "proxy",
            "Paper uses multiscale entropy. Our app currently uses variability as a simple proxy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_acceleration_social_movies",
            0,
            "not_implemented",
            "missing",
            "Paper computes derivative/acceleration of head movement. Our app does not yet store frame-wise head movement time series."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_acceleration_nonsocial_movies",
            0,
            "not_implemented",
            "missing",
            "Paper computes derivative/acceleration of head movement. Our app does not yet store frame-wise head movement time series."
        )

        # -----------------------------
        # 8. Touch-based bubble game
        # -----------------------------

        popped_count = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "game_popped_count",
                0
            )
        )

        total_reactions = PaperFeatureMapper.to_float(
            phenotype_vector.get(
                "game_total_reactions",
                0
            )
        )

        if total_reactions > 0:

            popping_rate = popped_count / total_reactions

        else:

            popping_rate = 0

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_popping_rate",
            popping_rate,
            "game_popped_count / game_total_reactions",
            "proxy",
            "Paper uses popped bubbles over touches. Our app uses popped events over total game events."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_accuracy_std",
            phenotype_vector.get(
                "game_motor_irregularity",
                0
            ),
            "game_motor_irregularity",
            "proxy",
            "Paper uses touch error standard deviation. Our app uses game motor irregularity proxy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_average_touch_length",
            0,
            "not_implemented",
            "missing",
            "Paper uses finger trajectory length on tablet. Our app must log mouse/touch movement path to compute this."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_average_applied_force",
            0,
            "not_available_on_laptop",
            "missing",
            "Paper uses device touch force/kinetic data. Standard laptop mouse/webcam setup cannot measure real applied touch force."
        )

        # -----------------------------
        # Coverage summary
        # -----------------------------

        exact_count = 0
        proxy_count = 0
        missing_count = 0

        for item in report.values():

            if item["match_type"] == "exact":
                exact_count += 1

            elif item["match_type"] == "proxy":
                proxy_count += 1

            elif item["match_type"] == "missing":
                missing_count += 1

        coverage = {
            "total_paper_features":
                len(report),

            "exact_count":
                exact_count,

            "proxy_count":
                proxy_count,

            "missing_count":
                missing_count,

            "coverage_score":
                round(
                    (exact_count + 0.5 * proxy_count) /
                    max(len(report), 1),
                    3
                )
        }

        return {
            "paper_aligned_features":
                features,

            "paper_feature_match_report":
                report,

            "paper_feature_coverage":
                coverage
        }