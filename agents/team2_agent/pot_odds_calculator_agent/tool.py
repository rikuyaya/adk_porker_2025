from google.adk.tools import FunctionTool
from typing import Dict, Any



def calculate_pot_odds(
    pot_size: float, 
    call_amount: float, 
    equity: float,
    # implied_odds_factor: float = 1.0
) -> Dict[str, Any]:
    """
    ポットオッズを計算し、コールが利益的かどうかを判定します。
    
    Args:
        pot_size: 現在のポットサイズ
        call_amount: コールに必要な金額
        equity: 勝率（0.0-1.0）
    
    Returns:
        Dict[str, Any]: ポットオッズ計算結果と推奨アクション
    """
    # implied_odds_factor: インプライドオッズ係数（デフォルト: 1.0）
    try:
        if call_amount <= 0:
            return {
                "status": "error",
                "error_message": "コール金額は0より大きい必要があります"
            }
        
        if pot_size < 0:
            return {
                "status": "error", 
                "error_message": "ポットサイズは0以上である必要があります"
            }
        
        if not (0.0 <= equity <= 1.0):
            return {
                "status": "error",
                "error_message": "勝率は0.0から1.0の間である必要があります"
            }
        
        # ポットオッズ計算
        total_pot_after_call = pot_size + call_amount
        pot_odds_ratio = call_amount / total_pot_after_call
        pot_odds_percentage = pot_odds_ratio * 100
        
        # 必要勝率（ブレイクイーブン勝率）
        required_equity = pot_odds_ratio
        required_equity_percentage = required_equity * 100
        
        # インプライドオッズを考慮した調整
        # adjusted_required_equity = required_equity / implied_odds_factor
        # adjusted_required_equity_percentage = adjusted_required_equity * 100
        
        # 利益性の判定
        is_profitable = equity >= required_equity
        # is_profitable = equity >= adjusted_required_equity
        
        # 期待値計算
        expected_value = (equity * total_pot_after_call) - call_amount
        
        # マージン計算（どれだけ有利/不利か）
        equity_margin = equity - required_equity
        # equity_margin = equity - adjusted_required_equity
        equity_margin_percentage = equity_margin * 100
        
        # 推奨アクション
        if is_profitable:
            if equity_margin >= 0.05:  # 5%以上のマージン
                recommendation = "strong_call"
                confidence = "高"
            elif equity_margin >= 0.02:  # 2%以上のマージン
                recommendation = "call"
                confidence = "中"
            else:  # わずかに利益的
                recommendation = "marginal_call"
                confidence = "低"
        else:
            if equity_margin <= -0.05:  # 5%以上不利
                recommendation = "strong_fold"
                confidence = "高"
            elif equity_margin <= -0.02:  # 2%以上不利
                recommendation = "fold"
                confidence = "中"
            else:  # わずかに不利
                recommendation = "marginal_fold"
                confidence = "低"
        
        return {
            "status": "success",
            "pot_size": pot_size,
            "call_amount": call_amount,
            "total_pot_after_call": total_pot_after_call,
            "equity": equity,
            "equity_percentage": equity * 100,
            "pot_odds_ratio": pot_odds_ratio,
            "pot_odds_percentage": pot_odds_percentage,
            "required_equity": required_equity,
            "required_equity_percentage": required_equity_percentage,
            # "adjusted_required_equity": adjusted_required_equity,
            # "adjusted_required_equity_percentage": adjusted_required_equity_percentage,
            "is_profitable": is_profitable,
            "expected_value": expected_value,
            "equity_margin": equity_margin,
            "equity_margin_percentage": equity_margin_percentage,
            "recommendation": recommendation,
            "confidence": confidence,
            # "implied_odds_factor": implied_odds_factor,
            "description": _generate_description(
                pot_odds_percentage, 
                equity * 100, 
                recommendation, 
                expected_value,
                confidence
            )
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"ポットオッズ計算エラー: {str(e)}"
        }


def _generate_description(
    pot_odds_percentage: float, 
    equity_percentage: float, 
    recommendation: str, 
    expected_value: float,
    confidence: str
) -> str:
    """結果の説明文を生成"""
    
    action_descriptions = {
        "strong_call": "強いコール推奨",
        "call": "コール推奨", 
        "marginal_call": "ギリギリコール",
        "marginal_fold": "ギリギリフォールド",
        "fold": "フォールド推奨",
        "strong_fold": "強いフォールド推奨"
    }
    
    action_desc = action_descriptions.get(recommendation, recommendation)
    ev_desc = f"+{expected_value:.2f}" if expected_value >= 0 else f"{expected_value:.2f}"
    
    return (
        f"ポットオッズ: {pot_odds_percentage:.1f}%, "
        f"勝率: {equity_percentage:.1f}%, "
        f"推奨: {action_desc} (信頼度: {confidence}), "
        f"期待値: {ev_desc}"
    )


def calculate_reverse_implied_odds(
    pot_size: float,
    call_amount: float, 
    equity: float,
    reverse_implied_factor: float = 0.8
) -> Dict[str, Any]:
    """
    リバースインプライドオッズを考慮したポットオッズ計算
    
    Args:
        pot_size: 現在のポットサイズ
        call_amount: コールに必要な金額
        equity: 勝率（0.0-1.0）
        reverse_implied_factor: リバースインプライド係数（デフォルト: 0.8）
    
    Returns:
        Dict[str, Any]: リバースインプライドオッズを考慮した計算結果
    """
    # 基本のポットオッズ計算
    basic_result = calculate_pot_odds(pot_size, call_amount, equity, 1.0)
    
    if basic_result["status"] == "error":
        return basic_result
    
    # リバースインプライドオッズの調整
    # ドローハンドなどで、ヒットしても相手に負ける可能性を考慮
    adjusted_equity = equity * reverse_implied_factor
    
    # 調整後の計算
    adjusted_result = calculate_pot_odds(pot_size, call_amount, adjusted_equity, 1.0)
    
    if adjusted_result["status"] == "success":
        adjusted_result["original_equity"] = equity
        adjusted_result["reverse_implied_factor"] = reverse_implied_factor
        adjusted_result["description"] = (
            f"リバースインプライド考慮: {adjusted_result['description']} "
            f"(元勝率: {equity*100:.1f}%)"
        )
    
    return adjusted_result


# ADK FunctionToolとして登録
PotOddsCalculator = FunctionTool(func=calculate_pot_odds)
ReverseImpliedOddsCalculator = FunctionTool(func=calculate_reverse_implied_odds)
