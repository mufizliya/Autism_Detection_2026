# import sys
# import os
# import time
# import threading
# import pandas as pd
# from gtts import gTTS
# import pygame
# from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
# from PyQt5.QtGui import QPixmap, QPalette, QBrush
# from PyQt5.QtCore import Qt

# # 1. Read name from CSV
# logs_dir = "logs"
# os.makedirs(logs_dir, exist_ok=True)
# df_path = os.path.join(logs_dir, "kid_info.csv")
# df = pd.read_csv(df_path)
# first_name = df.iloc[0]['name']

# # 2. Create greeting text and audio file
# greeting = f"Hello {first_name}, how are you!"
# audio_file = os.path.join(logs_dir, "greeting.mp3")
# if not os.path.exists(audio_file):
#     tts = gTTS(text=greeting, lang='en')
#     tts.save(audio_file)
#     print(f"✅ Audio saved as {audio_file}")

# # Function to play audio in background
# def play_greeting():
#     pygame.mixer.init()
#     pygame.mixer.music.load(audio_file)
#     pygame.mixer.music.play()
#     print("🔊 Playing the greeting...")
#     while pygame.mixer.music.get_busy():
#         pygame.time.delay(100)
#     pygame.mixer.quit()
#     print("✅ Playback finished.")
#     # Delete the audio file after playback
#     try:
#         os.remove(audio_file)
#         print(f"🗑️ Deleted audio file: {audio_file}")
#     except OSError as e:
#         print(f"⚠️ Could not delete audio file: {e}")

# # Function to record user response
# def record_response(response_text, response_time):
#     log_file = os.path.join(logs_dir, f"{first_name}_Response.csv")
#     header = ['response', 'response_time']
#     entry = {'response': response_text, 'response_time': response_time}
#     if not os.path.exists(log_file):
#         pd.DataFrame(columns=header).to_csv(log_file, index=False)
#     pd.DataFrame([entry]).to_csv(log_file, mode='a', header=False, index=False)
#     print(f"✅ Logged: {entry} to {log_file}")
#     QApplication.quit()

# # 3. Build and show UI
# def main():
#     app = QApplication(sys.argv)
#     window = QWidget()
#     window.setWindowTitle('How are you?')

#     # Load background image
#     bg_pixmap = QPixmap('src/background.jpg')
#     palette = QPalette()
#     palette.setBrush(QPalette.Window, QBrush(bg_pixmap.scaled(window.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
#     window.setPalette(palette)

#     # Ensure background scales on resize
#     def on_resize(event):
#         scaled = bg_pixmap.scaled(window.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
#         palette.setBrush(QPalette.Window, QBrush(scaled))
#         window.setPalette(palette)
#         QWidget.resizeEvent(window, event)
#     window.resizeEvent = on_resize

#     # Layout for overlay widgets
#     layout = QVBoxLayout(window)
#     layout.setAlignment(Qt.AlignCenter)
#     overlay = QWidget()
#     overlay_layout = QVBoxLayout(overlay)
#     overlay_layout.setSpacing(40)
#     overlay_layout.setAlignment(Qt.AlignCenter)
#     overlay.setStyleSheet("background-color: rgba(255, 255, 255, 180); border-radius: 15px;")

#     # Prompt label
#     prompt = QLabel('How are you?')
#     prompt.setStyleSheet("font-size: 36px; font-weight: bold;")
#     overlay_layout.addWidget(prompt)

#     # Helper to create styled buttons
#     def make_button(text):
#         btn = QPushButton(text)
#         btn.setFixedSize(400, 100)
#         btn.setStyleSheet(
#             "font-size: 32px; padding: 20px;"
#             "QPushButton { background-color: #4CAF50; color: white; border-radius: 20px; }"
#             "QPushButton:hover { background-color: #45a049; }"
#         )
#         return btn

#     # Create buttons
#     btn_good = make_button("I am good")
#     btn_not_good = make_button("I am not good")
#     overlay_layout.addWidget(btn_good)
#     overlay_layout.addWidget(btn_not_good)
#     layout.addWidget(overlay)

#     # Show window in fullscreen and start timing
#     window.showFullScreen()
#     start_time = time.time()

#     # Connect button signals
#     btn_good.clicked.connect(lambda: record_response('good', time.time() - start_time))
#     btn_not_good.clicked.connect(lambda: record_response('not_good', time.time() - start_time))

#     # Start audio in background thread
#     threading.Thread(target=play_greeting, daemon=True).start()

#     sys.exit(app.exec_())

# if __name__ == '__main__':
#     main()
import sys
import os
import time
import threading
import pandas as pd
from gtts import gTTS
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QFont
from PyQt5.QtCore import Qt

# 1. Read name from CSV
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)
df_path = os.path.join(logs_dir, "kid_info.csv")
df = pd.read_csv(df_path)
first_name = df.iloc[-1]['name']

# 2. Create greeting text and audio file
greeting = f"Hello {first_name}, how are you!"
audio_file = os.path.join(logs_dir, "greeting.mp3")
if not os.path.exists(audio_file):
    tts = gTTS(text=greeting, lang='en')
    tts.save(audio_file)
    print(f"✅ Audio saved as {audio_file}")

# Function to play audio in background
def play_greeting():
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    print("🔊 Playing the greeting...")
    while pygame.mixer.music.get_busy():
        pygame.time.delay(100)
    pygame.mixer.quit()
    print("✅ Playback finished.")
    # Delete the audio file after playback
    try:
        os.remove(audio_file)
        print(f"🗑️ Deleted audio file: {audio_file}")
    except OSError as e:
        print(f"⚠️ Could not delete audio file: {e}")

# Function to record user response
def record_response(response_text, response_time):
    log_file = os.path.join(logs_dir, f"{first_name}_Response.csv")
    header = ['response', 'response_time']
    entry = {'response': response_text, 'response_time': response_time}
    if not os.path.exists(log_file):
        pd.DataFrame(columns=header).to_csv(log_file, index=False)
    pd.DataFrame([entry]).to_csv(log_file, mode='a', header=False, index=False)
    print(f"✅ Logged: {entry} to {log_file}")
    QApplication.quit()

# 3. Build and show UI
def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('How are you?')

    # Load background image
    bg_pixmap = QPixmap('src/background.jpg')
    palette = QPalette()
    palette.setBrush(QPalette.Window, QBrush(bg_pixmap.scaled(window.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
    window.setPalette(palette)

    # Ensure background scales on resize
    def on_resize(event):
        scaled = bg_pixmap.scaled(window.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        window.setPalette(palette)
        QWidget.resizeEvent(window, event)
    window.resizeEvent = on_resize

    # Main layout
    layout = QVBoxLayout(window)
    layout.setAlignment(Qt.AlignCenter)
    layout.setContentsMargins(50, 50, 50, 50)

    # Overlay container
    overlay = QWidget()
    overlay_layout = QVBoxLayout(overlay)
    overlay_layout.setSpacing(60)
    overlay_layout.setAlignment(Qt.AlignCenter)
    overlay.setStyleSheet(
        "background-color: rgba(255, 255, 255, 230);"
        "border-radius: 25px;"
        "padding: 40px;"
    )
    # Drop shadow effect
    shadow = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=0)
    overlay.setGraphicsEffect(shadow)

    # Prompt label
    prompt = QLabel(f'How are you, {first_name}?')
    prompt_font = QFont('Arial', 40, QFont.Bold)
    prompt.setFont(prompt_font)
    prompt.setAlignment(Qt.AlignCenter)
    overlay_layout.addWidget(prompt)

    # Helper to create styled buttons
    def make_button(text):
        btn = QPushButton(text)
        btn.setFixedSize(500, 120)
        btn_font = QFont('Arial', 28)
        btn.setFont(btn_font)
        btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border-radius: 30px; padding: 20px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        return btn

    # Create buttons
    btn_good = make_button("I am good")
    btn_not_good = make_button("I am not good")
    overlay_layout.addWidget(btn_good, alignment=Qt.AlignCenter)
    overlay_layout.addWidget(btn_not_good, alignment=Qt.AlignCenter)
    layout.addWidget(overlay, alignment=Qt.AlignCenter)

    # Show window full-screen
    window.showFullScreen()
    start_time = time.time()

    # Connect button signals
    btn_good.clicked.connect(lambda: record_response('good', time.time() - start_time))
    btn_not_good.clicked.connect(lambda: record_response('not_good', time.time() - start_time))

    # Start audio
    threading.Thread(target=play_greeting, daemon=True).start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
