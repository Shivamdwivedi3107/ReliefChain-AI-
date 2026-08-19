# ReliefChain AI — Emergency Prioritization Decision Support System (DSS)

## Overview
This module trains and deploys a supervised Machine Learning pipeline (Random Forest Classifier + ColumnTransformer) to evaluate incoming disaster distress calls and suggest an urgency tier (`low`, `medium`, `high`, `critical`).

## Ethical AI & Decision Support Boundaries
> **IMPORTANT NOTE**: This AI prioritization model operates strictly as an **assistive Decision Support System (DSS)**. It is designed to flag potential high-urgency distress situations to human disaster response coordinators. It **does NOT** replace trained emergency responders or make autonomous life-safety decisions.

## Feature Architecture
* `disaster_type`: Categorical (Earthquake, Flood, Cyclone, Wildfire, Landslide, Tsunami)
* `affected_people`: Integer count of individuals stranded/affected
* `location_risk_score`: Continuous hazard metric (1.0 to 10.0)
* `medical_needed`: Binary indicator for injury / trauma / medical attention
* `water_needed`: Binary indicator for safe drinking water
* `food_needed`: Binary indicator for rations
* `vulnerable_population`: Binary indicator for infants, elderly, pregnant women
* `time_elapsed_hours`: Time since request creation without aid

## Usage
1. Generate synthetic dataset:
   ```powershell
   python ai/dataset/generate_dataset.py
   ```
2. Train model:
   ```powershell
   python ai/train.py
   ```
3. Evaluate metrics:
   ```powershell
   python ai/evaluate.py
   ```
