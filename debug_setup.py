import os
from dotenv import load_dotenv

# Load environment variables safely
load_dotenv()

# Basic check before loading heavy machinery
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in .env file.")
    print("Please add your key to .env before running.")
    exit(1)

print("✅ Environment check passed. Loading AgentBrain...")

try:
    from agent_reasoning.brain import AgentBrain

    # Initialize the brain
    brain = AgentBrain()
    
    # Run a test query against the demo CSV, checking samples/ first
    demo_file = "samples/large_hairfall_market_survey_demo.csv"
    if not os.path.exists(demo_file):
        demo_file = "samples/hairfall_market_survey_demo.csv"
    if not os.path.exists(demo_file):
        demo_file = "large_hairfall_market_survey_demo.csv"
    if not os.path.exists(demo_file):
        demo_file = "hairfall_market_survey_demo.csv"
    print(f"🧠 Running smoke test on {demo_file}...")
    
    prompt = f"""
    [SYSTEM_METADATA]
    ACTIVE_GOAL: 1. Launch New Product
    UPLOADED_FILE: {demo_file}
    USER_NOTES: 
    [/SYSTEM_METADATA]

    USER_QUERY: Run Analysis
    """
    
    response = brain.process_turn(prompt)
    
    print("\n--- 🟢 RESPONSE PREVIEW (First 300 chars) ---")
    print(response[:300] + "...\n")
    print("✅ Smoke test complete. The brain is functioning.")
    
except Exception as e:
    print(f"\n❌ Diagnostic failed with exception: {e}")