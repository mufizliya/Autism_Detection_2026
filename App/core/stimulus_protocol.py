import os
import json
import time
import cv2


class StimulusProtocol:

    DEFAULT_SCHEDULE_PATH = os.path.join(
        "assets",
        "stimuli",
        "stimulus_schedule.json"
    )

    def __init__(
        self,
        schedule_path=None
    ):

        self.schedule_path = (
            schedule_path
            if schedule_path is not None
            else self.DEFAULT_SCHEDULE_PATH
        )

        self.schedule = self.load_schedule()

    def load_schedule(self):

        if not os.path.exists(self.schedule_path):

            print(
                "❌ Stimulus schedule not found:",
                self.schedule_path
            )

            return {
                "protocol_name": "missing_schedule",
                "stimuli": []
            }

        with open(
            self.schedule_path,
            "r"
        ) as f:

            return json.load(f)

    def get_stimuli(self):

        return self.schedule.get(
            "stimuli",
            []
        )

    def get_video_stimuli(self):

        video_stimuli = []

        for stimulus in self.get_stimuli():

            stimulus_type = stimulus.get(
                "type",
                ""
            )

            if stimulus_type in [
                "social_movie",
                "nonsocial_movie",
                "mixed_social_nonsocial_movie",
                "speech_attention_movie"
            ]:

                video_stimuli.append(
                    stimulus
                )

        return video_stimuli

    def get_name_call_events(self):

        name_events = []

        for stimulus in self.get_stimuli():

            if stimulus.get("type") == "name_call_event":

                name_events.append(
                    stimulus
                )

        return name_events

    def play_video_segment(
        self,
        stimulus,
        window_name="STIMULUS"
    ):

        video_path = stimulus.get(
            "video_path",
            ""
        )

        if not os.path.exists(video_path):

            print(
                f"❌ Video not found for stimulus {stimulus.get('id')}: {video_path}"
            )

            return {
                "stimulus_id":
                    stimulus.get("id"),

                "video_path":
                    video_path,

                "completed":
                    False,

                "error":
                    "video_not_found"
            }

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():

            print(
                f"❌ Could not open video: {video_path}"
            )

            return {
                "stimulus_id":
                    stimulus.get("id"),

                "video_path":
                    video_path,

                "completed":
                    False,

                "error":
                    "could_not_open_video"
            }

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        if fps <= 0:
            fps = 30

        delay = int(
            1000 / fps
        )

        clip_start_sec = stimulus.get(
            "clip_start_sec",
            0
        )

        clip_end_sec = stimulus.get(
            "clip_end_sec",
            None
        )

        if clip_start_sec is None:
            clip_start_sec = 0

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            float(clip_start_sec) * 1000
        )

        start_timestamp = time.time()
        completed = True
        frame_count = 0

        print(
            f"▶ Playing stimulus: {stimulus.get('id')} ({stimulus.get('type')})"
        )

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            current_msec = cap.get(
                cv2.CAP_PROP_POS_MSEC
            )

            current_sec = current_msec / 1000.0

            if clip_end_sec is not None:

                if current_sec >= float(clip_end_sec):
                    break

            cv2.imshow(
                window_name,
                frame
            )

            frame_count += 1

            key = cv2.waitKey(delay)

            if key == 27:

                completed = False
                break

        end_timestamp = time.time()

        cap.release()
        cv2.destroyAllWindows()

        return {
            "stimulus_id":
                stimulus.get("id"),

            "stimulus_type":
                stimulus.get("type"),

            "paper_category":
                stimulus.get("paper_category"),

            "video_path":
                video_path,

            "clip_start_sec":
                clip_start_sec,

            "clip_end_sec":
                clip_end_sec,

            "start_timestamp":
                start_timestamp,

            "end_timestamp":
                end_timestamp,

            "duration_seconds":
                round(
                    end_timestamp - start_timestamp,
                    3
                ),

            "frame_count":
                frame_count,

            "completed":
                completed,

            "social_aoi":
                stimulus.get("social_aoi"),

            "nonsocial_aoi":
                stimulus.get("nonsocial_aoi"),

            "speaker_turns":
                stimulus.get("speaker_turns", []),

            "measurements":
                stimulus.get("measurements", [])
        }

    def build_protocol_summary(self):

        return {
            "protocol_name":
                self.schedule.get(
                    "protocol_name"
                ),

            "target_device":
                self.schedule.get(
                    "target_device"
                ),

            "camera":
                self.schedule.get(
                    "camera"
                ),

            "total_stimuli":
                len(
                    self.get_stimuli()
                ),

            "video_stimuli_count":
                len(
                    self.get_video_stimuli()
                ),

            "name_call_count":
                len(
                    self.get_name_call_events()
                )
        }