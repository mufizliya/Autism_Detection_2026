from core.session_manager import SessionManager
from modules.social_video_test.social_video_test_module import SocialVideoTestModule


session_manager = SessionManager()

session = {
    "session_id": session_manager.session_id,
    "session_manager": session_manager
}

module = SocialVideoTestModule()

module.run(
    session
)

print(session.keys())