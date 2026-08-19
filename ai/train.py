import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

def train():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "dataset", "disaster_relief_requests.csv")
    model_dir = os.path.join(current_dir, "model")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "priority_classifier.joblib")

    print(f"Loading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)

    # Features and Target
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

    # Preprocessing
    categorical_features = ["disaster_type"]
    numeric_features = [
        "affected_people",
        "location_risk_score",
        "medical_needed",
        "water_needed",
        "food_needed",
        "vulnerable_population",
        "time_elapsed_hours",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    # Pipeline with Random Forest Classifier
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=150,
                    max_depth=12,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training Random Forest Emergency Triage Classifier...")
    pipeline.fit(X_train, y_train)

    # Validation
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save artifact
    joblib.dump(pipeline, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    train()
