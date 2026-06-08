from data_intelligence.quant_engine import QuantInsightEngine

class ResearchTools:
    """
    The Toolkit Manager that bridges the Agent Brain (Person 1) 
    with the Intelligence Engines (Person 2).
    """
    def __init__(self):
        # Initialize the Quantitative Engine (Person 2)
        self.quant_engine = QuantInsightEngine()

    def analyze_dataset(self, file_path, goal_type="launch"):
        """
        Directly triggers Person 2 to analyze a file based on the goal.
        
        Args:
            file_path (str): Path to the CSV/Excel file.
            goal_type (str): The active goal (e.g., "1. Launch New Product").
            
        Returns:
            str: A formatted markdown report from Person 2.
        """
        # 1. Load Data
        df = self.quant_engine.load_data(file_path)
        
        if df is None:
            return "❌ Error: Could not load data. Please ensure the file exists and is a CSV."

        # 2. Route to correct Goal Function
        # Map frontend label to GOAL_KEY
        goal_mapping = {
            "1. Launch New Product": "GOAL_1_LAUNCH",
            "2. Diagnose Performance": "GOAL_2_PERFORMANCE",
            "3. Improve UX / Journey": "GOAL_3_UX_JOURNEY",
            "4. Increase Retention": "GOAL_4_RETENTION",
            "5. Test Hypothesis": "GOAL_5_HYPOTHESIS",
            "6. Prioritize Roadmap": "GOAL_6_PRIORITIZATION",
            "7. Executive Summary": "GOAL_7_SYNTHESIS"
        }
        
        goal_key = goal_mapping.get(goal_type, "GOAL_1_LAUNCH")
        
        function_mapping = {
            "GOAL_1_LAUNCH": self.quant_engine.run_goal_1_analysis,
            "GOAL_2_PERFORMANCE": self.quant_engine.run_goal_2_analysis,
            "GOAL_3_UX_JOURNEY": self.quant_engine.run_goal_3_analysis,
            "GOAL_4_RETENTION": self.quant_engine.run_goal_4_analysis,
            "GOAL_5_HYPOTHESIS": self.quant_engine.run_goal_5_analysis,
            "GOAL_6_PRIORITIZATION": self.quant_engine.run_goal_6_analysis,
            "GOAL_7_SYNTHESIS": self.quant_engine.run_goal_7_analysis,
        }
        
        if goal_key in function_mapping:
            return function_mapping[goal_key](df)
            
        return f"⚠️ Tool not configured for goal: '{goal_type}' yet."
