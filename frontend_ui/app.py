import streamlit as st
from state_manager import initialize_session_state
import pandas as pd
import tempfile

# --- 1. SETUP & STATE ---
st.set_page_config(page_title="AI Research Agent", page_icon="🧠", layout="wide")
initialize_session_state()

# --- 2. SIDEBAR: GOAL SELECTION (The "Entry Point") ---
with st.sidebar:
    st.title("🎛️ Research Controls")
    st.markdown("---")
    
    # "Goal-First Mode" as per PDF Page 69
    selected_goal = st.radio(
        "🎯 Select Research Goal",
        [
            "1. Launch New Product", 
            "2. Diagnose Performance", 
            "3. Improve UX / Journey", 
            "4. Increase Retention", 
            "5. Test Hypothesis", 
            "6. Prioritize Roadmap", 
            "7. Executive Summary"
        ],
        index=0
    )
    
    st.markdown("---")
    st.info(f"**Current Mission:**\n{selected_goal}")
    
    if st.button("🧹 Reset Research"):
        st.session_state.messages = []
        st.rerun()

# --- 3. MAIN INTERFACE ---
st.title("🧠 AI Research Intelligence")
st.markdown(f"### Mission: *{selected_goal}*")

# --- STEP 1: DATA GUIDANCE (Context-Aware) ---
# Displays specific advice based on the goal (PDF Page 70)
guidance_text = ""
if "Launch" in selected_goal:
    guidance_text = "💡 **Recommended Data:** Market size reports, competitor lists, or initial survey results."
elif "Diagnose" in selected_goal:
    guidance_text = "💡 **Recommended Data:** KPI spreadsheets (CAC, LTV), traffic sources, or conversion metrics."
elif "UX" in selected_goal:
    guidance_text = "💡 **Recommended Data:** User feedback CSVs, support tickets, or funnel drop-off rates."
elif "Retention" in selected_goal:
    guidance_text = "💡 **Recommended Data:** Retention cohorts (D1/D7/D30), churn reasons, or usage frequency data."

st.info(guidance_text)

# --- STEP 2: MULTI-MODAL INPUT (The "Canonical System") ---
# Accepts CSV, Excel, or Text (PDF Page 70)
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("📂 Upload Research Data (CSV, Excel)", type=["csv", "xlsx"])
    temp_file_path = None
    if uploaded_file:
        st.success(f"✅ Loaded: {uploaded_file.name}")
        # Save to temp file securely (avoiding leaks on rerun)
        if 'uploaded_file_id' not in st.session_state or st.session_state.uploaded_file_id != uploaded_file.file_id:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                st.session_state.temp_file_path = tmp.name
                st.session_state.uploaded_file_id = uploaded_file.file_id
        
        temp_file_path = st.session_state.temp_file_path
        
        # Display preview
        try:
            df = pd.read_csv(temp_file_path)
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")

with col2:
    st.markdown("#### 🎙️ / 📝 Context Input")
    context_text = st.text_area("Paste text, notes, or hypothesis here:", height=100)
    st.caption("You can paste emails, slack messages, or rough notes.")

# --- STEP 3: EXECUTION & REPORTING ---
# History Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Main Action
if prompt := st.chat_input("Ask a specific question or type 'Run Analysis' to process data..."):
    
    # 1. Construct the "Canonical Input" (Merging File + Text + Goal)
    # This prepares the data for Person 2 (The Intelligence Engine)
    full_context_prompt = f"""
    [SYSTEM_METADATA]
    ACTIVE_GOAL: {selected_goal}
    UPLOADED_FILE: {temp_file_path if temp_file_path else 'None'}
    USER_NOTES: {context_text}
    [/SYSTEM_METADATA]

    USER_QUERY: {prompt}
    """

    # 2. Show User Message (Visual only)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate Response
    if st.session_state.brain:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner(f"🧠 Running '{selected_goal}' Engine..."):
                try:
                    # Pass the FULL context to the brain, not just the chat
                    full_response = st.session_state.brain.process_turn(full_context_prompt)
                except Exception as e:
                    full_response = f"❌ Error: {e}"

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})