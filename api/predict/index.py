try:
    from http.server import BaseHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler

import json
import pickle
import pandas as pd
import numpy as np
from os import path

def preprocess_input(data):
    df = pd.DataFrame([data])
    
    scaler_path = path.join(path.dirname(__file__), 'scaler.pkl')
    with open(scaler_path, 'rb') as file:
        scaler = pickle.load(file)
    
    continuous_columns = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']
    binary_columns = ['sex', 'fbs', 'exang']
    other_numeric = ['ca']
    
    df[continuous_columns] = scaler.transform(df[continuous_columns])
    
    encoded_features = {
        'cp_1': 1 if data['cp'] == 1 else 0,
        'cp_2': 1 if data['cp'] == 2 else 0,
        'cp_3': 1 if data['cp'] == 3 else 0,
        'restecg_1': 1 if data['restecg'] == 1 else 0,
        'restecg_2': 1 if data['restecg'] == 2 else 0,
        'slope_1': 1 if data['slope'] == 1 else 0,
        'slope_2': 1 if data['slope'] == 2 else 0,
        'thal_1': 1 if data['thal'] == 1 else 0,
        'thal_2': 1 if data['thal'] == 2 else 0,
        'thal_3': 1 if data['thal'] == 3 else 0
    }
    
    final_features = {}
    
    for col in continuous_columns:
        final_features[col] = df[col].iloc[0]
    
    for col in binary_columns:
        final_features[col] = data[col]
    
    for col in other_numeric:
        final_features[col] = data[col]
    
    final_features.update(encoded_features)
    
    final_df = pd.DataFrame([final_features])
    
    expected_columns = [
        'age', 'sex', 'trestbps', 'chol', 'fbs', 'thalach', 'exang', 'oldpeak', 'ca',
        'cp_1', 'cp_2', 'cp_3', 'restecg_1', 'restecg_2', 'slope_1', 'slope_2',
        'thal_1', 'thal_2', 'thal_3'
    ]
    
    final_df = final_df[expected_columns]
    
    return final_df

def load_model():
    """Loads the trained model from pickle file"""
    try:
        model_path = path.join(path.dirname(__file__), 'random_forest_model_with_classification.pkl')
        with open(model_path, 'rb') as file:
            model_data = pickle.load(file)
        return model_data['model']
    except Exception as e:
        raise Exception(f"Failed to load model: {str(e)}")

def classify_stage(probability):
    """Classifies the disease stage based on probability"""
    if probability < 0.4:
        return "Early Stage"
    elif 0.4 <= probability < 0.7:
        return "Medium Stage"
    else:
        return "Critical Stage"

def classify_target(target, probability):
    """Combines target prediction and stage classification"""
    if target == 0:
        return "No Disease"
    else:
        return classify_stage(probability)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT')
        self.send_header('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Empty request body")

            post_data = self.rfile.read(content_length)
            if not post_data:
                raise ValueError("No data received")

            input_data = json.loads(post_data.decode('utf-8'))
            
            if not input_data:
                raise ValueError("Invalid JSON data")

            model = load_model()
            if not model:
                raise ValueError("Model failed to load")

            processed_input = preprocess_input(input_data)
            
            prediction = model.predict(processed_input)[0]
            probability = model.predict_proba(processed_input)[0][1]
            
            result = {
                "status": "success",
                "prediction": int(prediction),
                "probability": float(probability),
                "classification": classify_target(prediction, probability)
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "type": str(type(e).__name__)
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())