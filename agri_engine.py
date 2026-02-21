import json
import datetime
import urllib.request
import urllib.parse
import os
import xml.etree.ElementTree as ET
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# --- 1. NLP & RISK PRIORITIZATION SETUP ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

HIGH_IMPACT_KEYWORDS = [
    "sanctions", "export ban", "trade restriction", "blockade",
    "war", "conflict", "military escalation",
    "shipping disruption", "chokepoint", "port closure",
    "energy shortage", "oil supply", "gas supply",
    "critical minerals", "rare earth", "semiconductor",
    "currency crisis", "sovereign debt",
    "cyber attack", "infrastructure attack"
]

MEDIUM_IMPACT_KEYWORDS = [
    "tensions", "diplomatic standoff", "policy shift",
    "regulatory risk", "tariffs",
    "investment screening", "national security review",
    "supply risk", "resource nationalism"
]

global_alerts = []

def classify_risk(text):
    """Classifies risk based on specific Fortune 500 business threats."""
    text_lower = text.lower()
    high_score = sum(1 for k in HIGH_IMPACT_KEYWORDS if k in text_lower)
    medium_score = sum(1 for k in MEDIUM_IMPACT_KEYWORDS if k in text_lower)

    if high_score >= 2: return "HIGH"
    elif high_score == 1 or medium_score >= 2: return "MEDIUM"
    else: return "WATCH"

# --- 2. FINANCIAL & CLIMATE DATA FETCHERS ---
def fetch_currency_risk():
    try:
        url = "https://api.frankfurter.app/latest?from=USD"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return round(min(max(40 + (abs(data['rates']['EUR'] - 0.90) * 100), 0), 100), 1)
    except Exception: return 50.0

def fetch_climate_risk():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return round(min(20 + (len(data['features']) * 5), 100), 1)
    except Exception: return 40.0

def fetch_energy_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 68.5
    try:
        url = f"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return round(min(max(50 + ((float(data["data"][0]["value"]) - 75) * 1.5), 20), 100), 1)
    except Exception: return 68.5

def fetch_sovereign_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 55.0
    try:
        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={api_key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return round(min(max(50 + ((float(data["data"][0]["value"]) - 4.0) * 10), 20), 100), 1)
    except Exception: return 55.0

# --- 3. NLP NEWS SENTIMENT FETCHER ---
def fetch_nlp_news_risk(query, baseline):
    global global_alerts
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            items = ET.fromstring(response.read()).findall('.//item')
            risk_modifier = 0
            
            for item in items[:10]: 
                title = item.find('title').text
                severity = classify_risk(title)
                
                # Prevent duplicate alerts across pillars
                if not any(a['title'] == title for a in global_alerts):
                    global_alerts.append({"title": title, "severity": severity})
                
                # NLP Sentiment Math (Quantifying Chaos)
                sentiment = sia.polarity_scores(title)['compound']
                if sentiment < -0.3: risk_modifier += 0.8
                elif sentiment > 0.3: risk_modifier -= 0.4
                
                # Business Impact Math (Amplifying key threats)
                if severity == "HIGH": risk_modifier += 1.5
                elif severity == "MEDIUM": risk_modifier += 0.5
                        
            final_risk = baseline - 5 + risk_modifier + (len(items) * 0.2)
            return round(min(max(final_risk, 20), 100), 1)
    except Exception as e:
        print(f"News error: {e}")
        return baseline

# --- 4. AI INTERPRETATION LAYER ---
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
        "Geopolitical Conflict Intensity": 0.18, "Energy & Maritime Disruption": 0.15,
        "Trade & Supply Chain Stress": 0.12, "Sovereign Financial Stress": 0.12,
        "Currency & Liquidity Pressure": 0.10, "Sanctions & Regulatory Fragmentation": 0.10,
        "Cyber & Infrastructure Threats": 0.10, "Climate & Resource Shock": 0.13
    }
    
    print("Initializing Avellon NLP Engine across global sectors...")
    
    live_inputs = {
        "Geopolitical Conflict Intensity": fetch_nlp_news_risk("geopolitics AND (war OR conflict OR escalation)", 70.0), 
        "Energy & Maritime Disruption": fetch_energy_risk(),    
        "Trade & Supply Chain Stress": fetch_nlp_news_risk("supply chain AND (disruption OR shortage OR port)", 60.0),     
        "Sovereign Financial Stress": fetch_sovereign_risk(),   
        "Currency & Liquidity Pressure": fetch_currency_risk(), 
        "Sanctions & Regulatory Fragmentation": fetch_nlp_news_risk("sanctions AND (tariffs OR embargo OR trade war)", 55.0), 
        "Cyber & Infrastructure Threats": fetch_nlp_news_risk("cyberattack AND (infrastructure OR hack OR data breach)", 50.0),       
        "Climate & Resource Shock": fetch_climate_risk()        
    }
    
    current_agri = round(sum(live_inputs[p] * weights[p] for p in weights), 1)
    
    try:
        with open("data.json", "r") as f:
            old_data = json.load(f)
            previous_agri = old_data.get("AGRI_Score", current_agri)
    except Exception:
        previous_agri = current_agri
        
    velocity = round(current_agri - previous_agri, 1)
    str_velocity = f"+{velocity}" if velocity > 0 else str(velocity)
    
    top_driver = max(live_inputs, key=live_inputs.get)
    
    # Sort alerts by the highest severity
    severity_map = {"HIGH": 3, "MEDIUM": 2, "WATCH": 1}
    global_alerts.sort(key=lambda x: severity_map.get(x["severity"], 0), reverse=True)
    top_alerts = global_alerts[:5]
    
    if not top_alerts: top_alerts = [{"title": "SYSTEM ALERT: NO CRITICAL EVENTS DETECTED", "severity": "WATCH"}]
    
    # Pass the actual highest-priority news to Gemini
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}. Top driver: {top_driver} at {live_inputs[top_driver]}. "
    prompt += f"Today's highest priority global alert: {top_alerts[0]['title']}. "
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
        "Top_Alerts": top_alerts, 
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    print(f"Avellon AGRI Engine calculated score: {current_agri}. System fully autonomous.")

if __name__ == "__main__":
    calculate_agri()
