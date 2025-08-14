from google.adk.agents import Agent

# Import all the tool objects from the 'tools' package
from .tools.state_parser import ParseGameState
from .tools.pot_odds_calculator import PotOddsTool
from .tools.range_provider import PokerActionTool
from .tools.equity_simulator import EquityTool
from .tools.sizing_policy import SizingTool
from .tools.result_integrator import IntegratorTool

# Name of the agent
NAME = "team3_agent"
# Definition of the poker agent
root_agent = Agent(
    name=NAME,
    model="gemini-2.5-flash",
    description="Poker decision assistant",
    instruction="""Poker decision assistant. Follow this pipeline:
1. parse_game_state(input) → state (IMPORTANT: Pass the input JSON string exactly as received, do not escape quotes)
2. calculate_pot_odds(state) → pot_odds
3. get_poker_action(state) → mix
4. calculate_equity(state, []) → equity
5. decide_bet_size(state, mix) → sizing
6. integrate_tool_results(state, pot_odds, mix, equity, sizing) → final_action

    【出力形式】
    必ず次のJSON形式で回答してください：
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
      "reasoning": "各エージェントの分析結果を踏まえた決定理由を詳細に説明"
    }
"""
,



    tools=[
        ParseGameState,
        PotOddsTool,
        PokerActionTool,
        EquityTool,
        SizingTool,
        IntegratorTool
    ]
)