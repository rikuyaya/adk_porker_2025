from google.adk.agents import SequentialAgent
# from team1_agent.agents.analyze_agent import analyze_agent
from team1_agent.agents.decision_agent import decision_agent

pipeline_agent = SequentialAgent(
    name="pipeline_agent",
    model="gemini-2.5-flash-lite",
    sub_agents=[decision_agent], #analyze_agent, 
    description=("Coordinating agents to analyze the situation and make a decision.")
)