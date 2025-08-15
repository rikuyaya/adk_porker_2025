import json
import random
from typing import Dict, Any

from google.adk.tools import ToolContext, FunctionTool

def integrate_tool_results(
    state: str,
    pot_odds: str,
    mix: str,
    equity: str,
    sizing: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    期待値近似: EV(action) ≈ FE*pot_gain + (1-FE)*(equity*final_pot - cost)
    mix頻度も踏まえ最終アクションをargmaxで決定
    """
    # JSON文字列をパース
    state = json.loads(state)
    pot_odds = json.loads(pot_odds)
    mix = json.loads(mix)
    equity = json.loads(equity)
    sizing = json.loads(sizing)

    action_mix = mix.get("mix")

    # デバッグ情報
    debug_info = f"DEBUG: mix={mix}, action_mix={action_mix}"
    if action_mix:
        debug_info += f", sum={sum(action_mix.values())}"

    if not action_mix or sum(action_mix.values()) == 0:
        # フォールバックとして、ミックスが提供されない場合はフォールドする
        return {"action": "fold", "amount": 0, "reasoning": f"No valid action mix provided by range tool. {debug_info}"}

    # argmaxを使用して、最も頻度の高いアクションを決定論的に選択する
    chosen_action = max(action_mix, key=action_mix.get)

    amount = 0
    reasoning = f"Provided range suggests a mixed strategy: {action_mix}. "
    reasoning += f"Chose the most frequent action (argmax): '{chosen_action}'. "

    if chosen_action == "raise":
        amount = sizing.get("raise_amount", 0)
        reasoning += f"Sizing tool recommends a raise to {amount}."
    elif chosen_action == "call":
        amount = state.get("to_call", 0)
        reasoning += f"The amount to call is {amount}."
    elif chosen_action == "fold":
        amount = 0
        reasoning += "Action is to fold."

    return {"action": chosen_action, "amount": amount, "reasoning": reasoning}

IntegratorTool = FunctionTool(func=integrate_tool_results)