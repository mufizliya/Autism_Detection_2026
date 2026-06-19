import os
import csv


class AttentionToSpeechExtractor:

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
    def is_face_valid(row):

        face_detected = AttentionToSpeechExtractor.to_float(
            row.get(
                "face_detected",
                0
            )
        )

        return face_detected == 1

    @staticmethod
    def get_gaze_xy(row):

        gaze_x = AttentionToSpeechExtractor.to_float(
            row.get(
                "gaze_x",
                -1
            ),
            default=-1
        )

        gaze_y = AttentionToSpeechExtractor.to_float(
            row.get(
                "gaze_y",
                -1
            ),
            default=-1
        )

        return gaze_x, gaze_y

    @staticmethod
    def load_framewise_rows(framewise_log_path):

        if not os.path.exists(
            framewise_log_path
        ):

            return []

        rows = []

        with open(
            framewise_log_path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(
                f
            )

            for row in reader:

                rows.append(
                    row
                )

        return rows

    @staticmethod
    def get_local_elapsed_time(row, first_elapsed_time):

        elapsed_time = AttentionToSpeechExtractor.to_float(
            row.get(
                "elapsed_time",
                0
            )
        )

        return elapsed_time - first_elapsed_time

    @staticmethod
    def get_active_speaker_turn(local_time, speaker_turns):

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
                local_time >= start_sec
                and
                local_time <= end_sec
            ):

                return turn

        return None

    @staticmethod
    def gaze_matches_speaker(
        gaze_x,
        gaze_y,
        speaker_turn
    ):

        speaker = str(
            speaker_turn.get(
                "speaker",
                ""
            )
        ).strip().lower()

        aoi = speaker_turn.get(
            "aoi",
            None
        )

        # Preferred logic: use AOI boxes if present.
        if isinstance(aoi, dict):

            x_min = AttentionToSpeechExtractor.to_float(
                aoi.get(
                    "x_min",
                    0
                )
            )

            y_min = AttentionToSpeechExtractor.to_float(
                aoi.get(
                    "y_min",
                    0
                )
            )

            x_max = AttentionToSpeechExtractor.to_float(
                aoi.get(
                    "x_max",
                    1
                )
            )

            y_max = AttentionToSpeechExtractor.to_float(
                aoi.get(
                    "y_max",
                    1
                )
            )

            if (
                gaze_x >= x_min
                and
                gaze_x <= x_max
                and
                gaze_y >= y_min
                and
                gaze_y <= y_max
            ):

                return True

        # Fallback logic for older schedules.
        if speaker == "left":

            return gaze_x < 0.5

        if speaker == "right":

            return gaze_x >= 0.5

        if speaker == "center":

            return (
                gaze_x >= 0.20
                and
                gaze_x <= 0.80
            )

        return False

    @staticmethod
    def find_speech_stimulus_results(session):

        video_test = session.get(
            "video_test",
            {}
        )

        stimulus_results = video_test.get(
            "stimulus_results",
            []
        )

        speech_results = []

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            speaker_turns = stimulus.get(
                "speaker_turns",
                []
            )

            if isinstance(
                speaker_turns,
                list
            ) and len(speaker_turns) > 0:

                speech_results.append(
                    result
                )

        return speech_results

    @staticmethod
    def analyze_stimulus(
        session,
        stimulus_result
    ):

        stimulus = stimulus_result.get(
            "stimulus",
            {}
        )

        stimulus_id = stimulus.get(
            "id",
            ""
        )

        speaker_turns = stimulus.get(
            "speaker_turns",
            []
        )

        session_manager = session.get(
            "session_manager"
        )

        session_path = session_manager.get_session_path()

        framewise_log_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        rows = AttentionToSpeechExtractor.load_framewise_rows(
            framewise_log_path
        )

        if len(rows) == 0:

            return {
                "stimulus_id":
                    stimulus_id,

                "framewise_log":
                    framewise_log_path,

                "speaker_turns":
                    speaker_turns,

                "valid_frames":
                    0,

                "matched_frames":
                    0,

                "attention_to_speech_score":
                    0.0,

                "frame_results_sample":
                    [],

                "error":
                    "no_framewise_rows"
            }

        first_elapsed_time = AttentionToSpeechExtractor.to_float(
            rows[0].get(
                "elapsed_time",
                0
            )
        )

        valid_frames = 0
        matched_frames = 0
        frame_results_sample = []

        for row in rows:

            if not AttentionToSpeechExtractor.is_face_valid(
                row
            ):

                continue

            local_time = AttentionToSpeechExtractor.get_local_elapsed_time(
                row,
                first_elapsed_time
            )

            active_turn = AttentionToSpeechExtractor.get_active_speaker_turn(
                local_time,
                speaker_turns
            )

            if active_turn is None:
                continue

            gaze_x, gaze_y = AttentionToSpeechExtractor.get_gaze_xy(
                row
            )

            if gaze_x < 0 or gaze_y < 0:
                continue

            valid_frames += 1

            matched = AttentionToSpeechExtractor.gaze_matches_speaker(
                gaze_x,
                gaze_y,
                active_turn
            )

            if matched:

                matched_frames += 1

            if len(frame_results_sample) < 20:

                frame_results_sample.append(
                    {
                        "local_time":
                            round(
                                local_time,
                                3
                            ),

                        "speaker":
                            active_turn.get(
                                "speaker",
                                ""
                            ),

                        "gaze_x":
                            round(
                                gaze_x,
                                4
                            ),

                        "gaze_y":
                            round(
                                gaze_y,
                                4
                            ),

                        "matched":
                            matched
                    }
                )

        if valid_frames > 0:

            attention_score = matched_frames / valid_frames

        else:

            attention_score = 0.0

        return {
            "stimulus_id":
                stimulus_id,

            "framewise_log":
                framewise_log_path,

            "speaker_turns":
                speaker_turns,

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
                frame_results_sample
        }

    @staticmethod
    def build(session):

        speech_results = (
            AttentionToSpeechExtractor
            .find_speech_stimulus_results(
                session
            )
        )

        stimulus_outputs = []

        total_valid_frames = 0
        total_matched_frames = 0

        for stimulus_result in speech_results:

            output = AttentionToSpeechExtractor.analyze_stimulus(
                session,
                stimulus_result
            )

            stimulus_outputs.append(
                output
            )

            total_valid_frames += int(
                output.get(
                    "valid_frames",
                    0
                )
            )

            total_matched_frames += int(
                output.get(
                    "matched_frames",
                    0
                )
            )

        if total_valid_frames > 0:

            attention_to_speech = (
                total_matched_frames
                /
                total_valid_frames
            )

        else:

            attention_to_speech = 0.0

        return {
            "paper_attention_to_speech":
                round(
                    attention_to_speech,
                    4
                ),

            "paper_gaze_speech_correlation":
                round(
                    attention_to_speech,
                    4
                ),

            "speech_valid_frames":
                total_valid_frames,

            "speech_matched_frames":
                total_matched_frames,

            "speech_stimulus_count":
                len(
                    speech_results
                ),

            "speech_stimulus_results":
                stimulus_outputs
        }