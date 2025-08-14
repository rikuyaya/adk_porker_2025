from google.adk.agents import ParallelAgent
from team1_agent.agents.calc_bluff_rate import calc_bluff_rate
from team1_agent.agents.calc_confidence import calc_confidence
from team1_agent.agents.GTO_agent import GTO_agent

analyze_agent = ParallelAgent(
    name="analyze_agent",
    model="gemini-2.5-flash-lite",
    sub_agents=[calc_confidence, calc_bluff_rate, GTO_agent],
    description=("Runs multiple agents in parallel to analyze the situation.")
)