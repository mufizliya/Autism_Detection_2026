import cv2
import mediapipe as mp
import time
import math
import threading


def euclidean(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


class FacialExpressionModule:

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

        print("✅ Facial Expression Tracker Started")

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join()

        print("✅ Facial Expression Tracker Stopped")

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

        print("✅ Facial expression webcam started")

        start_time = time.time()
        elapsed = 0

        total_frames = 0
        face_frames = 0

        smiling_frames = 0

        smile_scores = []
        baseline_scores = []

        baseline_smile = None
        smile_threshold = None

        CALIBRATION_TIME = 5
        SMILE_DELTA = 0.8

        while self.running:

            ret, frame = cap.read()

            if not ret:
                break

            total_frames += 1

            elapsed = (
                time.time() -
                start_time
            )

            calibration_mode = (
                elapsed < CALIBRATION_TIME
            )

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:

                face_frames += 1

                face_landmarks = (
                    results.multi_face_landmarks[0]
                )

                h, w, _ = frame.shape

                LEFT_CORNER = 61
                RIGHT_CORNER = 291

                UPPER_LIP = 13
                LOWER_LIP = 14

                LEFT_CHEEK = 234
                RIGHT_CHEEK = 454

                left_corner = (
                    face_landmarks.landmark[
                        LEFT_CORNER
                    ]
                )

                right_corner = (
                    face_landmarks.landmark[
                        RIGHT_CORNER
                    ]
                )

                upper_lip = (
                    face_landmarks.landmark[
                        UPPER_LIP
                    ]
                )

                lower_lip = (
                    face_landmarks.landmark[
                        LOWER_LIP
                    ]
                )

                left_cheek = (
                    face_landmarks.landmark[
                        LEFT_CHEEK
                    ]
                )

                right_cheek = (
                    face_landmarks.landmark[
                        RIGHT_CHEEK
                    ]
                )

                mouth_width = euclidean(
                    left_corner,
                    right_corner
                )

                mouth_height = euclidean(
                    upper_lip,
                    lower_lip
                )

                cheek_width = euclidean(
                    left_cheek,
                    right_cheek
                )

                width_ratio = (
                    mouth_width /
                    max(cheek_width, 0.0001)
                )

                openness_ratio = (
                    mouth_height /
                    max(mouth_width, 0.0001)
                )

                corner_lift = (
                    (
                        upper_lip.y -
                        left_corner.y
                    )
                    +
                    (
                        upper_lip.y -
                        right_corner.y
                    )
                ) / 2

                smile_score = (
                    (width_ratio * 10)
                    -
                    (openness_ratio * 3)
                    +
                    (corner_lift * 100)
                )

                smile_scores.append(
                    smile_score
                )

                if calibration_mode:

                    baseline_scores.append(
                        smile_score
                    )

                    baseline_smile = (
                        sum(baseline_scores)
                        /
                        max(
                            len(baseline_scores),
                            1
                        )
                    )

                    smile_threshold = (
                        baseline_smile +
                        SMILE_DELTA
                    )

                else:

                    if (
                        smile_threshold is not None
                        and
                        smile_score > smile_threshold
                    ):

                        smiling_frames += 1

                if self.show_window:

                    for idx in [
                        LEFT_CORNER,
                        RIGHT_CORNER,
                        UPPER_LIP,
                        LOWER_LIP
                    ]:

                        lm = (
                            face_landmarks.landmark[
                                idx
                            ]
                        )

                        x = int(lm.x * w)
                        y = int(lm.y * h)

                        cv2.circle(
                            frame,
                            (x, y),
                            4,
                            (255, 255, 0),
                            -1
                        )

                    cv2.putText(
                        frame,
                        f"Smile Score: {smile_score:.2f}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )

                    if calibration_mode:

                        cv2.putText(
                            frame,
                            "CALIBRATING...",
                            (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 255),
                            2
                        )

                    else:

                        cv2.putText(
                            frame,
                            f"Threshold: {smile_threshold:.2f}",
                            (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
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
                    "Facial Expression Test",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord('q'):

                    self.running = False

                    break

        cap.release()

        if self.show_window:

            cv2.destroyAllWindows()

        avg_smile_score = (
            sum(smile_scores)
            /
            max(
                len(smile_scores),
                1
            )
        )

        smile_ratio = (
            smiling_frames
            /
            max(face_frames, 1)
        )

        session[
            "facial_expression_metrics"
        ] = {

            "total_frames":
                total_frames,

            "face_frames":
                face_frames,

            "avg_smile_score":
                round(
                    avg_smile_score,
                    3
                ),

            "baseline_smile":
                round(
                    baseline_smile
                    if baseline_smile is not None
                    else 0,
                    3
                ),

            "smile_threshold":
                round(
                    smile_threshold
                    if smile_threshold is not None
                    else 0,
                    3
                ),

            "smiling_frames":
                smiling_frames,

            "smile_ratio":
                round(
                    smile_ratio,
                    3
                )
        }

        session_manager = (
            session[
                "session_manager"
            ]
        )

        session_manager.save_json(
            "facial_expression_metrics.json",
            session[
                "facial_expression_metrics"
            ]
        )

        print(
            "✅ Facial expression metrics saved"
        )

        print(
            session[
                "facial_expression_metrics"
            ]
        )


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

    tracker = FacialExpressionModule()

    tracker.start(
        session,
        show_window=False
    )

    time.sleep(15)

    tracker.stop()