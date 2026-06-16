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

        # --------------------------------------------------
        # 1. Facing forward during social / nonsocial movies
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_facing_forward_social_movies",
            phenotype_vector.get(
                "paper_facing_forward_social_movies",
                0
            ),
            "paper_timeseries_features.paper_facing_forward_social_movies",
            "near_exact",
            "Computed from frame-wise logs using face detected + eyes open + yaw/pitch/head steadiness. Paper uses eyes open + gaze near screen + steady face."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_facing_forward_nonsocial_movies",
            phenotype_vector.get(
                "paper_facing_forward_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_facing_forward_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise logs using face detected + eyes open + yaw/pitch/head steadiness. Paper uses eyes open + gaze near screen + steady face."
        )

        # --------------------------------------------------
        # 2. Social attention / gaze features
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_gaze_percent_social",
            phenotype_vector.get(
                "paper_gaze_percent_social",
                0
            ),
            "gaze_silhouette_features.paper_gaze_percent_social",
            "near_exact",
            "Computed from frame-wise gaze points and schedule-defined social AOI side during mixed social/non-social stimulus."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_gaze_silhouette_score",
            phenotype_vector.get(
                "paper_gaze_silhouette_score",
                0
            ),
            "gaze_silhouette_features.paper_gaze_silhouette_score",
            "near_exact",
            "Computed using clustering separation of frame-wise gaze points across left/right AOIs during mixed social/non-social stimulus."
        )

        # --------------------------------------------------
        # 3. Attention to speech
        # --------------------------------------------------

               # --------------------------------------------------
        # 3. Attention to speech
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_attention_to_speech",
            phenotype_vector.get(
                "paper_attention_to_speech",
                0
            ),
            "attention_to_speech_features.paper_attention_to_speech",
            "near_exact",
            "Computed from speech-attention stimulus using speaker-turn timestamps and frame-wise gaze side matching. It becomes stronger when real two-speaker videos and exact speaker-turn annotations are used."
        )

        # --------------------------------------------------
        # 4. Response to name
        # --------------------------------------------------

                # --------------------------------------------------
        # 4. Response to name
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_response_to_name_delay",
            phenotype_vector.get(
                "paper_response_to_name_delay",
                0
            ),
            "response_to_name_features.paper_response_to_name_delay",
            "near_exact",
            "Computed from three scheduled name-call events during movie stimuli using frame-wise head-turn/yaw response detection."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_response_to_name_proportion",
            phenotype_vector.get(
                "paper_response_to_name_proportion",
                0
            ),
            "response_to_name_features.paper_response_to_name_proportion",
            "near_exact",
            "Computed as responded name calls over total scheduled name calls, using frame-wise head-turn/yaw response detection."
        )
        # --------------------------------------------------
        # 5. Blink rate during social / nonsocial movies
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_blink_rate_social_movies",
            phenotype_vector.get(
                "paper_blink_rate_social_movies",
                0
            ),
            "paper_timeseries_features.paper_blink_rate_social_movies",
            "near_exact",
            "Computed from frame-wise blink states during social movie segments."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_blink_rate_nonsocial_movies",
            phenotype_vector.get(
                "paper_blink_rate_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_blink_rate_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise blink states during nonsocial movie segments."
        )

        # --------------------------------------------------
        # 6. Facial dynamics complexity
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_eyebrows_complexity_social_movies",
            phenotype_vector.get(
                "paper_eyebrows_complexity_social_movies",
                0
            ),
            "paper_timeseries_features.paper_eyebrows_complexity_social_movies",
            "near_exact",
            "Computed from frame-wise eyebrow signal complexity. Paper uses multiscale entropy of eyebrow landmark dynamics."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_eyebrows_complexity_nonsocial_movies",
            phenotype_vector.get(
                "paper_eyebrows_complexity_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_eyebrows_complexity_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise eyebrow signal complexity. Paper uses multiscale entropy of eyebrow landmark dynamics."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_mouth_complexity_social_movies",
            phenotype_vector.get(
                "paper_mouth_complexity_social_movies",
                0
            ),
            "paper_timeseries_features.paper_mouth_complexity_social_movies",
            "near_exact",
            "Computed from frame-wise mouth-open signal complexity. Paper uses multiscale entropy of mouth landmark dynamics."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_mouth_complexity_nonsocial_movies",
            phenotype_vector.get(
                "paper_mouth_complexity_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_mouth_complexity_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise mouth-open signal complexity. Paper uses multiscale entropy of mouth landmark dynamics."
        )

        # --------------------------------------------------
        # 7. Head movement
        # --------------------------------------------------

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_social_movies",
            phenotype_vector.get(
                "paper_head_movement_social_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_social_movies",
            "near_exact",
            "Computed from frame-wise head movement during social movie segments."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_nonsocial_movies",
            phenotype_vector.get(
                "paper_head_movement_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise head movement during nonsocial movie segments."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_complexity_social_movies",
            phenotype_vector.get(
                "paper_head_movement_complexity_social_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_complexity_social_movies",
            "near_exact",
            "Computed from frame-wise head movement complexity. Paper uses multiscale entropy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_complexity_nonsocial_movies",
            phenotype_vector.get(
                "paper_head_movement_complexity_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_complexity_nonsocial_movies",
            "near_exact",
            "Computed from frame-wise head movement complexity. Paper uses multiscale entropy."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_acceleration_social_movies",
            phenotype_vector.get(
                "paper_head_movement_acceleration_social_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_acceleration_social_movies",
            "near_exact",
            "Computed from derivative-like frame-wise head movement acceleration during social movies."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_head_movement_acceleration_nonsocial_movies",
            phenotype_vector.get(
                "paper_head_movement_acceleration_nonsocial_movies",
                0
            ),
            "paper_timeseries_features.paper_head_movement_acceleration_nonsocial_movies",
            "near_exact",
            "Computed from derivative-like frame-wise head movement acceleration during nonsocial movies."
        )

        # --------------------------------------------------
        # 8. Bubble game touch features
        # --------------------------------------------------

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
        phenotype_vector.get(
            "paper_pop_the_bubbles_popping_rate",
            0
        ),
        "game_metrics.touch_features.touch_popping_rate",
        "near_exact",
        "Computed as popped bubbles over total touches, matching the paper concept."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_accuracy_std",
            phenotype_vector.get(
                "paper_pop_the_bubbles_accuracy_std",
                0
            ),
            "game_metrics.touch_features.touch_error_std",
            "near_exact",
            "Computed as standard deviation of distance from touch position to nearest bubble center."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_average_touch_length",
            phenotype_vector.get(
                "paper_pop_the_bubbles_average_touch_length",
                0
            ),
            "game_metrics.touch_features.touch_average_length",
            "near_exact",
            "Computed from mouse/touch path length during bubble interaction. On touchscreen this directly corresponds to finger trajectory length."
        )

        PaperFeatureMapper.add_feature(
            features,
            report,
            "paper_pop_the_bubbles_average_applied_force",
            phenotype_vector.get(
                "paper_pop_the_bubbles_average_applied_force",
                0
            ),
            "game_metrics.touch_features.touch_average_applied_force",
            "hardware_dependent",
            "Paper uses device touch force/kinetic information. Desktop mouse does not provide true force; Android/iOS/tablet implementation should use pressure/touch APIs when available."
        )

        # --------------------------------------------------
        # Coverage summary
        # --------------------------------------------------

        exact_count = 0
        near_exact_count = 0
        proxy_count = 0
        missing_count = 0
        hardware_dependent_count = 0

        for item in report.values():

            match_type = item.get(
                "match_type",
                ""
            )

            if match_type == "exact":
                exact_count += 1

            elif match_type == "near_exact":
                near_exact_count += 1

            elif match_type == "proxy":
                proxy_count += 1

            elif match_type == "missing":
                missing_count += 1

            elif match_type == "hardware_dependent":
                hardware_dependent_count += 1

        total = len(report)

        coverage_score = (
            exact_count * 1.0
            +
            near_exact_count * 0.8
            +
            proxy_count * 0.5
            +
            hardware_dependent_count * 0.3
        ) / max(
            total,
            1
        )

        coverage = {
            "total_paper_features":
                total,

            "exact_count":
                exact_count,

            "near_exact_count":
                near_exact_count,

            "proxy_count":
                proxy_count,

            "missing_count":
                missing_count,

            "hardware_dependent_count":
                hardware_dependent_count,

            "coverage_score":
                round(
                    coverage_score,
                    3
                ),

            "coverage_score_formula":
                "exact=1.0, near_exact=0.8, proxy=0.5, hardware_dependent=0.3, missing=0.0"
        }

        return {
            "paper_aligned_features":
                features,

            "paper_feature_match_report":
                report,

            "paper_feature_coverage":
                coverage
        }