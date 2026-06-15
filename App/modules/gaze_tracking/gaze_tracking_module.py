import cv2
import mediapipe as mp
import time
import math
import numpy as np
import statistics
import threading


def euclidean(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def calculate_ear(eye_points, landmarks):

    p1 = landmarks[eye_points[0]]
    p2 = landmarks[eye_points[1]]
    p3 = landmarks[eye_points[2]]
    p4 = landmarks[eye_points[3]]
    p5 = landmarks[eye_points[4]]
    p6 = landmarks[eye_points[5]]

    vertical1 = euclidean(p2, p6)
    vertical2 = euclidean(p3, p5)
    horizontal = euclidean(p1, p4)

    if horizontal == 0:
        return 0

    ear = (
        vertical1 +
        vertical2
    ) / (2 * horizontal)

    return ear


class GazeTrackingModule:

    def __init__(self):

        self.running = False
        self.thread = None
        self.session = None
        self.show_window = False

    def start(
        self,
        session,
        show_window=False
    ):

        self.session = session
        self.show_window = show_window
        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            args=(session,),
            daemon=True
        )

        self.thread.start()

        print("✅ Gaze Tracker Started")

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join()

        print("✅ Gaze Tracker Stopped")

    def run(self, session):

        mp_face_mesh = mp.solutions.face_mesh

        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():

            print("❌ Could not open webcam")
            return

        print("✅ Gaze webcam started")

        start_time = time.time()
        elapsed = 0

        total_frames = 0
        face_detected_frames = 0
        eye_landmark_frames = 0

        blink_count = 0
        eye_closed = False

        total_away_time = 0
        away_start_time = None

        yaw_values = []
        pitch_values = []

        calibration_yaws = []
        calibration_pitches = []

        baseline_yaw = None
        baseline_pitch = None

        gaze_ratios = []
        eye_contact_frames = 0

        CALIBRATION_TIME = 3
        BLINK_THRESHOLD = 0.20

        LEFT_EYE = [
            33, 133, 160,
            159, 158, 157,
            173, 144, 145,
            153, 154, 155
        ]

        RIGHT_EYE = [
            362, 263, 387,
            386, 385, 384,
            398, 373, 374,
            380, 381, 382
        ]

        LEFT_EYE_EAR = [
            33,
            160,
            158,
            133,
            153,
            144
        ]

        RIGHT_EYE_EAR = [
            362,
            385,
            387,
            263,
            373,
            380
        ]

        while self.running:

            ret, frame = cap.read()

            if not ret:
                break

            total_frames += 1

            elapsed = (
                time.time() -
                start_time
            )

            calibrating = (
                elapsed < CALIBRATION_TIME
            )

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = face_mesh.process(
                rgb_frame
            )

            if results.multi_face_landmarks:

                face_detected_frames += 1

                face_landmarks = (
                    results.multi_face_landmarks[0]
                )

                eye_landmark_frames += 1

                h, w, _ = frame.shape

                face_2d = []
                face_3d = []

                # -----------------------------
                # Head pose landmark collection
                # -----------------------------
                for idx, lm in enumerate(
                    face_landmarks.landmark
                ):

                    if idx in [
                        33,     # left eye corner
                        263,    # right eye corner
                        1,      # nose tip
                        61,     # left mouth
                        291,    # right mouth
                        199     # chin
                    ]:

                        x = int(lm.x * w)
                        y = int(lm.y * h)

                        face_2d.append([x, y])

                        face_3d.append([
                            x,
                            y,
                            lm.z
                        ])

                        if self.show_window:

                            cv2.circle(
                                frame,
                                (x, y),
                                3,
                                (0, 0, 255),
                                -1
                            )

                # -----------------------------
                # Iris / gaze proxy
                # -----------------------------
                gaze_ratio = None

                iris_center = (
                    face_landmarks.landmark[468]
                )

                left_corner = (
                    face_landmarks.landmark[33]
                )

                right_corner = (
                    face_landmarks.landmark[133]
                )

                eye_width = (
                    right_corner.x -
                    left_corner.x
                )

                if eye_width > 0:

                    gaze_ratio = (
                        iris_center.x -
                        left_corner.x
                    ) / eye_width

                    gaze_ratios.append(
                        gaze_ratio
                    )

                    if 0.30 <= gaze_ratio <= 0.70:

                        eye_contact_frames += 1

                # -----------------------------
                # Head pose estimation
                # -----------------------------
                if len(face_2d) == 6 and len(face_3d) == 6:

                    face_2d = np.array(
                        face_2d,
                        dtype=np.float64
                    )

                    face_3d = np.array(
                        face_3d,
                        dtype=np.float64
                    )

                    focal_length = w

                    cam_matrix = np.array([
                        [focal_length, 0, w / 2],
                        [0, focal_length, h / 2],
                        [0, 0, 1]
                    ])

                    dist_matrix = np.zeros(
                        (4, 1),
                        dtype=np.float64
                    )

                    success, rot_vec, trans_vec = (
                        cv2.solvePnP(
                            face_3d,
                            face_2d,
                            cam_matrix,
                            dist_matrix
                        )
                    )

                    if success:

                        rmat, jac = cv2.Rodrigues(
                            rot_vec
                        )

                        angles, _, _, _, _, _ = (
                            cv2.RQDecomp3x3(rmat)
                        )

                        pitch = angles[0] * 360
                        yaw = angles[1] * 360

                        if calibrating:

                            calibration_yaws.append(
                                yaw
                            )

                            calibration_pitches.append(
                                pitch
                            )

                            baseline_yaw = (
                                sum(calibration_yaws)
                                /
                                len(calibration_yaws)
                            )

                            baseline_pitch = (
                                sum(calibration_pitches)
                                /
                                len(calibration_pitches)
                            )

                        else:

                            yaw_values.append(yaw)
                            pitch_values.append(pitch)

                            if (
                                baseline_yaw is not None
                                and
                                baseline_pitch is not None
                            ):

                                yaw_offset = abs(
                                    yaw - baseline_yaw
                                )

                                pitch_offset = abs(
                                    pitch - baseline_pitch
                                )

                                is_away = (
                                    yaw_offset > 8
                                    or
                                    pitch_offset > 6
                                )

                                if is_away:

                                    if away_start_time is None:

                                        away_start_time = (
                                            time.time()
                                        )

                                else:

                                    if away_start_time is not None:

                                        total_away_time += (
                                            time.time()
                                            -
                                            away_start_time
                                        )

                                        away_start_time = None

                        if self.show_window:

                            cv2.putText(
                                frame,
                                f"Yaw: {yaw:.2f}",
                                (20, 160),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (255, 0, 255),
                                2
                            )

                            cv2.putText(
                                frame,
                                f"Pitch: {pitch:.2f}",
                                (20, 200),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (255, 0, 255),
                                2
                            )

                            if calibrating:

                                cv2.putText(
                                    frame,
                                    "CALIBRATING...",
                                    (20, 240),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1,
                                    (0, 255, 255),
                                    2
                                )

                # -----------------------------
                # Eye landmarks + blink detection
                # -----------------------------
                left_ear = calculate_ear(
                    LEFT_EYE_EAR,
                    face_landmarks.landmark
                )

                right_ear = calculate_ear(
                    RIGHT_EYE_EAR,
                    face_landmarks.landmark
                )

                avg_ear = (
                    left_ear +
                    right_ear
                ) / 2

                if avg_ear < BLINK_THRESHOLD:

                    if not eye_closed:

                        eye_closed = True

                else:

                    if eye_closed:

                        blink_count += 1

                        eye_closed = False

                if self.show_window:

                    for idx in LEFT_EYE:

                        lm = (
                            face_landmarks.landmark[idx]
                        )

                        x = int(lm.x * w)
                        y = int(lm.y * h)

                        cv2.circle(
                            frame,
                            (x, y),
                            2,
                            (0, 255, 0),
                            -1
                        )

                    for idx in RIGHT_EYE:

                        lm = (
                            face_landmarks.landmark[idx]
                        )

                        x = int(lm.x * w)
                        y = int(lm.y * h)

                        cv2.circle(
                            frame,
                            (x, y),
                            2,
                            (0, 255, 0),
                            -1
                        )

                    for idx in [468, 469, 470, 471, 472]:

                        lm = (
                            face_landmarks.landmark[idx]
                        )

                        x = int(lm.x * w)
                        y = int(lm.y * h)

                        cv2.circle(
                            frame,
                            (x, y),
                            3,
                            (255, 255, 0),
                            -1
                        )

                    cv2.putText(
                        frame,
                        f"EAR: {avg_ear:.2f}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"Blinks: {blink_count}",
                        (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 0),
                        2
                    )

                    if gaze_ratio is not None:

                        cv2.putText(
                            frame,
                            f"Gaze: {gaze_ratio:.2f}",
                            (20, 300),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 255),
                            2
                        )

            if self.show_window:

                cv2.putText(
                    frame,
                    f"Running: {int(elapsed)}s",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                cv2.imshow(
                    "Gaze Tracking Test",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord('q'):

                    self.running = False

                    break

        if away_start_time is not None:

            total_away_time += (
                time.time() -
                away_start_time
            )

        cap.release()

        if self.show_window:

            cv2.destroyAllWindows()

        face_presence_ratio = (
            face_detected_frames
            /
            max(total_frames, 1)
        )

        test_duration_minutes = max(
            elapsed / 60,
            0.01
        )

        blink_rate = (
            blink_count /
            test_duration_minutes
        )

        effective_duration = max(
            elapsed - CALIBRATION_TIME,
            1
        )

        attention_ratio = (
            effective_duration -
            total_away_time
        ) / effective_duration

        attention_ratio = max(
            0,
            min(attention_ratio, 1)
        )

        yaw_std = (
            statistics.stdev(yaw_values)
            if len(yaw_values) > 1
            else 0
        )

        pitch_std = (
            statistics.stdev(pitch_values)
            if len(pitch_values) > 1
            else 0
        )

        gaze_std = (
            statistics.stdev(gaze_ratios)
            if len(gaze_ratios) > 1
            else 0
        )

        session["gaze_metrics"] = {

            "total_frames":
                total_frames,

            "face_detected_frames":
                face_detected_frames,

            "eye_landmark_frames":
                eye_landmark_frames,

            "face_presence_ratio":
                round(face_presence_ratio, 3),

            "blink_count":
                blink_count,

            "blink_rate_per_min":
                round(blink_rate, 2),

            "away_time_sec":
                round(total_away_time, 2),

            "attention_ratio":
                round(attention_ratio, 3),

            "yaw_variability":
                round(yaw_std, 2),

            "pitch_variability":
                round(pitch_std, 2),

            "eye_contact_ratio":
                round(
                    eye_contact_frames
                    /
                    max(eye_landmark_frames, 1),
                    3
                ),

            "gaze_variability":
                round(gaze_std, 3)
        }

        session_manager = (
            session["session_manager"]
        )

        session_manager.save_json(
            "gaze_metrics.json",
            session["gaze_metrics"]
        )

        print("✅ Gaze metrics saved")

        print(session["gaze_metrics"])


if __name__ == "__main__":

    class DummySessionManager:

        def save_json(self, filename, data):

            print(f"Would save {filename}")
            print(data)

    session = {
        "session_manager": DummySessionManager()
    }

    tracker = GazeTrackingModule()

    tracker.start(
        session,
        show_window=False
    )

    time.sleep(15)

    tracker.stop()