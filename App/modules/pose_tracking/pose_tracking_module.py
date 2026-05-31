import cv2
import mediapipe as mp
import time
import statistics
import math
import threading


def euclidean(x1, y1, x2, y2):

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


class PoseTrackingModule:

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

        print("✅ Pose Tracker Started")

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join()

        print("✅ Pose Tracker Stopped")

    def run(self, session):

        mp_pose = mp.solutions.pose

        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():

            print("❌ Could not open webcam")
            return

        print("✅ Pose webcam started")

        start_time = time.time()
        elapsed = 0

        total_frames = 0
        pose_frames = 0

        nose_positions = []
        shoulder_center_positions = []

        while self.running:

            ret, frame = cap.read()

            if not ret:
                break

            total_frames += 1

            elapsed = (
                time.time() -
                start_time
            )

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = pose.process(rgb)

            if results.pose_landmarks:

                pose_frames += 1

                h, w, _ = frame.shape

                landmarks = (
                    results.pose_landmarks.landmark
                )

                NOSE = 0
                LEFT_SHOULDER = 11
                RIGHT_SHOULDER = 12

                nose = landmarks[NOSE]

                left_shoulder = landmarks[
                    LEFT_SHOULDER
                ]

                right_shoulder = landmarks[
                    RIGHT_SHOULDER
                ]

                nose_x = int(nose.x * w)
                nose_y = int(nose.y * h)

                left_x = int(
                    left_shoulder.x * w
                )

                left_y = int(
                    left_shoulder.y * h
                )

                right_x = int(
                    right_shoulder.x * w
                )

                right_y = int(
                    right_shoulder.y * h
                )

                shoulder_center_x = (
                    left_x + right_x
                ) / 2

                shoulder_center_y = (
                    left_y + right_y
                ) / 2

                nose_positions.append(
                    (nose_x, nose_y)
                )

                shoulder_center_positions.append(
                    (
                        shoulder_center_x,
                        shoulder_center_y
                    )
                )

                if self.show_window:

                    cv2.circle(
                        frame,
                        (nose_x, nose_y),
                        6,
                        (0, 255, 255),
                        -1
                    )

                    cv2.circle(
                        frame,
                        (left_x, left_y),
                        6,
                        (255, 0, 0),
                        -1
                    )

                    cv2.circle(
                        frame,
                        (right_x, right_y),
                        6,
                        (255, 0, 0),
                        -1
                    )

                    cv2.line(
                        frame,
                        (left_x, left_y),
                        (right_x, right_y),
                        (0, 255, 0),
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
                    "Pose Tracking Test",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord('q'):

                    self.running = False

                    break

        cap.release()

        if self.show_window:

            cv2.destroyAllWindows()

        nose_movements = []

        for i in range(
            1,
            len(nose_positions)
        ):

            prev = nose_positions[i - 1]
            curr = nose_positions[i]

            dist = euclidean(
                prev[0],
                prev[1],
                curr[0],
                curr[1]
            )

            nose_movements.append(dist)

        shoulder_movements = []

        for i in range(
            1,
            len(shoulder_center_positions)
        ):

            prev = shoulder_center_positions[
                i - 1
            ]

            curr = shoulder_center_positions[i]

            dist = euclidean(
                prev[0],
                prev[1],
                curr[0],
                curr[1]
            )

            shoulder_movements.append(dist)

        head_variability = (
            statistics.mean(nose_movements)
            if len(nose_movements) > 0
            else 0
        )

        shoulder_variability = (
            statistics.mean(shoulder_movements)
            if len(shoulder_movements) > 0
            else 0
        )

        body_stability_score = (
            1 /
            (
                1 +
                head_variability +
                shoulder_variability
            )
        )

        pose_presence_ratio = (
            pose_frames /
            max(total_frames, 1)
        )

        session["pose_metrics"] = {

            "total_frames":
                total_frames,

            "pose_frames":
                pose_frames,

            "pose_presence_ratio":
                round(
                    pose_presence_ratio,
                    3
                ),

            "head_variability":
                round(
                    head_variability,
                    3
                ),

            "shoulder_variability":
                round(
                    shoulder_variability,
                    3
                ),

            "body_stability_score":
                round(
                    body_stability_score,
                    3
                )
        }

        session_manager = (
            session[
                "session_manager"
            ]
        )

        session_manager.save_json(
            "pose_metrics.json",
            session[
                "pose_metrics"
            ]
        )

        print("✅ Pose metrics saved")
        print(session["pose_metrics"])


if __name__ == "__main__":

    class DummySessionManager:

        def save_json(
            self,
            filename,
            data
        ):

            print(
                f"Would save {filename}"
            )

            print(data)

    session = {
        "session_manager":
            DummySessionManager()
    }

    tracker = PoseTrackingModule()

    tracker.start(
        session,
        show_window=False
    )

    time.sleep(15)

    tracker.stop()