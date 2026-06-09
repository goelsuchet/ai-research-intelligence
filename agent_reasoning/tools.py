from data_intelligence.quant_engine import QuantInsightEngine

class ResearchTools:
    """
    The Toolkit Manager that bridges the Agent Brain (Person 1) 
    with the Intelligence Engines (Person 2).
    """
    def __init__(self):
        # Initialize the Quantitative Engine (Person 2)
        self.quant_engine = QuantInsightEngine()

    def analyze_dataset(self, file_path, goal_type="launch", context=None):
        """
        Directly triggers Person 2 to analyze a file based on the goal.
        
        Args:
            file_path (str): Path to the CSV/Excel file.
            goal_type (str): The active goal (e.g., "1. Launch New Product").
            
        Returns:
            str: A formatted markdown report from Person 2.
        """
        # 1. Load Data
        if context is None:
            context = {}
        df = self.quant_engine.load_data(file_path)
        
        if df is None:
            return "[ERROR] Could not load data. Please ensure the file exists and is a CSV.", {}

        # 2. Route to correct Goal Function
        from agent_reasoning.prompts.goal_library import GOAL_MAPPING
        
        function_mapping = {
            "GOAL_1_LAUNCH": self.quant_engine.run_goal_1_analysis,
            "GOAL_2_PERFORMANCE": self.quant_engine.run_goal_2_analysis,
            "GOAL_3_UX_JOURNEY": self.quant_engine.run_goal_3_analysis,
            "GOAL_4_RETENTION": self.quant_engine.run_goal_4_analysis,
            "GOAL_5_HYPOTHESIS": self.quant_engine.run_goal_5_analysis,
            "GOAL_6_PRIORITIZATION": self.quant_engine.run_goal_6_analysis,
            "GOAL_7_SYNTHESIS": self.quant_engine.run_goal_7_analysis,
        }

        if goal_type in function_mapping:
            goal_key = goal_type
        else:
            goal_key = GOAL_MAPPING.get(goal_type, "GOAL_1_LAUNCH")
        
        if goal_key in function_mapping:
            return function_mapping[goal_key](df, file_path, context)
            
        return f"⚠️ Tool not configured for goal: '{goal_type}' yet.", {}
