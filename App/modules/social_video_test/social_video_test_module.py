import time

from core.tracker_manager import TrackerManager
from core.stimulus_protocol import StimulusProtocol
from core.framewise_behavior_recorder import FramewiseBehaviorRecorder


class PrefixedSessionManager:

    def __init__(
        self,
        real_session_manager,
        prefix
    ):

        self.real_session_manager = real_session_manager
        self.prefix = prefix

    def save_json(
        self,
        filename,
        data
    ):

        prefixed_filename = (
            f"{self.prefix}_{filename}"
        )

        self.real_session_manager.save_json(
            prefixed_filename,
            data
        )


class SocialVideoTestModule:

    def __init__(self):

        self.protocol = StimulusProtocol()

        self.results = {
            "protocol_summary": {},
            "stimulus_results": [],
            "name_call_events": [],
            "category_summary": {}
        }

    def run_stimulus_with_tracking(
        self,
        session,
        stimulus
        ):

        stimulus_id = stimulus.get(
            "id",
            "unknown_stimulus"
        )

        stimulus_type = stimulus.get(
            "type",
            "unknown_type"
        )

        paper_category = stimulus.get(
            "paper_category",
            "unknown_category"
        )

        recorder = FramewiseBehaviorRecorder()

        recorder.start(
            session=session,
            stimulus_id=stimulus_id,
            stimulus_type=stimulus_type,
            paper_category=paper_category
        )

        video_metrics = (
            self.protocol.play_video_segment(
                stimulus,
                window_name=stimulus_id.upper()
            )
        )

        framewise_summary = recorder.stop()

        result = {
            "stimulus":
                stimulus,

            "video_metrics":
                video_metrics,

            "framewise_summary":
                framewise_summary,

            "gaze_metrics": {
                "face_presence_ratio":
                    framewise_summary.get(
                        "face_presence_ratio",
                        0
                    ),

                "blink_count":
                    framewise_summary.get(
                        "blink_count",
                        0
                    ),

                "blink_rate_per_min":
                    framewise_summary.get(
                        "blink_rate_per_min",
                        0
                    ),

                "attention_ratio":
                    framewise_summary.get(
                        "face_presence_ratio",
                        0
                    ),

                "gaze_variability":
                    framewise_summary.get(
                        "gaze_variability",
                        0
                    ),

                "yaw_variability":
                    framewise_summary.get(
                        "yaw_variability",
                        0
                    ),

                "pitch_variability":
                    framewise_summary.get(
                        "pitch_variability",
                        0
                    )
            },

            "facial_expression_metrics": {
                "avg_smile_score":
                    framewise_summary.get(
                        "mouth_open_mean",
                        0
                    ),

                "smile_ratio":
                    framewise_summary.get(
                        "mouth_open_mean",
                        0
                    ),

                "mouth_complexity_proxy":
                    framewise_summary.get(
                        "mouth_complexity_proxy",
                        0
                    ),

                "eyebrow_complexity_proxy":
                    framewise_summary.get(
                        "eyebrow_complexity_proxy",
                        0
                    )
            },

            "pose_metrics": {
                "pose_presence_ratio":
                    framewise_summary.get(
                        "face_presence_ratio",
                        0
                    ),

                "head_variability":
                    framewise_summary.get(
                        "head_movement_mean",
                        0
                    ),

                "head_movement_complexity_proxy":
                    framewise_summary.get(
                        "head_movement_complexity_proxy",
                        0
                    ),

                "head_acceleration_mean":
                    framewise_summary.get(
                        "head_acceleration_mean",
                        0
                    )
            },

            "motor_metrics": {
                "pose_presence_ratio":
                    framewise_summary.get(
                        "face_presence_ratio",
                        0
                    ),

                "arm_stereotypy_score":
                    0,

                "oscillation_frequency_hz":
                    0,

                "stereotypy_index":
                    0
            }
        }

        return result

    def build_category_summary(
        self,
        stimulus_results
    ):

        summary = {
            "social": {
                "count": 0,
                "attention_values": [],
                "blink_values": [],
                "smile_values": [],
                "head_values": []
            },
            "non_social": {
                "count": 0,
                "attention_values": [],
                "blink_values": [],
                "smile_values": [],
                "head_values": []
            },
            "mixed_social_non_social": {
                "count": 0,
                "attention_values": [],
                "blink_values": [],
                "smile_values": [],
                "head_values": []
            },
            "speech_social": {
                "count": 0,
                "attention_values": [],
                "blink_values": [],
                "smile_values": [],
                "head_values": []
            }
        }

        for result in stimulus_results:

            stimulus = result.get(
                "stimulus",
                {}
            )

            category = stimulus.get(
                "paper_category",
                "unknown"
            )

            if category not in summary:
                continue

            gaze_metrics = result.get(
                "gaze_metrics",
                {}
            )

            expression_metrics = result.get(
                "facial_expression_metrics",
                {}
            )

            pose_metrics = result.get(
                "pose_metrics",
                {}
            )

            summary[category]["count"] += 1

            summary[category]["attention_values"].append(
                gaze_metrics.get(
                    "attention_ratio",
                    0
                )
            )

            summary[category]["blink_values"].append(
                gaze_metrics.get(
                    "blink_rate_per_min",
                    0
                )
            )

            summary[category]["smile_values"].append(
                expression_metrics.get(
                    "smile_ratio",
                    0
                )
            )

            summary[category]["head_values"].append(
                pose_metrics.get(
                    "head_variability",
                    0
                )
            )

        compact_summary = {}

        for category, values in summary.items():

            count = values["count"]

            def avg(items):

                if len(items) == 0:
                    return 0

                return round(
                    sum(items) / len(items),
                    4
                )

            compact_summary[category] = {
                "count":
                    count,

                "avg_attention_ratio":
                    avg(
                        values["attention_values"]
                    ),

                "avg_blink_rate_per_min":
                    avg(
                        values["blink_values"]
                    ),

                "avg_smile_ratio":
                    avg(
                        values["smile_values"]
                    ),

                "avg_head_variability":
                    avg(
                        values["head_values"]
                    )
            }

        social_attention = compact_summary.get(
            "social",
            {}
        ).get(
            "avg_attention_ratio",
            0
        )

        nonsocial_attention = compact_summary.get(
            "non_social",
            {}
        ).get(
            "avg_attention_ratio",
            0
        )

        compact_summary["comparison"] = {
            "social_attention_average":
                social_attention,

            "nonsocial_attention_average":
                nonsocial_attention,

            "social_preference_score":
                round(
                    social_attention -
                    nonsocial_attention,
                    4
                )
        }

        return compact_summary

    def run(
        self,
        session
    ):

        print()
        print("==============================")
        print("PAPER-MATCH STIMULUS VIDEO TEST STARTED")
        print("==============================")
        print()

        protocol_summary = (
            self.protocol.build_protocol_summary()
        )

        stimulus_results = []

        video_stimuli = (
            self.protocol.get_video_stimuli()
        )

        for stimulus in video_stimuli:

            result = self.run_stimulus_with_tracking(
                session,
                stimulus
            )

            stimulus_results.append(
                result
            )

            time.sleep(0.5)

        name_call_events = (
            self.protocol.get_name_call_events()
        )

        category_summary = (
            self.build_category_summary(
                stimulus_results
            )
        )

        self.results = {
            "protocol_summary":
                protocol_summary,

            "stimulus_results":
                stimulus_results,

            "name_call_events":
                name_call_events,

            "category_summary":
                category_summary
        }

        session["video_test"] = (
            self.results
        )

        session[
            "session_manager"
        ].save_json(
            "stimulus_protocol_summary.json",
            protocol_summary
        )

        session[
            "session_manager"
        ].save_json(
            "stimulus_events.json",
            {
                "video_stimuli":
                    video_stimuli,

                "name_call_events":
                    name_call_events
            }
        )

        session[
            "session_manager"
        ].save_json(
            "video_test.json",
            self.results
        )

        print()
        print("✅ Paper-match Stimulus Video Test Completed")
        print()

        return self.results