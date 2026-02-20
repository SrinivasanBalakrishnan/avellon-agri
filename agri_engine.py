import json
import datetime

def calculate_agri():
    # 1. Define our current risk data (We will connect live feeds and Gemini later)
    agri_data = {
        "AGRI_Score": 63.4,
        "Velocity": "+3.2",
        "Acceleration": "1.1",
        "Top_Risk_Driver": "Energy & Maritime Disruption",
        "AI_Brief": "Geopolitical fragmentation has accelerated, heavily impacting the Energy & Maritime Disruption pillar. Sovereign Financial Stress shows secondary vulnerability.",
        "Last_Updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    # 2. Create the Database: Save this data directly into a JSON file
    with open("data.json", "w") as json_file:
        json.dump(agri_data, json_file, indent=4)
        
    # 3. Print a success message for our testing logs
    print("Avellon AGRI Engine run complete. data.json successfully generated.")

if __name__ == "__main__":
    calculate_agri()
