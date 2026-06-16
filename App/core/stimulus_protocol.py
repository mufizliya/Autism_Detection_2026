import os
import json
import time
import cv2

from core.project_paths import app_path


class StimulusProtocol:

    def __init__(
        self,
        schedule_path=None
    ):

        if schedule_path is None:

            schedule_path = app_path(
                "assets",
                "stimuli",
                "stimulus_schedule.json"
            )

        self.schedule_path = schedule_path
        self.schedule = self.load_schedule()

    def load_schedule(self):

        if not os.path.exists(
            self.schedule_path
        ):

            print(
                f"❌ Stimulus schedule not found: {self.schedule_path}"
            )

            return {
                "protocol_name":
                    "missing_schedule",

                "stimuli":
                    []
            }

        with open(
            self.schedule_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def get_all_stimuli(self):

        return self.schedule.get(
            "stimuli",
            []
        )

    def get_video_stimuli(self):

        video_stimuli = []

        for stimulus in self.get_all_stimuli():

            if stimulus.get("type") != "name_call_event":

                video_stimuli.append(
                    stimulus
                )

        return video_stimuli

    def get_name_call_events(self):

        name_events = []

        for stimulus in self.get_all_stimuli():

            if stimulus.get("type") == "name_call_event":

                name_events.append(
                    stimulus
                )

        return name_events

    def get_name_call_events_for_stimulus(
        self,
        stimulus_id
    ):

        events = []

        for event in self.get_name_call_events():

            if event.get("during_stimulus") == stimulus_id:

                events.append(
                    event
                )

        events.sort(
            key=lambda item: item.get(
                "call_time_sec",
                0
            )
        )

        return events

    def resolve_video_path(
        self,
        video_path
    ):

        if video_path is None:
            return None

        if os.path.isabs(
            video_path
        ):

            return video_path

        return app_path(
            video_path
        )

    def draw_name_call_cue(
        self,
        frame,
        child_name,
        cue_text
    ):

        display_text = cue_text

        if child_name is not None and child_name != "":

            display_text = (
                f"CALL NAME NOW: {child_name}"
            )

        h, w = frame.shape[:2]

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (
                0,
                0
            ),
            (
                w,
                90
            ),
            (
                0,
                0,
                0
            ),
            -1
        )

        alpha = 0.65

        frame = cv2.addWeighted(
            overlay,
            alpha,
            frame,
            1 - alpha,
            0
        )

        cv2.putText(
            frame,
            display_text,
            (
                30,
                55
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (
                255,
                255,
                255
            ),
            2,
            cv2.LINE_AA
        )

        return frame

    def play_video_segment(
        self,
        stimulus,
        window_name="STIMULUS",
        child_name=""
    ):

        stimulus_id = stimulus.get(
            "id",
            "unknown_stimulus"
        )

        video_path = self.resolve_video_path(
            stimulus.get(
                "video_path"
            )
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

        if video_path is None or not os.path.exists(
            video_path
        ):

            print(
                f"❌ Video not found for {stimulus_id}: {video_path}"
            )

            return {
                "stimulus_id":
                    stimulus_id,

                "video_path":
                    video_path,

                "played":
                    False,

                "error":
                    "video_not_found",

                "triggered_name_call_events":
                    []
            }

        name_call_events = (
            self.get_name_call_events_for_stimulus(
                stimulus_id
            )
        )

        triggered_events = []

        triggered_event_ids = set()

        cap = cv2.VideoCapture(
            video_path
        )

        if not cap.isOpened():

            print(
                f"❌ Could not open video: {video_path}"
            )

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

        duration_sec = (
            total_frames / fps
            if fps > 0
            else 0
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

        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.setWindowProperty(
            window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )

        frame_index = start_frame
        local_frame_index = 0

        playback_start_time = time.time()

        print(
            f"▶️ Playing {stimulus_id}"
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
            cue_text = ""

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

                    actual_trigger_time_sec = round(
                        elapsed_sec,
                        4
                    )

                    actual_wall_time = time.time()

                    triggered_event = dict(
                        event
                    )

                    triggered_event["actual_trigger_time_sec"] = (
                        actual_trigger_time_sec
                    )

                    triggered_event["actual_wall_time"] = (
                        actual_wall_time
                    )

                    triggered_event["stimulus_id"] = stimulus_id

                    triggered_event["triggered"] = True

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
                        f"   Time: {actual_trigger_time_sec} sec"
                    )
                    print(
                        f"   Say child name now: {child_name}"
                    )
                    print()

                if (
                    elapsed_sec >= call_time_sec
                    and
                    elapsed_sec <= call_time_sec + 1.2
                ):

                    cue_active = True
                    cue_text = "CALL NAME NOW"

            if cue_active:

                frame = self.draw_name_call_cue(
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
                    "⏹️ Stimulus stopped by ESC"
                )

                break

            frame_index += 1
            local_frame_index += 1

        playback_end_time = time.time()

        cap.release()

        cv2.destroyWindow(
            window_name
        )

        played_duration = (
            playback_end_time
            -
            playback_start_time
        )

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
                    duration_sec,
                    4
                ),

            "clip_start_sec":
                clip_start_sec,

            "clip_end_sec":
                clip_end_sec,

            "played_duration_wall_sec":
                round(
                    played_duration,
                    4
                ),

            "frames_played":
                local_frame_index,

            "scheduled_name_call_events":
                name_call_events,

            "triggered_name_call_events":
                triggered_events
        }