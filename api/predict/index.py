from http.server import BaseHTTPRequestHandler
import json
import joblib  # Replace pickle with joblib for better compression
import pandas as pd
import numpy as np
from os import path

def preprocess_input(data):
    df = pd.DataFrame([data])
    
    # Load scaler with joblib instead of pickle
    scaler_path = path.join(path.dirname(__file__), 'scaler.joblib')
    scaler = joblib.load(scaler_path)
    
    continuous_columns = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']
    binary_columns = ['sex', 'fbs', 'exang']
    other_numeric = ['ca']
    
    df[continuous_columns] = scaler.transform(df[continuous_columns])
    
    # Simplified one-hot encoding
    encoded_features = {
        f'cp_{i}': 1 if data['cp'] == i else 0 for i in range(1, 4)
    } | {
        f'restecg_{i}': 1 if data['restecg'] == i else 0 for i in range(1, 3)
    } | {
        f'slope_{i}': 1 if data['slope'] == i else 0 for i in range(1, 3)
    } | {
        f'thal_{i}': 1 if data['thal'] == i else 0 for i in range(1, 4)
    }
    
    # Combine features more efficiently
    final_features = {
        **{col: df[col].iloc[0] for col in continuous_columns},
        **{col: data[col] for col in binary_columns + other_numeric},
        **encoded_features
    }
    
    expected_columns = [
        'age', 'sex', 'trestbps', 'chol', 'fbs', 'thalach', 'exang', 'oldpeak', 'ca',
        'cp_1', 'cp_2', 'cp_3', 'restecg_1', 'restecg_2', 'slope_1', 'slope_2',
        'thal_1', 'thal_2', 'thal_3'
    ]
    
    return pd.DataFrame([final_features])[expected_columns]

def load_model():
    """Loads the trained model from joblib file"""
    try:
        model_path = path.join(path.dirname(__file__), 'random_forest_model.joblib')
        return joblib.load(model_path)
    except Exception as e:
        raise Exception(f"Failed to load model: {str(e)}")

def classify_stage(probability):
    if probability < 0.4:
        return "Early Stage"
    elif probability < 0.7:
        return "Medium Stage"
    return "Critical Stage"

def handler(request):
    """Handle incoming requests"""
    if request.method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS,PATCH,DELETE,POST,PUT",
                "Access-Control-Allow-Headers": "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
            },
            "body": ""
        }

    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        # Parse input
        body = request.body
        input_data = json.loads(body) if isinstance(body, str) else body
        if not input_data:
            raise ValueError("Invalid or empty request data")

        # Process and predict
        model = load_model()
        processed_input = preprocess_input(input_data)
        prediction = model.predict(processed_input)[0]
        probability = model.predict_proba(processed_input)[0][1]
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "success",
                "prediction": int(prediction),
                "probability": float(probability),
                "classification": "No Disease" if prediction == 0 else classify_stage(probability)
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "error",
                "message": str(e),
                "type": str(type(e).__name__)
            })
        }