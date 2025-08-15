import json
import ast
from typing import Dict, Any
from google.adk.tools import ToolContext, FunctionTool

def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """
    LLMが生成する様々な形式の文字列を安全にパースする
    """
    try:
        # 通常のJSONパース
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Pythonの辞書文字列として評価（シングルクォート対応）
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError):
            # 最後の手段：シングルクォートを単純置換
            fixed_str = json_str.replace("'", '"')
            return json.loads(fixed_str)

def calculate_pot_odds(state: str, tool_context: ToolContext) -> Dict[str, float]:
    """
    ポットオッズとSPR（Stack-to-Pot Ratio）を計算する。
    """
    # JSON文字列をパース（シングルクォート問題の対処）
    state = safe_json_loads(state)

    pot = state.get("pot", 0)
    to_call = state.get("to_call", 0)
    eff_stack = state.get("your_chips", 0)

    pot_after_call = pot + to_call

    pot_odds = to_call / pot_after_call if pot_after_call > 0 and to_call > 0 else 0.0

    # If the pot is 0 (or pot after call is 0), SPR is effectively infinite.
    # Use a large number instead of infinity for JSON compatibility
    spr = eff_stack / pot_after_call if pot_after_call > 0 else 999.0

    return {"pot_odds": pot_odds, "spr": spr}

PotOddsTool = FunctionTool(func=calculate_pot_odds)