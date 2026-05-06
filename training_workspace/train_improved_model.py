import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

def train_improved_model():
    # Load data
    df = pd.read_csv('final_training_data.csv')
    
    # Features and Target
    # We need to encode categorical variables
    le_district = LabelEncoder()
    le_season = LabelEncoder()
    le_crop = LabelEncoder()
    
    df['District_Encoded'] = le_district.fit_transform(df['District_Name'])
    df['Season_Encoded'] = le_season.fit_transform(df['Season'])
    df['Crop_Encoded'] = le_crop.fit_transform(df['Crop'])
    
    # Numerical Features to Scale
    scaler = StandardScaler()
    numerical_features = ['Area', 'Rainfall']
    df[numerical_features] = scaler.fit_transform(df[numerical_features])
    
    X = df[['District_Encoded', 'Season_Encoded', 'Crop_Encoded', 'Area', 'Rainfall']]
    
    # Log Transform Target
    # Use log1p to handle zeros if any (though production shouldn't be zero usually)
    y = np.log1p(df['Production'])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Model - Gradient Boosting
    print("Training Gradient Boosting Regressor...")
    model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    # Predict log values
    y_pred_log = model.predict(X_test)
    
    # Inverse transform to get actual values
    y_pred = np.expm1(y_pred_log)
    y_test_actual = np.expm1(y_test)
    
    mse = mean_squared_error(y_test_actual, y_pred)
    r2 = r2_score(y_test_actual, y_pred)
    mae = mean_absolute_error(y_test_actual, y_pred)
    
    print(f"Improved Model Performance:")
    print(f"Mean Squared Error: {mse}")
    print(f"R2 Score: {r2:.4f}")
    print(f"Mean Absolute Error: {mae:.2f}")
    
    # Save Model, Encoders, and Scaler
    # We need to create a wrapper class or handle the scaling/log transform in app.py
    # For now, let's just save the raw model and update app.py to handle the transforms
    
    with open('agriculture_model_improved.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    with open('label_encoders_improved.pkl', 'wb') as f:
        pickle.dump({
            'district': le_district,
            'season': le_season,
            'crop': le_crop,
            'scaler': scaler # Save scaler too
        }, f)
        
    print("Improved model and encoders saved.")

if __name__ == "__main__":
    train_improved_model()
