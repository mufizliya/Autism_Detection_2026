import os
import csv
import time
import math
import threading

import cv2
import mediapipe as mp
import numpy as np


class FramewiseBehaviorRecorder:

    def __init__(self):

        self.running = False
        self.thread = None

        self.cap = None
        self.face_mesh = None

        self.rows = []

        self.session = None
        self.stimulus_id = None
        self.stimulus_type = None
        self.paper_category = None

        self.output_csv_path = None

        self.frame_index = 0

        self.previous_head_center = None
        self.previous_head_speed = None

        self.blink_state_previous = 0
        self.blink_count = 0

    @staticmethod
    def distance(p1, p2):

        return math.sqrt(
            (p1[0] - p2[0]) ** 2
            +
            (p1[1] - p2[1]) ** 2
        )

    @staticmethod
    def landmark_xy(landmarks, index):

        lm = landmarks[index]

        return (
            float(lm.x),
            float(lm.y)
        )

    @staticmethod
    def safe_std(values):

        if len(values) == 0:
            return 0.0

        return float(
            np.std(values)
        )

    @staticmethod
    def safe_mean(values):

        if len(values) == 0:
            return 0.0

        return float(
            np.mean(values)
        )

    def compute_ear(
        self,
        landmarks,
        eye_indices
    ):

        p1 = self.landmark_xy(
            landmarks,
            eye_indices[0]
        )

        p2 = self.landmark_xy(
            landmarks,
            eye_indices[1]
        )

        p3 = self.landmark_xy(
            landmarks,
            eye_indices[2]
        )

        p4 = self.landmark_xy(
            landmarks,
            eye_indices[3]
        )

        p5 = self.landmark_xy(
            landmarks,
            eye_indices[4]
        )

        p6 = self.landmark_xy(
            landmarks,
            eye_indices[5]
        )

        vertical_1 = self.distance(
            p2,
            p6
        )

        vertical_2 = self.distance(
            p3,
            p5
        )

        horizontal = self.distance(
            p1,
            p4
        )

        if horizontal == 0:
            return 0.0

        ear = (
            vertical_1
            +
            vertical_2
        ) / (
            2.0 * horizontal
        )

        return ear

    def compute_features_from_landmarks(
        self,
        landmarks
    ):

        # MediaPipe FaceMesh landmark indices
        left_eye = [
            33,
            160,
            158,
            133,
            153,
            144
        ]

        right_eye = [
            362,
            385,
            387,
            263,
            373,
            380
        ]

        left_ear = self.compute_ear(
            landmarks,
            left_eye
        )

        right_ear = self.compute_ear(
            landmarks,
            right_eye
        )

        avg_ear = (
            left_ear
            +
            right_ear
        ) / 2.0

        blink_state = (
            1
            if avg_ear < 0.18
            else 0
        )

        if (
            blink_state == 1
            and
            self.blink_state_previous == 0
        ):

            self.blink_count += 1

        self.blink_state_previous = blink_state

        left_eye_center = np.mean(
            [
                self.landmark_xy(landmarks, 33),
                self.landmark_xy(landmarks, 133)
            ],
            axis=0
        )

        right_eye_center = np.mean(
            [
                self.landmark_xy(landmarks, 362),
                self.landmark_xy(landmarks, 263)
            ],
            axis=0
        )

        eye_center = (
            left_eye_center
            +
            right_eye_center
        ) / 2.0

        nose = np.array(
            self.landmark_xy(
                landmarks,
                1
            )
        )

        face_left = np.array(
            self.landmark_xy(
                landmarks,
                234
            )
        )

        face_right = np.array(
            self.landmark_xy(
                landmarks,
                454
            )
        )

        chin = np.array(
            self.landmark_xy(
                landmarks,
                152
            )
        )

        forehead = np.array(
            self.landmark_xy(
                landmarks,
                10
            )
        )

        face_width = self.distance(
            face_left,
            face_right
        )

        face_height = self.distance(
            forehead,
            chin
        )

        if face_width == 0:
            face_width = 1e-6

        if face_height == 0:
            face_height = 1e-6

        head_center = (
            face_left
            +
            face_right
        ) / 2.0

        yaw_proxy = (
            nose[0]
            -
            head_center[0]
        ) / face_width

        pitch_proxy = (
            nose[1]
            -
            eye_center[1]
        ) / face_height

        roll_proxy = math.atan2(
            right_eye_center[1] - left_eye_center[1],
            right_eye_center[0] - left_eye_center[0]
        )

        roll_proxy_deg = math.degrees(
            roll_proxy
        )

        mouth_top = np.array(
            self.landmark_xy(
                landmarks,
                13
            )
        )

        mouth_bottom = np.array(
            self.landmark_xy(
                landmarks,
                14
            )
        )

        mouth_open = (
            self.distance(
                mouth_top,
                mouth_bottom
            )
            /
            face_height
        )

        left_brow = np.array(
            self.landmark_xy(
                landmarks,
                105
            )
        )

        left_eye_upper = np.array(
            self.landmark_xy(
                landmarks,
                159
            )
        )

        right_brow = np.array(
            self.landmark_xy(
                landmarks,
                334
            )
        )

        right_eye_upper = np.array(
            self.landmark_xy(
                landmarks,
                386
            )
        )

        eyebrow_signal = (
            abs(left_brow[1] - left_eye_upper[1])
            +
            abs(right_brow[1] - right_eye_upper[1])
        ) / (
            2.0 * face_height
        )

        # Iris landmarks are available when refine_landmarks=True
        gaze_x = 0.0
        gaze_y = 0.0

        if len(landmarks) > 477:

            left_iris_points = [
                self.landmark_xy(landmarks, i)
                for i in [468, 469, 470, 471, 472]
            ]

            right_iris_points = [
                self.landmark_xy(landmarks, i)
                for i in [473, 474, 475, 476, 477]
            ]

            left_iris = np.mean(
                left_iris_points,
                axis=0
            )

            right_iris = np.mean(
                right_iris_points,
                axis=0
            )

            iris_center = (
                left_iris
                +
                right_iris
            ) / 2.0

            gaze_x = float(
                iris_center[0]
            )

            gaze_y = float(
                iris_center[1]
            )

        head_movement = 0.0
        head_acceleration = 0.0

        if self.previous_head_center is not None:

            head_movement = self.distance(
                head_center,
                self.previous_head_center
            )

            if self.previous_head_speed is not None:

                head_acceleration = abs(
                    head_movement
                    -
                    self.previous_head_speed
                )

        self.previous_head_center = head_center
        self.previous_head_speed = head_movement

        eye_open = (
            1
            if blink_state == 0
            else 0
        )

        return {
            "face_detected":
                1,

            "left_ear":
                left_ear,

            "right_ear":
                right_ear,

            "avg_ear":
                avg_ear,

            "eye_open":
                eye_open,

            "blink_state":
                blink_state,

            "gaze_x":
                gaze_x,

            "gaze_y":
                gaze_y,

            "yaw_proxy":
                yaw_proxy,

            "pitch_proxy":
                pitch_proxy,

            "roll_proxy_deg":
                roll_proxy_deg,

            "head_center_x":
                float(head_center[0]),

            "head_center_y":
                float(head_center[1]),

            "head_movement":
                head_movement,

            "head_acceleration":
                head_acceleration,

            "mouth_open":
                mouth_open,

            "eyebrow_signal":
                eyebrow_signal
        }

    def get_empty_features(self):

        return {
            "face_detected":
                0,

            "left_ear":
                0,

            "right_ear":
                0,

            "avg_ear":
                0,

            "eye_open":
                0,

            "blink_state":
                0,

            "gaze_x":
                0,

            "gaze_y":
                0,

            "yaw_proxy":
                0,

            "pitch_proxy":
                0,

            "roll_proxy_deg":
                0,

            "head_center_x":
                0,

            "head_center_y":
                0,

            "head_movement":
                0,

            "head_acceleration":
                0,

            "mouth_open":
                0,

            "eyebrow_signal":
                0
        }

    def start(
        self,
        session,
        stimulus_id,
        stimulus_type,
        paper_category
    ):

        if self.running:
            print("⚠️ Framewise recorder already running")
            return

        self.session = session
        self.stimulus_id = stimulus_id
        self.stimulus_type = stimulus_type
        self.paper_category = paper_category

        self.rows = []
        self.frame_index = 0

        self.previous_head_center = None
        self.previous_head_speed = None

        self.blink_state_previous = 0
        self.blink_count = 0

        session_path = session[
            "session_manager"
        ].get_session_path()

        self.output_csv_path = os.path.join(
            session_path,
            f"{stimulus_id}_framewise_log.csv"
        )

        self.running = True

        self.thread = threading.Thread(
            target=self.record_loop,
            daemon=True
        )

        self.thread.start()

        print(
            f"🎥 Framewise recorder started for {stimulus_id}"
        )

    def stop(self):

        if not self.running:
            return {}

        self.running = False

        if self.thread is not None:
            self.thread.join()

        summary = self.build_summary()

        summary_filename = (
            f"{self.stimulus_id}_framewise_summary.json"
        )

        self.session[
            "session_manager"
        ].save_json(
            summary_filename,
            summary
        )

        print(
            f"✅ Framewise recorder stopped for {self.stimulus_id}"
        )

        return summary

    def record_loop(self):

        mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():

            print("❌ Could not open webcam for framewise recorder")
            self.running = False
            return

        start_time = time.time()

        fieldnames = [
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

        with open(
            self.output_csv_path,
            "w",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames
            )

            writer.writeheader()

            while self.running:

                ret, frame = self.cap.read()

                if not ret:
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
                        self.stimulus_id,

                    "stimulus_type":
                        self.stimulus_type,

                    "paper_category":
                        self.paper_category,

                    "frame_index":
                        self.frame_index
                }

                row.update(
                    features
                )

                writer.writerow(
                    row
                )

                self.rows.append(
                    row
                )

                self.frame_index += 1

        self.cap.release()

        if self.face_mesh is not None:
            self.face_mesh.close()

    def build_summary(self):

        if len(self.rows) == 0:

            return {
                "stimulus_id":
                    self.stimulus_id,

                "total_frames":
                    0,

                "face_presence_ratio":
                    0,

                "error":
                    "no_rows_recorded"
            }

        total_frames = len(
            self.rows
        )

        duration = (
            self.rows[-1]["elapsed_time"]
            -
            self.rows[0]["elapsed_time"]
        )

        if duration <= 0:
            duration = 1e-6

        face_frames = [
            row
            for row in self.rows
            if int(row["face_detected"]) == 1
        ]

        face_presence_ratio = (
            len(face_frames)
            /
            total_frames
        )

        blink_rate_per_min = (
            self.blink_count
            /
            duration
            *
            60.0
        )

        def values(key):

            return [
                float(row[key])
                for row in face_frames
            ]

        summary = {
            "stimulus_id":
                self.stimulus_id,

            "stimulus_type":
                self.stimulus_type,

            "paper_category":
                self.paper_category,

            "total_frames":
                total_frames,

            "face_frames":
                len(face_frames),

            "duration_seconds":
                round(duration, 3),

            "face_presence_ratio":
                round(face_presence_ratio, 4),

            "blink_count":
                self.blink_count,

            "blink_rate_per_min":
                round(blink_rate_per_min, 4),

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

        return summary