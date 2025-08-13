from google.adk.tools import FunctionTool
from typing import Dict, Any, List


def calculate_bet_sizing(
    pot_size: float,
    hand_strength: float,
    board_texture: str,
    position: str,
    action_type: str = "bet",
    num_opponents: int = 1,
    stack_depth: int = 100
) -> Dict[str, Any]:
    """
    適切なベットサイズを計算します。
    
    Args:
        pot_size: 現在のポットサイズ
        hand_strength: ハンド強度（0.0-1.0）
        board_texture: ボードテクスチャ（"dry", "wet", "coordinated"）
        position: ポジション（"IP", "OOP"）
        action_type: アクションタイプ（"bet", "raise", "3bet"）
        num_opponents: 対戦相手数
        stack_depth: スタック深度（BBの倍数）
    
    Returns:
        Dict[str, Any]: 推奨ベットサイズと戦略的理由
    """
    try:
        # 入力検証
        if pot_size <= 0:
            return {
                "status": "error",
                "error_message": "ポットサイズは0より大きい必要があります"
            }
        
        if not (0.0 <= hand_strength <= 1.0):
            return {
                "status": "error",
                "error_message": "ハンド強度は0.0から1.0の間である必要があります"
            }
        
        valid_textures = ["dry", "wet", "coordinated"]
        if board_texture not in valid_textures:
            return {
                "status": "error",
                "error_message": f"ボードテクスチャは{valid_textures}のいずれかである必要があります"
            }
        
        # ベットサイズ計算
        sizing_result = _calculate_optimal_sizing(
            pot_size, hand_strength, board_texture, position, 
            action_type, num_opponents, stack_depth
        )
        
        return {
            "status": "success",
            "pot_size": pot_size,
            "hand_strength": hand_strength,
            "board_texture": board_texture,
            "position": position,
            "action_type": action_type,
            "num_opponents": num_opponents,
            "recommended_size": sizing_result["size"],
            "size_category": sizing_result["category"],
            "pot_percentage": sizing_result["pot_percentage"],
            "alternative_sizes": sizing_result["alternatives"],
            "reasoning": sizing_result["reasoning"],
            "strategic_goal": sizing_result["goal"],
            "description": f"{sizing_result['category']}ベット: {sizing_result['size']:.0f} (ポットの{sizing_result['pot_percentage']:.0f}%) - {sizing_result['reasoning']}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"ベットサイズ計算エラー: {str(e)}"
        }


def _calculate_optimal_sizing(
    pot_size: float, hand_strength: float, board_texture: str, 
    position: str, action_type: str, num_opponents: int, stack_depth: int
) -> Dict[str, Any]:
    """最適なベットサイズを計算"""
    
    # 基本サイズの決定
    base_sizing = _get_base_sizing(hand_strength, board_texture, action_type)
    
    # ポジション調整
    position_adjustment = _get_position_adjustment(position, board_texture)
    
    # 対戦相手数調整
    opponent_adjustment = _get_opponent_adjustment(num_opponents)
    
    # スタック深度調整
    stack_adjustment = _get_stack_adjustment(stack_depth, pot_size)
    
    # 最終サイズ計算
    adjusted_percentage = base_sizing["percentage"] * position_adjustment * opponent_adjustment * stack_adjustment
    adjusted_percentage = max(0.25, min(2.0, adjusted_percentage))  # 25%-200%の範囲に制限
    
    final_size = pot_size * adjusted_percentage
    
    # サイズカテゴリの決定
    category = _categorize_bet_size(adjusted_percentage)
    
    # 代替サイズの提案
    alternatives = _generate_alternative_sizes(pot_size, adjusted_percentage, hand_strength, board_texture)
    
    # 戦略的目標の決定
    strategic_goal = _determine_strategic_goal(hand_strength, board_texture, adjusted_percentage)
    
    # 理由の生成
    reasoning = _generate_sizing_reasoning(
        hand_strength, board_texture, position, num_opponents, 
        category, strategic_goal
    )
    
    return {
        "size": final_size,
        "category": category,
        "pot_percentage": adjusted_percentage * 100,
        "alternatives": alternatives,
        "reasoning": reasoning,
        "goal": strategic_goal
    }


def _get_base_sizing(hand_strength: float, board_texture: str, action_type: str) -> Dict[str, Any]:
    """基本ベットサイズの決定"""
    
    if action_type == "bet":
        if hand_strength >= 0.8:  # 非常に強いハンド
            if board_texture == "dry":
                return {"percentage": 0.75, "reasoning": "バリューを最大化"}
            elif board_texture == "wet":
                return {"percentage": 0.85, "reasoning": "プロテクションとバリュー"}
            else:  # coordinated
                return {"percentage": 0.90, "reasoning": "強いプロテクション"}
        
        elif hand_strength >= 0.6:  # 強いハンド
            if board_texture == "dry":
                return {"percentage": 0.60, "reasoning": "バランスの取れたバリュー"}
            elif board_texture == "wet":
                return {"percentage": 0.70, "reasoning": "プロテクションとバリュー"}
            else:  # coordinated
                return {"percentage": 0.75, "reasoning": "プロテクション重視"}
        
        elif hand_strength >= 0.4:  # 中程度のハンド
            if board_texture == "dry":
                return {"percentage": 0.50, "reasoning": "薄いバリューとプロテクション"}
            elif board_texture == "wet":
                return {"percentage": 0.60, "reasoning": "プロテクション重視"}
            else:  # coordinated
                return {"percentage": 0.65, "reasoning": "強いプロテクション"}
        
        else:  # ブラフ
            if board_texture == "dry":
                return {"percentage": 0.40, "reasoning": "効率的なブラフ"}
            elif board_texture == "wet":
                return {"percentage": 0.50, "reasoning": "セミブラフ"}
            else:  # coordinated
                return {"percentage": 0.60, "reasoning": "アグレッシブブラフ"}
    
    elif action_type == "raise":
        return {"percentage": 0.75, "reasoning": "レイズサイズ"}
    
    elif action_type == "3bet":
        return {"percentage": 1.0, "reasoning": "3ベットサイズ"}
    
    return {"percentage": 0.50, "reasoning": "標準サイズ"}


def _get_position_adjustment(position: str, board_texture: str) -> float:
    """ポジション調整係数"""
    if position == "IP":  # インポジション
        if board_texture == "dry":
            return 0.9  # やや小さめ
        else:
            return 1.0  # 標準
    else:  # アウトオブポジション
        if board_texture == "wet":
            return 1.1  # やや大きめ
        else:
            return 1.0  # 標準


def _get_opponent_adjustment(num_opponents: int) -> float:
    """対戦相手数調整係数"""
    if num_opponents == 1:
        return 1.0
    elif num_opponents == 2:
        return 1.1  # やや大きめ
    else:
        return 1.2  # 大きめ


def _get_stack_adjustment(stack_depth: int, pot_size: float) -> float:
    """スタック深度調整係数"""
    if stack_depth < 30:  # ショートスタック
        return 0.8  # 小さめ
    elif stack_depth > 150:  # ディープスタック
        return 1.1  # やや大きめ
    else:
        return 1.0  # 標準


def _categorize_bet_size(percentage: float) -> str:
    """ベットサイズのカテゴリ化"""
    if percentage < 0.4:
        return "スモール"
    elif percentage < 0.7:
        return "ミディアム"
    elif percentage < 1.0:
        return "ラージ"
    elif percentage < 1.5:
        return "オーバー"
    else:
        return "マッシブ"


def _generate_alternative_sizes(pot_size: float, base_percentage: float, hand_strength: float, board_texture: str) -> List[Dict[str, Any]]:
    """代替ベットサイズの生成"""
    alternatives = []
    
    # 小さめのサイズ
    if base_percentage > 0.4:
        small_percentage = max(0.33, base_percentage - 0.2)
        alternatives.append({
            "size": pot_size * small_percentage,
            "percentage": small_percentage * 100,
            "category": _categorize_bet_size(small_percentage),
            "use_case": "ブラフキャッチャーを誘う"
        })
    
    # 大きめのサイズ
    if base_percentage < 1.2:
        large_percentage = min(1.5, base_percentage + 0.3)
        alternatives.append({
            "size": pot_size * large_percentage,
            "percentage": large_percentage * 100,
            "category": _categorize_bet_size(large_percentage),
            "use_case": "最大プロテクション"
        })
    
    return alternatives


def _determine_strategic_goal(hand_strength: float, board_texture: str, percentage: float) -> str:
    """戦略的目標の決定"""
    if hand_strength >= 0.8:
        return "バリュー最大化"
    elif hand_strength >= 0.6:
        if percentage >= 0.7:
            return "プロテクション重視"
        else:
            return "バランス戦略"
    elif hand_strength >= 0.4:
        return "薄いバリューとプロテクション"
    else:
        if board_texture == "coordinated":
            return "セミブラフ"
        else:
            return "ピュアブラフ"


def _generate_sizing_reasoning(
    hand_strength: float, board_texture: str, position: str, 
    num_opponents: int, category: str, strategic_goal: str
) -> str:
    """ベットサイズの理由を生成"""
    
    reasons = []
    
    # ハンド強度による理由
    if hand_strength >= 0.8:
        reasons.append("強いハンドでバリューを追求")
    elif hand_strength >= 0.6:
        reasons.append("中強ハンドでバランス重視")
    elif hand_strength >= 0.4:
        reasons.append("マージナルハンドでプロテクション")
    else:
        reasons.append("ブラフで相手をフォールドさせる")
    
    # ボードテクスチャによる理由
    if board_texture == "wet":
        reasons.append("ウェットボードでプロテクション強化")
    elif board_texture == "coordinated":
        reasons.append("コーディネートボードで大きめサイズ")
    else:
        reasons.append("ドライボードで効率的サイズ")
    
    # ポジションによる理由
    if position == "OOP":
        reasons.append("OOPで主導権確保")
    
    # 対戦相手数による理由
    if num_opponents > 1:
        reasons.append("マルチウェイでプロテクション重視")
    
    return f"{category}ベット: " + "、".join(reasons)


# ADK FunctionToolとして登録
SizingTool = FunctionTool(func=calculate_bet_sizing)
