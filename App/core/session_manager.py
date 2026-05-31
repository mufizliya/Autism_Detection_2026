import os
import json
from datetime import datetime


class SessionManager:

    def __init__(self):

        self.session_id = datetime.now().strftime(
            "session_%Y%m%d_%H%M%S"
        )

        self.base_path = os.path.join(
            "logs",
            self.session_id
        )

        os.makedirs(
            self.base_path,
            exist_ok=True
        )

    def save_json(
        self,
        filename,
        data
    ):

        file_path = os.path.join(
            self.base_path,
            filename
        )

        with open(file_path, "w") as f:

            json.dump(
                data,
                f,
                indent=4
            )

        print(f"✅ Saved {file_path}")

    def get_session_path(self):

        return self.base_path