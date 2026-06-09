import logging
from langchain_openai import ChatOpenAI
# UPDATED IMPORTS for modern LangChain compatibility
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Setup Logger
logger = logging.getLogger("ClarityValidator")

class ClarityAssessment(BaseModel):
    question_coverage: bool = Field(description="Are the core questions of the goal answered?")
    risk_visibility: bool = Field(description="Are key risks and trade-offs explicitly surfaced?")
    structural_understanding: bool = Field(description="Are insights organized and structured?")
    diminishing_returns: bool = Field(description="Would more analysis only add minor details?")
    missing_info_type: str = Field(description="One of: 'None', 'Type A' (Priority), 'Type B' (Summary), 'Type C' (Data Gap)")
    reasoning: str = Field(description="Brief explanation of the assessment.")

class ClarityValidator:
    def __init__(self, model_name="gpt-4-turbo"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=ClarityAssessment)

    def check_clarity(self, goal: str, findings: dict, user_input: str) -> dict:
        """
        Runs the 4-Signal Clarity Check.
        """
        logger.info(f"🔍 Validating Clarity for {goal}...")

        template = """
        You are the Quality Assurance Judge. Determine if the user has "Sufficient Clarity".
        
        CONTEXT:
        User Goal: {goal}
        User Query: "{user_input}"
        Current Findings: {findings}

        INSTRUCTIONS:
        1. Check Question Coverage.
        2. Check Risk Visibility (CRITICAL).
        3. Check Structure.
        4. Check Diminishing Returns.
        
        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_template(template)
        
        for attempt in range(2):
            try:
                _input = prompt.format_prompt(
                    goal=goal,
                    user_input=user_input,
                    findings=str(findings)[:2000],
                    format_instructions=self.parser.get_format_instructions()
                )
                # Invoke properly with messages
                output = self.llm.invoke(_input.to_messages())
                assessment = self.parser.parse(output.content)

                # STRICT CLARITY LOGIC
                is_clear = all([
                    assessment.question_coverage,
                    assessment.risk_visibility,
                    assessment.structural_understanding,
                    assessment.diminishing_returns
                ])

                escalation_needed = False
                escalation_type = None

                if not is_clear:
                    if assessment.missing_info_type == "Type A":
                        escalation_needed = True
                        escalation_type = "prioritization"
                    elif assessment.missing_info_type == "Type B":
                        escalation_needed = True
                        escalation_type = "summary"
                    # Type C (Data Gap) does not escalate; it stops naturally.

                return {
                    "is_clear": is_clear,
                    "escalation_needed": escalation_needed,
                    "escalation_type": escalation_type,
                    "reason": assessment.reasoning
                }

            except Exception as e:
                logger.error(f"Validation failed on attempt {attempt+1}: {e}")
                if attempt == 1:
                    # Fallback to "Not Clear" but safe if LLM fails
                    return {"is_clear": False, "escalation_needed": False, "escalation_type": None, "reason": "Validation Error"}