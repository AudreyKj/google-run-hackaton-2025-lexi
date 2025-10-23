from google.adk.agents.sequential_agent import SequentialAgent
from agents.clause_analysis.extractor_agent import extractor_agent
from agents.clause_analysis.comparison_agent import comparison_agent
from agents.clause_analysis.risk_analysis_agent import risk_analysis_agent


clause_analysis_workflow_agent = SequentialAgent(
    name="ClauseAnalysisWorkflow",
    sub_agents=[extractor_agent, comparison_agent, risk_analysis_agent],
    description="Executes a sequence of clause extraction, comparison, and risk analysis.",
    # The agents will run in the order provided: Extractor -> Comparator -> Risk Analyzer
)
