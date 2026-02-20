import json
import datetime
import urllib.request
import os

# --- LIVE API DATA FETCHERS ---

def fetch_currency_risk():
    """Pulls live USD/EUR exchange rates to measure global liquidity stress."""
    try:
        url = "https://api.frankfurter.app/latest?from=USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            eur_rate = data['rates']['EUR']
            
            # Normalization Math: The baseline 'safe' rate is around 0.90. 
            # The further it deviates (rapid USD strength/weakness), the higher the risk score.
            deviation = abs(eur_rate - 0.90) * 100
            risk_score = min(max(40 + deviation, 0), 100) # Minimum 40, Maximum 100
            return round(risk_score, 1)
    except Exception as e:
        print(f"Currency feed error: {e}")
        return 50.0 # Fallback baseline if API is down

def fetch_climate_risk():
    """Pulls live 24-hour significant geological events from the US Government."""
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            event_count = len(data['features'])
            
            # Normalization Math: 0 events = 20 risk. Every major event adds 5 points.
            risk_score = min(20 + (event_count * 5), 100) # Maximum 100
            return round(risk_score, 1)
    except Exception as e:
        print(f"Climate feed error: {e}")
        return 40.0 # Fallback baseline if API is down

# --- AI INTERPRETATION LAYER ---

def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "AI Error: API Key not found."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": "You are the Avellon Risk AI. Provide a clinical, 120-word institutional-grade risk brief based on the provided data. Focus on second-order effects. Do not use dramatic language."}]}
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"AI Generation Failed: {str(e)}"

# --- MASTER CALCULATOR ---

def calculate_agri():
    weights = {
        "Geopolitical Conflict Intensity": 0.18,
        "Energy & Maritime Disruption": 0.15,
        "Trade & Supply Chain Stress": 0.12,
        "Sovereign Financial Stress": 0.12,
        "Currency & Liquidity Pressure": 0.10,
        "Sanctions & Regulatory Fragmentation": 0.10,
        "Cyber & Infrastructure Threats": 0.10,
        "Climate & Resource Shock": 0.13
    }
    
    # LIVE FEEDS COMBINED WITH BASELINES
    print("Fetching live global data...")
    live_inputs = {
        "Geopolitical Conflict Intensity": 72.0, # Baseline (Awaiting News API)
        "Energy & Maritime Disruption": 68.5,    # Baseline (Awaiting Commodity API)
        "Trade & Supply Chain Stress": 60.0,     # Baseline
        "Sovereign Financial Stress": 55.0,      # Baseline
        "Currency & Liquidity Pressure": fetch_currency_risk(), # 🟢 REAL LIVE DATA
        "Sanctions & Regulatory Fragmentation": 65.0, # Baseline
        "Cyber & Infrastructure Threats": 50.0,       # Baseline
        "Climate & Resource Shock": fetch_climate_risk()        # 🟢 REAL LIVE DATA
    }
    
    # Calculate final score
    current_agri = sum(live_inputs[pillar] * weights[pillar] for pillar in weights)
    current_agri = round(current_agri, 1)
    
    # Simulated Velocity
    previous_agri = 62.1 
    velocity = round(current_agri - previous_agri, 1)
    str_velocity = f"+{velocity}" if velocity > 0 else str(velocity)
    
    top_driver = max(live_inputs, key=live_inputs.get)
    
    # Ask AI to interpret the live data
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}. Top rising pillar: {top_driver}. Currency Risk: {live_inputs['Currency & Liquidity Pressure']}, Climate Risk: {live_inputs['Climate & Resource Shock']}."
    print("Calling Gemini AI...")
    ai_brief = call_gemini(prompt)

    # Package and save
    agri_data = {
        "AGRI_Score": current_agri,
        "Velocity": str_velocity,
        "Acceleration": "N/A",
        "Top_Risk_Driver": top_driver,
        "AI_Brief": ai_brief,
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    print(f"Engine Run Complete. Current AGRI: {current_agri}")

if __name__ == "__main__":
    calculate_agri()
