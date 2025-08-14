from google.adk.tools import FunctionTool
from typing import Tuple


def calculate_pot_odds(
    pot_size: float, 
    call_amount: float, 
    equity: float,


) -> Tuple[float, float, float, float]:
    """
    ポットオッズの包括的計算
    
    Args:
        pot_size: float 現在のポットサイズ
        call_amount: float コールに必要な金額
        equity: float 先ほどのエージェントから算出した勝率
        

    Returns:
        Tuple[float, float, float, float]: 
        (期待値, 必要勝率, リバースインプライド期待値, インプライド倍率)
    """
    # 期待値計算
    total_pot_after_call = pot_size + call_amount
    expected_value = (equity * total_pot_after_call ) - call_amount
    
    # 必要勝率計算
    required_equity = call_amount / total_pot_after_call
    
    # リバースインプライド期待値計算
    adjusted_equity = equity
    reverse_expected_value = (adjusted_equity * total_pot_after_call) - call_amount
    
    # インプライド倍率計算
    total_potential_winnings = pot_size + call_amount 
    basic_pot_odds = call_amount / (pot_size + call_amount)
    implied_pot_odds = call_amount / total_potential_winnings if total_potential_winnings > 0 else basic_pot_odds
    implied_multiplier = basic_pot_odds / implied_pot_odds if implied_pot_odds > 0 else 1.0
    
    return expected_value, required_equity, reverse_expected_value, implied_multiplier


# ADK FunctionToolとして登録
PotOddsCalculator = FunctionTool(func=calculate_pot_odds)