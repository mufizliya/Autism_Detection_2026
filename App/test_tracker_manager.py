import time

from core.session_manager import SessionManager
from core.tracker_manager import TrackerManager


session_manager = SessionManager()

session = {
    "session_manager": session_manager,
    "session_id": session_manager.session_id
}

tracker_manager = TrackerManager()

tracker_manager.start(
    session,
    show_window=False
)

time.sleep(15)

tracker_manager.stop()

print("Final Session:")
print(session)