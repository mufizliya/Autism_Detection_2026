import os
import csv


class DatasetExporter:

    DATASET_DIR = os.path.join(
        "logs",
        "dataset"
    )

    DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset.csv"
    )

    @staticmethod
    def flatten_value(value):

        if value is None:
            return ""

        if isinstance(value, (int, float, str)):
            return value

        return str(value)

    @staticmethod
    def build_dataset_row(session):

        phenotype_vector = session.get(
            "phenotype_vector",
            {}
        )

        risk_assessment = session.get(
            "risk_assessment",
            {}
        )

        session_quality = session.get(
            "session_quality",
            {}
        )

        child_info = session.get(
            "child_info",
            {}
        )

        row = {
            "session_id":
                session.get(
                    "session_id",
                    ""
                ),

            "session_quality_score":
                session_quality.get(
                    "quality_score",
                    ""
                ),

            "session_quality_level":
                session_quality.get(
                    "quality_level",
                    ""
                ),

            "session_is_valid":
                session_quality.get(
                    "is_valid",
                    ""
                ),

            "child_age":
                child_info.get(
                    "age",
                    ""
                ),

            "child_gender":
                child_info.get(
                    "gender",
                    ""
                ),

            "risk_level_rule_based":
                risk_assessment.get(
                    "risk_level",
                    ""
                ),

            "risk_score_rule_based":
                risk_assessment.get(
                    "overall_risk_score",
                    ""
                ),

            # This is intentionally empty for now.
            # Later we can fill it with:
            # ASD / Non-ASD
            # High Risk / Low Risk
            # Clinician confirmed labels, etc.
            "label":
                ""
        }

        for key, value in phenotype_vector.items():

            row[key] = DatasetExporter.flatten_value(
                value
            )

        return row

    @staticmethod
    def append_session(session):

        os.makedirs(
            DatasetExporter.DATASET_DIR,
            exist_ok=True
        )

        row = DatasetExporter.build_dataset_row(
            session
        )

        file_exists = os.path.exists(
            DatasetExporter.DATASET_FILE
        )

        existing_headers = []

        if file_exists:

            with open(
                DatasetExporter.DATASET_FILE,
                "r",
                newline=""
            ) as f:

                reader = csv.reader(f)

                try:
                    existing_headers = next(reader)

                except StopIteration:
                    existing_headers = []

        new_headers = list(row.keys())

        if existing_headers:

            headers = existing_headers.copy()

            for header in new_headers:

                if header not in headers:
                    headers.append(header)

        else:

            headers = new_headers

        rows = []

        if file_exists and existing_headers:

            with open(
                DatasetExporter.DATASET_FILE,
                "r",
                newline=""
            ) as f:

                reader = csv.DictReader(f)

                for existing_row in reader:
                    rows.append(existing_row)

        rows.append(row)

        with open(
            DatasetExporter.DATASET_FILE,
            "w",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=headers
            )

            writer.writeheader()

            for dataset_row in rows:

                cleaned_row = {}

                for header in headers:

                    cleaned_row[header] = (
                        dataset_row.get(
                            header,
                            ""
                        )
                    )

                writer.writerow(cleaned_row)

        print(
            f"✅ Dataset row appended to "
            f"{DatasetExporter.DATASET_FILE}"
        )