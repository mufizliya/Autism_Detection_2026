import os
import csv
import json


class ResponseToNameExtractor:

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
    def find_framewise_log(
        session,
        stimulus_id
    ):

        session_path = (
            ResponseToNameExtractor.get_session_path(
                session
            )
        )

        expected_file = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        if os.path.exists(expected_file):
            return expected_file

        for filename in os.listdir(session_path):

            if filename.endswith("_framewise_log.csv"):

                if filename.startswith(stimulus_id):

                    return os.path.join(
                        session_path,
                        filename
                    )

        return None

    @staticmethod
    def load_name_call_events(session):

        video_test = session.get(
            "video_test",
            {}
        )

        name_events = video_test.get(
            "name_call_events",
            []
        )

        if name_events:
            return name_events

        session_path = (
            ResponseToNameExtractor.get_session_path(
                session
            )
        )

        stimulus_events_path = os.path.join(
            session_path,
            "stimulus_events.json"
        )

        if not os.path.exists(stimulus_events_path):
            return []

        try:

            with open(
                stimulus_events_path,
                "r"
            ) as f:

                data = json.load(f)

            return data.get(
                "name_call_events",
                []
            )

        except Exception:

            return []

    @staticmethod
    def detect_response_in_rows(
        rows,
        call_time_sec,
        response_window_sec=3.0,
        baseline_window_sec=0.8,
        yaw_threshold=0.08,
        movement_threshold=0.025
    ):

        """
        Paper idea:
        after name call, child responds by orienting/head turn.

        Our detection:
        - compute baseline yaw before call
        - search after call for yaw change or head movement spike
        - first valid response gives delay
        """

        if len(rows) == 0:

            return {
                "responded":
                    False,

                "delay_sec":
                    None,

                "reason":
                    "no_framewise_rows"
            }

        baseline_rows = []
        response_rows = []

        for row in rows:

            elapsed = ResponseToNameExtractor.to_float(
                row.get(
                    "elapsed_time",
                    0
                )
            )

            face_detected = int(
                ResponseToNameExtractor.to_float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            if (
                elapsed >= call_time_sec - baseline_window_sec
                and
                elapsed < call_time_sec
            ):

                baseline_rows.append(row)

            if (
                elapsed >= call_time_sec
                and
                elapsed <= call_time_sec + response_window_sec
            ):

                response_rows.append(row)

        if len(response_rows) == 0:

            return {
                "responded":
                    False,

                "delay_sec":
                    None,

                "reason":
                    "no_response_window_rows"
            }

        if len(baseline_rows) > 0:

            baseline_yaw = sum(
                ResponseToNameExtractor.to_float(
                    row.get(
                        "yaw_proxy",
                        0
                    )
                )
                for row in baseline_rows
            ) / len(baseline_rows)

        else:

            baseline_yaw = ResponseToNameExtractor.to_float(
                response_rows[0].get(
                    "yaw_proxy",
                    0
                )
            )

        for row in response_rows:

            elapsed = ResponseToNameExtractor.to_float(
                row.get(
                    "elapsed_time",
                    0
                )
            )

            yaw = ResponseToNameExtractor.to_float(
                row.get(
                    "yaw_proxy",
                    0
                )
            )

            head_movement = ResponseToNameExtractor.to_float(
                row.get(
                    "head_movement",
                    0
                )
            )

            yaw_change = abs(
                yaw - baseline_yaw
            )

            if (
                yaw_change >= yaw_threshold
                or
                head_movement >= movement_threshold
            ):

                return {
                    "responded":
                        True,

                    "delay_sec":
                        round(
                            elapsed - call_time_sec,
                            4
                        ),

                    "yaw_change":
                        round(
                            yaw_change,
                            4
                        ),

                    "head_movement":
                        round(
                            head_movement,
                            4
                        ),

                    "reason":
                        "head_turn_detected"
                }

        return {
            "responded":
                False,

            "delay_sec":
                None,

            "reason":
                "no_head_turn_detected"
        }

    @staticmethod
    def build(session):

        name_events = (
            ResponseToNameExtractor.load_name_call_events(
                session
            )
        )

        call_results = []

        for event in name_events:

            stimulus_id = event.get(
                "during_stimulus"
            )

            call_index = event.get(
                "call_index",
                len(call_results) + 1
            )

            call_time_sec = (
                ResponseToNameExtractor.to_float(
                    event.get(
                        "call_time_sec",
                        0
                    )
                )
            )

            log_path = (
                ResponseToNameExtractor.find_framewise_log(
                    session,
                    stimulus_id
                )
            )

            if log_path is None:

                call_results.append(
                    {
                        "call_index":
                            call_index,

                        "during_stimulus":
                            stimulus_id,

                        "call_time_sec":
                            call_time_sec,

                        "responded":
                            False,

                        "delay_sec":
                            None,

                        "reason":
                            "framewise_log_not_found"
                    }
                )

                continue

            rows = (
                ResponseToNameExtractor.read_csv_rows(
                    log_path
                )
            )

            detection = (
                ResponseToNameExtractor.detect_response_in_rows(
                    rows,
                    call_time_sec
                )
            )

            result = {
                "call_index":
                    call_index,

                "during_stimulus":
                    stimulus_id,

                "call_time_sec":
                    call_time_sec,

                "framewise_log":
                    log_path,

                "responded":
                    detection.get(
                        "responded",
                        False
                    ),

                "delay_sec":
                    detection.get(
                        "delay_sec"
                    ),

                "reason":
                    detection.get(
                        "reason"
                    )
            }

            if "yaw_change" in detection:

                result["yaw_change"] = detection.get(
                    "yaw_change"
                )

            if "head_movement" in detection:

                result["head_movement"] = detection.get(
                    "head_movement"
                )

            call_results.append(
                result
            )

        total_calls = len(
            call_results
        )

        responded_calls = [
            call
            for call in call_results
            if call.get("responded") is True
        ]

        delays = [
            call.get("delay_sec")
            for call in responded_calls
            if call.get("delay_sec") is not None
        ]

        response_count = len(
            responded_calls
        )

        if total_calls > 0:

            response_proportion = (
                response_count /
                total_calls
            )

        else:

            response_proportion = 0.0

        if len(delays) > 0:

            average_delay = (
                sum(delays)
                /
                len(delays)
            )

        else:

            average_delay = 0.0

        features = {
            "paper_response_to_name_proportion":
                round(
                    response_proportion,
                    4
                ),

            "paper_response_to_name_delay":
                round(
                    average_delay,
                    4
                ),

            "name_call_count":
                total_calls,

            "name_response_count":
                response_count,

            "name_call_results":
                call_results
        }

        return features