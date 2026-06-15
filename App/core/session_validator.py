class SessionValidator:

    @staticmethod
    def get(data, key, default=0):

        if data is None:
            return default

        return data.get(
            key,
            default
        )

    @staticmethod
    def validate(session):

        issues = []
        warnings = []

        quality_points = 0
        max_points = 0

        phenotype_vector = session.get(
            "phenotype_vector",
            {}
        )

        # -------------------------
        # Required major sections
        # -------------------------

        required_sections = [
            "child_info",
            "questionnaire",
            "name_response",
            "game_metrics",
            "gaze_metrics",
            "facial_expression_metrics",
            "pose_metrics",
            "motor_metrics",
            "phenotype_vector"
        ]

        for section in required_sections:

            max_points += 1

            if session.get(section) is not None:

                quality_points += 1

            else:

                issues.append(
                    f"Missing session section: {section}"
                )

        # -------------------------
        # Gaze quality
        # -------------------------

        gaze_face_presence = SessionValidator.get(
            phenotype_vector,
            "gaze_face_presence_ratio",
            0
        )

        max_points += 1

        if gaze_face_presence >= 0.7:

            quality_points += 1

        elif gaze_face_presence >= 0.4:

            warnings.append(
                "Gaze face presence ratio is moderate; gaze metrics may be less reliable."
            )

        else:

            issues.append(
                "Gaze face presence ratio is too low; gaze metrics may be unreliable."
            )

        # -------------------------
        # Expression quality
        # -------------------------

        expression_face_frames = SessionValidator.get(
            session.get("facial_expression_metrics", {}),
            "face_frames",
            0
        )

        expression_total_frames = SessionValidator.get(
            session.get("facial_expression_metrics", {}),
            "total_frames",
            0
        )

        expression_presence_ratio = (
            expression_face_frames /
            max(expression_total_frames, 1)
        )

        max_points += 1

        if expression_presence_ratio >= 0.7:

            quality_points += 1

        elif expression_presence_ratio >= 0.4:

            warnings.append(
                "Facial expression face presence is moderate; expression metrics may be less reliable."
            )

        else:

            issues.append(
                "Facial expression face presence is too low."
            )

        # -------------------------
        # Pose quality
        # -------------------------

        pose_presence = SessionValidator.get(
            phenotype_vector,
            "pose_pose_presence_ratio",
            0
        )

        max_points += 1

        if pose_presence >= 0.7:

            quality_points += 1

        elif pose_presence >= 0.4:

            warnings.append(
                "Pose presence ratio is moderate; pose metrics may be less reliable."
            )

        else:

            issues.append(
                "Pose presence ratio is too low; pose metrics may be unreliable."
            )

        # -------------------------
        # Motor quality
        # -------------------------

        motor_presence = SessionValidator.get(
            phenotype_vector,
            "motor_pose_presence_ratio",
            0
        )

        max_points += 1

        if motor_presence >= 0.7:

            quality_points += 1

        elif motor_presence >= 0.4:

            warnings.append(
                "Motor pose presence ratio is moderate; motor stereotypy metrics may be less reliable."
            )

        else:

            issues.append(
                "Motor pose presence ratio is too low; motor metrics may be unreliable."
            )

        # -------------------------
        # Game quality
        # -------------------------

        total_reactions = SessionValidator.get(
            phenotype_vector,
            "game_total_reactions",
            0
        )

        max_points += 1

        if total_reactions >= 10:

            quality_points += 1

        elif total_reactions >= 5:

            warnings.append(
                "Game produced limited reaction events."
            )

        else:

            issues.append(
                "Game produced too few reaction events."
            )

        # -------------------------
        # Name response quality
        # -------------------------

        response_time = SessionValidator.get(
            phenotype_vector,
            "name_response_time",
            0
        )

        max_points += 1

        if response_time > 0:

            quality_points += 1

        else:

            issues.append(
                "Name response was not recorded properly."
            )

        # -------------------------
        # Sanity warnings
        # -------------------------

        blink_rate = SessionValidator.get(
            phenotype_vector,
            "gaze_blink_rate_per_min",
            0
        )

        if blink_rate == 0:

            warnings.append(
                "Blink rate is zero; eye tracking or test duration may need review."
            )

        elif blink_rate > 60:

            warnings.append(
                "Blink rate is unusually high; verify eye landmark tracking quality."
            )

        smile_ratio = SessionValidator.get(
            phenotype_vector,
            "expression_smile_ratio",
            0
        )

        if smile_ratio == 0:

            warnings.append(
                "Smile ratio is zero; this may be valid but should be reviewed."
            )

        motor_index = SessionValidator.get(
            phenotype_vector,
            "motor_stereotypy_index",
            0
        )

        if motor_index > 50:

            warnings.append(
                "Motor stereotypy index is very high; verify whether movement was intentional/test behavior."
            )

        # -------------------------
        # Final quality score
        # -------------------------

        quality_score = (
            quality_points /
            max(max_points, 1)
        )

        is_valid = (
            quality_score >= 0.75
            and
            len(issues) == 0
        )

        if quality_score >= 0.85:

            quality_level = "Good"

        elif quality_score >= 0.65:

            quality_level = "Usable with caution"

        else:

            quality_level = "Poor"

        return {
            "is_valid":
                is_valid,

            "quality_score":
                round(quality_score, 3),

            "quality_level":
                quality_level,

            "issues":
                issues,

            "warnings":
                warnings
        }