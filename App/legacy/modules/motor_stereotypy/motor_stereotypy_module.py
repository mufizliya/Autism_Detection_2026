import cv2
import mediapipe as mp
import time
import math
import statistics
import threading

try:
    from scipy.signal import find_peaks
except ImportError:
    find_peaks = None


def calculate_angle(a, b, c):

    angle = math.degrees(
        math.atan2(
            c[1] - b[1],
            c[0] - b[0]
        )
        -
        math.atan2(
            a[1] - b[1],
            a[0] - b[0]
        )
    )

    angle = abs(angle)

    if angle > 180:
        angle = 360 - angle

    return angle


def calculate_frequency(angle_series, duration):

    if (
        find_peaks is None
        or len(angle_series) < 10
        or duration <= 0
    ):
        return 0

    peaks, _ = find_peaks(
        angle_series,
        prominence=5
    )

    frequency = len(peaks) / duration

    return frequency


class MotorStereotypyModule:

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

        print("✅ Motor Stereotypy Tracker Started")

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join()

        print("✅ Motor Stereotypy Tracker Stopped")

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

        print("✅ Motor stereotypy webcam started")

        start_time = time.time()
        elapsed = 0

        total_frames = 0
        pose_frames = 0

        left_elbow_angles = []
        right_elbow_angles = []

        while self.running:

            ret, frame = cap.read()

            if not ret:
                break

            total_frames += 1

            elapsed = time.time() - start_time

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = pose.process(rgb)

            if results.pose_landmarks:

                pose_frames += 1

                h, w, _ = frame.shape

                landmarks = results.pose_landmarks.landmark

                left_shoulder = (
                    int(landmarks[11].x * w),
                    int(landmarks[11].y * h)
                )

                left_elbow = (
                    int(landmarks[13].x * w),
                    int(landmarks[13].y * h)
                )

                left_wrist = (
                    int(landmarks[15].x * w),
                    int(landmarks[15].y * h)
                )

                right_shoulder = (
                    int(landmarks[12].x * w),
                    int(landmarks[12].y * h)
                )

                right_elbow = (
                    int(landmarks[14].x * w),
                    int(landmarks[14].y * h)
                )

                right_wrist = (
                    int(landmarks[16].x * w),
                    int(landmarks[16].y * h)
                )

                left_angle = calculate_angle(
                    left_shoulder,
                    left_elbow,
                    left_wrist
                )

                right_angle = calculate_angle(
                    right_shoulder,
                    right_elbow,
                    right_wrist
                )

                left_elbow_angles.append(left_angle)
                right_elbow_angles.append(right_angle)

                if self.show_window:

                    cv2.circle(
                        frame,
                        left_shoulder,
                        5,
                        (0, 255, 255),
                        -1
                    )

                    cv2.circle(
                        frame,
                        left_elbow,
                        5,
                        (0, 255, 255),
                        -1
                    )

                    cv2.circle(
                        frame,
                        left_wrist,
                        5,
                        (0, 255, 255),
                        -1
                    )

                    cv2.line(
                        frame,
                        left_shoulder,
                        left_elbow,
                        (0, 255, 255),
                        2
                    )

                    cv2.line(
                        frame,
                        left_elbow,
                        left_wrist,
                        (0, 255, 255),
                        2
                    )

                    cv2.circle(
                        frame,
                        right_shoulder,
                        5,
                        (255, 255, 0),
                        -1
                    )

                    cv2.circle(
                        frame,
                        right_elbow,
                        5,
                        (255, 255, 0),
                        -1
                    )

                    cv2.circle(
                        frame,
                        right_wrist,
                        5,
                        (255, 255, 0),
                        -1
                    )

                    cv2.line(
                        frame,
                        right_shoulder,
                        right_elbow,
                        (255, 255, 0),
                        2
                    )

                    cv2.line(
                        frame,
                        right_elbow,
                        right_wrist,
                        (255, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"L Angle: {left_angle:.1f}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"R Angle: {right_angle:.1f}",
                        (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 0),
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
                    "Motor Stereotypy Test",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord('q'):

                    self.running = False

                    break

        cap.release()

        if self.show_window:
            cv2.destroyAllWindows()

        left_std = (
            statistics.stdev(left_elbow_angles)
            if len(left_elbow_angles) > 1
            else 0
        )

        right_std = (
            statistics.stdev(right_elbow_angles)
            if len(right_elbow_angles) > 1
            else 0
        )

        arm_stereotypy_score = (
            left_std + right_std
        ) / 2

        test_duration = max(
            elapsed,
            1
        )

        left_frequency = calculate_frequency(
            left_elbow_angles,
            test_duration
        )

        right_frequency = calculate_frequency(
            right_elbow_angles,
            test_duration
        )

        oscillation_frequency = (
            left_frequency + right_frequency
        ) / 2

        stereotypy_index = (
            arm_stereotypy_score *
            oscillation_frequency
        )

        pose_presence_ratio = (
            pose_frames /
            max(total_frames, 1)
        )

        session["motor_metrics"] = {

            "total_frames":
                total_frames,

            "pose_frames":
                pose_frames,

            "pose_presence_ratio":
                round(pose_presence_ratio, 3),

            "left_arm_variability":
                round(left_std, 2),

            "right_arm_variability":
                round(right_std, 2),

            "arm_stereotypy_score":
                round(arm_stereotypy_score, 2),

            "left_frequency_hz":
                round(left_frequency, 2),

            "right_frequency_hz":
                round(right_frequency, 2),

            "oscillation_frequency_hz":
                round(oscillation_frequency, 2),

            "stereotypy_index":
                round(stereotypy_index, 2)
        }

        session_manager = session["session_manager"]

        session_manager.save_json(
            "motor_metrics.json",
            session["motor_metrics"]
        )

        print("✅ Motor metrics saved")
        print(session["motor_metrics"])


if __name__ == "__main__":

    class DummySessionManager:

        def save_json(self, filename, data):

            print(f"Would save {filename}")
            print(data)

    session = {
        "session_manager": DummySessionManager()
    }

    tracker = MotorStereotypyModule()

    tracker.start(
        session,
        show_window=False
    )

    time.sleep(15)

    tracker.stop()