import streamlit as st
from state_manager import initialize_session_state
from agent_reasoning.prompts.goal_library import GOAL_MAPPING
GOAL_DISPLAY_NAME = {v: k for k, v in GOAL_MAPPING.items()}
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
elif "Hypothesis" in selected_goal:
    guidance_text = "💡 **Recommended Data:** A/B test results, experiment logs, or feature rollout stats."
elif "Prioritize" in selected_goal:
    guidance_text = "💡 **Recommended Data:** Feature backlogs with impact/effort scores."
elif "Executive" in selected_goal:
    guidance_text = "💡 **Recommended Data:** High-level metrics, aggregated company performance data."
st.info(guidance_text)

# --- STEP 2: MULTI-MODAL INPUT (The "Canonical System") ---
# Accepts CSV, Excel, or Text (PDF Page 70)
col1, col2 = st.columns([1, 1])

with col1:
    sample_mapping = {
        "1. Launch New Product": "samples/hairfall_market_survey_demo.csv",
        "2. Diagnose Performance": "samples/app_funnel_demo.csv",
        "3. Improve UX / Journey": "samples/app_funnel_demo.csv",
        "4. Increase Retention": "samples/subscription_retention_demo.csv",
        "5. Test Hypothesis": "samples/ab_test_demo.csv",
        "6. Prioritize Roadmap": "samples/feature_backlog_demo.csv",
        "7. Executive Summary": "samples/large_hairfall_market_survey_demo.csv"
    }
    recommended_sample = sample_mapping.get(selected_goal, "")
    
    data_source = st.selectbox("📁 Try sample data", ["(Upload your own)", recommended_sample])
    
    temp_file_path = None
    
    if data_source != "(Upload your own)":
        temp_file_path = data_source
        st.success(f"✅ Loaded Sample: {temp_file_path}")
        try:
            df = pd.read_csv(temp_file_path)
            st.dataframe(df.head())
            
            if 'sample_loaded' not in st.session_state or st.session_state.sample_loaded != temp_file_path:
                if 'goal_queue' in st.session_state:
                    st.session_state.goal_queue = []
                st.session_state.sample_loaded = temp_file_path
                with st.spinner("Indexing textual data into VectorDB..."):
                    st.session_state.brain.db.ingest_csv(df, temp_file_path, selected_goal)
        except Exception as e:
            st.error("Sample not found. Run `python generate_data.py --all` first.")
    else:
        uploaded_file = st.file_uploader("📂 Upload Research Data (CSV, Excel)", type=["csv", "xlsx"])
        if uploaded_file:
            st.success(f"✅ Loaded: {uploaded_file.name}")
            # Save to temp file securely (avoiding leaks on rerun)
            if 'uploaded_file_id' not in st.session_state or st.session_state.uploaded_file_id != uploaded_file.file_id:
                st.session_state.pop('db_ingested', None)
                if 'goal_queue' in st.session_state:
                    st.session_state.goal_queue = []
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    st.session_state.temp_file_path = tmp.name
                    st.session_state.uploaded_file_id = uploaded_file.file_id
            
            temp_file_path = st.session_state.temp_file_path
            
            # Display preview
            try:
                df = pd.read_csv(temp_file_path)
                st.dataframe(df.head())
                if 'uploaded_file_id' in st.session_state and st.session_state.uploaded_file_id == uploaded_file.file_id and 'db_ingested' not in st.session_state:
                    with st.spinner("Indexing textual data into VectorDB..."):
                        st.session_state.brain.db.ingest_csv(df, temp_file_path, selected_goal)
                        st.session_state.db_ingested = True
            except Exception as e:
                st.error(f"Error reading file: {e}")

with col2:
    st.markdown("#### 🎙️ / 📝 Context Input")
    context_text = st.text_area("Paste text, notes, or hypothesis here:", height=100)
    st.caption("You can paste emails, slack messages, or rough notes.")

# --- STEP 3: EXECUTION & REPORTING ---
# Initialize queue
if 'goal_queue' not in st.session_state:
    st.session_state.goal_queue = []

# History Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("escalation") and message["escalation"].get("escalation_needed"):
            esc = message["escalation"]
            st.warning(f"⚠️ Clarity gate: {esc.get('reason', '')} Switching to {esc.get('escalation_type', 'summary')}.")
        if message.get("trace"):
            with st.expander("🔍 Trace"):
                st.json(message["trace"])

# --- QUEUE & LAYER ACTIONS ---
def run_agent(query_text, active_goal, layer="handover"):
    full_context_prompt = f"""
    [SYSTEM_METADATA]
    ACTIVE_GOAL: {active_goal}
    UPLOADED_FILE: {temp_file_path if temp_file_path else 'None'}
    USER_NOTES: {context_text}
    [/SYSTEM_METADATA]

    USER_QUERY: {query_text}
    """
    
    st.session_state.messages.append({"role": "user", "content": f"*{layer.upper()}*: {query_text}"})
    
    with st.chat_message("assistant"):
        status = st.empty()
        status.markdown(f"⏳ 🧠 Running '{active_goal}' (Layer: {layer})...")
        try:
            res_dict = st.session_state.brain.process_turn(full_context_prompt, layer=layer)
        except Exception as e:
            res_dict = {"response": f"❌ Error: {e}", "trace": {}, "next_goals": []}
            
        status.empty()

        if "response_stream" in res_dict:
            full_response = st.write_stream(res_dict["response_stream"])
        else:
            full_response = res_dict.get("response", "")
            st.markdown(full_response)
        
        # Enqueue new goals if detected
        active_goal_key = GOAL_MAPPING.get(active_goal, active_goal)
        if res_dict.get("next_goals"):
            for g in res_dict["next_goals"]:
                if g not in st.session_state.goal_queue and g != active_goal_key:
                    st.session_state.goal_queue.append(g)

        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "trace": res_dict.get("trace", {}),
            "escalation": res_dict.get("escalation")
        })

# Action Buttons
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    cols = st.columns([1, 1, 1, 2])
    with cols[0]:
        if st.button("📝 Executive Summary"):
            run_agent("Please provide the Executive Summary.", selected_goal, layer="summary")
            st.rerun()
    with cols[1]:
        if st.button("📊 Show Evidence"):
            run_agent("Please show me the evidence and traceability.", selected_goal, layer="evidence")
            st.rerun()
    with cols[2]:
        if st.button("📁 Show Raw Data"):
            run_agent("Please dump the raw data for deep research.", selected_goal, layer="deep_research")
            st.rerun()
    
    if st.session_state.goal_queue:
        with cols[3]:
            next_g = st.session_state.goal_queue[0]
            display_g = GOAL_DISPLAY_NAME.get(next_g, next_g)
            if st.button(f"➡ Next: {display_g} ({len(st.session_state.goal_queue)} left)"):
                popped_goal = st.session_state.goal_queue.pop(0)
                run_agent("Run next analysis.", popped_goal, layer="handover")
                st.rerun()
                
    st.divider()
    last_msg = st.session_state.messages[-1]
    export_content = last_msg.get("content", "")
    if last_msg.get("trace"):
        export_content += f"\n\n### Trace Data\n```json\n{last_msg['trace']}\n```"
    st.download_button(
        label="📄 Export Brief (Markdown)",
        data=export_content,
        file_name="research_brief.md",
        mime="text/markdown"
    )

# Queue Progress UI
if st.session_state.goal_queue:
    current_g = st.session_state.goal_queue[0]
    st.info(f"Currently analyzing... Up next: {GOAL_DISPLAY_NAME.get(current_g, current_g)}")

# Main Action (Chat)
if prompt := st.chat_input("Ask a specific question or type 'Run Analysis' to process data..."):
    run_agent(prompt, selected_goal, layer="handover")
    st.rerun()