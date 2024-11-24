import sys
import json
import pickle
import pandas as pd
import numpy as np

def preprocess_input(data):
    df = pd.DataFrame([data])
    
    with open('scaler.pkl', 'rb') as file:
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
    with open('random_forest_model_with_classification.pkl', 'rb') as file:
        model_data = pickle.load(file)
    return model_data['model']

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

if __name__ == "__main__":
    try:
        input_data = json.loads(sys.argv[1])
        
        model = load_model()
        
        processed_input = preprocess_input(input_data)
        
        prediction = model.predict(processed_input)[0]
        probability = model.predict_proba(processed_input)[0][1]
        
        result = {
            "status": "success",
            "prediction": int(prediction),
            "probability": float(probability),
            "classification": classify_target(prediction, probability)
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)