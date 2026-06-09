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
from data_intelligence.db_manager import VectorDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentBrain")

class AgentBrain:
    def __init__(self, model_name="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.context_memory: Dict = {}
        
        self.validator = ClarityValidator()
        self.output_manager = OutputManager()
        self.tools = ResearchTools() 
        self.db = VectorDBManager()

    def process_turn(self, user_input: str, layer: str = "handover") -> dict:
        """
        Main Loop for Phase 5: 
        1. Parse Input
        2. Detect Goals
        3. Run Tools & RAG
        4. Progressively Render Layer
        5. Clarity Gate
        """
        file_name = None
        active_goal_hint = "1. Launch New Product"
        clean_user_query = user_input

        if "[SYSTEM_METADATA]" in user_input:
            file_match = re.search(r"UPLOADED_FILE: (.+)", user_input)
            if file_match and "None" not in file_match.group(1):
                file_name = file_match.group(1).strip()
            
            goal_match = re.search(r"ACTIVE_GOAL: (.+)", user_input)
            if goal_match:
                active_goal_hint = goal_match.group(1).strip()
                
            notes_match = re.search(r"USER_NOTES: (.*?)(?=\[/SYSTEM_METADATA\])", user_input, re.DOTALL)
            if notes_match:
                raw_notes = notes_match.group(1).strip()
                self.user_context = self._parse_context(raw_notes)
                
            if "USER_QUERY:" in user_input:
                clean_user_query = user_input.split("USER_QUERY:")[-1].strip()

        # Goal Detection (3d.1)
        next_goals = []
        if layer == "handover":
            next_goals = self._detect_goals(clean_user_query)
        
        tool_output = ""
        trace_dict = {}

        # 2. RUN TOOLS (Only if layer is handover or memory is empty)
        cache_key = f"{file_name}_{active_goal_hint}"
        if file_name:
            if layer == "handover" or cache_key not in self.context_memory:
                import os
                if not os.path.exists(file_name):
                    return {
                        "response": f"[ERROR] The uploaded file could not be found at {file_name}.",
                        "trace": {},
                        "next_goals": []
                    }
                logger.info(f"📂 Brain: Running Quant Engine on {file_name}")
                tool_output, trace_dict = self.tools.analyze_dataset(file_name, active_goal_hint, getattr(self, 'user_context', {}))
                
                # RAG Integration (3e.3)
                if self.db.collection.count() > 0:
                    rag_res = self.db.query_evidence(clean_user_query, n_results=3)
                    if rag_res and rag_res["documents"] and rag_res["documents"][0]:
                        tool_output += "\n\n**Evidence Quotes:**\n"
                        for q in rag_res["documents"][0]:
                            tool_output += f"- \"{q}\"\n"
                
                self.context_memory[cache_key] = {"tool_output": tool_output, "trace": trace_dict}
            else:
                cached = self.context_memory[cache_key]
                tool_output = cached["tool_output"]
                trace_dict = cached["trace"]

        # Error Guard (3a.2)
        if tool_output and tool_output.startswith("[ERROR]"):
            return {
                "response": tool_output,
                "trace": trace_dict,
                "next_goals": next_goals
            }

        # 3. SYNTHESIS via OutputManager (3b.1)
        draft_stream = self.output_manager.generate_response(
            goal=active_goal_hint, 
            data=tool_output, 
            layer=layer, 
            trace_dict=trace_dict
        )

        # 4. CLARITY GATE (3c.1) (Only run on summary/evidence layers, not handover/deep)
        if layer in ["summary", "evidence"]:
            val_result = self.validator.check_clarity(
                goal=active_goal_hint,
                findings=tool_output,
                user_input=clean_user_query
            )
            
            if val_result.get("escalation_needed"):
                return {
                    "response_stream": draft_stream, 
                    "trace": trace_dict,
                    "next_goals": next_goals,
                    "escalation": val_result
                }

        return {
            "response_stream": draft_stream,
            "trace": trace_dict,
            "next_goals": next_goals,
            "escalation": None
        }

    def _detect_goals(self, user_input: str) -> List[str]:
        # Only detect if there's actually a real query, not just a button click
        if len(user_input.strip()) < 5:
            return []
        prompt = f"Map input to goals: {list(GOAL_DEFINITIONS.keys())}. Return comma-separated list. Input: {user_input}"
        response = self.llm.invoke([SystemMessage(content=SYSTEM_INSTRUCTIONS), HumanMessage(content=prompt)])
        detected = [g.strip() for g in response.content.split(',') if g.strip() in GOAL_DEFINITIONS]
        return detected

    def _parse_context(self, user_notes: str) -> dict:
        context = {}
        if not user_notes or user_notes == "None":
            return context
            
        # Parse price
        price_match = re.search(r"[₹$]\s?(\d+)|priced at (\d+)", user_notes, re.IGNORECASE)
        if price_match:
            price_val = price_match.group(1) if price_match.group(1) else price_match.group(2)
            context["price_target"] = float(price_val)
            
        context["notes"] = user_notes
        return context