import json
import datetime
import urllib.request
import urllib.parse
import os
import xml.etree.ElementTree as ET

# --- 1. FINANCIAL & CLIMATE DATA FETCHERS ---

def fetch_currency_risk():
    try:
        url = "https://api.frankfurter.app/latest?from=USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            eur_rate = data['rates']['EUR']
            deviation = abs(eur_rate - 0.90) * 100
            return round(min(max(40 + deviation, 0), 100), 1)
    except Exception: return 50.0

def fetch_climate_risk():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            event_count = len(data['features'])
            return round(min(20 + (event_count * 5), 100), 1)
    except Exception: return 40.0

def fetch_energy_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 68.5
    try:
        url = f"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_price = float(data["data"][0]["value"])
            risk = 50 + ((latest_price - 75) * 1.5)
            return round(min(max(risk, 20), 100), 1)
    except Exception: return 68.5

def fetch_sovereign_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 55.0
    try:
        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_yield = float(data["data"][0]["value"])
            risk = 50 + ((latest_yield - 4.0) * 10)
            return round(min(max(risk, 20), 100), 1)
    except Exception: return 55.0

# --- 2. GLOBAL NEWS SENTIMENT FETCHER ---

def fetch_news_risk(query, baseline):
    """Pulls global breaking news volume for specific risk keywords."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')
            count = len(items)
            risk = baseline - 10 + (count * 0.5) 
            return round(min(max(risk, 20), 100), 1)
    except Exception as e:
        print(f"News error: {e}")
        return baseline

# --- 3. LIVE HEADLINE SCRAPER (NEW FOR TERMINAL UI) ---

def fetch_top_headlines():
    """Scrapes the top 5 real global risk headlines for the UI Ticker."""
    try:
        url = "https://news.google.com/rss/search?q=geopolitics+OR+macroeconomics+OR+supply+chain+OR+sanctions&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            items = ET.fromstring(response.read()).findall('.//item')[:5]
            return [item.find('title').text for item in items]
    except Exception:
        return ["SYSTEM ALERT: LIVE NEWS FEED DISCONNECTED", "AWAITING SATELLITE TELEMETRY"]

# --- 4. AI INTERPRETATION LAYER (NARRATIVE UPGRADE) ---

def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return "AI Error: API Key not found."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": "You are the Avellon Risk AI. Write a 130-word incident-based narrative. Do not just list metrics. Tell a story about specific geopolitical events, country-level crises, or market shocks driving the score today. Explain the real-world cascading effects on logistics, energy, or diplomacy. Be clinical but compelling."}]}
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"AI Generation Failed: {str(e)}"

# --- 5. MASTER CALCULATOR ---

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
    
    print("Fetching live global data across 8 sectors...")
    
    live_inputs = {
        "Geopolitical Conflict Intensity": fetch_news_risk("geopolitics AND (war OR conflict OR escalation)", 70.0), 
        "Energy & Maritime Disruption": fetch_energy_risk(),    
        "Trade & Supply Chain Stress": fetch_news_risk("supply chain AND (disruption OR shortage OR port)", 60.0),     
        "Sovereign Financial Stress": fetch_sovereign_risk(),   
        "Currency & Liquidity Pressure": fetch_currency_risk(), 
        "Sanctions & Regulatory Fragmentation": fetch_news_risk("sanctions AND (tariffs OR embargo OR trade war)", 55.0), 
        "Cyber & Infrastructure Threats": fetch_news_risk("cyberattack AND (infrastructure OR hack OR data breach)", 50.0),       
        "Climate & Resource Shock": fetch_climate_risk()        
    }
    
    current_agri = sum(live_inputs[pillar] * weights[pillar] for pillar in weights)
    current_agri = round(current_agri, 1)
    
    try:
        with open("data.json", "r") as f:
            old_data = json.load(f)
            previous_agri = old_data.get("AGRI_Score", current_agri)
    except Exception:
        previous_agri = current_agri
        
    velocity = round(current_agri - previous_agri, 1)
    str_velocity = f"+{velocity}" if velocity > 0 else str(velocity)
    
    top_driver = max(live_inputs, key=live_inputs.get)
    headlines = fetch_top_headlines()
    
    # Dynamic prompt building for Gemini (Now injecting real news!)
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}. Top driver: {top_driver} at {live_inputs[top_driver]}. "
    prompt += f"Today's top news driving risk: {headlines[0]}. "
    prompt += f"Geo: {live_inputs['Geopolitical Conflict Intensity']}, Energy: {live_inputs['Energy & Maritime Disruption']}, "
    prompt += f"Trade: {live_inputs['Trade & Supply Chain Stress']}, Cyber: {live_inputs['Cyber & Infrastructure Threats']}."
    
    print("Generating Avellon Intelligence Narrative...")
    ai_brief = call_gemini(prompt)

    agri_data = {
        "AGRI_Score": current_agri,
        "Velocity": str_velocity,
        "Acceleration": "N/A",
        "Top_Risk_Driver": top_driver,
        "AI_Brief": ai_brief,
        "Pillar_Scores": live_inputs, 
        "Top_Headlines": headlines, # Passing the headlines to the UI JSON
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    print(f"Avellon AGRI Engine calculated score: {current_agri}. System fully autonomous.")

if __name__ == "__main__":
    calculate_agri()
