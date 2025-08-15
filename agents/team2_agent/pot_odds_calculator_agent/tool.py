from google.adk.tools import FunctionTool
from typing import Tuple

def calculate_poker_metrics(
    pot_size: float, 
    call_amount: float, 
    equity: float,
) -> Tuple[float, float, float]:
    """
    ポットオッズ、期待値、およびインプライドオッズに関連する指標を計算します。
    
    Args:
        pot_size: float 現在のポットサイズ
        call_amount: float コールに必要な金額
        equity: float ハンドの勝率 (0.0 ~ 1.0)
        
    Returns:
        Tuple[float, float, float]: 
        (期待値, 必要勝率, 追加で必要な獲得額)
    """
    if call_amount == 0:
        # チェック可能な状況では、これらの計算は不要
        return (equity * pot_size, 0.0, 0.0)

    # --- 1. 必要勝率 (Pot Odds) の計算 ---
    # コールした後の合計ポット = 現在のポット + 相手のベット + 自分のコール
    total_pot_after_call = pot_size + call_amount + call_amount
    # エラー回避
    if total_pot_after_call == 0:
        return 0.0, 0.0, 0.0
    
    required_equity = call_amount / total_pot_after_call
    
    # --- 2. 期待値 (EV) の計算 ---
    # 勝った時に得られる利益 = 現在のポット + 相手のベット
    winnings = pot_size + call_amount
    # 負けた時に失う損失 = 自分のコール額
    loss = call_amount
    
    expected_value = (equity * winnings) - ((1 - equity) * loss)

    # --- 3. 追加で必要な獲得額 (Required Implied Amount) の計算 ---
    # 現在のオッズではコールが割に合わない場合 (EVがマイナスの場合)に、
    # このコールを正当化するために、後のラウンドでいくら追加で勝つ必要があるかを示す。
    required_implied_amount = 0.0
    if expected_value < 0:
        # (コール額 / 勝率) が、損益分岐点となるポットの総額
        breakeven_pot_size = call_amount / equity
        required_implied_amount = breakeven_pot_size - (pot_size + call_amount + call_amount)
        
    return expected_value, required_equity, max(0, required_implied_amount)


# ADK FunctionToolとして登録
PokerMetricsCalculator = FunctionTool(func=calculate_poker_metrics)