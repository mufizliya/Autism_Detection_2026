import os
import csv


class LabelManager:

    RAW_DATASET_FILE = os.path.join(
        "logs",
        "dataset",
        "phenotype_dataset.csv"
    )

    CLEANED_DATASET_FILE = os.path.join(
        "logs",
        "dataset",
        "phenotype_dataset_cleaned.csv"
    )

    @staticmethod
    def ask_label():

        print()
        print("Optional session label:")
        print("0 = Low-risk / non-ASD-like")
        print("1 = High-risk / ASD-like")
        print("skip = leave unlabeled")
        print()

        label = input(
            "Enter label for this session: "
        ).strip().lower()

        if label in ["0", "1"]:
            return label

        return ""

    @staticmethod
    def update_label_in_csv(
        file_path,
        session_id,
        label
    ):

        if not os.path.exists(file_path):

            print(
                f"⚠️ Dataset file not found: {file_path}"
            )

            return

        rows = []

        with open(
            file_path,
            "r",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            headers = reader.fieldnames

            if headers is None:

                print(
                    f"⚠️ No headers found in {file_path}"
                )

                return

            if "label" not in headers:

                headers.append("label")

            for row in reader:

                if row.get("session_id") == session_id:

                    row["label"] = label

                rows.append(row)

        with open(
            file_path,
            "w",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=headers
            )

            writer.writeheader()

            for row in rows:

                cleaned_row = {}

                for header in headers:

                    cleaned_row[header] = row.get(
                        header,
                        ""
                    )

                writer.writerow(cleaned_row)

        print(
            f"✅ Label updated in {file_path}"
        )

    @staticmethod
    def label_session(session):

        session_id = session.get(
            "session_id"
        )

        if not session_id:

            print(
                "⚠️ No session_id found. Cannot label session."
            )

            return

        label = LabelManager.ask_label()

        session["label"] = label

        if label == "":

            print(
                "ℹ️ Session left unlabeled."
            )

        else:

            print(
                f"✅ Session label set to: {label}"
            )

        LabelManager.update_label_in_csv(
            LabelManager.RAW_DATASET_FILE,
            session_id,
            label
        )

        LabelManager.update_label_in_csv(
            LabelManager.CLEANED_DATASET_FILE,
            session_id,
            label
        )