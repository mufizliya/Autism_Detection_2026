import os
import csv
import json


class ResponseToNameExtractor:

    RESPONSE_WINDOW_SEC = 3.0
    MIN_RESPONSE_DELAY_SEC = 0.15

    YAW_CHANGE_THRESHOLD = 0.12
    HEAD_MOVEMENT_THRESHOLD = 0.015

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
    def load_csv_rows(path):

        if not os.path.exists(path):
            return []

        rows = []

        with open(
            path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                rows.append(row)

        return rows

    @staticmethod
    def load_name_call_events(session):

        video_test = session.get(
            "video_test",
            {}
        )

        triggered_events = video_test.get(
            "triggered_name_call_events",
            []
        )

        if triggered_events:
            return triggered_events

        session_manager = session.get(
            "session_manager"
        )

        if session_manager is not None:

            session_path = session_manager.get_session_path()

            stimulus_events_path = os.path.join(
                session_path,
                "stimulus_events.json"
            )

            if os.path.exists(stimulus_events_path):

                with open(
                    stimulus_events_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                triggered_events = data.get(
                    "triggered_name_call_events",
                    []
                )

                if triggered_events:
                    return triggered_events

                return data.get(
                    "scheduled_name_call_events",
                    []
                )

        return []

    @staticmethod
    def get_stimulus_id_from_event(event):

        stimulus_id = event.get(
            "stimulus_id",
            ""
        )

        if stimulus_id == "":

            stimulus_id = event.get(
                "during_stimulus",
                ""
            )

        return stimulus_id

    @staticmethod
    def get_call_time_sec(event):

        # In our current master-video pipeline:
        # actual_trigger_time_sec = local time inside the stimulus.
        if "actual_trigger_time_sec" in event:

            return ResponseToNameExtractor.to_float(
                event.get(
                    "actual_trigger_time_sec",
                    0
                )
            )

        return ResponseToNameExtractor.to_float(
            event.get(
                "call_time_sec",
                0
            )
        )

    @staticmethod
    def normalize_rows_to_local_time(rows):

        if len(rows) == 0:
            return rows

        elapsed_values = [
            ResponseToNameExtractor.to_float(
                row.get(
                    "elapsed_time",
                    0
                )
            )
            for row in rows
        ]

        first_elapsed = min(
            elapsed_values
        )

        normalized = []

        for row in rows:

            row_copy = dict(
                row
            )

            elapsed = ResponseToNameExtractor.to_float(
                row_copy.get(
                    "elapsed_time",
                    0
                )
            )

            row_copy["local_elapsed_time"] = (
                elapsed
                -
                first_elapsed
            )

            normalized.append(
                row_copy
            )

        return normalized

    @staticmethod
    def get_face_rows(rows):

        face_rows = []

        for row in rows:

            face_detected = ResponseToNameExtractor.to_float(
                row.get(
                    "face_detected",
                    0
                )
            )

            if face_detected == 1:
                face_rows.append(row)

        return face_rows

    @staticmethod
    def get_baseline_yaw(rows, call_time_sec):

        baseline_rows = []

        for row in rows:

            local_time = ResponseToNameExtractor.to_float(
                row.get(
                    "local_elapsed_time",
                    0
                )
            )

            if (
                local_time >= call_time_sec - 0.5
                and
                local_time <= call_time_sec
            ):

                baseline_rows.append(row)

        if baseline_rows:

            yaw_values = [
                ResponseToNameExtractor.to_float(
                    row.get(
                        "yaw_proxy",
                        0
                    )
                )
                for row in baseline_rows
            ]

            return sum(yaw_values) / len(yaw_values)

        # Fallback: nearest row before call.
        before_rows = []

        for row in rows:

            local_time = ResponseToNameExtractor.to_float(
                row.get(
                    "local_elapsed_time",
                    0
                )
            )

            if local_time <= call_time_sec:
                before_rows.append(row)

        if before_rows:

            nearest = before_rows[-1]

            return ResponseToNameExtractor.to_float(
                nearest.get(
                    "yaw_proxy",
                    0
                )
            )

        if rows:

            return ResponseToNameExtractor.to_float(
                rows[0].get(
                    "yaw_proxy",
                    0
                )
            )

        return 0.0

    @staticmethod
    def detect_response(rows, call_time_sec):

        face_rows = ResponseToNameExtractor.get_face_rows(
            rows
        )

        if len(face_rows) == 0:

            return {
                "responded":
                    False,

                "delay_sec":
                    None,

                "reason":
                    "no_face_rows",

                "response_window_rows":
                    0
            }

        baseline_yaw = ResponseToNameExtractor.get_baseline_yaw(
            face_rows,
            call_time_sec
        )

        response_rows = []

        for row in face_rows:

            local_time = ResponseToNameExtractor.to_float(
                row.get(
                    "local_elapsed_time",
                    0
                )
            )

            if (
                local_time >= call_time_sec + ResponseToNameExtractor.MIN_RESPONSE_DELAY_SEC
                and
                local_time <= call_time_sec + ResponseToNameExtractor.RESPONSE_WINDOW_SEC
            ):

                response_rows.append(row)

        if len(response_rows) == 0:

            return {
                "responded":
                    False,

                "delay_sec":
                    None,

                "reason":
                    "no_response_window_rows",

                "response_window_rows":
                    0,

                "baseline_yaw":
                    round(
                        baseline_yaw,
                        4
                    )
            }

        max_yaw_change = 0.0
        max_head_movement = 0.0

        for row in response_rows:

            local_time = ResponseToNameExtractor.to_float(
                row.get(
                    "local_elapsed_time",
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
                yaw
                -
                baseline_yaw
            )

            max_yaw_change = max(
                max_yaw_change,
                yaw_change
            )

            max_head_movement = max(
                max_head_movement,
                head_movement
            )

            if (
                yaw_change >= ResponseToNameExtractor.YAW_CHANGE_THRESHOLD
                or
                head_movement >= ResponseToNameExtractor.HEAD_MOVEMENT_THRESHOLD
            ):

                return {
                    "responded":
                        True,

                    "delay_sec":
                        round(
                            local_time - call_time_sec,
                            4
                        ),

                    "reason":
                        "head_turn_detected",

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

                    "baseline_yaw":
                        round(
                            baseline_yaw,
                            4
                        ),

                    "response_window_rows":
                        len(response_rows),

                    "max_yaw_change_in_window":
                        round(
                            max_yaw_change,
                            4
                        ),

                    "max_head_movement_in_window":
                        round(
                            max_head_movement,
                            4
                        )
                }

        return {
            "responded":
                False,

            "delay_sec":
                None,

            "reason":
                "no_head_turn_above_threshold",

            "baseline_yaw":
                round(
                    baseline_yaw,
                    4
                ),

            "response_window_rows":
                len(response_rows),

            "max_yaw_change_in_window":
                round(
                    max_yaw_change,
                    4
                ),

            "max_head_movement_in_window":
                round(
                    max_head_movement,
                    4
                )
        }

    @staticmethod
    def analyze_event(session, event):

        stimulus_id = ResponseToNameExtractor.get_stimulus_id_from_event(
            event
        )

        call_time_sec = ResponseToNameExtractor.get_call_time_sec(
            event
        )

        session_manager = session.get(
            "session_manager"
        )

        session_path = session_manager.get_session_path()

        framewise_log_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        rows = ResponseToNameExtractor.load_csv_rows(
            framewise_log_path
        )

        rows = ResponseToNameExtractor.normalize_rows_to_local_time(
            rows
        )

        result = ResponseToNameExtractor.detect_response(
            rows,
            call_time_sec
        )

        output = {
            "call_index":
                event.get(
                    "call_index"
                ),

            "during_stimulus":
                stimulus_id,

            "call_time_sec":
                round(
                    call_time_sec,
                    4
                ),

            "framewise_log":
                framewise_log_path
        }

        output.update(
            result
        )

        return output

    @staticmethod
    def build(session):

        name_call_events = ResponseToNameExtractor.load_name_call_events(
            session
        )

        call_results = []

        response_count = 0
        delays = []

        for event in name_call_events:

            result = ResponseToNameExtractor.analyze_event(
                session,
                event
            )

            call_results.append(
                result
            )

            if result.get(
                "responded",
                False
            ):

                response_count += 1

                delay = result.get(
                    "delay_sec"
                )

                if delay is not None:

                    delays.append(
                        delay
                    )

        call_count = len(
            name_call_events
        )

        if call_count > 0:

            response_proportion = (
                response_count
                /
                call_count
            )

        else:

            response_proportion = 0.0

        if delays:

            average_delay = (
                sum(delays)
                /
                len(delays)
            )

        else:

            average_delay = None

        return {
            "paper_response_to_name_proportion":
                round(
                    response_proportion,
                    4
                ),

            "paper_response_to_name_delay":
                (
                    round(
                        average_delay,
                        4
                    )
                    if average_delay is not None
                    else None
                ),

            "name_call_count":
                call_count,

            "name_response_count":
                response_count,

            "name_call_results":
                call_results
        }