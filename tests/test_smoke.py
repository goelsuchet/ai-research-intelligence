import pytest
import os
import sys
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_reasoning.prompts.goal_library import GOAL_MAPPING
from agent_reasoning.tools import ResearchTools
from data_intelligence.quant_engine import QuantInsightEngine

# Maps GOAL_KEY to the expected sample CSV filename from generate_data.py
GOAL_CSV_MAP = {
    "GOAL_1_LAUNCH": "hairfall_market_survey_demo.csv",
    "GOAL_2_PERFORMANCE": "app_funnel_demo.csv",
    "GOAL_3_UX_JOURNEY": "app_funnel_demo.csv",
    "GOAL_4_RETENTION": "subscription_retention_demo.csv",
    "GOAL_5_HYPOTHESIS": "ab_test_demo.csv",
    "GOAL_6_PRIORITIZATION": "feature_backlog_demo.csv",
    "GOAL_7_SYNTHESIS": "large_hairfall_market_survey_demo.csv"
}

# Section headers that must appear in each goal's report, derived directly from
# the named sections in quant_engine.py. Catches wrong routing and missing sections.
GOAL_EXPECTED_SECTIONS = {
    "GOAL_1_LAUNCH": ["Market Attractiveness", "Competitive Landscape", "Pricing Feasibility"],
    "GOAL_2_PERFORMANCE": ["KPI Health Check", "Funnel Analysis", "Churn Diagnosis"],
    "GOAL_3_UX_JOURNEY": ["Cognitive Load Analysis", "Friction Taxonomy"],
    "GOAL_4_RETENTION": ["Retention Health", "Habit Formation"],
    "GOAL_5_HYPOTHESIS": ["Primary Metric Shift", "Evidence Classification"],
    "GOAL_6_PRIORITIZATION": ["Backlog Sizing"],
    "GOAL_7_SYNTHESIS": ["The Bottom Line", "Aggregate Statistics"],
}

@pytest.mark.parametrize("goal_key, filename", GOAL_CSV_MAP.items())
def test_goals_on_samples(goal_key, filename):
    sample_path = os.path.join("samples", filename)

    assert os.path.exists(sample_path), f"Missing demo file {filename}"

    tools = ResearchTools()
    report, trace = tools.analyze_dataset(sample_path, goal_key)

    # Trace contract
    assert report is not None
    assert "[ERROR]" not in report, f"Report contained error for {goal_key}: {report}"
    assert isinstance(trace, dict)
    assert "tool" in trace
    assert "rows_analyzed" in trace
    assert trace["rows_analyzed"] > 0
    assert "scenarios" in trace, f"Missing 'scenarios' in trace for {goal_key}"
    assert "gap" in trace, f"Missing 'gap' in trace for {goal_key}"

    # Per-goal section assertions: each section is unique to that goal's quant analysis,
    # so a missing entry means either wrong routing or a broken engine method.
    for section in GOAL_EXPECTED_SECTIONS[goal_key]:
        assert section in report, (
            f"[{goal_key}] Expected section '{section}' not found in report.\n"
            f"Report preview: {report[:300]}"
        )
        
    # Visuals assertions
    assert "visuals" in trace, f"Missing 'visuals' in trace for {goal_key}"
    for spec in trace["visuals"]:
        assert "type" in spec
        assert spec["type"] in ["bar", "hist", "line", "funnel", "scatter"]
        assert "x" in spec and "y" in spec
        # x and y should be same length unless it's a histogram where we expect len(x) == len(y) usually 
        # Actually for hist we used bin edges for x and counts for y, and we took x[:-1] so they are same length!
        assert len(spec["x"]) == len(spec["y"]), f"Length mismatch in visual spec {spec['title']}"

def test_recompute_functions():
    # reach_at_price
    df = pd.DataFrame({"willingness_to_pay_inr": [100, 200, 300, 400, 500]})
    reach_100 = QuantInsightEngine.reach_at_price(df, 100)
    reach_300 = QuantInsightEngine.reach_at_price(df, 300)
    reach_600 = QuantInsightEngine.reach_at_price(df, 600)
    
    assert reach_100 == 100.0
    assert reach_300 == 60.0
    assert reach_600 == 0.0
    
    # monotonically non-increasing
    assert reach_100 >= reach_300 >= reach_600
    
    # rice_at
    rice1 = QuantInsightEngine.rice_at(reach=1000, impact=3, conf=100, effort=1)
    assert rice1 == 3000.0
    
    rice2 = QuantInsightEngine.rice_at(reach=1000, impact=3, conf=50, effort=2)
    assert rice2 == 750.0

def test_system_persona_no_email_rules():
    from agent_reasoning.prompts.system_persona import SYSTEM_INSTRUCTIONS
    prompt = SYSTEM_INSTRUCTIONS.lower()
    assert "dear" in prompt or "subject" in prompt or "best regards" in prompt, "System prompt should explicitly mention forbidden email formats"
    assert "no email" in prompt or "do not write" in prompt or "never use" in prompt, "System prompt should explicitly forbid email formatting"
