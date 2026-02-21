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
            
            for item in items[:15]: 
                title = item.find('title').text
                severity = classify_risk(title)
                
                if not any(a['title'] == title for a in global_alerts):
                    global_alerts.append({"title": title, "severity": severity})
                
                sentiment = sia.polarity_scores(title)['compound']
                if sentiment < -0.3: risk_modifier += 0.8
                elif sentiment > 0.3: risk_modifier -= 0.4
                
                if severity == "HIGH": risk_modifier += 1.5
                elif severity == "MEDIUM": risk_modifier += 0.5
                        
            final_risk = baseline - 5 + risk_modifier + (len(items) * 0.2)
            return round(min(max(final_risk, 20), 100), 1)
    except Exception as e:
        return baseline

# --- 4. ADVANCED AI INTERPRETATION LAYER (NARRATIVE UPGRADE) ---
def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return {"main_brief": "AI Error: API Key not found.", "pillar_narratives": {}}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    sys_instruction = """You are the Avellon Risk AI, a premium geopolitical intelligence analyst. You MUST respond with a valid JSON object ONLY. Format:
    {
      "main_brief": "A gripping, 200-250 word geopolitical story explaining the cascading global impacts of today's top risk drivers. Weave the provided news headlines and data into a compelling narrative that executives must read. Do not just list numbers; tell the story of the chaos.",
      "pillar_narratives": {
        "Geopolitical Conflict Intensity": "A 2-3 sentence live intelligence brief. You MUST explicitly cite a relevant news headline or data point from the provided context to justify this score.",
        "Energy & Maritime Disruption": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Trade & Supply Chain Stress": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Sovereign Financial Stress": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Currency & Liquidity Pressure": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Sanctions & Regulatory Fragmentation": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Cyber & Infrastructure Threats": "A 2-3 sentence live intelligence brief citing specific provided news/data.",
        "Climate & Resource Shock": "A 2-3 sentence live intelligence brief citing specific provided news/data."
      }
    }"""
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": sys_instruction}]},
        "generationConfig": {"responseMimeType": "application/json"} 
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return json.loads(raw_text)
    except Exception as e:
        print(f"AI Generation Failed: {str(e)}")
        return {"main_brief": "System error generating narrative.", "pillar_narratives": {}}

# --- 5. MASTER CALCULATOR & DATABASE WRITER ---
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
    
    severity_map = {"HIGH": 3, "MEDIUM": 2, "WATCH": 1}
    global_alerts.sort(key=lambda x: severity_map.get(x["severity"], 0), reverse=True)
    all_alerts = global_alerts[:40] 
    
    if not all_alerts: all_alerts = [{"title": "SYSTEM ALERT: NO CRITICAL EVENTS DETECTED", "severity": "WATCH"}]
    
    # NEW: Injecting the headlines into the prompt for citation
    top_headlines_text = " | ".join([a['title'] for a in all_alerts[:15]])
    
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}. Top driver: {top_driver}. "
    prompt += f"Live Scores: {json.dumps(live_inputs)}. "
    prompt += f"LATEST GLOBAL NEWS TO CITE: {top_headlines_text}. "
    prompt += "Generate the main narrative and the 8 pillar diagnostics based strictly on these live news alerts."
    
    print("Generating Interactive AI Diagnostics...")
    ai_response = call_gemini(prompt)

    current_time_str = datetime.datetime.utcnow().isoformat() + "Z"

    # --- SAVE CURRENT STATE (data.json) ---
    agri_data = {
        "AGRI_Score": current_agri,
        "Velocity": str_velocity,
        "Acceleration": "N/A",
        "Top_Risk_Driver": top_driver,
        "AI_Brief": ai_response.get("main_brief", "Error loading main brief."),
        "Pillar_Scores": live_inputs, 
        "Pillar_Narratives": ai_response.get("pillar_narratives", {}),
        "All_Alerts": all_alerts, 
        "Last_Updated": current_time_str
    }
    
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    # --- SAVE HISTORICAL DATA FOR CHART (history.json) ---
    history_file = "history.json"
    history_data = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history_data = json.load(f)
        except Exception: pass

    # Append the new reading to our history database
    history_data.append({"timestamp": current_time_str, "score": current_agri})
    
    # Cap the history at 3000 records to prevent file bloat
    if len(history_data) > 3000:
        history_data = history_data[-3000:]

    with open(history_file, "w") as f:
        json.dump(history_data, f, indent=4)

    print(f"Avellon AGRI Engine calculated score: {current_agri}. History database updated successfully.")

if __name__ == "__main__":
    calculate_agri()
