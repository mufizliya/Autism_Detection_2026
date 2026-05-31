import pandas as pd
import sys
import os
import csv
import json
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets

BG_COLOR = "#F5F7FA"
PRIMARY_COLOR = "#34495E"
SECONDARY_COLOR = "#1ABC9C"
ACCENT_COLOR = "#E74C3C"
FONT_NAME = "Segoe UI"
SCQ_THRESHOLD = 15  # Total score threshold for further evaluation
LOG_DIR = "logs"

SCQ_QUESTIONS = [
    "Is she/he now able to talk using short phrases or sentences?",
    "Can you have a to-and-fro \"conversation\" with her/him that involves taking turns or building on what she/he has said?",
    "Does she/he ever use gestures to indicate interest in something?",
    "Does she/he ever point to express interest in something?",
    "Does she/he ever bring objects over to show you something?",
    "Does she/he look you in the eye when talking to you?",
    "Does she/he ever seem overly sensitive to noise?",
    "Does she/he respond when you call her/his name?",
    "Does she/he smile back when someone smiles at her/him?",
    "Does she/he ever show interest in other children her/his age?",
    "Does she/he ever engage in \"pretend\" or \"make-believe\" play?",
    "Does she/he ever use her/his index finger to point, to ask for something?",
    "Does she/he ever use her/his index finger to point, to indicate interest in something?",
    "Can she/he play appropriately with small toys (cars, dolls, building blocks) without just mouthing, fiddling, or dropping them?",
    "Does she/he ever pretend objects are something else? (e.g., cup as a telephone)",
    "Does she/he ever imitate you?",
    "Does she/he ever imitate other children?",
    "Does she/he respond positively when others approach her/him?",
    "Does she/he try to comfort someone who is hurt or upset?",
    "Does she/he enjoy being held or cuddled?",
    "Does she/he get affected by unusual or unexpected noises?",
    "Does she/he have any unusual preoccupations?",
    "Does she/he have any compulsive or repetitive behaviors?",
    "Does she/he ever injure herself deliberately (e.g., biting, banging head)?",
    "Does she/he have any unusual sensory interests (e.g., sniffing objects)?",
    "Does she/he display complex body movements (e.g., hand flapping)?",
    "Does she/he ever repeat things that you or others have said (echolalia)?",
    "Does she/he ever use stereotyped or repetitive speech?",
    "Does she/he have difficulty with changes in routine or surroundings?",
    "Does she/he have any special interests or hobbies?",
    "Does she/he ever seem to be in a world of her/his own?",
    "Does she/he ever become excessively distressed for no apparent reason?",
    "Does she/he have difficulty understanding other people's feelings?",
    "Does she/he ever laugh or giggle inappropriately?",
    "Does she/he ever make unusual facial expressions?",
    "Does she/he ever look at things from unusual angles?",
    "Does she/he ever have any strange or unusual interests?",
    "Has she/he ever seemed uninterested in interacting with you?",
    "Does she/he tend to walk on her/his toes?",
    "Does she/he have any unusual fears or anxieties?"
]

# Autism-indicative response for each question ("Yes" or "No")
SCQ_AUTISM_RESPONSE = [
    "No", "No", "No", "No", "No", "No",
    "Yes", "No", "No", "No",
    "No", "No", "No", "No", "No",
    "No", "No", "No", "No", "No",
    "Yes", "Yes", "Yes", "Yes", "Yes",
    "Yes", "Yes", "Yes", "Yes",
    "Yes", "Yes", "Yes", "Yes", "Yes",
    "Yes", "Yes", "Yes", "Yes",
    "Yes", "Yes"
]

PHENOTYPE_MAP = {

    "social_communication": [
        1, 2, 3, 4, 5, 6, 8, 9, 10,
        11, 12, 13, 15, 16, 17, 18,
        19, 33, 38
    ],

    "sensory_sensitivity": [
        7, 21, 25, 36
    ],

    "repetitive_behavior": [
        22, 23, 24, 26, 27, 28,
        29, 30, 39
    ],

    "emotional_regulation": [
        31, 32, 34, 40
    ],

    "motor_behavior": [
        26, 39
    ]
}


class InfoPage(QtWidgets.QWidget):
    submitted = QtCore.pyqtSignal(dict)

    def __init__(self, session):
        super().__init__()
        self.setup_ui()
        self.session = session

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Child Information Entry")
        title.setFont(QtGui.QFont(FONT_NAME, 24, QtGui.QFont.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR};")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        form_frame = QtWidgets.QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: white; border-radius: 15px; padding: 30px; }}")
        form_layout = QtWidgets.QFormLayout(form_frame)
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        form_layout.setHorizontalSpacing(30)

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter full name")
        self.age_input = QtWidgets.QSpinBox()
        self.age_input.setRange(2, 18)
        self.gender_input = QtWidgets.QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])

        for widget in (self.name_input, self.age_input, self.gender_input):
            widget.setFixedHeight(35)
            widget.setStyleSheet(
                "QLineEdit, QComboBox, QSpinBox { border: 1px solid #ccc; border-radius: 8px; padding: 0 10px; }"
            )

        form_layout.addRow("Full Name:", self.name_input)
        form_layout.addRow("Age:", self.age_input)
        form_layout.addRow("Gender:", self.gender_input)
        layout.addWidget(form_frame)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        submit_btn = QtWidgets.QPushButton("Submit Information")
        submit_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        submit_btn.setFixedHeight(45)
        submit_btn.setStyleSheet(
            f"QPushButton {{ background: {SECONDARY_COLOR}; color: white; font-size: 16px; border-radius: 8px; }}"
            "QPushButton:hover { background: #16A085; }"
        )
        submit_btn.clicked.connect(self.on_submit)
        layout.addWidget(submit_btn)

    def on_submit(self):
        name = self.name_input.text().strip()
        age = str(self.age_input.value())
        gender = self.gender_input.currentText()
        if not name:
            self.status_label.setText("Please enter the child's name.")
            self.status_label.setStyleSheet("color: red;")
            return
        info = {"name": name, "age": age, "gender": gender, "timestamp": datetime.now().isoformat()}
        self.session["child_info"] = info
        session_manager = self.session["session_manager"]
        session_manager.save_json(
            "child_info.json", info
        )
        self.status_label.setText("Information saved. Proceeding to questionnaire...")
        self.status_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        QtCore.QTimer.singleShot(1000, lambda: self.submitted.emit(info))

class QuestionnairePage(QtWidgets.QWidget):
    finished = QtCore.pyqtSignal(int, dict, dict)

    def __init__(self, questions, kid_info):
        super().__init__()
        self.questions = questions
        self.kid_info = kid_info
        self.vars = []
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QtWidgets.QLabel("Social Communication Questionnaire (SCQ)")
        title.setFont(QtGui.QFont(FONT_NAME, 20, QtGui.QFont.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR}; margin-bottom: 20px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        info_lbl = QtWidgets.QLabel(f"Child: {self.kid_info['name']} | Age: {self.kid_info['age']} | Gender: {self.kid_info['gender']}")
        info_lbl.setFont(QtGui.QFont(FONT_NAME, 12))
        info_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info_lbl)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setSpacing(20)

        for q in self.questions:
            frame = QtWidgets.QFrame()
            frame.setStyleSheet("QFrame { background: white; border-radius: 10px; padding: 20px; }")
            v_layout = QtWidgets.QVBoxLayout(frame)
            lbl = QtWidgets.QLabel(q)
            lbl.setWordWrap(True)
            lbl.setFont(QtGui.QFont(FONT_NAME, 11))
            v_layout.addWidget(lbl)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setSpacing(40)
            group = QtWidgets.QButtonGroup(frame)
            yes = QtWidgets.QRadioButton("Yes")
            no = QtWidgets.QRadioButton("No")
            yes.setChecked(True)
            for btn in (yes, no):
                btn.setFixedHeight(25)
                btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                btn_layout.addWidget(btn)
                group.addButton(btn)
            v_layout.addLayout(btn_layout)
            container_layout.addWidget(frame)
            self.vars.append(group)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        submit_btn = QtWidgets.QPushButton("Submit SCQ")
        submit_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        submit_btn.setFixedHeight(45)
        submit_btn.setStyleSheet(
            f"QPushButton {{ background: {SECONDARY_COLOR}; color: white; font-size: 16px; border-radius: 8px; }}"
            "QPushButton:hover { background: #16A085; }"
        )
        submit_btn.clicked.connect(self.on_submit)
        layout.addWidget(submit_btn)

    def on_submit(self):
        answers = {f"Q{i+1}": ('Yes' if grp.checkedButton().text() == 'Yes' else 'No')
                   for i, grp in enumerate(self.vars)}
        score = sum(1 for i, resp in enumerate(answers.values())
                    if resp == SCQ_AUTISM_RESPONSE[i])
        self.finished.emit(score, answers, self.kid_info)
        
class QuestionnaireModule:
    def __init__(self):
        self.app = None
        self.kid_info = None
        self.score = None
        self.answers = None
    
    def calculate_phenotypes(self, answers):

        phenotype_scores = {}

        for phenotype, question_indexes in PHENOTYPE_MAP.items():

            score = 0

            for q_index in question_indexes:

                question_key = f"Q{q_index}"

                response = answers[question_key]

                autism_response = (
                SCQ_AUTISM_RESPONSE[q_index - 1]
                )

                if response == autism_response:
                    score += 1

            max_score = len(question_indexes)

            normalized_score = round(
                score / max_score,
                2
            )

            phenotype_scores[phenotype] = {
                "raw_score": score,
                "max_score": max_score,
                "severity": normalized_score
            }

        return phenotype_scores

    def run(self, session):
        self.session = session
        
        self.app = QtWidgets.QApplication(sys.argv)

        self.info_page = InfoPage(self.session)
        self.info_page.submitted.connect(self.handle_info_submission)

        self.info_page.show()
        self.app.exec_()

    def handle_info_submission(self, info):
        self.session["child_info"] = info

        self.question_page = QuestionnairePage(
            SCQ_QUESTIONS,
            info
        )

        self.question_page.finished.connect(self.handle_questionnaire_finish)

        self.info_page.close()
        self.question_page.show()

    def handle_questionnaire_finish(self, score, answers, kid_info):
        outcome = (
            "Further evaluation recommended"
            if score >= SCQ_THRESHOLD
            else "Screening indicates low risk"
        )
        phenotype_scores = self.calculate_phenotypes(
            answers
        )

        self.session["questionnaire"] = {
            "score": score,
            "outcome": outcome,
            "answers": answers,
            "phenotypes": phenotype_scores,
        }

        record = {
            "timestamp": datetime.now().isoformat(),
            "name": kid_info['name'],
            "age": kid_info['age'],
            "gender": kid_info['gender'],
            "scq_score": score,
            "outcome": outcome,
            "phenotypes": phenotype_scores,
            "answers": json.dumps(answers)
        }

        self.session["scq_results"] = record

        session_manager = self.session["session_manager"]

        session_manager.save_json(
            "scq_results.json",record
        )

        QtWidgets.QMessageBox.information(
            None,
            "SCQ Result",
            f"Score: {score}\nOutcome: {outcome}"
        )

        self.question_page.close()

        self.app.quit()