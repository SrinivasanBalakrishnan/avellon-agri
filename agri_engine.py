import json
import datetime
import urllib.request
import os

def call_gemini(prompt):
    # Securely pulls API key from GitHub Vault
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "AI Error: API Key not found. Please configure GitHub Secrets."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Strict System Instruction for Avellon
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

def calculate_agri():
    # 1. THE AVELLON METHODOLOGY: 8 Core Pillars & Weights
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
    
    # 2. SIMULATED LIVE FEEDS (For now, we simulate 0-100 inputs)
    live_inputs = {
        "Geopolitical Conflict Intensity": 78.5,
        "Energy & Maritime Disruption": 82.0,
        "Trade & Supply Chain Stress": 60.0,
        "Sovereign Financial Stress": 55.0,
        "Currency & Liquidity Pressure": 45.0,
        "Sanctions & Regulatory Fragmentation": 65.0,
        "Cyber & Infrastructure Threats": 50.0,
        "Climate & Resource Shock": 40.0
    }
    
    # 3. CALCULATE AGRI SCORE (Weighted Sum)
    current_agri = sum(live_inputs[pillar] * weights[pillar] for pillar in weights)
    current_agri = round(current_agri, 1)
    
    # 4. CALCULATE VELOCITY & ACCELERATION (Simulated previous cycle)
    previous_agri = 62.1 
    previous_velocity = 1.2
    
    velocity = round(current_agri - previous_agri, 1)
    acceleration = round(velocity - previous_velocity, 1)
    
    # Format with + signs for positive shifts
    str_velocity = f"+{velocity}" if velocity > 0 else str(velocity)
    str_accel = f"+{acceleration}" if acceleration > 0 else str(acceleration)
    
    # 5. IDENTIFY TOP RISK DRIVER (Pillar with highest severity)
    top_driver = max(live_inputs, key=live_inputs.get)
    
    # 6. GENERATE INTELLIGENCE BRIEF
    prompt = f"Current AGRI: {current_agri}, Velocity: {str_velocity}, Acceleration: {str_accel}. Top rising pillar: {top_driver}. Energy metric: {live_inputs['Energy & Maritime Disruption']}, Geopolitics metric: {live_inputs['Geopolitical Conflict Intensity']}."
    print("Calling Gemini AI...")
    ai_brief = call_gemini(prompt)

    # 7. PACKAGE AND SAVE DATA
    agri_data = {
        "AGRI_Score": current_agri,
        "Velocity": str_velocity,
        "Acceleration": str_accel,
        "Top_Risk_Driver": top_driver,
        "AI_Brief": ai_brief,
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    print(f"Avellon AGRI Engine calculated score: {current_agri}. Run complete.")

if __name__ == "__main__":
    calculate_agri()
