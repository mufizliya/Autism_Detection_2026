import os
import time
import cv2

from core.tracker_manager import TrackerManager


class PrefixedSessionManager:

    def __init__(self, real_session_manager, prefix):

        self.real_session_manager = real_session_manager
        self.prefix = prefix

    def save_json(self, filename, data):

        prefixed_filename = (
            f"{self.prefix}_{filename}"
        )

        self.real_session_manager.save_json(
            prefixed_filename,
            data
        )


class SocialVideoTestModule:

    def __init__(self):

        self.results = {
            "social_video": {},
            "nonsocial_video": {},
            "comparison": {}
        }

    def play_video(
        self,
        video_path,
        video_type
    ):

        if not os.path.exists(video_path):

            print(
                f"❌ Video not found: {video_path}"
            )

            return None

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():

            print(
                f"❌ Could not open video: {video_path}"
            )

            return None

        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            fps = 30

        delay = int(1000 / fps)

        start_time = time.time()

        completed = True

        print(
            f"▶ Playing {video_type} video..."
        )

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            cv2.imshow(
                f"{video_type.upper()} VIDEO",
                frame
            )

            key = cv2.waitKey(delay)

            if key == 27:

                completed = False

                break

        end_time = time.time()

        cap.release()

        cv2.destroyAllWindows()

        metrics = {
            "video_type":
                video_type,

            "video_path":
                video_path,

            "start_timestamp":
                start_time,

            "end_timestamp":
                end_time,

            "duration_seconds":
                round(
                    end_time - start_time,
                    2
                ),

            "completed":
                completed
        }

        return metrics

    def run_video_with_tracking(
        self,
        session,
        video_path,
        video_type
    ):

        segment_session = {}

        segment_session["session_id"] = (
            session.get("session_id")
        )

        segment_session["session_manager"] = (
            PrefixedSessionManager(
                session["session_manager"],
                video_type
            )
        )

        tracker_manager = TrackerManager()

        tracker_manager.start(
            segment_session,
            show_window=False
        )

        video_metrics = self.play_video(
            video_path,
            video_type
        )

        tracker_manager.stop()

        segment_result = {
            "video_metrics":
                video_metrics,

            "gaze_metrics":
                segment_session.get(
                    "gaze_metrics",
                    {}
                ),

            "facial_expression_metrics":
                segment_session.get(
                    "facial_expression_metrics",
                    {}
                ),

            "pose_metrics":
                segment_session.get(
                    "pose_metrics",
                    {}
                ),

            "motor_metrics":
                segment_session.get(
                    "motor_metrics",
                    {}
                )
        }

        return segment_result

    def build_comparison(
        self,
        social_result,
        nonsocial_result
    ):

        social_gaze = social_result.get(
            "gaze_metrics",
            {}
        )

        nonsocial_gaze = nonsocial_result.get(
            "gaze_metrics",
            {}
        )

        social_expression = social_result.get(
            "facial_expression_metrics",
            {}
        )

        nonsocial_expression = nonsocial_result.get(
            "facial_expression_metrics",
            {}
        )

        social_pose = social_result.get(
            "pose_metrics",
            {}
        )

        nonsocial_pose = nonsocial_result.get(
            "pose_metrics",
            {}
        )

        social_motor = social_result.get(
            "motor_metrics",
            {}
        )

        nonsocial_motor = nonsocial_result.get(
            "motor_metrics",
            {}
        )

        social_attention = social_gaze.get(
            "attention_ratio",
            0
        )

        nonsocial_attention = nonsocial_gaze.get(
            "attention_ratio",
            0
        )

        social_smile = social_expression.get(
            "smile_ratio",
            0
        )

        nonsocial_smile = nonsocial_expression.get(
            "smile_ratio",
            0
        )

        social_body_stability = social_pose.get(
            "body_stability_score",
            0
        )

        nonsocial_body_stability = nonsocial_pose.get(
            "body_stability_score",
            0
        )

        social_motor_index = social_motor.get(
            "stereotypy_index",
            0
        )

        nonsocial_motor_index = nonsocial_motor.get(
            "stereotypy_index",
            0
        )

        social_preference_score = (
            social_attention -
            nonsocial_attention
        )

        smile_response_difference = (
            social_smile -
            nonsocial_smile
        )

        motor_difference = (
            social_motor_index -
            nonsocial_motor_index
        )

        if social_preference_score > 0.1:

            attention_interpretation = (
                "Higher attention during social video."
            )

        elif social_preference_score < -0.1:

            attention_interpretation = (
                "Higher attention during non-social video."
            )

        else:

            attention_interpretation = (
                "Similar attention across social and non-social videos."
            )

        comparison = {
            "social_attention_ratio":
                social_attention,

            "nonsocial_attention_ratio":
                nonsocial_attention,

            "social_preference_score":
                round(
                    social_preference_score,
                    3
                ),

            "social_smile_ratio":
                social_smile,

            "nonsocial_smile_ratio":
                nonsocial_smile,

            "smile_response_difference":
                round(
                    smile_response_difference,
                    3
                ),

            "social_body_stability_score":
                social_body_stability,

            "nonsocial_body_stability_score":
                nonsocial_body_stability,

            "social_motor_stereotypy_index":
                social_motor_index,

            "nonsocial_motor_stereotypy_index":
                nonsocial_motor_index,

            "motor_difference":
                round(
                    motor_difference,
                    3
                ),

            "attention_interpretation":
                attention_interpretation
        }

        return comparison

    def run(self, session):

        social_video = os.path.join(
            "temp",
            "peekaboo.mp4"
        )

        nonsocial_video = os.path.join(
            "temp",
            "domino.mp4"
        )

        print()
        print("==============================")
        print("SOCIAL / NON-SOCIAL VIDEO TEST STARTED")
        print("==============================")
        print()

        social_result = self.run_video_with_tracking(
            session,
            social_video,
            "social"
        )

        time.sleep(1)

        nonsocial_result = self.run_video_with_tracking(
            session,
            nonsocial_video,
            "nonsocial"
        )

        comparison = self.build_comparison(
            social_result,
            nonsocial_result
        )

        self.results = {
            "social_video":
                social_result,

            "nonsocial_video":
                nonsocial_result,

            "comparison":
                comparison
        }

        session["video_test"] = (
            self.results
        )

        session[
            "session_manager"
        ].save_json(
            "video_test.json",
            self.results
        )

        print()
        print("✅ Social / Non-social Video Test Completed")
        print()

        return self.results