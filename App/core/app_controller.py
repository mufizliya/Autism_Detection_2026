from core.session_manager import SessionManager

from modules.questionnaire.questionnaire_module import QuestionnaireModule
from modules.social_video_test.social_video_test_module import SocialVideoTestModule
from modules.bubble_game.bubble_game_module import BubbleGameModule

from core.phenotype_fusion import PhenotypeFusion
from core.paper_feature_mapper import PaperFeatureMapper
from core.paper_timeseries_feature_extractor import PaperTimeSeriesFeatureExtractor
from core.response_to_name_extractor import ResponseToNameExtractor
from core.attention_to_speech_extractor import AttentionToSpeechExtractor
from core.gaze_silhouette_extractor import GazeSilhouetteExtractor
from core.session_validator import SessionValidator
from core.dataset_exporter import DatasetExporter
from core.feature_cleaner import FeatureCleaner
from core.label_manager import LabelManager


class AppController:

    def __init__(self):

        self.session_manager = SessionManager()

        self.session = {}

        self.session["session_manager"] = self.session_manager
        self.session["session_id"] = self.session_manager.session_id

        self.questionnaire_module = QuestionnaireModule()
        self.social_video_test_module = SocialVideoTestModule()
        self.bubble_game_module = BubbleGameModule()

    def run(self):

        print()
        print("==============================")
        print("AUTISM DIGITAL PHENOTYPING SESSION STARTED")
        print("==============================")
        print("Session:", self.session["session_id"])
        print()

        # --------------------------------------------------
        # 1. Questionnaire / intake screening
        # --------------------------------------------------
        # This stays in our app, but it is NOT counted as one of
        # the paper's 23 app-derived SenseToKnow variables.
        self.questionnaire_module.run(
            self.session
        )

        # --------------------------------------------------
        # 2. SenseToKnow-style movie protocol
        # --------------------------------------------------
        # This includes stimulus videos, frame-wise behavior logging,
        # and scheduled name-call events during movies.
        self.social_video_test_module.run(
            self.session
        )

        # --------------------------------------------------
        # 3. Bubble popping game
        # --------------------------------------------------
        self.bubble_game_module.run(
            self.session
        )

        # --------------------------------------------------
        # 4. General phenotype vector
        # --------------------------------------------------
        self.session["phenotype_vector"] = (
            PhenotypeFusion.build(
                self.session
            )
        )

        # --------------------------------------------------
        # 5. Paper-style movie time-series features
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 6. Response-to-name from scheduled calls during videos
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 7. Attention-to-speech from speaker turn annotations
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 8. Gaze silhouette / social gaze features
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 9. Map to paper's 23 app-derived variables
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 10. Session quality
        # --------------------------------------------------
        self.session["session_quality"] = (
            SessionValidator.validate(
                self.session
            )
        )

        self.session_manager.save_json(
            "session_quality.json",
            self.session["session_quality"]
        )

        # --------------------------------------------------
        # 11. Optional label before dataset export
        # --------------------------------------------------
        LabelManager.label_session(
            self.session
        )

        # --------------------------------------------------
        # 12. Dataset export and cleaning
        # --------------------------------------------------
        DatasetExporter.append_session(
            self.session
        )

        FeatureCleaner.clean_dataset()

        self.save_final_session()

        print()
        print("==============================")
        print("AUTISM DIGITAL PHENOTYPING SESSION COMPLETED")
        print("==============================")
        print()

    def save_final_session(self):

        final_session = {
            "session_id":
                self.session.get("session_id"),

            "questionnaire":
                self.session.get("questionnaire"),

            "scq_results":
                self.session.get("scq_results"),

            "video_test":
                self.session.get("video_test"),

            "game_metrics":
                self.session.get("game_metrics"),

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

            "label":
                self.session.get("label")
        }

        self.session_manager.save_json(
            "final_session.json",
            final_session
        )