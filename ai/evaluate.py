"""
ReliefChain AI - Machine Learning Model Evaluation & Metrics Report
Evaluates the trained Random Forest Priority Classifier against the disaster dataset.
"""
import os
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, precision_score, recall_score


def evaluate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "dataset", "disaster_relief_requests.csv")
    model_path = os.path.join(current_dir, "model", "priority_classifier.joblib")

    if not os.path.exists(model_path):
        print("Model file not found. Training model first via train.py...")
        from train import train
        train()

    print(f"Loading trained model from: {model_path}")
    pipeline = joblib.load(model_path)

    print(f"Loading evaluation dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)

    feature_cols = [
        "disaster_type",
        "affected_people",
        "location_risk_score",
        "medical_needed",
        "water_needed",
        "food_needed",
        "vulnerable_population",
        "time_elapsed_hours",
    ]
    target_col = "priority"

    X = df[feature_cols]
    y = df[target_col]

    y_pred = pipeline.predict(X)

    accuracy = accuracy_score(y, y_pred)
    macro_f1 = f1_score(y, y_pred, average="macro")
    macro_precision = precision_score(y, y_pred, average="macro")
    macro_recall = recall_score(y, y_pred, average="macro")

    labels = ["low", "medium", "high", "critical"]
    cm = confusion_matrix(y, y_pred, labels=labels)

    print("\n========================================================")
    print("      RELIEFCHAIN AI - EMERGENCY TRIAGE EVALUATION      ")
    print("========================================================")
    print(f"Dataset Size:           {len(df)} historical/synthetic disaster reports")
    print(f"Overall Accuracy:       {accuracy * 100:.2f}%")
    print(f"Macro Precision:        {macro_precision * 100:.2f}%")
    print(f"Macro Recall:           {macro_recall * 100:.2f}%")
    print(f"Macro F1-Score:         {macro_f1 * 100:.2f}%\n")

    print("Confusion Matrix (Rows: Actual, Cols: Predicted):")
    header = f"{'':10}" + "".join([f"{lbl.upper():>10}" for lbl in labels])
    print(header)
    print("-" * 50)
    for idx, row in enumerate(cm):
        row_str = f"{labels[idx].upper():10}" + "".join([f"{val:10d}" for val in row])
        print(row_str)

    print("\nDetailed Classification Report:")
    print(classification_report(y, y_pred, labels=labels, digits=4))
    print("========================================================")
    print("Technical Note: The model operates as an emergency decision")
    print("support classifier for prioritizing humanitarian responses.")
    print("========================================================\n")


if __name__ == "__main__":
    evaluate()
