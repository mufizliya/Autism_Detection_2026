from core.session_manager import SessionManager
from core.tracker_manager import TrackerManager

from modules.questionnaire.questionnaire_module import QuestionnaireModule
from modules.bubble_game.bubble_game_module import BubbleGameModule
from modules.response_name.name_response_module import NameResponseModule
from modules.social_video_test.social_video_test_module import SocialVideoTestModule
from core.phenotype_fusion import PhenotypeFusion
from core.risk_engine import RiskEngine
from core.report_generator import ReportGenerator
from core.dataset_exporter import DatasetExporter
from core.feature_cleaner import FeatureCleaner
from core.label_manager import LabelManager
from core.session_validator import SessionValidator
from core.paper_feature_mapper import PaperFeatureMapper
from core.paper_timeseries_feature_extractor import PaperTimeSeriesFeatureExtractor
from core.response_to_name_extractor import ResponseToNameExtractor
from core.attention_to_speech_extractor import AttentionToSpeechExtractor
from core.gaze_silhouette_extractor import GazeSilhouetteExtractor

class AppController:

    def __init__(self):

        self.session_manager = SessionManager()

        self.tracker_manager = TrackerManager()

        self.session = {}

        self.session["session_manager"] = (
            self.session_manager
        )

        self.session["session_id"] = (
            self.session_manager.session_id
        )

        self.questionnaire_module = (
            QuestionnaireModule()
        )

        self.name_response_module = (
            NameResponseModule()
        )

        self.bubble_game_module = (
            BubbleGameModule()
        )

        self.social_video_test_module = (
            SocialVideoTestModule()
        )

    def run(self):

        print("Starting Session:", self.session["session_id"])

        self.questionnaire_module.run(
            self.session
        )

        # Track physical phenotype during name response
        self.tracker_manager.start(
            self.session,
            show_window=False
        )

        self.name_response_module.run(
            self.session
        )

        self.tracker_manager.stop()

        # Video test has its own separate tracking
        self.social_video_test_module.run(
            self.session
        )

        # Track physical phenotype during bubble game
        self.tracker_manager.start(
            self.session,
            show_window=False
        )

        self.bubble_game_module.run(
            self.session
        )

        self.tracker_manager.stop()

        self.session["phenotype_vector"] = (
            PhenotypeFusion.build(
                self.session
            )
        )
        self.session["paper_timeseries_features"] = (
            PaperTimeSeriesFeatureExtractor.build(
                self.session
            )
        )

        self.session["phenotype_vector"].update(
            self.session["paper_timeseries_features"]
        )

        self.session_manager.save_json(
            "paper_timeseries_features.json",
            self.session["paper_timeseries_features"]
        )

        self.session["response_to_name_features"] = (
            ResponseToNameExtractor.build(
                self.session
            )
        )

        self.session["phenotype_vector"].update(
            self.session["response_to_name_features"]
        )

        self.session_manager.save_json(
            "response_to_name_features.json",
            self.session["response_to_name_features"]
        )

        self.session["attention_to_speech_features"] = (
            AttentionToSpeechExtractor.build(
                self.session
            )
        )

        self.session["phenotype_vector"].update(
            self.session["attention_to_speech_features"]
        )

        self.session_manager.save_json(
            "attention_to_speech_features.json",
            self.session["attention_to_speech_features"]
        )

        self.session["gaze_silhouette_features"] = (
            GazeSilhouetteExtractor.build(
                self.session
            )
        )

        self.session["phenotype_vector"].update(
            self.session["gaze_silhouette_features"]
        )

        self.session_manager.save_json(
            "gaze_silhouette_features.json",
            self.session["gaze_silhouette_features"]
        )

        paper_mapping = PaperFeatureMapper.build(
            self.session
        )

        self.session["paper_aligned_features"] = (
            paper_mapping["paper_aligned_features"]
        )

        self.session["paper_feature_match_report"] = (
            paper_mapping["paper_feature_match_report"]
        )

        self.session["paper_feature_coverage"] = (
            paper_mapping["paper_feature_coverage"]
        )

        self.session["phenotype_vector"].update(
            self.session["paper_aligned_features"]
        )
        self.session_manager.save_json(
            "paper_aligned_features.json",
            self.session["paper_aligned_features"]
        )

        self.session_manager.save_json(
            "paper_feature_match_report.json",
            self.session["paper_feature_match_report"]
        )

        self.session_manager.save_json(
            "paper_feature_coverage.json",
            self.session["paper_feature_coverage"]
        )

        self.session_manager.save_json(
            "phenotype_vector.json",
            self.session["phenotype_vector"]
        )

        self.session["session_quality"] = (
            SessionValidator.validate(
                self.session
            )
        )

        self.session_manager.save_json(
            "session_quality.json",
            self.session["session_quality"]
        )

        self.session["risk_assessment"] = (
            RiskEngine.build(
                self.session["phenotype_vector"]
            )
        )

        self.session_manager.save_json(
            "risk_assessment.json",
            self.session["risk_assessment"]
        )

        self.session["report_summary"] = (
            ReportGenerator.build(
                self.session
            )
        )

        self.session_manager.save_json(
            "report_summary.json",
            self.session["report_summary"]
        )

        DatasetExporter.append_session(
            self.session
        )

        FeatureCleaner.clean_dataset()

        LabelManager.label_session(
            self.session
        )

        self.save_final_session()

        print("Session Completed")
        print(self.session)
        
    def save_final_session(self):

        final_session = {
            "session_id":
                self.session.get("session_id"),

            "child_info":
                self.session.get("child_info"),

            "questionnaire":
                self.session.get("questionnaire"),

            "scq_results":
                self.session.get("scq_results"),

            "name_response":
                self.session.get("name_response"),

            "game_metrics":
                self.session.get("game_metrics"),

            "video_test":
                self.session.get("video_test"),

            "gaze_metrics":
                self.session.get("gaze_metrics"),

            "facial_expression_metrics":
                self.session.get(
                    "facial_expression_metrics"
                ),

            "pose_metrics":
                self.session.get("pose_metrics"),

            "motor_metrics":
                self.session.get("motor_metrics"),

            "phenotype_vector":
                self.session.get("phenotype_vector"),

            "paper_timeseries_features":
                self.session.get("paper_timeseries_features"),

            "response_to_name_features":
                self.session.get("response_to_name_features"),

            "attention_to_speech_features":
                self.session.get("attention_to_speech_features"),
            
            "gaze_silhouette_features":
                self.session.get("gaze_silhouette_features"),

            "paper_aligned_features":
                self.session.get("paper_aligned_features"),

            "paper_feature_match_report":
                self.session.get("paper_feature_match_report"),

            "paper_feature_coverage":
                self.session.get("paper_feature_coverage"),

            "session_quality":
                self.session.get("session_quality"),
            
            "risk_assessment":
                self.session.get("risk_assessment"),

            "report_summary":
                self.session.get("report_summary"),

            "label":
                self.session.get("label")
        }

        self.session_manager.save_json(
            "final_session.json",
            final_session
        )