import os
import csv
import json


class DatasetExporter:

    DATASET_DIR = os.path.join(
        "logs",
        "dataset"
    )

    DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset.csv"
    )

    CLEANED_DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset_cleaned.csv"
    )

    TRAIN_READY_DATASET_FILE = os.path.join(
        DATASET_DIR,
        "phenotype_dataset_train_ready.csv"
    )

    @staticmethod
    def flatten_value(value):

        if value is None:
            return ""

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (int, float, str)):
            return value

        return json.dumps(
            value,
            ensure_ascii=False
        )

    @staticmethod
    def count_quality_issues(session_quality):

        issues = session_quality.get(
            "issues",
            []
        )

        error_count = 0
        warning_count = 0
        info_count = 0

        issue_codes = []

        for issue in issues:

            severity = issue.get(
                "severity",
                ""
            )

            code = issue.get(
                "code",
                ""
            )

            if code:
                issue_codes.append(code)

            if severity == "error":
                error_count += 1

            elif severity == "warning":
                warning_count += 1

            elif severity == "info":
                info_count += 1

        return {
            "quality_error_count":
                error_count,

            "quality_warning_count":
                warning_count,

            "quality_info_count":
                info_count,

            "quality_issue_codes":
                "|".join(issue_codes)
        }

    @staticmethod
    def build_dataset_row(session):

        phenotype_vector = session.get(
            "phenotype_vector",
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

        questionnaire = session.get(
            "questionnaire",
            {}
        )

        risk_assessment = session.get(
            "risk_assessment",
            {}
        )

        quality_issue_summary = DatasetExporter.count_quality_issues(
            session_quality
        )

        label = session.get(
            "label",
            ""
        )

        row = {
            "session_id":
                session.get(
                    "session_id",
                    ""
                ),

            "label":
                label,

            "session_quality_score":
                session_quality.get(
                    "quality_score",
                    ""
                ),

            "session_quality_grade":
                session_quality.get(
                    "quality_grade",
                    session_quality.get(
                        "quality_level",
                        ""
                    )
                ),

            "session_is_valid":
                session_quality.get(
                    "is_valid",
                    ""
                ),

            "validator_version":
                session_quality.get(
                    "validator_version",
                    ""
                ),

            "child_age":
                child_info.get(
                    "age",
                    questionnaire.get(
                        "age",
                        ""
                    )
                ),

            "child_gender":
                child_info.get(
                    "gender",
                    questionnaire.get(
                        "gender",
                        ""
                    )
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
                )
        }

        row.update(
            quality_issue_summary
        )

        for key, value in phenotype_vector.items():

            row[key] = DatasetExporter.flatten_value(
                value
            )

        return row

    @staticmethod
    def read_csv_rows(path):

        if not os.path.exists(path):
            return [], []

        with open(
            path,
            "r",
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            headers = reader.fieldnames or []

            rows = []

            for row in reader:
                rows.append(row)

        return headers, rows

    @staticmethod
    def write_csv_rows(path, headers, rows):

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True
        )

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=headers
            )

            writer.writeheader()

            for row in rows:

                clean_row = {}

                for header in headers:

                    clean_row[header] = row.get(
                        header,
                        ""
                    )

                writer.writerow(
                    clean_row
                )

    @staticmethod
    def merge_headers(existing_headers, new_headers):

        headers = list(
            existing_headers
        )

        for header in new_headers:

            if header not in headers:

                headers.append(
                    header
                )

        return headers

    @staticmethod
    def upsert_row_by_session_id(rows, new_row):

        new_session_id = new_row.get(
            "session_id",
            ""
        )

        if new_session_id == "":

            rows.append(
                new_row
            )

            return rows

        updated = False

        output_rows = []

        for row in rows:

            if row.get(
                "session_id",
                ""
            ) == new_session_id:

                merged = dict(
                    row
                )

                merged.update(
                    new_row
                )

                output_rows.append(
                    merged
                )

                updated = True

            else:

                output_rows.append(
                    row
                )

        if not updated:

            output_rows.append(
                new_row
            )

        return output_rows

    @staticmethod
    def is_clean_row(row):

        session_is_valid = str(
            row.get(
                "session_is_valid",
                ""
            )
        ).lower()

        error_count = row.get(
            "quality_error_count",
            "0"
        )

        try:

            error_count = int(
                float(
                    error_count
                )
            )

        except Exception:

            error_count = 0

        return (
            session_is_valid in [
                "true",
                "1"
            ]
            and
            error_count == 0
        )

    @staticmethod
    def is_train_ready_row(row):

        if not DatasetExporter.is_clean_row(
            row
        ):

            return False

        label = str(
            row.get(
                "label",
                ""
            )
        ).strip()

        if label == "":
            return False

        if label.lower() in [
            "skip",
            "none",
            "null",
            "unlabeled"
        ]:
            return False

        return True

    @staticmethod
    def save_cleaned_and_train_ready(headers, all_rows):

        cleaned_rows = []

        train_ready_rows = []

        for row in all_rows:

            if DatasetExporter.is_clean_row(
                row
            ):

                cleaned_rows.append(
                    row
                )

            if DatasetExporter.is_train_ready_row(
                row
            ):

                train_ready_rows.append(
                    row
                )

        DatasetExporter.write_csv_rows(
            DatasetExporter.CLEANED_DATASET_FILE,
            headers,
            cleaned_rows
        )

        DatasetExporter.write_csv_rows(
            DatasetExporter.TRAIN_READY_DATASET_FILE,
            headers,
            train_ready_rows
        )

        print(
            f"✅ Cleaned dataset saved to: "
            f"{DatasetExporter.CLEANED_DATASET_FILE}"
        )

        print(
            f"Rows: {len(cleaned_rows)}"
        )

        print(
            f"✅ Train-ready dataset saved to: "
            f"{DatasetExporter.TRAIN_READY_DATASET_FILE}"
        )

        print(
            f"Train-ready rows: {len(train_ready_rows)}"
        )

    @staticmethod
    def append_session(session):

        os.makedirs(
            DatasetExporter.DATASET_DIR,
            exist_ok=True
        )

        row = DatasetExporter.build_dataset_row(
            session
        )

        existing_headers, rows = DatasetExporter.read_csv_rows(
            DatasetExporter.DATASET_FILE
        )

        new_headers = list(
            row.keys()
        )

        headers = DatasetExporter.merge_headers(
            existing_headers,
            new_headers
        )

        rows = DatasetExporter.upsert_row_by_session_id(
            rows,
            row
        )

        DatasetExporter.write_csv_rows(
            DatasetExporter.DATASET_FILE,
            headers,
            rows
        )

        print(
            f"✅ Dataset row appended/updated in "
            f"{DatasetExporter.DATASET_FILE}"
        )

        DatasetExporter.save_cleaned_and_train_ready(
            headers,
            rows
        )