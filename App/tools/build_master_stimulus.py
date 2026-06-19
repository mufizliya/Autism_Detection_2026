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


SCHEDULE_PATH = os.path.join(
    APP_DIR,
    "assets",
    "stimuli",
    "stimulus_schedule.json"
)


MASTER_DIR = os.path.join(
    APP_DIR,
    "assets",
    "stimuli",
    "master"
)


NORMALIZED_DIR = os.path.join(
    MASTER_DIR,
    "normalized"
)


MASTER_VIDEO_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_protocol.mp4"
)


MASTER_TIMELINE_PATH = os.path.join(
    MASTER_DIR,
    "stimulus_master_timeline.json"
)


def app_path(relative_path):

    return os.path.join(
        APP_DIR,
        relative_path
    )


def get_video_duration(video_path):

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():
        return 0.0, 24.0, 0

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps is None or fps <= 0:
        fps = 24.0

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (
        frame_count / fps
        if fps > 0
        else 0.0
    )

    cap.release()

    return duration, fps, frame_count


def video_has_audio(video_path):

    ffprobe_path = shutil.which(
        "ffprobe"
    )

    if ffprobe_path is None:
        return False

    command = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        video_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return result.stdout.strip() != ""


def normalize_clip(
    ffmpeg_path,
    input_path,
    output_path,
    clip_start_sec,
    clip_duration_sec
):

    has_audio = video_has_audio(
        input_path
    )

    if has_audio:

        command = [
            ffmpeg_path,
            "-y",
            "-ss",
            str(clip_start_sec),
            "-t",
            str(clip_duration_sec),
            "-i",
            input_path,
            "-vf",
            "scale=1280:720,setsar=1",
            "-r",
            "24",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            output_path
        ]

    else:

        command = [
            ffmpeg_path,
            "-y",
            "-ss",
            str(clip_start_sec),
            "-t",
            str(clip_duration_sec),
            "-i",
            input_path,
            "-f",
            "lavfi",
            "-t",
            str(clip_duration_sec),
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-vf",
            "scale=1280:720,setsar=1",
            "-r",
            "24",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            output_path
        ]

    result = subprocess.run(
        command
    )

    return result.returncode == 0


def main():

    ffmpeg_path = shutil.which(
        "ffmpeg"
    )

    if ffmpeg_path is None:

        print(
            "❌ ffmpeg not found. Install it with: brew install ffmpeg"
        )

        return

    if not os.path.exists(
        SCHEDULE_PATH
    ):

        print(
            "❌ Schedule not found:",
            SCHEDULE_PATH
        )

        return

    os.makedirs(
        MASTER_DIR,
        exist_ok=True
    )

    os.makedirs(
        NORMALIZED_DIR,
        exist_ok=True
    )

    with open(
        SCHEDULE_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        schedule = json.load(f)

    stimuli = schedule.get(
        "stimuli",
        []
    )

    video_stimuli = [
        item
        for item in stimuli
        if item.get("type") != "name_call_event"
    ]

    name_call_events = [
        item
        for item in stimuli
        if item.get("type") == "name_call_event"
    ]

    timeline = []
    normalized_paths = []

    global_time = 0.0

    for index, stimulus in enumerate(video_stimuli):

        stimulus_id = stimulus.get(
            "id",
            f"stimulus_{index}"
        )

        relative_video_path = stimulus.get(
            "video_path"
        )

        input_path = app_path(
            relative_video_path
        )

        if not os.path.exists(
            input_path
        ):

            print(
                f"❌ Missing video for {stimulus_id}: {input_path}"
            )

            continue

        source_duration, source_fps, source_frames = get_video_duration(
            input_path
        )

        clip_start_sec = float(
            stimulus.get(
                "clip_start_sec",
                0
            )
        )

        clip_end_sec = stimulus.get(
            "clip_end_sec"
        )

        if clip_end_sec is not None:
            clip_end_sec = float(clip_end_sec)

        if clip_end_sec is None:

            clip_duration_sec = max(
                0.0,
                source_duration - clip_start_sec
            )

        else:

            clip_duration_sec = max(
                0.0,
                clip_end_sec - clip_start_sec
            )

        output_path = os.path.join(
            NORMALIZED_DIR,
            f"{index:02d}_{stimulus_id}.mp4"
        )

        print(
            f"🎞️ Normalizing {stimulus_id}..."
        )

        ok = normalize_clip(
            ffmpeg_path=ffmpeg_path,
            input_path=input_path,
            output_path=output_path,
            clip_start_sec=clip_start_sec,
            clip_duration_sec=clip_duration_sec
        )

        if not ok:

            print(
                f"❌ Failed to normalize: {stimulus_id}"
            )

            continue

        normalized_paths.append(
            output_path
        )

        scheduled_calls = []

        for event in name_call_events:

            if event.get("during_stimulus") == stimulus_id:

                local_call_time = float(
                    event.get(
                        "call_time_sec",
                        0
                    )
                )

                event_copy = dict(
                    event
                )

                event_copy["global_call_time_sec"] = round(
                    global_time + local_call_time,
                    4
                )

                scheduled_calls.append(
                    event_copy
                )

        timeline_item = {
            "stimulus":
                stimulus,

            "stimulus_id":
                stimulus_id,

            "video_path":
                relative_video_path,

            "normalized_video_path":
                os.path.relpath(
                    output_path,
                    APP_DIR
                ),

            "global_start_sec":
                round(
                    global_time,
                    4
                ),

            "global_end_sec":
                round(
                    global_time + clip_duration_sec,
                    4
                ),

            "clip_start_sec":
                clip_start_sec,

            "clip_end_sec":
                clip_end_sec,

            "clip_duration_sec":
                round(
                    clip_duration_sec,
                    4
                ),

            "source_duration_sec":
                round(
                    source_duration,
                    4
                ),

            "source_fps":
                source_fps,

            "source_frames":
                source_frames,

            "scheduled_name_call_events":
                scheduled_calls
        }

        timeline.append(
            timeline_item
        )

        global_time += clip_duration_sec

    concat_list_path = os.path.join(
        MASTER_DIR,
        "concat_list.txt"
    )

    with open(
        concat_list_path,
        "w",
        encoding="utf-8"
    ) as f:

        for path in normalized_paths:

            safe_path = path.replace(
                "'",
                "'\\''"
            )

            f.write(
                f"file '{safe_path}'\n"
            )

    print()
    print("🎬 Creating one smooth master video...")
    print()

    concat_command = [
        ffmpeg_path,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-c",
        "copy",
        MASTER_VIDEO_PATH
    ]

    result = subprocess.run(
        concat_command
    )

    if result.returncode != 0:

        print(
            "⚠️ Stream-copy concat failed. Retrying with re-encode..."
        )

        concat_command = [
            ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list_path,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            MASTER_VIDEO_PATH
        ]

        result = subprocess.run(
            concat_command
        )

    if result.returncode != 0:

        print(
            "❌ Failed to create master video."
        )

        return

    timeline_json = {
        "master_video_path":
            os.path.relpath(
                MASTER_VIDEO_PATH,
                APP_DIR
            ),

        "total_duration_sec":
            round(
                global_time,
                4
            ),

        "stimulus_count":
            len(
                timeline
            ),

        "timeline":
            timeline
    }

    with open(
        MASTER_TIMELINE_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            timeline_json,
            f,
            indent=4
        )

    print()
    print("✅ Master video created:")
    print(MASTER_VIDEO_PATH)
    print()
    print("✅ Timeline created:")
    print(MASTER_TIMELINE_PATH)
    print()
    print("Now the app can play this prebuilt master video directly.")


if __name__ == "__main__":

    main()