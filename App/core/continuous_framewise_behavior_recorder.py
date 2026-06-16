import os
import csv
import time
import threading

import cv2
import mediapipe as mp

from core.framewise_behavior_recorder import FramewiseBehaviorRecorder


class ContinuousFramewiseBehaviorRecorder(FramewiseBehaviorRecorder):

    def __init__(self):

        super().__init__()

        self.lock = threading.Lock()

        self.current_stimulus_id = ""
        self.current_stimulus_type = ""
        self.current_paper_category = ""

        self.session = None
        self.session_path = None

    def set_current_stimulus(
        self,
        stimulus_id,
        stimulus_type,
        paper_category
    ):

        with self.lock:

            self.current_stimulus_id = stimulus_id
            self.current_stimulus_type = stimulus_type
            self.current_paper_category = paper_category

            # Reset movement baseline when stimulus changes.
            self.previous_head_center = None
            self.previous_head_speed = None
            self.blink_state_previous = 0

        if stimulus_id:

            print(
                f"🎬 Recorder now tagging frames as: {stimulus_id}"
            )

    def start(
        self,
        session
    ):

        if self.running:

            print(
                "⚠️ Continuous framewise recorder already running"
            )

            return

        self.session = session

        self.session_path = session[
            "session_manager"
        ].get_session_path()

        self.rows = []
        self.frame_index = 0
        self.running = True

        self.previous_head_center = None
        self.previous_head_speed = None
        self.blink_state_previous = 0
        self.blink_count = 0

        self.thread = threading.Thread(
            target=self.record_loop,
            daemon=True
        )

        self.thread.start()

        print(
            "🎥 Continuous framewise recorder started"
        )

    def stop(self):

        if not self.running:
            return {}

        self.running = False

        if self.thread is not None:
            self.thread.join()

        summaries = self.write_outputs_by_stimulus()

        print(
            "✅ Continuous framewise recorder stopped"
        )

        return summaries

    def record_loop(self):

        mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.cap = cv2.VideoCapture(
            0
        )

        if not self.cap.isOpened():

            print(
                "❌ Could not open webcam for continuous framewise recorder"
            )

            self.running = False
            return

        start_time = time.time()

        while self.running:

            ret, frame = self.cap.read()

            if not ret:
                continue

            with self.lock:

                stimulus_id = self.current_stimulus_id
                stimulus_type = self.current_stimulus_type
                paper_category = self.current_paper_category

            # Skip frames during tiny transitions between clips.
            if stimulus_id == "":

                time.sleep(
                    0.005
                )

                continue

            timestamp = time.time()
            elapsed = timestamp - start_time

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            result = self.face_mesh.process(
                rgb
            )

            if (
                result.multi_face_landmarks
                and
                len(result.multi_face_landmarks) > 0
            ):

                landmarks = (
                    result
                    .multi_face_landmarks[0]
                    .landmark
                )

                features = (
                    self.compute_features_from_landmarks(
                        landmarks
                    )
                )

            else:

                features = self.get_empty_features()

            row = {
                "timestamp":
                    timestamp,

                "elapsed_time":
                    elapsed,

                "stimulus_id":
                    stimulus_id,

                "stimulus_type":
                    stimulus_type,

                "paper_category":
                    paper_category,

                "frame_index":
                    self.frame_index
            }

            row.update(
                features
            )

            self.rows.append(
                row
            )

            self.frame_index += 1

        self.cap.release()

        if self.face_mesh is not None:
            self.face_mesh.close()

    def get_fieldnames(self):

        return [
            "timestamp",
            "elapsed_time",
            "stimulus_id",
            "stimulus_type",
            "paper_category",
            "frame_index",
            "face_detected",
            "left_ear",
            "right_ear",
            "avg_ear",
            "eye_open",
            "blink_state",
            "gaze_x",
            "gaze_y",
            "yaw_proxy",
            "pitch_proxy",
            "roll_proxy_deg",
            "head_center_x",
            "head_center_y",
            "head_movement",
            "head_acceleration",
            "mouth_open",
            "eyebrow_signal"
        ]

    def split_rows_by_stimulus(self):

        grouped = {}

        for row in self.rows:

            stimulus_id = row.get(
                "stimulus_id",
                ""
            )

            if stimulus_id == "":
                continue

            if stimulus_id not in grouped:

                grouped[stimulus_id] = []

            grouped[stimulus_id].append(
                row
            )

        return grouped

    def count_blinks_from_rows(
        self,
        rows
    ):

        blink_count = 0
        previous_state = 0

        for row in rows:

            face_detected = int(
                float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            )

            if face_detected != 1:
                continue

            blink_state = int(
                float(
                    row.get(
                        "blink_state",
                        0
                    )
                )
            )

            if (
                blink_state == 1
                and
                previous_state == 0
            ):

                blink_count += 1

            previous_state = blink_state

        return blink_count

    def build_summary_from_rows(
        self,
        stimulus_id,
        rows
    ):

        if len(rows) == 0:

            return {
                "stimulus_id":
                    stimulus_id,

                "total_frames":
                    0,

                "face_presence_ratio":
                    0,

                "error":
                    "no_rows_recorded"
            }

        total_frames = len(
            rows
        )

        duration = (
            float(rows[-1]["elapsed_time"])
            -
            float(rows[0]["elapsed_time"])
        )

        if duration <= 0:
            duration = 1e-6

        face_rows = [
            row
            for row in rows
            if int(
                float(
                    row.get(
                        "face_detected",
                        0
                    )
                )
            ) == 1
        ]

        face_presence_ratio = (
            len(face_rows) / total_frames
            if total_frames > 0
            else 0
        )

        blink_count = self.count_blinks_from_rows(
            rows
        )

        blink_rate_per_min = (
            blink_count / duration * 60.0
        )

        def values(key):

            return [
                float(row.get(key, 0))
                for row in face_rows
            ]

        stimulus_type = rows[0].get(
            "stimulus_type",
            ""
        )

        paper_category = rows[0].get(
            "paper_category",
            ""
        )

        return {
            "stimulus_id":
                stimulus_id,

            "stimulus_type":
                stimulus_type,

            "paper_category":
                paper_category,

            "total_frames":
                total_frames,

            "face_frames":
                len(face_rows),

            "duration_seconds":
                round(
                    duration,
                    3
                ),

            "face_presence_ratio":
                round(
                    face_presence_ratio,
                    4
                ),

            "blink_count":
                blink_count,

            "blink_rate_per_min":
                round(
                    blink_rate_per_min,
                    4
                ),

            "avg_ear":
                round(
                    self.safe_mean(
                        values("avg_ear")
                    ),
                    4
                ),

            "avg_gaze_x":
                round(
                    self.safe_mean(
                        values("gaze_x")
                    ),
                    4
                ),

            "avg_gaze_y":
                round(
                    self.safe_mean(
                        values("gaze_y")
                    ),
                    4
                ),

            "gaze_variability":
                round(
                    self.safe_std(
                        values("gaze_x")
                        +
                        values("gaze_y")
                    ),
                    4
                ),

            "yaw_variability":
                round(
                    self.safe_std(
                        values("yaw_proxy")
                    ),
                    4
                ),

            "pitch_variability":
                round(
                    self.safe_std(
                        values("pitch_proxy")
                    ),
                    4
                ),

            "roll_variability":
                round(
                    self.safe_std(
                        values("roll_proxy_deg")
                    ),
                    4
                ),

            "head_movement_mean":
                round(
                    self.safe_mean(
                        values("head_movement")
                    ),
                    4
                ),

            "head_movement_complexity_proxy":
                round(
                    self.safe_std(
                        values("head_movement")
                    ),
                    4
                ),

            "head_acceleration_mean":
                round(
                    self.safe_mean(
                        values("head_acceleration")
                    ),
                    4
                ),

            "head_acceleration_variability":
                round(
                    self.safe_std(
                        values("head_acceleration")
                    ),
                    4
                ),

            "mouth_open_mean":
                round(
                    self.safe_mean(
                        values("mouth_open")
                    ),
                    4
                ),

            "mouth_complexity_proxy":
                round(
                    self.safe_std(
                        values("mouth_open")
                    ),
                    4
                ),

            "eyebrow_signal_mean":
                round(
                    self.safe_mean(
                        values("eyebrow_signal")
                    ),
                    4
                ),

            "eyebrow_complexity_proxy":
                round(
                    self.safe_std(
                        values("eyebrow_signal")
                    ),
                    4
                )
        }

    def write_outputs_by_stimulus(self):

        grouped = self.split_rows_by_stimulus()

        summaries = {}

        fieldnames = self.get_fieldnames()

        for stimulus_id, rows in grouped.items():

            csv_path = os.path.join(
                self.session_path,
                f"{stimulus_id}_framewise_log.csv"
            )

            with open(
                csv_path,
                "w",
                newline=""
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames
                )

                writer.writeheader()

                for row in rows:

                    writer.writerow(
                        row
                    )

            summary = self.build_summary_from_rows(
                stimulus_id,
                rows
            )

            summaries[stimulus_id] = summary

            summary_filename = (
                f"{stimulus_id}_framewise_summary.json"
            )

            self.session[
                "session_manager"
            ].save_json(
                summary_filename,
                summary
            )

        return summaries