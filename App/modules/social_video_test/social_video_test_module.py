import time
import cv2

from core.stimulus_protocol import StimulusProtocol
from core.continuous_framewise_behavior_recorder import ContinuousFramewiseBehaviorRecorder


class SocialVideoTestModule:

    def __init__(self):

        self.protocol = StimulusProtocol()

        self.results = {
            "stimulus_results": [],
            "category_summary": {},
            "name_call_events": [],
            "triggered_name_call_events": [],
            "protocol_summary": {}
        }

    @staticmethod
    def safe_mean(values):

        if len(values) == 0:
            return 0.0

        return sum(values) / len(values)

    def get_child_name(
        self,
        session
    ):

        child_name = ""

        child_info = session.get(
            "child_info",
            {}
        )

        questionnaire = session.get(
            "questionnaire",
            {}
        )

        if isinstance(child_info, dict):

            child_name = child_info.get(
                "name",
                ""
            )

        if child_name == "" and isinstance(questionnaire, dict):

            child_name = questionnaire.get(
                "name",
                ""
            )

        return child_name

    def play_single_stimulus(
        self,
        stimulus,
        recorder,
        child_name,
        window_name
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

        recorder.set_current_stimulus(
            stimulus_id,
            stimulus_type,
            paper_category
        )

        video_path = self.protocol.resolve_video_path(
            stimulus.get(
                "video_path"
            )
        )

        if video_path is None:

            return {
                "stimulus_id":
                    stimulus_id,

                "played":
                    False,

                "error":
                    "missing_video_path",

                "triggered_name_call_events":
                    []
            }

        cap = cv2.VideoCapture(
            video_path
        )

        if not cap.isOpened():

            return {
                "stimulus_id":
                    stimulus_id,

                "video_path":
                    video_path,

                "played":
                    False,

                "error":
                    "could_not_open_video",

                "triggered_name_call_events":
                    []
            }

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        if fps is None or fps <= 0:
            fps = 30

        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        source_duration_sec = (
            total_frames / fps
            if fps > 0
            else 0
        )

        clip_start_sec = float(
            stimulus.get(
                "clip_start_sec",
                0
            )
        )

        clip_end_sec = stimulus.get(
            "clip_end_sec"
        )

        if clip_end_sec is not None:

            clip_end_sec = float(
                clip_end_sec
            )

        start_frame = int(
            clip_start_sec * fps
        )

        if clip_end_sec is None:

            end_frame = total_frames

        else:

            end_frame = int(
                clip_end_sec * fps
            )

        cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            start_frame
        )

        name_call_events = (
            self.protocol.get_name_call_events_for_stimulus(
                stimulus_id
            )
        )

        triggered_events = []
        triggered_event_ids = set()

        frame_index = start_frame
        local_frame_index = 0

        playback_start = time.time()

        print(
            f"▶️ Playing smoothly: {stimulus_id}"
        )

        print(
            f"   Name call events in this stimulus: {len(name_call_events)}"
        )

        while cap.isOpened():

            if frame_index >= end_frame:
                break

            ret, frame = cap.read()

            if not ret:
                break

            elapsed_sec = (
                frame_index - start_frame
            ) / fps

            cue_active = False
            cue_text = "CALL NAME NOW"

            for event in name_call_events:

                event_id = event.get(
                    "id",
                    f"name_call_{event.get('call_index', '')}"
                )

                call_time_sec = float(
                    event.get(
                        "call_time_sec",
                        0
                    )
                )

                if (
                    elapsed_sec >= call_time_sec
                    and
                    event_id not in triggered_event_ids
                ):

                    triggered_event_ids.add(
                        event_id
                    )

                    triggered_event = dict(
                        event
                    )

                    triggered_event["stimulus_id"] = stimulus_id
                    triggered_event["triggered"] = True
                    triggered_event["actual_trigger_time_sec"] = round(
                        elapsed_sec,
                        4
                    )
                    triggered_event["actual_wall_time"] = time.time()

                    triggered_events.append(
                        triggered_event
                    )

                    print()
                    print("🔊 NAME CALL CUE")
                    print(
                        f"   Stimulus: {stimulus_id}"
                    )
                    print(
                        f"   Call index: {event.get('call_index')}"
                    )
                    print(
                        f"   Time: {round(elapsed_sec, 4)} sec"
                    )
                    print(
                        f"   Human should say child name now: {child_name}"
                    )
                    print()

                if (
                    elapsed_sec >= call_time_sec
                    and
                    elapsed_sec <= call_time_sec + 1.2
                ):

                    cue_active = True

            if cue_active:

                frame = self.protocol.draw_name_call_cue(
                    frame,
                    child_name,
                    cue_text
                )

            cv2.imshow(
                window_name,
                frame
            )

            key = cv2.waitKey(
                int(
                    1000 / fps
                )
            ) & 0xFF

            if key == 27:

                print(
                    "⏹️ Stimulus protocol stopped by ESC"
                )

                break

            frame_index += 1
            local_frame_index += 1

        cap.release()

        playback_end = time.time()

        return {
            "stimulus_id":
                stimulus_id,

            "video_path":
                video_path,

            "played":
                True,

            "fps":
                fps,

            "source_duration_sec":
                round(
                    source_duration_sec,
                    4
                ),

            "clip_start_sec":
                clip_start_sec,

            "clip_end_sec":
                clip_end_sec,

            "frames_played":
                local_frame_index,

            "played_duration_wall_sec":
                round(
                    playback_end - playback_start,
                    4
                ),

            "scheduled_name_call_events":
                name_call_events,

            "triggered_name_call_events":
                triggered_events
        }

    def build_category_summary(self):

        category_data = {}

        for result in self.results.get(
            "stimulus_results",
            []
        ):

            stimulus = result.get(
                "stimulus",
                {}
            )

            category = stimulus.get(
                "paper_category",
                "unknown_category"
            )

            framewise_summary = result.get(
                "framewise_summary",
                {}
            )

            if category not in category_data:

                category_data[category] = {
                    "face_presence_ratio": [],
                    "blink_rate_per_min": [],
                    "head_movement_mean": [],
                    "head_movement_complexity_proxy": [],
                    "head_acceleration_mean": [],
                    "mouth_complexity_proxy": [],
                    "eyebrow_complexity_proxy": []
                }

            for key in category_data[category].keys():

                category_data[category][key].append(
                    framewise_summary.get(
                        key,
                        0
                    )
                )

        summary = {}

        for category, metrics in category_data.items():

            summary[category] = {}

            for key, values in metrics.items():

                summary[category][key] = round(
                    self.safe_mean(values),
                    4
                )

        social_attention = summary.get(
            "social",
            {}
        ).get(
            "face_presence_ratio",
            0
        )

        nonsocial_attention = summary.get(
            "non_social",
            {}
        ).get(
            "face_presence_ratio",
            0
        )

        summary["comparison"] = {
            "social_attention_average":
                social_attention,

            "nonsocial_attention_average":
                nonsocial_attention,

            "social_preference_score":
                round(
                    social_attention - nonsocial_attention,
                    4
                )
        }

        return summary

    def run(self, session):

        print()
        print("==============================")
        print("SMOOTH PAPER-MATCH STIMULUS VIDEO TEST STARTED")
        print("==============================")
        print()

        self.results = {
            "stimulus_results": [],
            "category_summary": {},
            "name_call_events": [],
            "triggered_name_call_events": [],
            "protocol_summary": {}
        }

        stimuli = self.protocol.get_video_stimuli()
        name_call_events = self.protocol.get_name_call_events()
        child_name = self.get_child_name(
            session
        )

        self.results["name_call_events"] = name_call_events

        recorder = ContinuousFramewiseBehaviorRecorder()

        recorder.start(
            session
        )

        window_name = "SENSETOKNOW_STIMULI"

        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.setWindowProperty(
            window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )

        temporary_results = []

        for stimulus in stimuli:

            video_metrics = self.play_single_stimulus(
                stimulus=stimulus,
                recorder=recorder,
                child_name=child_name,
                window_name=window_name
            )

            temporary_results.append(
                {
                    "stimulus":
                        stimulus,

                    "video_metrics":
                        video_metrics
                }
            )

        recorder.set_current_stimulus(
            "",
            "",
            ""
        )

        cv2.destroyWindow(
            window_name
        )

        framewise_summaries = recorder.stop()

        all_triggered_name_call_events = []

        final_results = []

        for item in temporary_results:

            stimulus = item.get(
                "stimulus",
                {}
            )

            stimulus_id = stimulus.get(
                "id",
                ""
            )

            video_metrics = item.get(
                "video_metrics",
                {}
            )

            triggered_events = video_metrics.get(
                "triggered_name_call_events",
                []
            )

            all_triggered_name_call_events.extend(
                triggered_events
            )

            final_results.append(
                {
                    "stimulus":
                        stimulus,

                    "video_metrics":
                        video_metrics,

                    "framewise_summary":
                        framewise_summaries.get(
                            stimulus_id,
                            {}
                        ),

                    "triggered_name_call_events":
                        triggered_events
                }
            )

        self.results["stimulus_results"] = final_results

        self.results["triggered_name_call_events"] = (
            all_triggered_name_call_events
        )

        self.results["category_summary"] = (
            self.build_category_summary()
        )

        self.results["protocol_summary"] = {
            "total_video_stimuli":
                len(stimuli),

            "total_name_call_events":
                len(name_call_events),

            "total_triggered_name_call_events":
                len(all_triggered_name_call_events),

            "uses_tracker_manager":
                False,

            "measurement_source":
                "continuous_framewise_behavior_recorder",

            "smooth_playlist":
                True,

            "paper_style_note":
                "Stimuli are played in one continuous fullscreen playlist while one camera recorder logs frame-wise child behavior."
        }

        session["video_test"] = self.results

        session_manager = session[
            "session_manager"
        ]

        session_manager.save_json(
            "stimulus_protocol_summary.json",
            self.results["protocol_summary"]
        )

        session_manager.save_json(
            "stimulus_events.json",
            {
                "scheduled_name_call_events":
                    name_call_events,

                "triggered_name_call_events":
                    all_triggered_name_call_events
            }
        )

        session_manager.save_json(
            "video_test.json",
            self.results
        )

        print()
        print("✅ Smooth Paper-match Stimulus Video Test Completed")
        print()