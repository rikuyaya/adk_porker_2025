import json
from typing import Dict, Any
from google.adk.tools import ToolContext, FunctionTool

def parse_game_state(game_state_json: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    入力JSONを解析し、phase/position/pot/to_call/actions等を正規化
    Returns: {"phase":..., "pos":"BTN", "pot":..., "to_call":..., "actions":[...], ...}
    """
    # 二重エスケープ問題の対処
    try:
        game_state = json.loads(game_state_json)
    except json.JSONDecodeError:
        # 二重エスケープされている可能性があるので修正を試行
        try:
            # バックスラッシュエスケープを除去
            cleaned_json = game_state_json.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            game_state = json.loads(cleaned_json)
        except json.JSONDecodeError:
            # それでもダメな場合は、さらに積極的な修正
            import re
            # 二重エスケープパターンを修正
            fixed_json = re.sub(r'\\(.)', r'\1', game_state_json)
            game_state = json.loads(fixed_json)

    # 実際の入力形式に対応
    your_id = game_state.get("your_id")
    if your_id is None:
        raise ValueError("'your_id' not found in game state JSON.")

    players = game_state.get("players", [])
    dealer_button = game_state.get("dealer_button", 0)

    # プレイヤー数から自分のポジションを推定
    num_players = len(players) + 1  # 自分を含む

    # 簡単なポジション推定
    if num_players == 2:
        my_position = "BTN" if your_id == dealer_button else "BB"
    else:
        # 3人以上の場合の簡単な推定
        position_names = ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        relative_pos = (your_id - dealer_button) % num_players
        my_position = position_names[min(relative_pos, len(position_names) - 1)]

    # コールする金額を取得
    to_call = game_state.get("to_call", 0)

    normalized = {
        "phase": game_state.get("phase"),
        "position": my_position,
        "pot": game_state.get("pot"),
        "to_call": to_call,
        "your_chips": game_state.get("your_chips"),
        "your_cards": game_state.get("your_cards"),
        "community": game_state.get("community", []),
        "actions": game_state.get("actions", []),
        "players": players,
        "dealer_button": dealer_button,
        "your_id": your_id,
        "history": game_state.get("history", [])
    }

    return normalized

ParseGameState = FunctionTool(func=parse_game_state)