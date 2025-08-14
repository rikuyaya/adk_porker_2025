"""
結果統合レイヤー: 各ツールの結果を統合して最終アクションを決定
"""

from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


def integrate_tool_results(
    equity_result: Dict[str, Any],
    pot_odds_result: Dict[str, Any],
    gto_result: Dict[str, Any],
    sizing_result: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    各ツールの結果を統合して最終アクションを決定
    
    Args:
        equity_result: EquityCalculatorの結果
        pot_odds_result: PotOddsCalculatorの結果
        gto_result: GtoPreflopChartToolの結果
        sizing_result: SizingToolの結果
        context: ゲーム状況のコンテキスト
    
    Returns:
        最終的なアクション決定
    """
    try:
        available_actions = context.get("available_actions", [])
        phase = context.get("phase", "preflop")
        your_chips = context.get("your_chips", 1000)
        
        # 各ツールの結果を検証
        equity = _extract_equity(equity_result)
        pot_odds_decision = _extract_pot_odds_decision(pot_odds_result)
        gto_decision = _extract_gto_decision(gto_result, phase)
        sizing_info = _extract_sizing_info(sizing_result)
        
        # 統合的な意思決定
        final_decision = _make_integrated_decision(
            equity, pot_odds_decision, gto_decision, sizing_info,
            available_actions, phase, your_chips, context
        )
        
        # 詳細な理由を生成
        reasoning = _generate_detailed_reasoning(
            equity_result, pot_odds_result, gto_result, sizing_result,
            final_decision, context
        )
        
        return {
            "action": final_decision["action"],
            "amount": final_decision["amount"],
            "reasoning": reasoning
        }
    
    except Exception as e:
        logger.error(f"Result integration error: {e}")
        from .data_converter import get_fallback_action
        return get_fallback_action(context.get("available_actions", []), context)


def _extract_equity(equity_result: Dict[str, Any]) -> Dict[str, Any]:
    """勝率計算結果から重要な情報を抽出"""
    if equity_result.get("status") != "success":
        return {"equity": 0.5, "confidence": "低", "hand_category": "不明"}
    
    return {
        "equity": equity_result.get("equity", 0.5),
        "hand_strength": equity_result.get("hand_strength", 0.5),
        "hand_category": equity_result.get("hand_category", "不明"),
        "confidence": equity_result.get("confidence", "低"),
        "outs": equity_result.get("outs", 0)
    }


def _extract_pot_odds_decision(pot_odds_result: Dict[str, Any]) -> Dict[str, Any]:
    """ポットオッズ計算結果から決定情報を抽出"""
    if pot_odds_result.get("status") != "success":
        return {"recommendation": "fold", "confidence": "低", "profitable": False}
    
    return {
        "recommendation": pot_odds_result.get("recommendation", "fold"),
        "confidence": pot_odds_result.get("confidence", "低"),
        "profitable": pot_odds_result.get("is_profitable", False),
        "expected_value": pot_odds_result.get("expected_value", 0),
        "equity_margin": pot_odds_result.get("equity_margin_percentage", 0)
    }


def _extract_gto_decision(gto_result: Dict[str, Any], phase: str) -> Dict[str, Any]:
    """GTO決定結果から情報を抽出"""
    if gto_result.get("status") != "success" or phase != "preflop":
        return {"recommendation": "fold", "frequency": 0, "tier": "weak"}
    
    return {
        "recommendation": gto_result.get("recommended_action", "fold"),
        "frequency": gto_result.get("action_frequency", 0),
        "tier": gto_result.get("hand_strength_tier", "weak"),
        "alternatives": gto_result.get("alternative_actions", [])
    }


def _extract_sizing_info(sizing_result: Dict[str, Any]) -> Dict[str, Any]:
    """ベットサイズ情報を抽出"""
    if sizing_result.get("status") != "success":
        return {"size": 0, "category": "スモール", "goal": "不明"}
    
    return {
        "recommended_size": sizing_result.get("recommended_size", 0),
        "size_category": sizing_result.get("size_category", "スモール"),
        "strategic_goal": sizing_result.get("strategic_goal", "不明"),
        "pot_percentage": sizing_result.get("pot_percentage", 50)
    }


def _make_integrated_decision(
    equity: Dict[str, Any],
    pot_odds: Dict[str, Any], 
    gto: Dict[str, Any],
    sizing: Dict[str, Any],
    available_actions: List[str],
    phase: str,
    your_chips: int,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """統合的な意思決定を行う"""
    
    equity_value = equity.get("equity", 0.5)
    hand_strength = equity.get("hand_strength", 0.5)
    
    # アクション候補の評価
    action_scores = {}
    
    # 各アクションを評価
    for action_str in available_actions:
        action_type = _parse_action_type(action_str)
        score = _calculate_action_score(
            action_type, action_str, equity_value, hand_strength,
            pot_odds, gto, sizing, phase, context
        )
        action_scores[action_str] = score
    
    # 最高スコアのアクションを選択
    if not action_scores:
        return {"action": "fold", "amount": 0}
    
    best_action_str = max(action_scores.items(), key=lambda x: x[1])[0]
    best_action = _parse_action_details(best_action_str, sizing, your_chips)
    
    return best_action


def _parse_action_type(action_str: str) -> str:
    """アクション文字列からタイプを抽出"""
    action_lower = action_str.lower()
    if "fold" in action_lower:
        return "fold"
    elif "check" in action_lower:
        return "check"
    elif "call" in action_lower:
        return "call"
    elif "raise" in action_lower:
        return "raise"
    elif "all-in" in action_lower or "all_in" in action_lower:
        return "all_in"
    else:
        return "fold"


def _calculate_action_score(
    action_type: str, action_str: str, equity: float, hand_strength: float,
    pot_odds: Dict[str, Any], gto: Dict[str, Any], sizing: Dict[str, Any],
    phase: str, context: Dict[str, Any]
) -> float:
    """各アクションのスコアを計算"""
    
    base_score = 0.0
    
    # エクイティベースのスコア
    if action_type == "fold":
        base_score = 0.1 if equity < 0.3 else -0.5
    elif action_type == "check":
        base_score = 0.3 if 0.3 <= equity <= 0.6 else 0.1
    elif action_type == "call":
        # ポットオッズの推奨を重視
        if pot_odds.get("profitable", False):
            base_score = 0.7 + pot_odds.get("equity_margin", 0) / 100
        else:
            base_score = 0.2
    elif action_type == "raise":
        base_score = 0.8 if equity > 0.6 else (0.4 if equity > 0.4 else 0.1)
    elif action_type == "all_in":
        base_score = 0.9 if equity > 0.8 else (0.3 if equity > 0.6 else 0.05)
    
    # GTOの推奨を考慮（プリフロップのみ）
    if phase == "preflop" and gto.get("recommendation") == action_type:
        gto_frequency = gto.get("frequency", 0) / 100
        base_score += gto_frequency * 0.3
    
    # ポットオッズの推奨を考慮
    pot_odds_rec = pot_odds.get("recommendation", "fold")
    if _action_matches_recommendation(action_type, pot_odds_rec):
        confidence_bonus = {"高": 0.3, "中": 0.2, "低": 0.1}.get(pot_odds.get("confidence", "低"), 0.1)
        base_score += confidence_bonus
    
    return max(0.0, min(1.0, base_score))


def _action_matches_recommendation(action_type: str, recommendation: str) -> bool:
    """アクションが推奨と一致するかチェック"""
    rec_lower = recommendation.lower()
    if "call" in rec_lower and action_type == "call":
        return True
    elif "fold" in rec_lower and action_type == "fold":
        return True
    elif "raise" in rec_lower and action_type == "raise":
        return True
    return False


def _parse_action_details(action_str: str, sizing: Dict[str, Any], your_chips: int) -> Dict[str, Any]:
    """アクション文字列から詳細情報を抽出"""
    action_type = _parse_action_type(action_str)
    
    if action_type in ["fold", "check"]:
        return {"action": action_type, "amount": 0}
    
    elif action_type == "call":
        # "call (20)" から金額を抽出
        match = re.search(r"call \((\d+)\)", action_str)
        amount = int(match.group(1)) if match else 0
        return {"action": "call", "amount": amount}
    
    elif action_type == "raise":
        # "raise (min 40)" から最低額を抽出
        match = re.search(r"raise.*min (\d+)", action_str)
        min_raise = int(match.group(1)) if match else 0
        
        # サイジングツールの推奨を使用
        recommended_size = sizing.get("recommended_size", min_raise)
        final_amount = max(min_raise, int(recommended_size))
        final_amount = min(final_amount, your_chips)  # チップ制限
        
        return {"action": "raise", "amount": final_amount}
    
    elif action_type == "all_in":
        return {"action": "all_in", "amount": your_chips}
    
    else:
        return {"action": "fold", "amount": 0}


def _generate_detailed_reasoning(
    equity_result: Dict[str, Any],
    pot_odds_result: Dict[str, Any], 
    gto_result: Dict[str, Any],
    sizing_result: Dict[str, Any],
    final_decision: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """詳細な判断理由を生成"""
    
    reasoning_parts = []
    
    # エクイティ情報
    if equity_result.get("status") == "success":
        equity = equity_result.get("equity", 0.5)
        hand_category = equity_result.get("hand_category", "不明")
        reasoning_parts.append(f"ハンド強度: {hand_category} (勝率 {equity:.1%})")
    
    # ポットオッズ情報
    if pot_odds_result.get("status") == "success":
        recommendation = pot_odds_result.get("recommendation", "fold")
        expected_value = pot_odds_result.get("expected_value", 0)
        reasoning_parts.append(f"ポットオッズ分析: {recommendation}推奨 (期待値 {expected_value:+.1f})")
    
    # GTO情報（プリフロップのみ）
    if context.get("phase") == "preflop" and gto_result.get("status") == "success":
        gto_action = gto_result.get("recommended_action", "fold")
        frequency = gto_result.get("action_frequency", 0)
        tier = gto_result.get("hand_strength_tier", "weak")
        reasoning_parts.append(f"GTO戦略: {tier}ハンドで{gto_action} ({frequency}%)")
    
    # サイジング情報
    if final_decision["action"] in ["raise", "bet"] and sizing_result.get("status") == "success":
        size_category = sizing_result.get("size_category", "ミディアム")
        strategic_goal = sizing_result.get("strategic_goal", "不明")
        reasoning_parts.append(f"ベットサイズ: {size_category} ({strategic_goal})")
    
    # 最終決定の理由
    action = final_decision["action"]
    amount = final_decision["amount"]
    
    if action == "fold":
        reasoning_parts.append("総合判断: リスクが高すぎるためフォールド")
    elif action == "check":
        reasoning_parts.append("総合判断: 様子見のためチェック")
    elif action == "call":
        reasoning_parts.append(f"総合判断: {amount}でコール（ポットオッズ有利）")
    elif action == "raise":
        reasoning_parts.append(f"総合判断: {amount}にレイズ（バリュー/プロテクション）")
    elif action == "all_in":
        reasoning_parts.append("総合判断: オールイン（最大バリュー追求）")
    
    return " | ".join(reasoning_parts)
