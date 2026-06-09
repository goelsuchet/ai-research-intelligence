# agent_reasoning/prompts/goal_library.py

GOAL_DEFINITIONS = {
    "GOAL_1_LAUNCH": {
        "name": "New B2C Product Launch Research",
        "description": "Assess market viability, demand, and launch strategy for a new product.",
        "keywords": ["launch", "market", "entry", "go to market", "viability", "idea", "new product"],
        "context_required": ["product_concept", "target_audience_hypothesis", "price_range_idea"],
        "tools_required": [
            "estimate_tam_sam_som", "analyze_trends_and_timing", 
            "score_problem_market_fit", "analyze_substitutes",    
            "identify_early_adopters", "map_competitive_landscape", 
            "define_mvp_scope", "estimate_willingness_to_pay",    
            "recommend_launch_channels", "stress_test_assumptions" 
        ]
    },
    "GOAL_2_PERFORMANCE": {
        "name": "Product Performance Diagnosis",
        "description": "Diagnose why metrics are changing (e.g., drop in sales, low retention).",
        "keywords": ["metrics", "kpi", "drop", "why is X down", "health", "performance"],
        "context_required": ["current_kpis", "time_period", "recent_changes"],
        "tools_required": [
            "validate_north_star", "scan_kpi_health", "benchmark_against_industry",
            "map_funnel_dropoffs", "rank_bottlenecks"
        ]
    },
    "GOAL_3_UX_JOURNEY": {
        "name": "UX & User Journey Research",
        "description": "Identify friction points, onboarding issues, and journey breaks.",
        "keywords": ["friction", "onboarding", "flow", "user experience", "ux", "confusing"],
        "context_required": ["user_journey_steps", "platform_type", "feedback_data"],
        "tools_required": [
            "decompose_user_journey", "score_effort_and_friction", 
            "analyze_time_to_value", "audit_heuristic_violations", 
            "map_emotional_curve"
        ]
    },
    "GOAL_4_RETENTION": {
        "name": "Retention & Loyalty Analysis",
        "description": "Analyze churn drivers, cohort health, and loyalty levers.",
        "keywords": ["churn", "retention", "loyalty", "ltv", "leaving", "repeat"],
        "context_required": ["retention_data", "business_model", "usage_frequency"],
        "tools_required": [
            "analyze_retention_decay", "identify_churn_triggers", 
            "score_habit_strength", "calculate_switching_costs",
            "evaluate_loyalty_program"
        ]
    },
    "GOAL_5_HYPOTHESIS": {
        "name": "Hypothesis Testing & Validation",
        "description": "Structure, validate, or reject specific business assumptions.",
        "keywords": ["validate", "test", "experiment", "hypothesis", "assumption", "if we do X"],
        "context_required": ["hypothesis_statement", "metric_to_move"],
        "tools_required": [
            "validate_hypothesis_structure", "score_assumption_fragility",
            "select_evidence_strategy", "design_test_blueprint",
            "interpret_test_results"
        ]
    },
    "GOAL_6_PRIORITIZATION": {
        "name": "Roadmap & Prioritization",
        "description": "Rank initiatives based on impact, effort, and strategy.",
        "keywords": ["roadmap", "priority", "rank", "what first", "trade-off", "backlog"],
        "context_required": ["list_of_initiatives", "strategic_goals", "time_horizon", "team_constraints"],
        "tools_required": [
            "check_strategy_alignment", "estimate_impact_vs_effort",
            "rank_rice_score", "detect_strategy_drift",
            "simulate_roadmap_scenarios"
        ]
    },
    "GOAL_7_SYNTHESIS": {
        "name": "Executive Synthesis & Decision Briefing",
        "description": "Synthesize findings into decision-ready executive artifacts.",
        "keywords": ["summary", "brief", "presentation", "executive", "deck", "report"],
        "context_required": ["audience_type", "decision_stakes", "format_preference"],
        "tools_required": [
            "distill_key_signals", "generate_executive_recommendation",
            "anticipate_objections", "format_decision_brief"
        ]
    }
}

GOAL_MAPPING = {
    "1. Launch New Product": "GOAL_1_LAUNCH",
    "2. Diagnose Performance": "GOAL_2_PERFORMANCE",
    "3. Improve UX / Journey": "GOAL_3_UX_JOURNEY",
    "4. Increase Retention": "GOAL_4_RETENTION",
    "5. Test Hypothesis": "GOAL_5_HYPOTHESIS",
    "6. Prioritize Roadmap": "GOAL_6_PRIORITIZATION",
    "7. Executive Summary": "GOAL_7_SYNTHESIS"
}