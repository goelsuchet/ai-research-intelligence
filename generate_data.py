import pandas as pd
import numpy as np
import random
import os
import argparse

# --- CONFIGURATION ---
NUM_RESPONSES = 50000
SAMPLES_DIR = "samples"

def ensure_samples_dir():
    if not os.path.exists(SAMPLES_DIR):
        os.makedirs(SAMPLES_DIR)

def generate_goal_1():
    print(f"Generating Goal 1 data ({NUM_RESPONSES} rows)...")
    data = {
        "response_id": [f"RESP_{i:04d}" for i in range(1, NUM_RESPONSES + 1)],
        "age_group": np.random.choice(["18-24", "25-34", "35-44", "45-54", "55+"], NUM_RESPONSES, p=[0.25, 0.35, 0.20, 0.15, 0.05]),
        "gender": np.random.choice(["Female", "Male", "Other"], NUM_RESPONSES, p=[0.6, 0.39, 0.01]),
        "city_tier": np.random.choice(["Tier 1", "Tier 2", "Tier 3"], NUM_RESPONSES, p=[0.5, 0.3, 0.2]),
        "primary_hair_concern": np.random.choice(["Hairfall", "Dandruff", "Frizz", "Oily Scalp", "Dryness"], NUM_RESPONSES, p=[0.55, 0.15, 0.10, 0.10, 0.10]),
        "hairfall_severity": np.random.choice(["Mild (Seasonal)", "Moderate (Clumps)", "Severe (Visible Thinning)"], NUM_RESPONSES, p=[0.4, 0.3, 0.3]),
        "current_brand": np.random.choice(["Head & Shoulders", "Dove", "Pantene", "Mamaearth", "Tresemme", "Generic/Ayurvedic"], NUM_RESPONSES),
        "satisfaction_score": np.random.randint(1, 11, NUM_RESPONSES),
        "willingness_to_pay_inr": np.random.choice([150, 250, 399, 499, 699, 999], NUM_RESPONSES, p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]),
        "purchase_frequency": np.random.choice(["Monthly", "Bi-Monthly", "Quarterly"], NUM_RESPONSES),
        "ingredient_preference": np.random.choice(["Ayurvedic/Herbal", "Chemical/Scientific", "No Preference"], NUM_RESPONSES, p=[0.6, 0.3, 0.1]),
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
    df = pd.DataFrame(data)
    df.loc[df['satisfaction_score'] < 4, 'willingness_to_pay_inr'] = 699
    
    # Save both large and standard for backwards compatibility with tests
    df.to_csv(os.path.join(SAMPLES_DIR, "large_hairfall_market_survey_demo.csv"), index=False)
    df.head(500).to_csv(os.path.join(SAMPLES_DIR, "hairfall_market_survey_demo.csv"), index=False)
    print("-> Created hairfall_market_survey_demo.csv")

def generate_goal_2_3():
    print(f"Generating Goal 2 & 3 data ({NUM_RESPONSES} rows)...")
    data = {
        "session_id": [f"SESS_{i:04d}" for i in range(1, NUM_RESPONSES + 1)],
        "acquisition_cost": np.random.uniform(5.0, 50.0, NUM_RESPONSES),
        "time_to_value_seconds": np.random.uniform(30.0, 600.0, NUM_RESPONSES),
        "retention_d30": np.random.choice([0, 1], NUM_RESPONSES, p=[0.75, 0.25]),
        "funnel_stage": np.random.choice(["Landing", "Signup", "Onboarding", "Activation", "Paid"], NUM_RESPONSES, p=[0.4, 0.25, 0.2, 0.1, 0.05]),
        "effort_score": np.random.randint(1, 11, NUM_RESPONSES),
        "friction_type": np.random.choice(["Cognitive", "Technical", "Pricing", "None"], NUM_RESPONSES, p=[0.4, 0.2, 0.3, 0.1]),
        "churn_reason": np.random.choice(["Too expensive", "Hard to use", "Found alternative", "Bugs", "N/A"], NUM_RESPONSES, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(SAMPLES_DIR, "app_funnel_demo.csv"), index=False)
    print("-> Created app_funnel_demo.csv")

def generate_goal_4():
    print(f"Generating Goal 4 data ({NUM_RESPONSES} rows)...")
    data = {
        "user_id": [f"USR_{i:04d}" for i in range(1, NUM_RESPONSES + 1)],
        "retention_d30": np.random.choice([0, 1], NUM_RESPONSES, p=[0.6, 0.4]),
        "login_frequency": np.random.randint(1, 20, NUM_RESPONSES),
        "habit_score": np.random.randint(1, 100, NUM_RESPONSES),
        "plan_type": np.random.choice(["Basic", "Pro", "Enterprise"], NUM_RESPONSES, p=[0.7, 0.2, 0.1]),
        "nps_score": np.random.randint(1, 11, NUM_RESPONSES)
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(SAMPLES_DIR, "subscription_retention_demo.csv"), index=False)
    print("-> Created subscription_retention_demo.csv")

def generate_goal_5():
    print(f"Generating Goal 5 data ({NUM_RESPONSES} rows)...")
    data = {
        "experiment_id": np.random.choice([f"EXP_{i:02d}" for i in range(1, 10)], NUM_RESPONSES),
        "variant": np.random.choice(["Control", "Treatment A", "Treatment B"], NUM_RESPONSES),
        "conversion_rate": np.random.uniform(0.01, 0.15, NUM_RESPONSES),
        "p_value": np.random.uniform(0.001, 0.5, NUM_RESPONSES),
        "sample_size": np.random.randint(1000, 100000, NUM_RESPONSES)
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(SAMPLES_DIR, "ab_test_demo.csv"), index=False)
    print("-> Created ab_test_demo.csv")

def generate_goal_6():
    # Typically feature backlogs are smaller, like 100-500 features
    num_features = 200
    print(f"Generating Goal 6 data ({num_features} rows)...")
    data = {
        "feature_name": [f"Feature_{i:03d}" for i in range(1, num_features + 1)],
        "impact_score": np.random.randint(1, 11, num_features),
        "effort_score": np.random.randint(1, 11, num_features),
        "reach": np.random.randint(100, 10000, num_features),
        "confidence_score": np.random.choice([0.5, 0.8, 1.0], num_features),
        "strategic_alignment": np.random.choice(["High", "Medium", "Low"], num_features)
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(SAMPLES_DIR, "feature_backlog_demo.csv"), index=False)
    print("-> Created feature_backlog_demo.csv")

def main():
    parser = argparse.ArgumentParser(description="Generate demo data for the AI Research Agent.")
    parser.add_argument("--goal", type=int, choices=[1, 2, 3, 4, 5, 6, 7], help="Generate data for a specific goal (1-7)")
    parser.add_argument("--all", action="store_true", help="Generate data for all goals")
    
    args = parser.parse_args()
    
    ensure_samples_dir()
    
    if args.all or not args.goal:
        generate_goal_1()
        generate_goal_2_3()
        generate_goal_4()
        generate_goal_5()
        generate_goal_6()
        print("\n[SUCCESS] All demo datasets generated successfully!")
        return

    if args.goal == 1:
        generate_goal_1()
    elif args.goal in [2, 3]:
        generate_goal_2_3()
    elif args.goal == 4:
        generate_goal_4()
    elif args.goal == 5:
        generate_goal_5()
    elif args.goal == 6:
        generate_goal_6()
    elif args.goal == 7:
        generate_goal_1()

if __name__ == "__main__":
    main()