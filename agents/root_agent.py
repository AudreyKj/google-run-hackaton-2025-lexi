from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents import Agent
from agents.clause_analysis.extractor_agent import extractor_agent
from agents.clause_analysis.standard_clause_retriever_agent import standard_clause_retriever_agent
from agents.clause_analysis.clause_comparison_agent import clause_comparison_agent
from agents.clause_analysis.risk_analysis_agent import risk_analysis_agent
from utils.block_keyword_guardrails import block_keyword_guardrail
from utils.constants import MODEL_GEMINI_2_0_FLASH

workflow_agent = SequentialAgent(
    name="ClauseAnalysisWorkflow",
    sub_agents=[extractor_agent, standard_clause_retriever_agent, clause_comparison_agent, risk_analysis_agent],
    description="Executes a sequence of clause extraction, standard clause retrieval, comparison, and risk analysis: you should call these agents in order to analyze contract clauses and pass the output of one as the input to the next.",
)

root_agent = Agent(
        name="lexi_root_agent", 
        model=MODEL_GEMINI_2_0_FLASH,  
        description="Main agent: Delegates to workflow agent, includes guardrails.",
        instruction="You are the root agent: delegate to the ClauseAnalysisWorkflow agent to analyze contract clauses. Ensure all guardrails are enforced.",
        sub_agents=[workflow_agent],
        before_model_callback=block_keyword_guardrail,
    )