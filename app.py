from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
import datetime
import requests
import json
import os
import subprocess
import sys

app = Flask(__name__)
CORS(app)

# ── Load Model and Encoders ────────────────────────────────────────────────────
try:
    with open('agriculture_model_improved.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('label_encoders_improved.pkl', 'rb') as f:
        encoders = pickle.load(f)
        scaler = encoders.get('scaler')
    print("Model and encoders loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    encoders = None
    scaler = None

# ── Load Monthly Rainfall Averages ─────────────────────────────────────────────
try:
    rainfall_df = pd.read_csv('rainfall_monthly_averages.csv')
    rainfall_data = rainfall_df.set_index('District').to_dict('index')
    print("Rainfall data loaded successfully.")
except Exception as e:
    print(f"Error loading rainfall data: {e}")
    rainfall_data = {}

# ── Load Training Data for Stats ──────────────────────────────────────────────
try:
    training_df = pd.read_csv('training_workspace/final_training_data.csv')
    print(f"Training data loaded: {len(training_df)} records.")
except Exception as e:
    print(f"Error loading training data: {e}")
    training_df = None

# ── District Slope Data (actual Meghalaya geography) ──────────────────────────
# ── MLOps Config ──────────────────────────────────────────────────────────────
PRED_LOG_PATH   = os.path.join(os.path.dirname(__file__), 'prediction_log.jsonl')
MODEL_INFO_PATH = os.path.join(os.path.dirname(__file__), 'model_info.json')
DRIFT_CACHE     = os.path.join(os.path.dirname(__file__), 'drift_report.json')
WORKSPACE       = os.path.join(os.path.dirname(__file__), 'training_workspace')


def _log_prediction(entry: dict):
    """Append a prediction input record to prediction_log.jsonl."""
    entry['ts'] = datetime.datetime.now().isoformat()
    with open(PRED_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def _load_model_info():
    if os.path.exists(MODEL_INFO_PATH):
        with open(MODEL_INFO_PATH) as f:
            return json.load(f)
    return {
        'model_name':    'agriculture-yield-model',
        'training_date': 'unknown',
        'n_samples':     'unknown',
        'r2':            None,
        'mae':           None,
        'rmse':          None,
        'version':       1,
    }


# ── District Slope Data (actual Meghalaya geography) ──────────────────────────
DISTRICT_SLOPES = {
    'EAST KHASI HILLS': {'slope': 'Steep', 'degrees': 28},
    'WEST KHASI HILLS': {'slope': 'Steep', 'degrees': 26},
    'SOUTH WEST KHASI HILLS': {'slope': 'Steep', 'degrees': 30},
    'EAST JAINTIA HILLS': {'slope': 'Steep', 'degrees': 24},
    'WEST JAINTIA HILLS': {'slope': 'Steep', 'degrees': 22},
    'EAST GARO HILLS': {'slope': 'Gentle', 'degrees': 12},
    'WEST GARO HILLS': {'slope': 'Gentle', 'degrees': 10},
    'NORTH GARO HILLS': {'slope': 'Gentle', 'degrees': 8},
    'SOUTH GARO HILLS': {'slope': 'Steep', 'degrees': 20},
    'SOUTH WEST GARO HILLS': {'slope': 'Gentle', 'degrees': 9},
    'RI BHOI': {'slope': 'Gentle', 'degrees': 11},
}

# ── Crop Knowledge Base (Indian MSP + agronomic facts) ────────────────────────
CROP_KNOWLEDGE = {
    'Rice':                  {'price_per_quintal': 2183, 'N': 'High',   'P': 'Medium', 'K': 'Medium', 'pH': '5.5-6.5', 'growth_days': 120, 'water': 'High'},
    'Maize':                 {'price_per_quintal': 1962, 'N': 'High',   'P': 'Medium', 'K': 'High',   'pH': '5.8-7.0', 'growth_days': 90,  'water': 'Medium'},
    'Wheat':                 {'price_per_quintal': 2275, 'N': 'High',   'P': 'High',   'K': 'Medium', 'pH': '6.0-7.0', 'growth_days': 120, 'water': 'Medium'},
    'Potato':                {'price_per_quintal': 1200, 'N': 'High',   'P': 'High',   'K': 'High',   'pH': '5.0-6.5', 'growth_days': 90,  'water': 'High'},
    'Banana':                {'price_per_quintal': 1500, 'N': 'High',   'P': 'Medium', 'K': 'High',   'pH': '6.0-7.5', 'growth_days': 365, 'water': 'High'},
    'Arecanut':              {'price_per_quintal': 35000,'N': 'Medium', 'P': 'Medium', 'K': 'High',   'pH': '5.5-7.0', 'growth_days': 365, 'water': 'Medium'},
    'Sugarcane':             {'price_per_quintal': 315,  'N': 'High',   'P': 'Medium', 'K': 'High',   'pH': '6.0-7.5', 'growth_days': 365, 'water': 'High'},
    'Soyabean':              {'price_per_quintal': 4600, 'N': 'Low',    'P': 'Medium', 'K': 'Medium', 'pH': '6.0-7.0', 'growth_days': 100, 'water': 'Medium'},
    'Jute':                  {'price_per_quintal': 4500, 'N': 'High',   'P': 'Low',    'K': 'Medium', 'pH': '6.0-7.5', 'growth_days': 120, 'water': 'High'},
    'Cotton(lint)':          {'price_per_quintal': 6620, 'N': 'High',   'P': 'Medium', 'K': 'High',   'pH': '6.0-8.0', 'growth_days': 180, 'water': 'Medium'},
    'Dry chillies':          {'price_per_quintal': 8000, 'N': 'Medium', 'P': 'High',   'K': 'Medium', 'pH': '6.0-7.0', 'growth_days': 150, 'water': 'Medium'},
    'Turmeric':              {'price_per_quintal': 7000, 'N': 'Medium', 'P': 'Medium', 'K': 'High',   'pH': '5.5-7.0', 'growth_days': 270, 'water': 'High'},
    'Ginger':                {'price_per_quintal': 4000, 'N': 'Medium', 'P': 'Medium', 'K': 'High',   'pH': '5.5-6.5', 'growth_days': 240, 'water': 'High'},
    'Black pepper':          {'price_per_quintal': 40000,'N': 'Medium', 'P': 'Medium', 'K': 'High',   'pH': '5.0-6.5', 'growth_days': 365, 'water': 'High'},
    'Cashewnut':             {'price_per_quintal': 10000,'N': 'Low',    'P': 'Medium', 'K': 'Medium', 'pH': '4.0-6.5', 'growth_days': 365, 'water': 'Low'},
    'Tapioca':               {'price_per_quintal': 600,  'N': 'Medium', 'P': 'Medium', 'K': 'High',   'pH': '5.5-7.5', 'growth_days': 300, 'water': 'Medium'},
    'Sweet potato':          {'price_per_quintal': 1000, 'N': 'Medium', 'P': 'High',   'K': 'High',   'pH': '5.5-7.0', 'growth_days': 90,  'water': 'Medium'},
    'Rapeseed &Mustard':     {'price_per_quintal': 5650, 'N': 'High',   'P': 'Medium', 'K': 'Low',    'pH': '5.5-7.0', 'growth_days': 110, 'water': 'Low'},
    'Arhar/Tur':             {'price_per_quintal': 7000, 'N': 'Low',    'P': 'Medium', 'K': 'Low',    'pH': '6.0-7.5', 'growth_days': 180, 'water': 'Low'},
    'Gram':                  {'price_per_quintal': 5440, 'N': 'Low',    'P': 'High',   'K': 'Medium', 'pH': '6.0-8.0', 'growth_days': 120, 'water': 'Low'},
    'Masoor':                {'price_per_quintal': 5500, 'N': 'Low',    'P': 'Medium', 'K': 'Low',    'pH': '6.0-8.0', 'growth_days': 110, 'water': 'Low'},
    'Linseed':               {'price_per_quintal': 5900, 'N': 'Medium', 'P': 'Medium', 'K': 'Low',    'pH': '5.5-7.0', 'growth_days': 120, 'water': 'Low'},
    'Sesamum':               {'price_per_quintal': 7307, 'N': 'Medium', 'P': 'Low',    'K': 'Low',    'pH': '5.5-8.0', 'growth_days': 90,  'water': 'Low'},
    'Small millets':         {'price_per_quintal': 3578, 'N': 'Low',    'P': 'Low',    'K': 'Low',    'pH': '5.0-7.5', 'growth_days': 75,  'water': 'Low'},
    'Cowpea(Lobia)':         {'price_per_quintal': 5100, 'N': 'Low',    'P': 'Medium', 'K': 'Medium', 'pH': '5.5-7.0', 'growth_days': 70,  'water': 'Medium'},
    'Peas & beans (Pulses)': {'price_per_quintal': 5100, 'N': 'Low',    'P': 'High',   'K': 'Medium', 'pH': '6.0-7.5', 'growth_days': 90,  'water': 'Low'},
    'Castor seed':           {'price_per_quintal': 6000, 'N': 'Medium', 'P': 'Medium', 'K': 'Medium', 'pH': '6.0-7.5', 'growth_days': 180, 'water': 'Low'},
    'Mesta':                 {'price_per_quintal': 4500, 'N': 'High',   'P': 'Medium', 'K': 'Medium', 'pH': '6.0-7.5', 'growth_days': 120, 'water': 'Medium'},
    'Tobacco':               {'price_per_quintal': 8000, 'N': 'High',   'P': 'Medium', 'K': 'High',   'pH': '5.5-7.0', 'growth_days': 120, 'water': 'Medium'},
}

# ── Crop season calendar (days offset from sowing) ────────────────────────────
CROP_CALENDAR_STAGES = {
    'Kharif':     [('Land Preparation', -14), ('Sowing', 0), ('First Irrigation', 12),
                   ('Fertilizer (Basal)', 7), ('Weeding', 30), ('Pest Monitoring', 45),
                   ('Top Dressing', 60), ('Harvest', 120)],
    'Rabi':       [('Land Preparation', -14), ('Sowing', 0), ('First Irrigation', 20),
                   ('Fertilizer (Basal)', 7), ('Weeding', 25), ('Pest Monitoring', 40),
                   ('Top Dressing', 50), ('Harvest', 120)],
    'Autumn':     [('Land Preparation', -10), ('Sowing', 0), ('First Irrigation', 10),
                   ('Weeding', 25), ('Pest Monitoring', 40), ('Harvest', 90)],
    'Winter':     [('Land Preparation', -14), ('Sowing', 0), ('Irrigation', 15),
                   ('Fertilizer', 10), ('Weeding', 30), ('Harvest', 110)],
    'Summer':     [('Land Preparation', -7), ('Sowing', 0), ('Irrigation', 7),
                   ('Weeding', 20), ('Harvest', 75)],
    'Whole Year': [('Planting', 0), ('Fertilizer (1st)', 30), ('Pruning', 90),
                   ('Pest Monitoring', 120), ('Fertilizer (2nd)', 180), ('Harvest', 365)],
}


def _make_features(district, season, crop, area, rainfall):
    """Build a named-column DataFrame so sklearn doesn't warn about feature names."""
    district_enc = encoders['district'].transform([district])[0]
    season_enc   = encoders['season'].transform([season])[0]
    crop_enc     = encoders['crop'].transform([crop])[0]
    num_df       = pd.DataFrame([[area, rainfall]], columns=['Area', 'Rainfall'])
    scaled       = scaler.transform(num_df)
    features     = pd.DataFrame(
        [[district_enc, season_enc, crop_enc, scaled[0][0], scaled[0][1]]],
        columns=['District_Encoded', 'Season_Encoded', 'Crop_Encoded', 'Area', 'Rainfall']
    )
    return features


def _get_district_annual_avg_rainfall(district):
    if district not in rainfall_data:
        return 1500.0  # Meghalaya average fallback
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return sum(rainfall_data[district].get(m, 0) for m in months)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Smart Agriculture Backend is Running",
        "endpoints": ["/info", "/predict", "/forecast", "/recommend", "/advisory",
                      "/district-info", "/crop-stats", "/pro-analysis"]
    })


@app.route('/info', methods=['GET'])
def get_info():
    if not encoders:
        return jsonify({"error": "Model not loaded"}), 500
    return jsonify({
        "districts": list(encoders['district'].classes_),
        "seasons":   list(encoders['season'].classes_),
        "crops":     list(encoders['crop'].classes_)
    })


@app.route('/district-info', methods=['GET'])
def district_info():
    """Return slope, degrees, and full 12-month rainfall for a district."""
    district = request.args.get('district', '').upper()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    slope_info = DISTRICT_SLOPES.get(district, {'slope': 'Gentle', 'degrees': 10})
    monthly_rain = {}
    if district in rainfall_data:
        monthly_rain = {m: round(rainfall_data[district].get(m, 0), 1) for m in months}
    else:
        monthly_rain = {m: 0 for m in months}

    annual_total = sum(monthly_rain.values())
    current_month = months[datetime.datetime.now().month - 1]
    current_month_rain = monthly_rain.get(current_month, 0)

    return jsonify({
        "district": district,
        "slope": slope_info['slope'],
        "slope_degrees": slope_info['degrees'],
        "monthly_rainfall": monthly_rain,
        "annual_total_rainfall": round(annual_total, 1),
        "current_month": current_month,
        "current_month_rainfall": round(current_month_rain, 1)
    })


@app.route('/crop-stats', methods=['GET'])
def crop_stats():
    """Return historical yield stats for a crop (optionally filtered by district)."""
    if training_df is None:
        return jsonify({"error": "Training data not available"}), 500

    crop     = request.args.get('crop', '')
    district = request.args.get('district', '')

    filtered = training_df[training_df['Crop'] == crop]
    if district:
        filtered = filtered[filtered['District_Name'] == district.upper()]

    if filtered.empty:
        return jsonify({"error": "No historical data for this crop/district combination"}), 404

    stats = {
        "crop": crop,
        "district": district or "All Meghalaya",
        "records": int(len(filtered)),
        "avg_yield_per_ha":  round(float(filtered['Yield'].mean()), 2),
        "max_yield_per_ha":  round(float(filtered['Yield'].max()), 2),
        "min_yield_per_ha":  round(float(filtered['Yield'].min()), 2),
        "avg_area_ha":       round(float(filtered['Area'].mean()), 1),
        "avg_production_t":  round(float(filtered['Production'].mean()), 1),
        "best_season":       filtered.groupby('Season')['Yield'].mean().idxmax(),
        "years_covered":     sorted(filtered['Crop_Year'].unique().tolist()),
    }
    return jsonify(stats)


@app.route('/predict', methods=['POST'])
def predict():
    if not model or not encoders:
        return jsonify({"error": "Model not loaded"}), 500

    data     = request.json
    district = data.get('district')
    season   = data.get('season')
    crop     = data.get('crop')
    area     = float(data.get('area'))

    # Auto-use district annual avg if rainfall not provided
    rainfall = data.get('rainfall')
    if not rainfall or float(rainfall) == 0:
        rainfall = _get_district_annual_avg_rainfall(district)
    else:
        rainfall = float(rainfall)

    try:
        features        = _make_features(district, season, crop, area, rainfall)
        prediction_log  = model.predict(features)[0]
        prediction      = np.expm1(prediction_log)
        yield_per_ha    = prediction / area if area > 0 else 0

        # Get historical stats for context
        hist = None
        if training_df is not None:
            mask = (training_df['Crop'] == crop) & (training_df['District_Name'] == district)
            hist_data = training_df[mask]
            if not hist_data.empty:
                hist = {
                    "avg_historical_yield": round(float(hist_data['Yield'].mean()), 2),
                    "max_historical_yield": round(float(hist_data['Yield'].max()), 2),
                }

        _log_prediction({
            'district': district, 'season': season, 'crop': crop,
            'area': area, 'rainfall': round(rainfall, 1)
        })

        return jsonify({
            "production":      round(prediction, 2),
            "yield":           round(yield_per_ha, 3),
            "rainfall_used":   round(rainfall, 1),
            "historical_context": hist
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/recommend', methods=['POST'])
def recommend():
    if not model or not encoders:
        return jsonify({"error": "Model not loaded"}), 500

    data     = request.json
    district = data.get('district')
    area     = float(data.get('area'))
    slope    = data.get('slope', 'Gentle')
    season   = data.get('season', 'Kharif')

    rainfall = data.get('rainfall')
    if not rainfall or float(rainfall) == 0:
        rainfall = _get_district_annual_avg_rainfall(district)
    else:
        rainfall = float(rainfall)

    slope_suitability = {
        'Flat':   ['Rice', 'Wheat', 'Jute', 'Potato', 'Sugarcane'],
        'Gentle': ['Maize', 'Soyabean', 'Pulses', 'Vegetables', 'Potato', 'Rice',
                   'Banana', 'Tapioca', 'Sweet potato', 'Cowpea'],
        'Steep':  ['Tea', 'Coffee', 'Arecanut', 'Black pepper', 'Cashewnut',
                   'Turmeric', 'Ginger', 'Dry chillies'],
    }

    all_crops  = list(encoders['crop'].classes_)
    candidates = []

    for crop in all_crops:
        suitable = slope in ('Gentle',)  # Gentle is okay for most
        if slope == 'Steep':
            suitable = any(s.lower() in crop.lower() for s in slope_suitability['Steep'])
        elif slope == 'Flat':
            suitable = any(s.lower() in crop.lower() for s in slope_suitability['Flat'])

        if suitable:
            try:
                features       = _make_features(district, season, crop, area, rainfall)
                pred_log       = model.predict(features)[0]
                pred_prod      = np.expm1(pred_log)
                pred_yield     = pred_prod / area if area > 0 else 0
                crop_info      = CROP_KNOWLEDGE.get(crop, {})
                price          = crop_info.get('price_per_quintal', 2000)
                # Revenue estimate: yield (t/ha) * area * 10 quintals/tonne * price
                revenue_est    = pred_yield * area * 10 * price

                candidates.append({
                    "crop":         crop,
                    "production":   round(pred_prod, 2),
                    "yield":        round(pred_yield, 3),
                    "revenue_est":  round(revenue_est, 0),
                    "water_need":   crop_info.get('water', 'Medium'),
                })
            except Exception as e:
                continue

    candidates.sort(key=lambda x: x['yield'], reverse=True)

    return jsonify({
        "recommendations": candidates[:5],
        "best_crop":       candidates[0] if candidates else None,
        "rainfall_used":   round(rainfall, 1)
    })


@app.route('/forecast', methods=['POST'])
def forecast():
    data              = request.json
    district          = data.get('district')
    current_month_idx = data.get('month_idx', datetime.datetime.now().month - 1)

    if district not in rainfall_data:
        return jsonify({"error": "District rainfall data not found"}), 404

    months        = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    forecast_data = []

    for i in range(6):  # 6 months ahead instead of 3
        idx            = (current_month_idx + i) % 12
        month_name     = months[idx]
        predicted_rain = rainfall_data[district].get(month_name, 0)

        erosion_risk = "Low"
        if predicted_rain > 300:
            erosion_risk = "High"
        elif predicted_rain > 100:
            erosion_risk = "Moderate"

        forecast_data.append({
            "month":        month_name,
            "rainfall":     round(predicted_rain, 1),
            "erosion_risk": erosion_risk
        })

    return jsonify({"forecast": forecast_data})


@app.route('/advisory', methods=['POST'])
def advisory():
    data         = request.json
    crop         = data.get('crop')
    weather_data = data.get('weather_data', [])

    forecast_list = []
    alerts        = []

    for day_data in weather_data:
        date = day_data.get('date')
        temp = day_data.get('temp', 0)
        rain = day_data.get('rain', 0)
        wind = day_data.get('wind', 0)

        forecast_list.append({"date": date, "temp": temp, "rain": rain, "wind": wind})

        if rain > 50:
            alerts.append(f"Heavy rain ({rain}mm) on {date} — ensure field drainage.")
        if wind > 30:
            alerts.append(f"High wind ({wind} km/h) on {date} — support tall crops.")
        if temp > 35:
            alerts.append(f"Heat stress ({temp}°C) on {date} — irrigate to cool soil.")
        if temp > 25 and rain > 10:
            alerts.append(f"Fungal risk on {date} — humid warm conditions favour leaf blight.")

    crop_advice = ""
    if crop:
        try:
            search_crop = crop.split('/')[0].split('(')[0].strip()
            wiki_url = (f"https://en.wikipedia.org/api/rest_v1/page/summary/"
                        f"{search_crop.replace(' ', '_')}")
            headers  = {"User-Agent": "SmartAgricultureApp/1.0"}
            wiki_res = requests.get(wiki_url, headers=headers, timeout=5)
            if wiki_res.status_code == 200:
                crop_advice = wiki_res.json().get("extract", "")
            else:
                crop_advice = f"Encyclopedia data for {crop} currently unavailable."
        except Exception:
            crop_advice = f"Network offline — crop advice for {crop} unavailable."

    return jsonify({
        "forecast":   forecast_list,
        "alerts":     list(dict.fromkeys(alerts)),  # deduplicate
        "crop_advice": crop_advice
    })


@app.route('/pro-analysis', methods=['POST'])
def pro_analysis():
    """
    Generates data-driven Pro Analysis from real inputs.
    Expects: district, season, crop, area (ha), rainfall, weather_data, sowing_date
    """
    data         = request.json
    district     = data.get('district', '')
    season       = data.get('season', 'Kharif')
    crop         = data.get('crop', '')
    area         = float(data.get('area', 1))
    weather_data = data.get('weather_data', [])
    sowing_date  = data.get('sowing_date', '')

    rainfall = data.get('rainfall')
    if not rainfall or float(rainfall) == 0:
        rainfall = _get_district_annual_avg_rainfall(district)
    else:
        rainfall = float(rainfall)

    crop_info = CROP_KNOWLEDGE.get(crop, {
        'price_per_quintal': 2000, 'N': 'Medium', 'P': 'Medium', 'K': 'Medium',
        'pH': '6.0-7.0', 'growth_days': 120, 'water': 'Medium'
    })

    # ── 1. Market Estimate ──────────────────────────────────────────────────────
    price = crop_info['price_per_quintal']
    try:
        if model and encoders:
            features    = _make_features(district, season, crop, area, rainfall)
            pred_log    = model.predict(features)[0]
            pred_prod   = np.expm1(pred_log)
            pred_yield  = pred_prod / area if area > 0 else 0
        else:
            pred_prod   = 0
            pred_yield  = 0
    except Exception:
        pred_prod  = 0
        pred_yield = 0

    # Revenue = production (tonnes) * 10 quintals/tonne * price/quintal
    revenue_estimate = round(pred_prod * 10 * price, 0)
    cost_estimate    = round(area * 35000, 0)  # avg input cost ₹35k/ha
    profit_estimate  = round(revenue_estimate - cost_estimate, 0)

    # Historical price trend (derived from MSP growth ~5-8%/year, last 4 seasons)
    price_trend = []
    season_labels = ['Last Year', '6 Months Ago', 'Current', 'Forecast']
    for i, label in enumerate(season_labels):
        factor = 0.88 + i * 0.06  # simulate ~6% growth
        price_trend.append({"period": label, "price": round(price * factor, 0)})

    # ── 2. Soil Recommendations ─────────────────────────────────────────────────
    soil_health = {
        "nitrogen":       crop_info['N'],
        "phosphorus":     crop_info['P'],
        "potassium":      crop_info['K'],
        "pH_range":       crop_info['pH'],
        "water_need":     crop_info['water'],
        "recommendations": []
    }
    recs = []
    if crop_info['N'] == 'High':
        recs.append("Apply urea (46-0-0) at 120 kg/ha in 2 splits.")
    elif crop_info['N'] == 'Medium':
        recs.append("Apply DAP at 80 kg/ha as basal dose.")
    else:
        recs.append("Minimal nitrogen needed — apply 40 kg/ha urea.")

    if crop_info['P'] == 'High':
        recs.append("Apply SSP (single super phosphate) at 100 kg/ha.")
    elif crop_info['P'] == 'Medium':
        recs.append("Apply DAP at 60 kg/ha as basal dose.")

    if crop_info['K'] == 'High':
        recs.append("Apply MOP (muriate of potash) at 80 kg/ha.")
    elif crop_info['K'] == 'Medium':
        recs.append("Apply MOP at 40 kg/ha before sowing.")

    ph_parts = crop_info['pH'].replace(' ', '').split('-')
    ph_min   = float(ph_parts[0]) if ph_parts else 6.0
    if ph_min < 5.5:
        recs.append("Soil acidic — add lime at 2 t/ha to raise pH.")
    soil_health['recommendations'] = recs

    # ── 3. Pest Risk (from actual weather patterns) ─────────────────────────────
    pest_risks = []
    if weather_data:
        for day in weather_data:
            temp     = day.get('temp', 25)
            rain     = day.get('rain', 0)
            humidity = day.get('humidity', 70)
            date_str = day.get('date', '')

            # Stem borer: warm + moderate humidity
            if temp > 26 and 60 < humidity < 85 and crop in ('Rice', 'Maize', 'Sugarcane'):
                pest_risks.append({
                    "date": date_str, "pest": "Stem Borer", "risk": "High",
                    "action": "Apply Chlorpyrifos 20EC at 2.5 ml/L or Neem oil spray."
                })
                break

        # Leaf blight: high humidity + rain
        for day in weather_data:
            if day.get('humidity', 70) > 85 and day.get('rain', 0) > 5:
                pest_risks.append({
                    "date": day.get('date', ''),
                    "pest": "Leaf Blight / Fungal",
                    "risk": "Moderate",
                    "action": "Apply Mancozeb 75WP at 2.5 g/L preventively."
                })
                break

        # Aphids: dry + warm
        dry_warm = [d for d in weather_data if d.get('temp', 0) > 28 and d.get('rain', 10) < 2]
        if dry_warm:
            pest_risks.append({
                "date": dry_warm[0].get('date', ''),
                "pest": "Aphids / Thrips",
                "risk": "Moderate",
                "action": "Install yellow sticky traps; spray Imidacloprid 0.5 ml/L if infestation exceeds threshold."
            })

    if not pest_risks:
        pest_risks.append({
            "date": "N/A", "pest": "No immediate risk detected",
            "risk": "Low", "action": "Continue regular scouting every 7 days."
        })

    # ── 4. Smart Calendar ───────────────────────────────────────────────────────
    calendar_stages = CROP_CALENDAR_STAGES.get(season, CROP_CALENDAR_STAGES['Kharif'])

    try:
        base = datetime.date.fromisoformat(sowing_date) if sowing_date else datetime.date.today()
    except ValueError:
        base = datetime.date.today()

    today    = datetime.date.today()
    calendar = []
    for stage_name, offset in calendar_stages:
        stage_date = base + datetime.timedelta(days=offset)
        delta_days = (stage_date - today).days
        if delta_days < -7:
            status = "completed"
        elif delta_days <= 7:
            status = "active"
        else:
            status = "upcoming"
        calendar.append({
            "stage":      stage_name,
            "date":       stage_date.isoformat(),
            "status":     status,
            "days_from_today": delta_days
        })

    return jsonify({
        "market": {
            "price_per_quintal": price,
            "revenue_estimate":  revenue_estimate,
            "cost_estimate":     cost_estimate,
            "profit_estimate":   profit_estimate,
            "predicted_production_t": round(pred_prod, 2),
            "price_trend":       price_trend,
        },
        "soil": soil_health,
        "pest_risks": pest_risks[:3],  # top 3
        "calendar":   calendar,
    })


# ── MLOps Endpoints ────────────────────────────────────────────────────────────

@app.route('/model-info', methods=['GET'])
def model_info():
    """Return current model metadata: version, R², MAE, training date, sample count."""
    info = _load_model_info()
    return jsonify(info)


@app.route('/drift-report', methods=['GET'])
def drift_report():
    """
    Return drift report. Uses cached report if fresh (< 10 min),
    otherwise runs a new check synchronously.
    """
    # Use cache if recent
    if os.path.exists(DRIFT_CACHE):
        with open(DRIFT_CACHE) as f:
            cached = json.load(f)
        ts = cached.get('timestamp', '')
        if ts:
            age = (datetime.datetime.now() - datetime.datetime.fromisoformat(ts)).total_seconds()
            if age < 600:  # 10 minutes
                return jsonify(cached)

    # Run drift check
    try:
        sys.path.insert(0, WORKSPACE)
        from drift_monitor import run_drift_check
        report = run_drift_check()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/retrain', methods=['POST'])
def retrain():
    """Trigger the retraining pipeline. Runs synchronously and returns result."""
    script = os.path.join(WORKSPACE, 'retrain_pipeline.py')
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=300,
            cwd=WORKSPACE
        )
        # Find the JSON block in stdout
        stdout = result.stdout.strip()
        lines  = stdout.split('\n')
        json_str = ''
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_str = '\n'.join(lines[i:])
                break

        if json_str:
            data = json.loads(json_str)
            # Reload model if upgraded
            if data.get('status') == 'upgraded':
                global model, encoders, scaler
                try:
                    with open(os.path.join(WORKSPACE, 'agriculture_model_improved.pkl'), 'rb') as f:
                        model = pickle.load(f)
                    with open(os.path.join(WORKSPACE, 'label_encoders_improved.pkl'), 'rb') as f:
                        encoders = pickle.load(f)
                        scaler = encoders.get('scaler')
                except Exception:
                    pass
            return jsonify(data)
        else:
            return jsonify({'error': 'No JSON output from pipeline', 'stdout': stdout}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Retraining timed out (>5 min)'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/prediction-stats', methods=['GET'])
def prediction_stats():
    """Return distribution stats of the last 100 logged predictions."""
    if not os.path.exists(PRED_LOG_PATH):
        return jsonify({'count': 0, 'by_district': {}, 'by_crop': {}, 'by_season': {}})

    rows = []
    with open(PRED_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    recent = rows[-100:]
    df = pd.DataFrame(recent) if recent else pd.DataFrame()

    if df.empty:
        return jsonify({'count': 0, 'by_district': {}, 'by_crop': {}, 'by_season': {}})

    by_district = df['district'].value_counts().to_dict() if 'district' in df else {}
    by_crop     = df['crop'].value_counts().to_dict()     if 'crop'     in df else {}
    by_season   = df['season'].value_counts().to_dict()   if 'season'   in df else {}
    avg_area    = round(float(df['area'].mean()), 2)      if 'area'     in df else 0

    return jsonify({
        'count':       len(recent),
        'by_district': by_district,
        'by_crop':     by_crop,
        'by_season':   by_season,
        'avg_area_ha': avg_area,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
