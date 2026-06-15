class ReportGenerator:

    @staticmethod
    def get(data, key, default="N/A"):

        if data is None:
            return default

        return data.get(
            key,
            default
        )

    @staticmethod
    def summarize_scq(session):

        scq_results = session.get(
            "scq_results",
            {}
        )

        questionnaire = session.get(
            "questionnaire",
            {}
        )

        phenotypes = questionnaire.get(
            "phenotypes",
            {}
        )

        return {
            "score":
                scq_results.get(
                    "scq_score",
                    questionnaire.get("score", "N/A")
                ),

            "outcome":
                scq_results.get(
                    "outcome",
                    questionnaire.get("outcome", "N/A")
                ),

            "phenotype_scores":
                phenotypes
        }

    @staticmethod
    def summarize_name_response(session):

        name_response = session.get(
            "name_response",
            {}
        )

        response = name_response.get(
            "response",
            "N/A"
        )

        response_time = name_response.get(
            "response_time",
            "N/A"
        )

        if response == "good":

            interpretation = (
                "Child reported feeling good during the greeting task."
            )

        elif response == "not_good":

            interpretation = (
                "Child reported not feeling good during the greeting task."
            )

        else:

            interpretation = (
                "No valid response was recorded during the greeting task."
            )

        return {
            "response":
                response,

            "response_time_sec":
                round(response_time, 2)
                if isinstance(response_time, (int, float))
                else response_time,

            "interpretation":
                interpretation
        }

    @staticmethod
    def summarize_game(session):

        game = session.get(
            "game_metrics",
            {}
        )

        score = game.get(
            "score",
            0
        )

        total_reactions = game.get(
            "total_reactions",
            0
        )

        reaction_data = game.get(
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

        avg_reaction = (
            sum(reaction_times) /
            len(reaction_times)
            if reaction_times
            else 0
        )

        miss_ratio = (
            len(missed) /
            len(reaction_data)
            if len(reaction_data) > 0
            else 0
        )

        if miss_ratio > 0.6:

            interpretation = (
                "The child missed a high proportion of game targets, "
                "which may suggest reduced task engagement, attention, "
                "or motor responsiveness during this session."
            )

        elif miss_ratio > 0.3:

            interpretation = (
                "The child missed a moderate number of targets during "
                "the game task."
            )

        else:

            interpretation = (
                "The child responded to most game targets successfully."
            )

        return {
            "score":
                score,

            "total_events":
                total_reactions,

            "popped_count":
                len(popped),

            "missed_count":
                len(missed),

            "miss_ratio":
                round(miss_ratio, 3),

            "average_reaction_time_sec":
                round(avg_reaction, 2),

            "interpretation":
                interpretation
        }

    @staticmethod
    def summarize_gaze(session):

        gaze = session.get(
            "gaze_metrics",
            {}
        )

        attention_ratio = gaze.get(
            "attention_ratio",
            0
        )

        face_presence = gaze.get(
            "face_presence_ratio",
            0
        )

        blink_rate = gaze.get(
            "blink_rate_per_min",
            0
        )

        eye_contact = gaze.get(
            "eye_contact_ratio",
            0
        )

        if attention_ratio < 0.7:

            interpretation = (
                "Visual attention appeared reduced during the observed tasks."
            )

        else:

            interpretation = (
                "Visual attention appeared relatively stable during the observed tasks."
            )

        return {
            "face_presence_ratio":
                face_presence,

            "attention_ratio":
                attention_ratio,

            "blink_rate_per_min":
                blink_rate,

            "eye_contact_proxy_ratio":
                eye_contact,

            "interpretation":
                interpretation,

            "note":
                (
                    "Eye contact ratio is a proxy measure based on "
                    "FaceMesh/iris landmarks and should not be treated "
                    "as clinical eye-tracking."
                )
        }

    @staticmethod
    def summarize_expression(session):

        expression = session.get(
            "facial_expression_metrics",
            {}
        )

        smile_ratio = expression.get(
            "smile_ratio",
            0
        )

        avg_smile_score = expression.get(
            "avg_smile_score",
            0
        )

        baseline_smile = expression.get(
            "baseline_smile",
            0
        )

        if smile_ratio < 0.1:

            interpretation = (
                "Facial expressiveness appeared reduced based on smile activity "
                "during the observed session."
            )

        elif smile_ratio < 0.3:

            interpretation = (
                "Some smiling or positive facial expression was observed."
            )

        else:

            interpretation = (
                "Frequent smiling or positive facial expression was observed."
            )

        return {
            "baseline_smile_score":
                baseline_smile,

            "average_smile_score":
                avg_smile_score,

            "smile_ratio":
                smile_ratio,

            "interpretation":
                interpretation
        }

    @staticmethod
    def summarize_pose(session):

        pose = session.get(
            "pose_metrics",
            {}
        )

        body_stability = pose.get(
            "body_stability_score",
            0
        )

        head_variability = pose.get(
            "head_variability",
            0
        )

        shoulder_variability = pose.get(
            "shoulder_variability",
            0
        )

        if body_stability < 0.2:

            interpretation = (
                "Body stability score was low, suggesting increased movement "
                "or postural variability during the session."
            )

        else:

            interpretation = (
                "Body posture appeared relatively stable during the session."
            )

        return {
            "body_stability_score":
                body_stability,

            "head_variability":
                head_variability,

            "shoulder_variability":
                shoulder_variability,

            "interpretation":
                interpretation
        }

    @staticmethod
    def summarize_motor(session):

        motor = session.get(
            "motor_metrics",
            {}
        )

        stereotypy_index = motor.get(
            "stereotypy_index",
            0
        )

        oscillation_frequency = motor.get(
            "oscillation_frequency_hz",
            0
        )

        arm_score = motor.get(
            "arm_stereotypy_score",
            0
        )

        if stereotypy_index > 20:

            interpretation = (
                "Repetitive upper-limb movement index was elevated during "
                "the session."
            )

        elif stereotypy_index > 10:

            interpretation = (
                "Some repetitive upper-limb movement was observed."
            )

        else:

            interpretation = (
                "No strong repetitive upper-limb movement pattern was detected."
            )

        return {
            "arm_stereotypy_score":
                arm_score,

            "oscillation_frequency_hz":
                oscillation_frequency,

            "stereotypy_index":
                stereotypy_index,

            "interpretation":
                interpretation
        }

    @staticmethod
    def summarize_risk(session):

        risk = session.get(
            "risk_assessment",
            {}
        )

        return {
            "overall_risk_score":
                risk.get(
                    "overall_risk_score",
                    "N/A"
                ),

            "risk_level":
                risk.get(
                    "risk_level",
                    "N/A"
                ),

            "domain_scores":
                risk.get(
                    "domain_scores",
                    {}
                ),

            "primary_concerns":
                risk.get(
                    "primary_concerns",
                    []
                ),

            "note":
                risk.get(
                    "note",
                    (
                        "This report is not a clinical diagnosis."
                    )
                )
        }

    @staticmethod
    def build(session):

        child_info = session.get(
            "child_info",
            {}
        )

        report = {
            "session_id":
                session.get(
                    "session_id",
                    "N/A"
                ),

            "child_information": {
                "name":
                    child_info.get(
                        "name",
                        "N/A"
                    ),

                "age":
                    child_info.get(
                        "age",
                        "N/A"
                    ),

                "gender":
                    child_info.get(
                        "gender",
                        "N/A"
                    ),

                "timestamp":
                    child_info.get(
                        "timestamp",
                        "N/A"
                    )
            },

            "scq_summary":
                ReportGenerator.summarize_scq(
                    session
                ),

            "name_response_summary":
                ReportGenerator.summarize_name_response(
                    session
                ),

            "game_summary":
                ReportGenerator.summarize_game(
                    session
                ),

            "gaze_attention_summary":
                ReportGenerator.summarize_gaze(
                    session
                ),

            "facial_expression_summary":
                ReportGenerator.summarize_expression(
                    session
                ),

            "pose_stability_summary":
                ReportGenerator.summarize_pose(
                    session
                ),

            "motor_stereotypy_summary":
                ReportGenerator.summarize_motor(
                    session
                ),

            "risk_summary":
                ReportGenerator.summarize_risk(
                    session
                ),

            "disclaimer":
                (
                    "This report is generated by a prototype screening "
                    "support system. It is intended for research and "
                    "decision-support purposes only and must not be used "
                    "as a clinical diagnosis. Clinical interpretation "
                    "should be performed by qualified professionals."
                )
        }

        return report