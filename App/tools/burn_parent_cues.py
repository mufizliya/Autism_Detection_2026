import os
import json
import shutil
import subprocess
import cv2


APP_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)


MASTER_DIR = os.path.join(
    APP_DIR,
    "assets",
    "stimuli",
    "master"
)


MASTER_VIDEO_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_protocol.mp4"
)


MASTER_TIMELINE_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_timeline.json"
)


TEMP_CUED_VIDEO_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_protocol_cued_no_audio.avi"
)


CUED_MASTER_VIDEO_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_protocol_cued.mp4"
)


def load_timeline():

    with open(
        MASTER_TIMELINE_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data.get(
        "timeline",
        []
    )


def get_name_call_windows(timeline):

    windows = []

    for item in timeline:

        stimulus_id = item.get(
            "stimulus_id",
            ""
        )

        for event in item.get(
            "scheduled_name_call_events",
            []
        ):

            start_time = float(
                event.get(
                    "global_call_time_sec",
                    0
                )
            )

            windows.append(
                {
                    "stimulus_id":
                        stimulus_id,

                    "call_index":
                        event.get(
                            "call_index",
                            ""
                        ),

                    "start_sec":
                        start_time,

                    "end_sec":
                        start_time + 1.5
                }
            )

    return windows


def is_cue_active(time_sec, windows):

    for window in windows:

        if (
            time_sec >= window["start_sec"]
            and
            time_sec <= window["end_sec"]
        ):

            return True

    return False


def draw_parent_cue(frame):

    h, w = frame.shape[:2]

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (w, 115),
        (0, 0, 0),
        -1
    )

    frame = cv2.addWeighted(
        overlay,
        0.75,
        frame,
        0.25,
        0
    )

    text = "PARENT: CALL CHILD NAME NOW"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.35
    thickness = 3

    text_size, _ = cv2.getTextSize(
        text,
        font,
        font_scale,
        thickness
    )

    x = int(
        (w - text_size[0]) / 2
    )

    y = 72

    cv2.putText(
        frame,
        text,
        (x, y),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA
    )

    return frame


def build_cued_video():

    if not os.path.exists(
        MASTER_VIDEO_PATH
    ):

        print(
            "❌ Master video not found:",
            MASTER_VIDEO_PATH
        )

        print(
            "Run first: python tools/build_master_stimulus.py"
        )

        return

    if not os.path.exists(
        MASTER_TIMELINE_PATH
    ):

        print(
            "❌ Master timeline not found:",
            MASTER_TIMELINE_PATH
        )

        return

    ffmpeg_path = shutil.which(
        "ffmpeg"
    )

    if ffmpeg_path is None:

        print(
            "❌ ffmpeg not found. Install with: brew install ffmpeg"
        )

        return

    timeline = load_timeline()
    cue_windows = get_name_call_windows(
        timeline
    )

    print(
        "Name-call cue windows:",
        cue_windows
    )

    cap = cv2.VideoCapture(
        MASTER_VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            "❌ Could not open master video:",
            MASTER_VIDEO_PATH
        )

        return

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps is None or fps <= 0:
        fps = 24

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    writer = None

    for codec_name in [
        "MJPG",
        "XVID"
    ]:

        fourcc = cv2.VideoWriter_fourcc(
            *codec_name
        )

        test_writer = cv2.VideoWriter(
            TEMP_CUED_VIDEO_PATH,
            fourcc,
            fps,
            (width, height)
        )

        if test_writer.isOpened():

            writer = test_writer

            print(
                "✅ OpenCV writer opened with codec:",
                codec_name
            )

            break

        test_writer.release()

    if writer is None:

        print(
            "❌ Could not open OpenCV writer."
        )

        return

    print()
    print(
        "🎬 Burning parent name-call cues into master video..."
    )
    print(
        "This is one-time only."
    )
    print()

    frame_index = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        time_sec = frame_index / fps

        if is_cue_active(
            time_sec,
            cue_windows
        ):

            frame = draw_parent_cue(
                frame
            )

        writer.write(
            frame
        )

        frame_index += 1

    cap.release()
    writer.release()

    print()
    print(
        "🎧 Muxing original audio back into cued video..."
    )
    print()

    mux_command = [
        ffmpeg_path,
        "-y",
        "-i",
        TEMP_CUED_VIDEO_PATH,
        "-i",
        MASTER_VIDEO_PATH,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        CUED_MASTER_VIDEO_PATH
    ]

    result = subprocess.run(
        mux_command
    )

    if result.returncode != 0:

        print(
            "❌ Failed to mux audio."
        )

        return

    print()
    print(
        "✅ Cued master video created:"
    )
    print(
        CUED_MASTER_VIDEO_PATH
    )


if __name__ == "__main__":

    build_cued_video()