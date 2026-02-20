import json
import datetime
import urllib.request
import os

# --- LIVE API DATA FETCHERS ---

def fetch_currency_risk():
    try:
        url = "https://api.frankfurter.app/latest?from=USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            eur_rate = data['rates']['EUR']
            deviation = abs(eur_rate - 0.90) * 100
            return round(min(max(40 + deviation, 0), 100), 1)
    except Exception as e:
        print(f"Currency error: {e}")
        return 50.0

def fetch_climate_risk():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            event_count = len(data['features'])
            return round(min(20 + (event_count * 5), 100), 1)
    except Exception as e:
        print(f"Climate error: {e}")
        return 40.0

def fetch_energy_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 68.5
    try:
        # Pulling Brent Crude Oil Prices
        url = f"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_price = float(data["data"][0]["value"])
            # Normalization: $75 is our baseline (50 risk). Spikes increase risk.
            risk = 50 + ((latest_price - 75) * 1.5)
            return round(min(max(risk, 20), 100), 1)
    except Exception as e:
        print(f"Energy error: {e}")
        return 68.5

def fetch_sovereign_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 55.0
    try:
        # Pulling 10-Year Treasury Yields
        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_yield = float(data["data"][0]["value"])
            # Normalization: 4.0% yield is our baseline (50 risk). 
            risk = 50 + ((latest_yield - 4.0) * 10)
            return round(min(max(risk, 20), 100), 1)
    except Exception as e:
        print(f"Sovereign error: {e}")
        return 55.0

# --- AI INTERPRETATION LAYER ---

def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return "AI Error: API Key not found."
    
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
    
    print("Fetching live global data...")
    live_inputs = {
        "Geopolitical Conflict Intensity": 72.0, 
        "Energy & Maritime Disruption": fetch_energy_risk(),    # 🟢 REAL LIVE DATA
        "Trade & Supply Chain Stress": 60.0,     
        "Sovereign Financial Stress": fetch_sovereign_risk(),   # 🟢 REAL LIVE DATA
        "Currency & Liquidity Pressure": fetch_currency_risk(), # 🟢 REAL LIVE DATA
        "Sanctions & Regulatory Fragmentation": 65.0, 
        "Cyber & Infrastructure Threats": 50.0,       
        "Climate & Resource Shock": fetch_climate_risk()        # 🟢 REAL LIVE DATA
    }
    
    current_agri = sum(live_inputs[pillar] * weights[pillar] for pillar in weights)
    current_agri = round(current_agri, 1)
    
    previous_agri = 62.1 
    velocity = round(current_agri - previous_agri, 1)
    str_velocity = f"+{velocity}" if velocity > 0 else str(velocity)
    
    top_driver = max(live_inputs, key=live_inputs.get)
    
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}. Top rising pillar: {top_driver}. Energy Risk: {live_inputs['Energy & Maritime Disruption']}, Sovereign Risk: {live_inputs['Sovereign Financial Stress']}, Currency Risk: {live_inputs['Currency & Liquidity Pressure']}, Climate Risk: {live_inputs['Climate & Resource Shock']}."
    print("Calling Gemini AI...")
    ai_brief = call_gemini(prompt)

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
