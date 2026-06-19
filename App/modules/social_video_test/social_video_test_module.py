import os
import time
import json
import cv2
import subprocess
import shutil

from core.project_paths import app_path
from core.stimulus_protocol import StimulusProtocol
from core.continuous_framewise_behavior_recorder import ContinuousFramewiseBehaviorRecorder


class SocialVideoTestModule:

    def __init__(self):

        self.protocol = StimulusProtocol()

        self.master_video_path = app_path(
            "assets",
            "stimuli",
            "master",
            "stimulus_master_protocol_cued.mp4"
        )

        self.master_timeline_path = app_path(
            "assets",
            "stimuli",
            "master",
            "stimulus_master_timeline.json"
        )

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

    def load_master_timeline(self):

        if not os.path.exists(
            self.master_timeline_path
        ):

            print(
                "❌ Master timeline not found:",
                self.master_timeline_path
            )

            return None

        with open(
            self.master_timeline_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def format_srt_time(
        self,
        seconds
    ):

        seconds = float(
            seconds
        )

        hours = int(
            seconds // 3600
        )

        seconds = seconds % 3600

        minutes = int(
            seconds // 60
        )

        seconds = seconds % 60

        whole_seconds = int(
            seconds
        )

        milliseconds = int(
            round(
                (
                    seconds
                    -
                    whole_seconds
                )
                *
                1000
            )
        )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{whole_seconds:02d},"
            f"{milliseconds:03d}"
        )

    def create_parent_cue_subtitle_file(
        self,
        session,
        timeline,
        child_name
    ):

        session_path = session[
            "session_manager"
        ].get_session_path()

        subtitle_path = os.path.join(
            session_path,
            "parent_name_call_cues.srt"
        )

        cue_index = 1

        with open(
            subtitle_path,
            "w",
            encoding="utf-8"
        ) as f:

            for item in timeline:

                for event in item.get(
                    "scheduled_name_call_events",
                    []
                ):

                    start_time = float(
                        event.get(
                            "global_call_time_sec",
                            0
                        )
                    )

                    end_time = start_time + 1.5

                    if child_name:

                        text = (
                            f"PARENT: CALL {child_name} NOW"
                        )

                    else:

                        text = (
                            "PARENT: CALL CHILD NAME NOW"
                        )

                    f.write(
                        f"{cue_index}\n"
                    )

                    f.write(
                        self.format_srt_time(
                            start_time
                        )
                    )

                    f.write(
                        " --> "
                    )

                    f.write(
                        self.format_srt_time(
                            end_time
                        )
                    )

                    f.write(
                        "\n"
                    )

                    f.write(
                        text
                    )

                    f.write(
                        "\n\n"
                    )

                    cue_index += 1

        return subtitle_path

    def start_master_video_player(
        self,
        subtitle_path=None
    ):

        ffplay_path = shutil.which(
            "ffplay"
        )

        if ffplay_path is None:

            print()
            print(
                "❌ ffplay not found. Install ffmpeg first:"
            )
            print(
                "   brew install ffmpeg"
            )
            print()

            return None

        absolute_video_path = os.path.abspath(
            self.master_video_path
        )

        command = [
            ffplay_path,
            "-fs",
            "-autoexit",
            "-loglevel",
            "warning",
            absolute_video_path
        ]

        print()
        print(
            "🎬 Starting pre-cued master video..."
        )
        print(
            absolute_video_path
        )
        print()

        try:

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(
                1.0
            )

            if process.poll() is None:

                print(
                    "✅ Pre-cued master video started."
                )

                return process

            stderr_output = process.stderr.read()

            print()
            print(
                "❌ Master video playback failed. ffplay said:"
            )
            print(
                stderr_output[:1500]
            )
            print()

            return None

        except Exception as error:

            print(
                "❌ Could not start ffplay:",
                error
            )

            return None
        
    def stop_player(
        self,
        process
    ):

        if process is None:
            return

        try:

            if process.poll() is None:

                process.terminate()

                try:

                    process.wait(
                        timeout=1
                    )

                except subprocess.TimeoutExpired:

                    process.kill()

        except Exception:

            pass

    def get_active_timeline_item(
        self,
        timeline,
        elapsed_sec
    ):

        for item in timeline:

            if (
                elapsed_sec >= float(
                    item.get(
                        "global_start_sec",
                        0
                    )
                )
                and
                elapsed_sec < float(
                    item.get(
                        "global_end_sec",
                        0
                    )
                )
            ):

                return item

        return None

    def monitor_master_playback(
        self,
        timeline,
        recorder,
        child_name,
        subtitle_path
    ):

        player_process = self.start_master_video_player(
            subtitle_path
        )

        if player_process is None:

            return {
                "played":
                    False,

                "error":
                    "ffplay_failed",

                "triggered_name_call_events":
                    []
            }

        triggered_events = []
        triggered_event_ids = set()

        previous_stimulus_id = None

        playback_start = time.time()

        total_duration = 0

        if len(timeline) > 0:

            total_duration = float(
                timeline[-1].get(
                    "global_end_sec",
                    0
                )
            )

        try:

            while True:

                elapsed_sec = (
                    time.time()
                    -
                    playback_start
                )

                active_item = self.get_active_timeline_item(
                    timeline,
                    elapsed_sec
                )

                if active_item is not None:

                    stimulus = active_item.get(
                        "stimulus",
                        {}
                    )

                    stimulus_id = active_item.get(
                        "stimulus_id",
                        "unknown_stimulus"
                    )

                    if stimulus_id != previous_stimulus_id:

                        recorder.set_current_stimulus(
                            stimulus_id,
                            stimulus.get(
                                "type",
                                "unknown_type"
                            ),
                            stimulus.get(
                                "paper_category",
                                "unknown_category"
                            )
                        )

                        print(
                            f"▶️ Now playing: {stimulus_id}"
                        )

                        previous_stimulus_id = stimulus_id

                    for event in active_item.get(
                        "scheduled_name_call_events",
                        []
                    ):

                        event_id = event.get(
                            "id",
                            f"name_call_{event.get('call_index', '')}"
                        )

                        global_call_time = float(
                            event.get(
                                "global_call_time_sec",
                                0
                            )
                        )

                        if (
                            elapsed_sec >= global_call_time
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
                            triggered_event["actual_global_trigger_time_sec"] = round(
                                elapsed_sec,
                                4
                            )
                            triggered_event["actual_trigger_time_sec"] = round(
                                elapsed_sec
                                -
                                float(
                                    active_item.get(
                                        "global_start_sec",
                                        0
                                    )
                                ),
                                4
                            )
                            triggered_event["actual_wall_time"] = time.time()

                            triggered_events.append(
                                triggered_event
                            )

                            print()
                            print(
                                "🔊 NAME CALL CUE"
                            )
                            print(
                                f"   Stimulus: {stimulus_id}"
                            )
                            print(
                                f"   Call index: {event.get('call_index')}"
                            )
                            print(
                                f"   Human should say child name now: {child_name}"
                            )
                            print()

                if player_process.poll() is not None:
                    break

                if (
                    total_duration > 0
                    and
                    elapsed_sec >= total_duration + 0.5
                ):

                    break

                time.sleep(
                    0.01
                )

        finally:

            recorder.set_current_stimulus(
                "",
                "",
                ""
            )

            self.stop_player(
                player_process
            )

        playback_end = time.time()

        return {
            "played":
                True,

            "master_video_path":
                self.master_video_path,

            "subtitle_path":
                subtitle_path,

            "played_duration_wall_sec":
                round(
                    playback_end - playback_start,
                    4
                ),

            "triggered_name_call_events":
                triggered_events,

            "audio_video_playback":
                {
                    "method":
                        "prebuilt_master_ffplay_with_srt",

                    "sync":
                        "managed_by_ffplay",

                    "smooth_playlist":
                        True,

                    "on_screen_name_call_cue":
                        True
                }
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

    def run(
        self,
        session
    ):

        print()
        print(
            "=============================="
        )
        print(
            "PREBUILT MASTER STIMULUS VIDEO TEST STARTED"
        )
        print(
            "=============================="
        )
        print()

        self.results = {
            "stimulus_results": [],
            "category_summary": {},
            "name_call_events": [],
            "triggered_name_call_events": [],
            "protocol_summary": {}
        }

        if not os.path.exists(
            self.master_video_path
        ):

            print(
                "❌ Master video not found:",
                self.master_video_path
            )

            print(
                "Run first: python tools/build_master_stimulus.py"
            )

            session["video_test"] = self.results
            return

        timeline_json = self.load_master_timeline()

        if timeline_json is None:

            session["video_test"] = self.results
            return

        timeline = timeline_json.get(
            "timeline",
            []
        )

        name_call_events = self.protocol.get_name_call_events()

        child_name = self.get_child_name(
            session
        )

        subtitle_path = self.create_parent_cue_subtitle_file(
            session=session,
            timeline=timeline,
            child_name=child_name
        )

        self.results["name_call_events"] = name_call_events

        recorder = ContinuousFramewiseBehaviorRecorder()

        recorder.start(
            session
        )

        master_metrics = self.monitor_master_playback(
            timeline=timeline,
            recorder=recorder,
            child_name=child_name,
            subtitle_path=subtitle_path
        )

        framewise_summaries = recorder.stop()

        all_triggered_name_call_events = master_metrics.get(
            "triggered_name_call_events",
            []
        )

        final_results = []

        for item in timeline:

            stimulus = item.get(
                "stimulus",
                {}
            )

            stimulus_id = item.get(
                "stimulus_id",
                ""
            )

            triggered_events = []

            for event in all_triggered_name_call_events:

                if event.get(
                    "stimulus_id"
                ) == stimulus_id:

                    triggered_events.append(
                        event
                    )

            video_metrics = {
                "stimulus_id":
                    stimulus_id,

                "video_path":
                    item.get(
                        "video_path"
                    ),

                "played":
                    master_metrics.get(
                        "played",
                        False
                    ),

                "master_video_path":
                    self.master_video_path,

                "global_start_sec":
                    item.get(
                        "global_start_sec"
                    ),

                "global_end_sec":
                    item.get(
                        "global_end_sec"
                    ),

                "clip_start_sec":
                    item.get(
                        "clip_start_sec"
                    ),

                "clip_end_sec":
                    item.get(
                        "clip_end_sec"
                    ),

                "clip_duration_sec":
                    item.get(
                        "clip_duration_sec"
                    ),

                "scheduled_name_call_events":
                    item.get(
                        "scheduled_name_call_events",
                        []
                    ),

                "triggered_name_call_events":
                    triggered_events,

                "audio_video_playback":
                    master_metrics.get(
                        "audio_video_playback",
                        {}
                    )
            }

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
                len(
                    timeline
                ),

            "total_name_call_events":
                len(
                    name_call_events
                ),

            "total_triggered_name_call_events":
                len(
                    all_triggered_name_call_events
                ),

            "uses_tracker_manager":
                False,

            "measurement_source":
                "continuous_framewise_behavior_recorder",

            "smooth_playlist":
                True,

            "playback_backend":
                "prebuilt_master_ffplay_with_srt",

            "master_video_path":
                self.master_video_path,

            "master_timeline_path":
                self.master_timeline_path,

            "subtitle_path":
                subtitle_path,

            "on_screen_name_call_cue":
                True,

            "paper_style_note":
                "A prebuilt master stimulus video is played with ffplay for smooth synchronized audio-video playback. A generated SRT subtitle provides parent name-call cues while a continuous recorder tags frames using the master timeline."
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
        print(
            "✅ Prebuilt Master Stimulus Video Test Completed"
        )
        print()