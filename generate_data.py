import pandas as pd
import numpy as np
import random

# --- CONFIGURATION ---
NUM_RESPONSES = 50000

# --- DATA GENERATION ---
data = {
    "response_id": [f"RESP_{i:04d}" for i in range(1, NUM_RESPONSES + 1)],
    "age_group": np.random.choice(
        ["18-24", "25-34", "35-44", "45-54", "55+"], 
        NUM_RESPONSES, 
        p=[0.25, 0.35, 0.20, 0.15, 0.05] # Most users are 25-34
    ),
    "gender": np.random.choice(["Female", "Male", "Other"], NUM_RESPONSES, p=[0.6, 0.39, 0.01]),
    "city_tier": np.random.choice(["Tier 1", "Tier 2", "Tier 3"], NUM_RESPONSES, p=[0.5, 0.3, 0.2]),
    
    # PROBLEM VALIDATION (Goal 1, Module 2)
    "primary_hair_concern": np.random.choice(
        ["Hairfall", "Dandruff", "Frizz", "Oily Scalp", "Dryness"], 
        NUM_RESPONSES, 
        p=[0.55, 0.15, 0.10, 0.10, 0.10] # Biased towards hairfall
    ),
    "hairfall_severity": np.random.choice(
        ["Mild (Seasonal)", "Moderate (Clumps)", "Severe (Visible Thinning)"], 
        NUM_RESPONSES, 
        p=[0.4, 0.3, 0.3]
    ),
    
    # COMPETITIVE LANDSCAPE (Goal 1, Module 4)
    "current_brand": np.random.choice(
        ["Head & Shoulders", "Dove", "Pantene", "Mamaearth", "Tresemme", "Generic/Ayurvedic"], 
        NUM_RESPONSES
    ),
    "satisfaction_score": np.random.randint(1, 11, NUM_RESPONSES), # 1-10 scale
    
    # PURCHASE BEHAVIOR (Goal 1, Module 6)
    "willingness_to_pay_inr": np.random.choice(
        [150, 250, 399, 499, 699, 999], 
        NUM_RESPONSES, 
        p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]
    ),
    "purchase_frequency": np.random.choice(
        ["Monthly", "Bi-Monthly", "Quarterly"], 
        NUM_RESPONSES
    ),
    
    # PREFERENCES
    "ingredient_preference": np.random.choice(
        ["Ayurvedic/Herbal", "Chemical/Scientific", "No Preference"], 
        NUM_RESPONSES, 
        p=[0.6, 0.3, 0.1]
    ),
    "feedback_text": [
        random.choice([
            "I want something that actually stops hairfall.",
            "Too expensive for daily use.",
            "Made my hair dry but stopped fall.",
            "I prefer natural smell.",
            "Nothing works on my scalp.",
            "Good but causes dandruff.",
            "I need a solution for post-partum hair loss.",
            "Just marketing gimmicks."
        ]) for _ in range(NUM_RESPONSES)
    ]
}

# --- ADJUST LOGIC TO MAKE IT REALISTIC ---
# If Satisfaction is Low (<5), they are more likely to have "Severe" hairfall
df = pd.DataFrame(data)
df.loc[df['satisfaction_score'] < 4, 'willingness_to_pay_inr'] = 699 # Desperate users pay more

# --- SAVE ---
df.to_csv("large_hairfall_market_survey_demo.csv", index=False)
print("Demo Data Generated: 'large_hairfall_market_survey_demo.csv' (50000 rows)")