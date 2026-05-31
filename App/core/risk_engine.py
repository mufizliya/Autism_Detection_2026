class RiskEngine:

    @staticmethod
    def clamp(value, min_value=0, max_value=1):

        return max(
            min_value,
            min(value, max_value)
        )

    @staticmethod
    def get(vector, key, default=0):

        if vector is None:
            return default

        return vector.get(
            key,
            default
        )

    @staticmethod
    def calculate_scq_risk(vector):

        scq_score = RiskEngine.get(
            vector,
            "scq_score",
            0
        )

        scq_risk = RiskEngine.clamp(
            scq_score / 40
        )

        repetitive = RiskEngine.get(
            vector,
            "scq_repetitive_behavior_severity",
            0
        )

        sensory = RiskEngine.get(
            vector,
            "scq_sensory_sensitivity_severity",
            0
        )

        emotional = RiskEngine.get(
            vector,
            "scq_emotional_regulation_severity",
            0
        )

        motor = RiskEngine.get(
            vector,
            "scq_motor_behavior_severity",
            0
        )

        phenotype_risk = (
            repetitive +
            sensory +
            emotional +
            motor
        ) / 4

        return RiskEngine.clamp(
            (scq_risk * 0.6) +
            (phenotype_risk * 0.4)
        )

    @staticmethod
    def calculate_game_risk(vector):

        miss_ratio = RiskEngine.get(
            vector,
            "game_miss_ratio",
            0
        )

        disengagement = RiskEngine.get(
            vector,
            "game_disengagement",
            0
        )

        responsiveness = RiskEngine.get(
            vector,
            "game_responsiveness",
            1
        )

        attention_deficit = RiskEngine.get(
            vector,
            "game_attention_deficit",
            0
        )

        low_responsiveness_risk = (
            1 - responsiveness
        )

        game_risk = (
            (miss_ratio * 0.3) +
            (disengagement * 0.3) +
            (attention_deficit * 0.2) +
            (low_responsiveness_risk * 0.2)
        )

        return RiskEngine.clamp(
            game_risk
        )

    @staticmethod
    def calculate_gaze_risk(vector):

        attention_ratio = RiskEngine.get(
            vector,
            "gaze_attention_ratio",
            1
        )

        face_presence = RiskEngine.get(
            vector,
            "gaze_face_presence_ratio",
            1
        )

        eye_contact = RiskEngine.get(
            vector,
            "gaze_eye_contact_ratio",
            1
        )

        yaw_variability = RiskEngine.get(
            vector,
            "gaze_yaw_variability",
            0
        )

        pitch_variability = RiskEngine.get(
            vector,
            "gaze_pitch_variability",
            0
        )

        low_attention_risk = (
            1 - attention_ratio
        )

        low_face_presence_risk = (
            1 - face_presence
        )

        low_eye_contact_risk = (
            1 - eye_contact
        )

        head_variability_risk = RiskEngine.clamp(
            (
                yaw_variability +
                pitch_variability
            ) / 30
        )

        gaze_risk = (
            (low_attention_risk * 0.35) +
            (low_face_presence_risk * 0.2) +
            (low_eye_contact_risk * 0.25) +
            (head_variability_risk * 0.2)
        )

        return RiskEngine.clamp(
            gaze_risk
        )

    @staticmethod
    def calculate_expression_risk(vector):

        smile_ratio = RiskEngine.get(
            vector,
            "expression_smile_ratio",
            0
        )

        avg_smile = RiskEngine.get(
            vector,
            "expression_avg_smile_score",
            0
        )

        baseline_smile = RiskEngine.get(
            vector,
            "expression_baseline_smile",
            0
        )

        low_smile_ratio_risk = (
            1 - smile_ratio
        )

        smile_change = (
            avg_smile -
            baseline_smile
        )

        low_expression_change_risk = RiskEngine.clamp(
            1 - (smile_change / 1.5)
        )

        expression_risk = (
            (low_smile_ratio_risk * 0.6) +
            (low_expression_change_risk * 0.4)
        )

        return RiskEngine.clamp(
            expression_risk
        )

    @staticmethod
    def calculate_pose_risk(vector):

        body_stability = RiskEngine.get(
            vector,
            "pose_body_stability_score",
            1
        )

        head_variability = RiskEngine.get(
            vector,
            "pose_head_variability",
            0
        )

        shoulder_variability = RiskEngine.get(
            vector,
            "pose_shoulder_variability",
            0
        )

        low_stability_risk = (
            1 - body_stability
        )

        movement_variability_risk = RiskEngine.clamp(
            (
                head_variability +
                shoulder_variability
            ) / 20
        )

        pose_risk = (
            (low_stability_risk * 0.5) +
            (movement_variability_risk * 0.5)
        )

        return RiskEngine.clamp(
            pose_risk
        )

    @staticmethod
    def calculate_motor_risk(vector):

        stereotypy_index = RiskEngine.get(
            vector,
            "motor_stereotypy_index",
            0
        )

        arm_score = RiskEngine.get(
            vector,
            "motor_arm_stereotypy_score",
            0
        )

        frequency = RiskEngine.get(
            vector,
            "motor_oscillation_frequency_hz",
            0
        )

        stereotypy_risk = RiskEngine.clamp(
            stereotypy_index / 50
        )

        arm_variability_risk = RiskEngine.clamp(
            arm_score / 50
        )

        frequency_risk = RiskEngine.clamp(
            frequency / 3
        )

        motor_risk = (
            (stereotypy_risk * 0.5) +
            (arm_variability_risk * 0.3) +
            (frequency_risk * 0.2)
        )

        return RiskEngine.clamp(
            motor_risk
        )

    @staticmethod
    def determine_risk_level(score):

        if score >= 0.75:
            return "High"

        if score >= 0.45:
            return "Moderate"

        return "Low"

    @staticmethod
    def generate_concerns(
        vector,
        scores
    ):

        concerns = []

        if RiskEngine.get(
            vector,
            "scq_score",
            0
        ) >= 15:

            concerns.append(
                "SCQ score indicates need for further evaluation"
            )

        if RiskEngine.get(
            vector,
            "game_miss_ratio",
            0
        ) > 0.6:

            concerns.append(
                "High missed-response ratio during game task"
            )

        if RiskEngine.get(
            vector,
            "game_responsiveness",
            1
        ) < 0.4:

            concerns.append(
                "Low responsiveness during game task"
            )

        if RiskEngine.get(
            vector,
            "gaze_attention_ratio",
            1
        ) < 0.7:

            concerns.append(
                "Reduced visual attention during interaction"
            )

        if RiskEngine.get(
            vector,
            "expression_smile_ratio",
            1
        ) < 0.1:

            concerns.append(
                "Reduced smiling or facial expressiveness"
            )

        if RiskEngine.get(
            vector,
            "pose_body_stability_score",
            1
        ) < 0.2:

            concerns.append(
                "Low body stability score / increased movement variability"
            )

        if RiskEngine.get(
            vector,
            "motor_stereotypy_index",
            0
        ) > 20:

            concerns.append(
                "Elevated repetitive motor movement index"
            )

        if scores.get(
            "motor_risk",
            0
        ) > 0.6:

            concerns.append(
                "Motor phenotype risk is elevated"
            )

        return concerns

    @staticmethod
    def build(phenotype_vector):

        scq_risk = RiskEngine.calculate_scq_risk(
            phenotype_vector
        )

        game_risk = RiskEngine.calculate_game_risk(
            phenotype_vector
        )

        gaze_risk = RiskEngine.calculate_gaze_risk(
            phenotype_vector
        )

        expression_risk = RiskEngine.calculate_expression_risk(
            phenotype_vector
        )

        pose_risk = RiskEngine.calculate_pose_risk(
            phenotype_vector
        )

        motor_risk = RiskEngine.calculate_motor_risk(
            phenotype_vector
        )

        domain_scores = {
            "scq_risk":
                round(scq_risk, 3),

            "game_risk":
                round(game_risk, 3),

            "gaze_risk":
                round(gaze_risk, 3),

            "expression_risk":
                round(expression_risk, 3),

            "pose_risk":
                round(pose_risk, 3),

            "motor_risk":
                round(motor_risk, 3)
        }

        overall_risk_score = (
            (scq_risk * 0.30) +
            (game_risk * 0.15) +
            (gaze_risk * 0.15) +
            (expression_risk * 0.15) +
            (pose_risk * 0.10) +
            (motor_risk * 0.15)
        )

        overall_risk_score = RiskEngine.clamp(
            overall_risk_score
        )

        risk_level = RiskEngine.determine_risk_level(
            overall_risk_score
        )

        primary_concerns = RiskEngine.generate_concerns(
            phenotype_vector,
            domain_scores
        )

        return {
            "overall_risk_score":
                round(overall_risk_score, 3),

            "risk_level":
                risk_level,

            "domain_scores":
                domain_scores,

            "primary_concerns":
                primary_concerns,

            "note":
                (
                    "This is a rule-based screening support score, "
                    "not a clinical diagnosis."
                )
        }