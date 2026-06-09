import logging
from typing import List, Dict, Any, Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent_reasoning.prompts.system_persona import SYSTEM_INSTRUCTIONS

logger = logging.getLogger("OutputManager")

class OutputManager:
    def __init__(self, model_name="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)

    def generate_response(self, goal: str, data: str, layer: str = "summary", trace_dict: dict = None) -> Generator[str, None, None]:
        """
        Router for Progressive Disclosure & Traceability.
        
        Layers:
        - 'handover': The "I'm Ready" signal. Used immediately after data processing.
        - 'summary': High-level Executive Summary (BLUF).
        - 'evidence': Detailed answer with Logic Trace (How I found it).
        - 'deep_research': Raw data dump.
        """
        if trace_dict is None:
            trace_dict = {}

        logger.info(f"📝 Generating Output. Layer: {layer}")

        if layer == "handover":
            yield from self._generate_handover(goal, data, trace_dict)
        elif layer == "summary":
            yield from self._generate_layer_1(goal, data, trace_dict)
        elif layer == "evidence":
            yield from self._generate_layer_2(goal, data, trace_dict)
        elif layer == "deep_research":
            yield from self._generate_layer_3(data, trace_dict)
        else:
            yield from self._generate_layer_1(goal, data, trace_dict) # Default fallback

    def _generate_handover(self, goal: str, data: str, trace_dict: dict):
        """
        NEW: The 'Ready State' message.
        Does NOT give the full solution. Just summarizes the *effort* and invites questions.
        """
        template = """
        CONTEXT:
        - Goal: {goal}
        - Trace Data: {trace_dict}
        - Key Data Points Found: {data}
        
        TASK:
        Write a brief "readout / briefing" ping.
        1. Confirm the analysis is complete.
        2. Mention 2-3 interesting areas you detected.
        3. DO NOT give the full report yet.
        4. End by stating the full brief is ready to be explored.
        """
        
        content = template.format(goal=goal, trace_dict=trace_dict, data=str(data))
        for chunk in self.llm.stream([SystemMessage(content=SYSTEM_INSTRUCTIONS), HumanMessage(content=content)]):
            yield chunk.content

    def _generate_layer_1(self, goal, data, trace_dict):
        """Layer 1: The Executive Summary (BLUF)."""
        template = """
        Draft a tight 5-7 sentence "Clarity Summary" (Executive Brief).
        
        GOAL: {goal}
        TRACE DICT: {trace_dict}
        DATA: {data}
        
        RULES:
        1. Start with the Direct Answer / Verdict.
        2. Highlight the #1 Risk clearly.
        3. Every numeric claim MUST end with `[Source: <tool> on <file>]` where <tool> and <file> come from the TRACE DICT.
        """
        content = template.format(goal=goal, trace_dict=trace_dict, data=str(data))
        for chunk in self.llm.stream([SystemMessage(content=SYSTEM_INSTRUCTIONS), HumanMessage(content=content)]):
            yield chunk.content

    def _generate_layer_2(self, goal, data, trace_dict):
        """
        Layer 2: Evidence & Logic Traceability.
        This answers the user's need for "How did you figure this out?".
        """
        template = """
        You are explaining your research findings as a long-form brief.
        
        GOAL: {goal}
        TRACE DICT: {trace_dict}
        DATA FINDINGS: {data}
        
        INSTRUCTIONS:
        Draft a comprehensive brief using EXACTLY these 6 sections:
        1. **Bottom line** (The primary takeaway)
        2. **What the numbers say — and why each one matters** (Interpret every number; do not merely restate it)
        3. **Practical scenarios** (2-3 concrete situations grounded in the data)
        4. **What-if analysis** (Read from trace_dict["scenarios"] and explain implications)
        5. **Risks & data gaps** (Explicitly call out what we don't know or gaps in context)
        6. **What to investigate next**
        
        RULES:
        1. **Show Your Work (Traceability):** Explicitly mention which numbers you used.
        2. Every numeric claim MUST end with `[Source: <tool> on <file>]` using the TRACE DICT.
        """
        content = template.format(goal=goal, trace_dict=trace_dict, data=str(data))
        for chunk in self.llm.stream([SystemMessage(content=SYSTEM_INSTRUCTIONS), HumanMessage(content=content)]):
            yield chunk.content

    def _generate_layer_3(self, data, trace_dict):
        """Layer 3: Deep Data (Raw)."""
        yield f"### 📊 DEEP DATA VIEW\n\n**Trace Data:**\n```json\n{trace_dict}\n```\n\n**Raw Data:**\n```json\n{data}\n```"