from typing import Dict, Any, List
from google.adk.tools import ToolContext, FunctionTool
from .pokerkit_utils import safe_json_loads, get_hand_string, get_community_string, simulate_equity


def calculate_equity(state: str, villain_range: List[str], tool_context: ToolContext) -> Dict[str, float]:
    """
    PokerKitを使用して正確なエクイティを計算する。
    Returns: {"equity": 0.47}
    """
    # JSON文字列をパース
    game_data = safe_json_loads(state)

    # PokerKitの文字列形式でカードを取得
    hole_cards_str = get_hand_string(game_data)
    community_cards_str = get_community_string(game_data)

    if len(hole_cards_str) < 4:  # 2枚 * 2文字 = 4文字
        return {"equity": 0.0}

    # 相手の数を推定
    players = game_data.get("players", [])
    num_opponents = len(players)
    if num_opponents == 0:
        num_opponents = 1  # 最低1人の相手

    # PokerKitでエクイティをシミュレーション
    equity = simulate_equity(
        hole_cards_str=hole_cards_str,
        community_cards_str=community_cards_str,
        num_opponents=num_opponents,
        simulations=1000
    )

    return {"equity": equity}



EquityTool = FunctionTool(func=calculate_equity)