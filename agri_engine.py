import json
import datetime
import urllib.request
import os

def call_gemini(prompt):
    # This securely pulls your API key from the GitHub Vault
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "AI Error: API Key not found. Please configure GitHub Secrets."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # This is the strict System Instruction to keep the AI clinical and professional
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": "You are the Avellon Risk AI. Provide a clinical, 120-word institutional-grade risk brief based on the provided data. Focus on second-order effects. Do not use dramatic language."}]
        }
    }
    
    # Send the request to Google's servers
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"AI Generation Failed: {str(e)}"

def calculate_agri():
    # Phase 2 Simulated Math (We will connect live external APIs in Phase 3)
    agri_score = 64.2
    velocity = "+0.8"
    acceleration = "0.2"
    top_driver = "Geopolitical Conflict Intensity"
    
    # 1. Prepare the data package for the AI
    prompt = f"Current AGRI: {agri_score}, Velocity: {velocity}, Acceleration: {acceleration}. Top rising pillar: {top_driver}."
    
    # 2. Ask the AI to write the brief
    print("Calling Gemini AI...")
    ai_brief = call_gemini(prompt)

    # 3. Assemble the final data dictionary
    agri_data = {
        "AGRI_Score": agri_score,
        "Velocity": velocity,
        "Acceleration": acceleration,
        "Top_Risk_Driver": top_driver,
        "AI_Brief": ai_brief,
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    # 4. Save to your live database
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    print("Avellon AGRI Engine run complete with Gemini AI integration.")

if __name__ == "__main__":
    calculate_agri()
