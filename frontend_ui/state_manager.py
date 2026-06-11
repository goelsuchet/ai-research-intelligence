import streamlit as st
import sys
import os
from dotenv import load_dotenv

# --- MAGIC FIX: LOAD .ENV FROM ROOT FOLDER ---
# This tells Python: "Look one folder up for the .env file"
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)
load_dotenv(os.path.join(root_path, ".env"))
# ---------------------------------------------

from agent_reasoning.brain import AgentBrain

def initialize_session_state():
    """
    Sets up the session state variables if they don't exist yet.
    """
    # 1. Initialize Message History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. Initialize the AI Brain (Person 1)
    if "brain" not in st.session_state:
        try:
            # We use gpt-4-turbo for the best reasoning
            # The API Key is now loaded, so this will succeed!
            st.session_state.brain = AgentBrain(model_name="gpt-4-turbo") 
            st.toast("🧠 Brain Successfully Connected!", icon="✅")
        except Exception as e:
            st.error(f"❌ Failed to load AI Brain: {e}")
            st.session_state.brain = None

    # 3. Initialize UI Controls
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "temp_file_path" not in st.session_state:
        st.session_state.temp_file_path = None