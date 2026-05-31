from modules.gaze_tracking.gaze_tracking_module import GazeTrackingModule
from modules.facial_expression.facial_expression_module import FacialExpressionModule
from modules.pose_tracking.pose_tracking_module import PoseTrackingModule
from modules.motor_stereotypy.motor_stereotypy_module import MotorStereotypyModule


class TrackerManager:

    def __init__(self):

        self.gaze_tracker = GazeTrackingModule()

        self.facial_expression_tracker = (
            FacialExpressionModule()
        )

        self.pose_tracker = PoseTrackingModule()

        self.motor_stereotypy_tracker = (
            MotorStereotypyModule()
        )

        self.is_running = False

    def start(
        self,
        session,
        show_window=False
    ):

        if self.is_running:

            print(
                "⚠️ Trackers are already running"
            )

            return

        print(
            "🚀 Starting all phenotype trackers..."
        )

        self.gaze_tracker.start(
            session,
            show_window=show_window
        )

        self.facial_expression_tracker.start(
            session,
            show_window=show_window
        )

        self.pose_tracker.start(
            session,
            show_window=show_window
        )

        self.motor_stereotypy_tracker.start(
            session,
            show_window=show_window
        )

        self.is_running = True

        print(
            "✅ All phenotype trackers started"
        )

    def stop(self):

        if not self.is_running:

            print(
                "⚠️ Trackers are not running"
            )

            return

        print(
            "🛑 Stopping all phenotype trackers..."
        )

        self.gaze_tracker.stop()

        self.facial_expression_tracker.stop()

        self.pose_tracker.stop()

        self.motor_stereotypy_tracker.stop()

        self.is_running = False

        print(
            "✅ All phenotype trackers stopped"
        )