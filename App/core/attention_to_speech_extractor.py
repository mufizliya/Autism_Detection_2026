import os
import csv


class AttentionToSpeechExtractor:

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
    def read_csv_rows(file_path):

        if not os.path.exists(file_path):
            return []

        rows = []

        with open(
            file_path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                rows.append(row)

        return rows

    @staticmethod
    def get_session_path(session):

        return session[
            "session_manager"
        ].get_session_path()

    @staticmethod
    def find_speech_stimuli(session):

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        speech_stimuli = []

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            if stimulus.get("type") == "speech_attention_movie":

                speech_stimuli.append(
                    stimulus
                )

        return speech_stimuli

    @staticmethod
    def find_framewise_log(
        session,
        stimulus_id
    ):

        session_path = (
            AttentionToSpeechExtractor.get_session_path(
                session
            )
        )

        expected_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        if os.path.exists(expected_path):
            return expected_path

        for filename in os.listdir(session_path):

            if (
                filename.startswith(stimulus_id)
                and
                filename.endswith("_framewise_log.csv")
            ):

                return os.path.join(
                    session_path,
                    filename
                )

        return None

    @staticmethod
    def get_active_speaker(
        elapsed_time,
        speaker_turns
    ):

        for turn in speaker_turns:

            start_sec = AttentionToSpeechExtractor.to_float(
                turn.get(
                    "start_sec",
                    0
                )
            )

            end_sec = AttentionToSpeechExtractor.to_float(
                turn.get(
                    "end_sec",
                    0
                )
            )

            if (
                elapsed_time >= start_sec
                and
                elapsed_time < end_sec
            ):

                return turn.get(
                    "speaker",
                    ""
                )

        return ""

    @staticmethod
    def get_gaze_side(gaze_x):

        if gaze_x <= 0:
            return ""

        if gaze_x < 0.5:
            return "left"

        return "right"

    @staticmethod
    def compute_for_stimulus(
        rows,
        speaker_turns
    ):

        valid_frames = 0
        matched_frames = 0

        frame_results = []

        for row in rows:

            face_detected = int(
                AttentionToSpeechExtractor.to_float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            elapsed_time = AttentionToSpeechExtractor.to_float(
                row.get(
                    "elapsed_time",
                    0
                )
            )

            gaze_x = AttentionToSpeechExtractor.to_float(
                row.get(
                    "gaze_x",
                    0
                )
            )

            active_speaker = (
                AttentionToSpeechExtractor.get_active_speaker(
                    elapsed_time,
                    speaker_turns
                )
            )

            if active_speaker not in [
                "left",
                "right"
            ]:

                continue

            gaze_side = (
                AttentionToSpeechExtractor.get_gaze_side(
                    gaze_x
                )
            )

            if gaze_side not in [
                "left",
                "right"
            ]:

                continue

            valid_frames += 1

            matched = (
                gaze_side == active_speaker
            )

            if matched:

                matched_frames += 1

            frame_results.append(
                {
                    "elapsed_time":
                        round(
                            elapsed_time,
                            4
                        ),

                    "active_speaker":
                        active_speaker,

                    "gaze_side":
                        gaze_side,

                    "matched":
                        matched
                }
            )

        if valid_frames > 0:

            attention_score = (
                matched_frames /
                valid_frames
            )

        else:

            attention_score = 0.0

        return {
            "valid_frames":
                valid_frames,

            "matched_frames":
                matched_frames,

            "attention_to_speech_score":
                round(
                    attention_score,
                    4
                ),

            "frame_results_sample":
                frame_results[:50]
        }

    @staticmethod
    def build(session):

        speech_stimuli = (
            AttentionToSpeechExtractor.find_speech_stimuli(
                session
            )
        )

        stimulus_results = []

        total_valid_frames = 0
        total_matched_frames = 0

        for stimulus in speech_stimuli:

            stimulus_id = stimulus.get(
                "id",
                ""
            )

            speaker_turns = stimulus.get(
                "speaker_turns",
                []
            )

            log_path = (
                AttentionToSpeechExtractor.find_framewise_log(
                    session,
                    stimulus_id
                )
            )

            if log_path is None:

                stimulus_results.append(
                    {
                        "stimulus_id":
                            stimulus_id,

                        "error":
                            "framewise_log_not_found",

                        "attention_to_speech_score":
                            0
                    }
                )

                continue

            rows = (
                AttentionToSpeechExtractor.read_csv_rows(
                    log_path
                )
            )

            result = (
                AttentionToSpeechExtractor.compute_for_stimulus(
                    rows,
                    speaker_turns
                )
            )

            result["stimulus_id"] = stimulus_id
            result["framewise_log"] = log_path
            result["speaker_turns"] = speaker_turns

            stimulus_results.append(
                result
            )

            total_valid_frames += result.get(
                "valid_frames",
                0
            )

            total_matched_frames += result.get(
                "matched_frames",
                0
            )

        if total_valid_frames > 0:

            overall_score = (
                total_matched_frames /
                total_valid_frames
            )

        else:

            overall_score = 0.0

        return {
            "paper_attention_to_speech":
                round(
                    overall_score,
                    4
                ),

            "paper_gaze_speech_correlation":
                round(
                    overall_score,
                    4
                ),

            "speech_valid_frames":
                total_valid_frames,

            "speech_matched_frames":
                total_matched_frames,

            "speech_stimulus_count":
                len(
                    speech_stimuli
                ),

            "speech_stimulus_results":
                stimulus_results
        }