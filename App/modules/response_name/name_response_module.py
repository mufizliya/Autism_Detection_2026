import sys
import os
import time
import threading
from gtts import gTTS
import pygame

from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect
)

from PyQt5.QtGui import (
    QPixmap,
    QPalette,
    QBrush,
    QFont
)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)


class NameResponseModule:

    def __init__(self):
        self.response_data = {}

    def play_greeting(self, audio_file):

        pygame.mixer.init()

        pygame.mixer.music.load(audio_file)

        pygame.mixer.music.play()

        print("🔊 Playing greeting...")

        while pygame.mixer.music.get_busy():
            pygame.time.delay(100)

        

        try:
            os.remove(audio_file)

        except OSError as e:
            print(f"⚠️ Could not delete audio file: {e}")

    def calculate_emotional_phenotypes(
    self,
    response_text,
    response_time
    ):

        emotional_distress = (
            1.0
            if response_text == "not_good"
            else 0.0
        )

        social_hesitation = round(
            min(response_time / 10, 1),
            2
        )

        interaction_engagement = 1.0

        emotional_responsiveness = round(
            max(
                0,
                1 - (response_time / 10)
            ),
            2
        )

        phenotypes = {

            "emotional_distress":
                emotional_distress,

            "social_hesitation":
                social_hesitation,

            "interaction_engagement":
                interaction_engagement,

            "emotional_responsiveness":
                emotional_responsiveness
        }

        return phenotypes
    
    def run(self, session):

        child_info = session["child_info"]

        child_name = child_info["name"]

        greeting = f"Hello {child_name}, how are you!"

        audio_file = os.path.join(
            LOG_DIR,
            "greeting.mp3"
        )

        tts = gTTS(
            text=greeting,
            lang='en'
        )

        tts.save(audio_file)

        app = QApplication.instance()

        if app is None:
            app = QApplication(sys.argv)

        window = QWidget()

        window.setWindowTitle("How are you?")

        bg_pixmap = QPixmap('src/background.jpg')

        palette = QPalette()

        palette.setBrush(
            QPalette.Window,
            QBrush(
                bg_pixmap.scaled(
                    window.size(),
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        )

        window.setPalette(palette)

        def on_resize(event):

            scaled = bg_pixmap.scaled(
                window.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

            palette.setBrush(
                QPalette.Window,
                QBrush(scaled)
            )

            window.setPalette(palette)

            QWidget.resizeEvent(window, event)

        window.resizeEvent = on_resize

        layout = QVBoxLayout(window)

        layout.setAlignment(Qt.AlignCenter)

        overlay = QWidget()

        overlay_layout = QVBoxLayout(overlay)

        overlay_layout.setSpacing(60)

        overlay_layout.setAlignment(Qt.AlignCenter)

        overlay.setStyleSheet(
            "background-color: rgba(255,255,255,230);"
            "border-radius: 25px;"
            "padding: 40px;"
        )

        shadow = QGraphicsDropShadowEffect(
            blurRadius=20,
            xOffset=0,
            yOffset=0
        )

        overlay.setGraphicsEffect(shadow)

        prompt = QLabel(
            f'How are you, {child_name}?'
        )

        prompt_font = QFont(
            'Arial',
            40,
            QFont.Bold
        )

        prompt.setFont(prompt_font)

        prompt.setAlignment(Qt.AlignCenter)

        overlay_layout.addWidget(prompt)

        def make_button(text):

            btn = QPushButton(text)

            btn.setFixedSize(500, 120)

            btn_font = QFont(
                'Arial',
                28
            )

            btn.setFont(btn_font)

            btn.setStyleSheet(
                "QPushButton {"
                "background-color: #4CAF50;"
                "color: white;"
                "border-radius: 30px;"
                "padding: 20px;"
                "}"
                "QPushButton:hover {"
                "background-color: #45a049;"
                "}"
            )

            return btn

        btn_good = make_button("I am good")

        btn_not_good = make_button(
            "I am not good"
        )

        overlay_layout.addWidget(
            btn_good,
            alignment=Qt.AlignCenter
        )

        overlay_layout.addWidget(
            btn_not_good,
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            overlay,
            alignment=Qt.AlignCenter
        )

        window.showFullScreen()

        start_time = time.time()

        def record_response(response_text):

            response_time = (
                time.time() - start_time
            )
            emotional_phenotypes = (
                self.calculate_emotional_phenotypes(
                response_text,
                response_time
                )
            )

            self.response_data = {
                "response": response_text,
                "response_time": response_time,
                "emotional_phenotypes": emotional_phenotypes
            }

            session["name_response"] = (
                self.response_data
            )
            session_manager = (
                session["session_manager"]
            )
            session_manager.save_json(
                "name_response.json", self.response_data
            )

            window.close()

        btn_good.clicked.connect(
            lambda: record_response("good")
        )

        btn_not_good.clicked.connect(
            lambda: record_response("not_good")
        )

        threading.Thread(
            target=self.play_greeting,
            args=(audio_file,),
            daemon=True
        ).start()

        app.exec_()