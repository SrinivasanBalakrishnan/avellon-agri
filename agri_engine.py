import json
import datetime
import urllib.request
import urllib.parse
import os
import nltk
import random
import re
from difflib import SequenceMatcher
from nltk.sentiment import SentimentIntensityAnalyzer

# --- IMPORT THE VISUAL VAULT ---
try:
    from image_library import IMAGE_PROMPTS
except ImportError:
    IMAGE_PROMPTS = {"INFOGRAPHIC": ["Global geopolitical map abstract"]}

# --- 1. NLP & CONFIGURATION ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

global_alerts = []

# --- 2. DEDUPLICATION ENGINE ---
def is_duplicate(new_title, existing_alerts, threshold=0.65):
    """Checks for semantic similarity to avoid echo-chamber alerts."""
    for alert in existing_alerts:
        if SequenceMatcher(None, new_title.lower(), alert['title'].lower()).ratio() > threshold:
            return True
    return False

# --- 3. IMAGE FETCHING ENGINES ---
def get_cinematic_query(headline):
    text_lower = headline.lower()
    if any(x in text_lower for x in ["war", "conflict", "military", "army", "weapon", "border", "defense", "missile", "troops", "strike"]): 
        return random.choice(IMAGE_PROMPTS.get("GEOPOLITICS", ["Global conflict map"]))
    if any(x in text_lower for x in ["ship", "port", "sea", "maritime", "canal", "vessel", "freight", "shipping", "pirate", "navy"]): 
        return random.choice(IMAGE_PROMPTS.get("MARITIME", ["Cargo ship at sea"]))
    if any(x in text_lower for x in ["oil", "gas", "energy", "pipeline", "fuel", "lng", "barrel", "opec", "drilling"]): 
        return random.choice(IMAGE_PROMPTS.get("ENERGY", ["Oil refinery at night"]))
    if any(x in text_lower for x in ["cyber", "hack", "data", "ransomware", "digital", "network", "server", "bot"]): 
        return random.choice(IMAGE_PROMPTS.get("CYBER", ["Hacker code screen"]))
    if any(x in text_lower for x in ["climate", "flood", "drought", "storm", "weather", "carbon", "heat", "disaster"]): 
        return random.choice(IMAGE_PROMPTS.get("CLIMATE", ["Climate change landscape"]))
    if any(x in text_lower for x in ["sanction", "embargo", "seize", "freeze", "law", "court", "ban", "blacklist"]): 
        return random.choice(IMAGE_PROMPTS.get("SANCTIONS", ["Gavel and treaty"]))
    if any(x in text_lower for x in ["chip", "tech", "semiconductor", "ai", "5g", "robot", "satellite", "space"]): 
        return random.choice(IMAGE_PROMPTS.get("TECH", ["Semiconductor chip"]))
    if any(x in text_lower for x in ["economy", "trade", "tariff", "bank", "market", "stock", "finance", "inflation", "currency", "debt"]): 
        return random.choice(IMAGE_PROMPTS.get("ECONOMY", ["Stock market chart"]))
    return random.choice(IMAGE_PROMPTS.get("INFOGRAPHIC", ["Abstract global news background"]))

def fetch_pexels_fallback(query):
    api_key = os.environ.get("PEXELS_API_KEY")
    default_image = "https://images.pexels.com/photos/373543/pexels-photo-373543.jpeg?auto=compress&cs=tinysrgb&w=600"
    if not api_key: return default_image
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=1&orientation=landscape"
        req = urllib.request.Request(url, headers={'Authorization': api_key, 'User-Agent': 'AvellonBot/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data['photos'] and len(data['photos']) > 0:
                return data['photos'][0]['src']['medium']
    except Exception: pass 
    return default_image

# --- 4. RISK CLASSIFICATION & API ---
def classify_risk_level(text):
    text_lower = text.lower()
    high_keywords = ["war", "conflict", "sanction", "embargo", "blockade", "military", "crisis", "disaster", "collapse", "attack", "breach", "shortage", "nuclear"]
    med_keywords = ["tension", "tariff", "dispute", "warning", "risk", "volatile", "talks", "regulatory", "uncertainty", "debate", "meeting", "proposal", "monitor", "review", "election"]
    
    if sum(1 for k in high_keywords if k in text_lower) >= 1: return "HIGH"
    if sum(1 for k in med_keywords if k in text_lower) >= 1: return "MEDIUM"
    return "WATCH"

def fetch_newsdata_risk(query, baseline_score):
    global global_alerts
    api_key = os.environ.get("NEWSDATA_API_KEY")
    if not api_key: return baseline_score

    try:
        encoded_q = urllib.parse.quote(query)
        # Fetch 10 items to ensure Medium/Watch buckets are filled
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={encoded_q}&language=en&prioritydomain=top"
        req = urllib.request.Request(url, headers={'User-Agent': 'AvellonBot/2.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get('results', [])
            risk_modifier = 0
            
            for article in results[:10]: 
                title = article.get('title', '')
                if is_duplicate(title, global_alerts): continue 
                
                desc = article.get('description') or ''
                link = article.get('link', '#')
                full_text = f"{title} {desc}"
                severity = classify_risk_level(full_text)
                
                img_url = article.get('image_url')
                if not img_url:
                    img_url = fetch_pexels_fallback(get_cinematic_query(title))
                
                global_alerts.append({
                    "title": title, "severity": severity, "url": link,
                    "image": img_url, "source": article.get('source_id', 'Global News')
                })
                
                sentiment = sia.polarity_scores(full_text)['compound']
                if sentiment < -0.2: risk_modifier += 1.2
                elif sentiment > 0.2: risk_modifier -= 0.5
                if severity == "HIGH": risk_modifier += 2.0
                elif severity == "MEDIUM": risk_modifier += 0.8

            return round(min(max(baseline_score + risk_modifier, 20), 100), 1)
    except Exception as e:
        print(f"API Error for {query}: {e}")
        return baseline_score

# --- 5. FINANCIAL & PHYSICAL DATA ---
def fetch_currency_risk():
    try:
        url = "https://api.frankfurter.app/latest?from=USD"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            return round(min(max(40 + (abs(data['rates']['EUR'] - 0.90) * 100), 0), 100), 1)
    except: return 50.0

def fetch_climate_risk():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            # FIX: Threshold raised to 5.8 to filter out noise. Only Major events count.
            significant_events = [f for f in data['features'] if f['properties']['mag'] >= 5.8]
            # Scoring: 25 Base + 10 points per Major event. Max 100.
            return round(min(25 + (len(significant_events) * 10), 100), 1)
    except: return 40.0

def fetch_energy_price_risk():
    # Only fetches the PRICE component
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 50.0
    try:
        url = f"https://www.alphavantage.co/query?function=BRENT&interval=daily&apikey={api_key}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            val = float(data["data"][0]["value"])
            return round(min(max(50 + ((val - 75) * 1.5), 20), 100), 1)
    except: return 50.0

def fetch_sovereign_risk():
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key: return 55.0
    try:
        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={api_key}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            val = float(data["data"][0]["value"])
            return round(min(max(50 + ((val - 4.0) * 10), 20), 100), 1)
    except: return 55.0

# --- 6. AI INTERPRETATION LAYER ---
def clean_json_response(text):
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1)
    return text.strip()

def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return {"main_brief": "System Offline.", "pillar_narratives": {}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # UPDATED SYSTEM PROMPT: Forces detailed justification and real citations
    sys = """You are a Strategic Risk Analyst for Avellon Intelligence. 
    You MUST respond with pure, valid JSON. 
    
    INSTRUCTIONS:
    1. JUSTIFY THE SCORE: For the Main Brief, explicitly explain WHY the AGRI score is at its current level. Is it driven by Energy? War? Markets?
    2. CITE EVIDENCE: You must quote or reference specific news headlines from the provided feed to support your analysis.
    3. NO 'STABLE': Do not use the word 'stable'. If risk is low, describe it as 'routine monitoring' or 'baseline activity'.
    4. DIAGNOSTICS: Provide a 2-sentence specific analysis for ALL 8 pillars.
    
    Required JSON Structure:
    {
        "main_brief": "A 3-4 sentence strategic overview citing specific drivers of the total score.",
        "pillar_narratives": {
            "Geopolitical Conflict Intensity": "Analysis...",
            "Energy & Maritime Disruption": "Analysis...",
            "Trade & Supply Chain Stress": "Analysis...",
            "Sovereign Financial Stress": "Analysis...",
            "Currency & Liquidity Pressure": "Analysis...",
            "Sanctions & Regulatory Fragmentation": "Analysis...",
            "Cyber & Infrastructure Threats": "Analysis...",
            "Climate & Resource Shock": "Analysis..."
        }
    }"""
    
    data = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": sys}]}, "generationConfig": {"responseMimeType": "application/json"}}
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            raw_text = json.loads(response.read().decode("utf-8"))["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(clean_json_response(raw_text))
            
            # FALLBACK FILLER
            keys = ["Geopolitical Conflict Intensity", "Energy & Maritime Disruption", "Trade & Supply Chain Stress", 
                    "Sovereign Financial Stress", "Currency & Liquidity Pressure", "Sanctions & Regulatory Fragmentation", 
                    "Cyber & Infrastructure Threats", "Climate & Resource Shock"]
            for k in keys:
                if k not in result.get("pillar_narratives", {}):
                    if "pillar_narratives" not in result: result["pillar_narratives"] = {}
                    result["pillar_narratives"][k] = "Sector showing baseline activity levels; monitoring for emerging volatility."
            
            return result
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return {"main_brief": "Analyst system calibrating.", "pillar_narratives": {}}

# --- 7. MASTER CALCULATOR ---
def calculate_agri():
    weights = {
        "Geopolitical Conflict Intensity": 0.18, "Energy & Maritime Disruption": 0.15,
        "Trade & Supply Chain Stress": 0.12, "Sovereign Financial Stress": 0.12,
        "Currency & Liquidity Pressure": 0.10, "Sanctions & Regulatory Fragmentation": 0.10,
        "Cyber & Infrastructure Threats": 0.10, "Climate & Resource Shock": 0.13
    }
    
    print("Initializing Avellon Intelligence Engine...")
    
    # HYBRID ENERGY SCORING
    # 1. Get Financial Score
    energy_price_score = fetch_energy_price_risk()
    # 2. Get Geopolitical News Score for Energy
    energy_news_score = fetch_newsdata_risk("oil OR energy OR maritime OR tanker OR strait", 50.0)
    # 3. Take the HIGHER risk (Safety Protocol)
    final_energy_score = max(energy_price_score, energy_news_score)

    live_inputs = {
        "Geopolitical Conflict Intensity": fetch_newsdata_risk("war OR conflict OR military OR troops", 70.0), 
        "Energy & Maritime Disruption": final_energy_score,    
        "Trade & Supply Chain Stress": fetch_newsdata_risk("supply chain OR port OR cargo OR logistics", 60.0),     
        "Sovereign Financial Stress": fetch_sovereign_risk(),   
        "Currency & Liquidity Pressure": fetch_currency_risk(), 
        "Sanctions & Regulatory Fragmentation": fetch_newsdata_risk("sanctions OR tariffs OR embargo OR trade war", 55.0), 
        "Cyber & Infrastructure Threats": fetch_newsdata_risk("cyberattack OR ransomware OR hack OR data breach", 50.0),       
        "Climate & Resource Shock": fetch_climate_risk()        
    }
    
    current_agri = round(sum(live_inputs[p] * weights[p] for p in weights), 1)
    
    # Prepare AI Context
    severity_map = {"HIGH": 3, "MEDIUM": 2, "WATCH": 1}
    global_alerts.sort(key=lambda x: severity_map.get(x["severity"], 0), reverse=True)
    final_alerts = global_alerts[:40] if global_alerts else [{"title": "Global Markets Baseline Monitoring", "severity": "WATCH", "image": None, "url": "#"}]
    
    headlines_context = " | ".join([f"{a['title']} (Severity: {a['severity']})" for a in final_alerts[:20]])
    
    prompt = f"""
    ANALYSIS REQUEST:
    Current AGRI Score: {current_agri}/100.
    Pillar Breakdown: {json.dumps(live_inputs)}.
    REAL-TIME NEWS FEED: {headlines_context}
    INSTRUCTION: Provide the executive brief and specific root-cause analysis for each pillar based on the news above.
    """
    
    print("Generating Strategic Narrative...")
    ai_response = call_gemini(prompt)
    
    current_time_str = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Velocity & Save
    try:
        with open("data.json", "r") as f: previous = json.load(f).get("AGRI_Score", current_agri)
    except: previous = current_agri
    vel = round(current_agri - previous, 1)
    str_vel = f"+{vel}" if vel > 0 else str(vel)

    agri_data = {
        "AGRI_Score": current_agri, "Velocity": str_vel, "Top_Risk_Driver": max(live_inputs, key=live_inputs.get),
        "AI_Brief": ai_response.get("main_brief", "Data processing..."), 
        "Pillar_Scores": live_inputs, 
        "Pillar_Narratives": ai_response.get("pillar_narratives", {}), 
        "All_Alerts": final_alerts, 
        "Last_Updated": current_time_str
    }
    
    with open("data.json", "w") as f: json.dump(agri_data, f, indent=4)
    
    hist = []
    if os.path.exists("history.json"):
        try:
            with open("history.json", "r") as f: hist = json.load(f)
        except: pass
    hist.append({"timestamp": current_time_str, "score": current_agri})
    if len(hist) > 3000: hist = hist[-3000:]
    with open("history.json", "w") as f: json.dump(hist, f, indent=4)
    
    print(f"Success. Score: {current_agri}")

if __name__ == "__main__":
    calculate_agri()
