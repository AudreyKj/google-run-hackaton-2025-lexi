from google.adk.agents.sequential_agent import SequentialAgent
from agents.clause_analysis.extractor_agent import extractor_agent
from agents.clause_analysis.standard_clause_retriever_agent import standard_clause_retriever_agent
from agents.clause_analysis.clause_comparison_agent import clause_comparison_agent
from agents.clause_analysis.risk_analysis_agent import risk_analysis_agent

# ==== Root orchestrator =

core_orchestrator_agent = SequentialAgent(
    name="ClauseAnalysisWorkflow",
    sub_agents=[extractor_agent, standard_clause_retriever_agent, clause_comparison_agent, risk_analysis_agent],
    description="Executes a sequence of clause extraction, standard clause retrieval, comparison, and risk analysis: you should call these agents in order to analyze contract clauses and pass the output of one as the input to the next.",
    # The agents will run in the order provided: Extractor -> Standard Clause Retriever -> Comparator -> Risk Analyzer
)