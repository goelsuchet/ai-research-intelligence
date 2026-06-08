import logging
import re
from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .prompts.system_persona import SYSTEM_INSTRUCTIONS
from .prompts.goal_library import GOAL_DEFINITIONS
from .tools import ResearchTools
from .validator import ClarityValidator
from .output_manager import OutputManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentBrain")

class AgentBrain:
    def __init__(self, model_name="gpt-4-turbo"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.goal_queue: List[str] = []
        self.active_goal: Optional[str] = None
        self.context_memory: Dict = {}
        
        self.validator = ClarityValidator()
        self.output_manager = OutputManager()
        self.tools = ResearchTools() 

    def process_turn(self, user_input: str) -> str:
        """
        Main Loop: 
        1. Parse Input
        2. Run Tools (if needed)
        3. SYNTHESIZE Answer (Using OpenAI)
        """
        
        # --- 1. PARSE FRONTEND METADATA ---
        # We need to separate the "User's Question" from the "System Data"
        file_name = None
        active_goal_hint = "1. Launch New Product"
        clean_user_query = user_input # Default

        if "[SYSTEM_METADATA]" in user_input:
            # Extract File
            file_match = re.search(r"UPLOADED_FILE: (.+)", user_input)
            if file_match and "None" not in file_match.group(1):
                file_name = file_match.group(1).strip()
            
            # Extract Goal
            goal_match = re.search(r"ACTIVE_GOAL: (.+)", user_input)
            if goal_match:
                active_goal_hint = goal_match.group(1).strip()
                
            # Extract The Real Question (Remove the metadata block)
            # The prompt format is usually [METADATA]...[/METADATA] USER_QUERY: <text>
            if "USER_QUERY:" in user_input:
                clean_user_query = user_input.split("USER_QUERY:")[-1].strip()

        # --- 2. DATA INTELLIGENCE LAYER (Person 2) ---
        tool_output = ""
        
        # Only run the heavy tool if we haven't seen this file/goal combo yet, 
        # OR if it's the first run. For now, we run it every time a file is present 
        # to ensure we have fresh data, but we feed it to the LLM.
        if file_name:
            import os
            if not os.path.exists(file_name):
                return f"❌ Error: The uploaded file could not be found at {file_name}."
            logger.info(f"📂 Brain: Running Quant Engine on {file_name}")
            tool_output = self.tools.analyze_dataset(file_name, active_goal_hint)

        # --- 3. COGNITIVE LAYER (Person 1 - OpenAI) ---
        # THIS IS THE MISSING PIECE. We don't return the tool output. 
        # We send it to OpenAI to "read" and explain.
        
        if tool_output:
            # We construct a "Reasoning Prompt"
            synthesis_prompt = f"""
            SYSTEM CONTEXT:
            You are an expert AI Research Analyst.
            You have just run a quantitative analysis using your Data Engine.
            
            THE DATA ENGINE OUTPUT:
            {tool_output}
            
            USER'S QUESTION:
            "{clean_user_query}"
            
            INSTRUCTIONS:
            1. Answer the user's question using ONLY the facts from the Data Engine Output.
            2. If the user asks something not in the report (like "Age Groups"), clearly say: 
               "My current analysis report covers the selected metrics, but does not yet contain specific data on [User Topic]. Would you like me to update the analysis code to include that?"
            3. Do not just dump the raw report unless asked. Synthesize the answer.
            """
            
            # Call OpenAI
            response = self.llm.invoke([
                SystemMessage(content="You are a helpful Research Intelligence Assistant."),
                HumanMessage(content=synthesis_prompt)
            ])
            return response.content

        # --- 4. FALLBACK (No File / General Chat) ---
        # (Existing logic for intent detection...)
        return self._handle_standard_chat(clean_user_query)

    def _handle_standard_chat(self, user_input):
        # Existing logic for intent detection/escalation
        if not self.active_goal:
             new_goals = self._detect_goals(user_input)
             self._update_queue(new_goals)
        
        # Simple response for now if no file is present
        return self.output_manager.generate_response(self.active_goal, {}, "summary")

    def _detect_goals(self, user_input: str) -> List[str]:
        prompt = f"Map input to goals: {list(GOAL_DEFINITIONS.keys())}. Return comma-separated list. Input: {user_input}"
        response = self.llm.invoke([SystemMessage(content=SYSTEM_INSTRUCTIONS), HumanMessage(content=prompt)])
        return [g.strip() for g in response.content.split(',') if g.strip() in GOAL_DEFINITIONS]

    def _update_queue(self, new_goals: List[str]):
        for goal in new_goals:
            if goal not in self.goal_queue and goal != self.active_goal:
                self.goal_queue.append(goal)
        if not self.active_goal and self.goal_queue:
            self.active_goal = self.goal_queue.pop(0)

    def _has_required_context(self, goal, user_input) -> bool:
        return True 

    def _complete_current_goal(self):
        self.active_goal = None
        if self.goal_queue:
            self.active_goal = self.goal_queue.pop(0)

    def _handle_escalation(self, escalation_type):
        return "Thinking..."