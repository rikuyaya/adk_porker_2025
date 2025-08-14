from google.adk.tools import FunctionTool
from typing import Dict, Any, List


def get_gto_preflop_action(
    hole_cards: List[str], 
    position: str, 
    action_before: str = "none",
    stack_depth: int = 100
) -> Dict[str, Any]:
    """
    GTOプリフロップチャートに基づいてアクションを推奨します。
    
    Args:
        hole_cards: プレイヤーのホールカード（例: ["A♥", "K♠"]）
        position: ポジション（"UTG", "MP", "CO", "BTN", "SB", "BB"）
        action_before: 前のアクション（"none", "raise", "call", "fold"）
        stack_depth: スタック深度（BBの倍数、デフォルト: 100）
    
    Returns:
        Dict[str, Any]: GTO推奨アクションと理由
    """
    try:
        # 入力検証
        if not hole_cards or len(hole_cards) != 2:
            return {
                "status": "error",
                "error_message": "ホールカードは正確に2枚である必要があります"
            }
        
        valid_positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
        if position not in valid_positions:
            return {
                "status": "error",
                "error_message": f"ポジションは{valid_positions}のいずれかである必要があります"
            }
        
        # ハンドを標準化
        hand_notation = _standardize_hand(hole_cards)
        
        # GTOチャートからアクションを取得
        gto_action = _get_gto_action_from_chart(hand_notation, position, action_before, stack_depth)
        
        return {
            "status": "success",
            "hole_cards": hole_cards,
            "hand_notation": hand_notation,
            "position": position,
            "action_before": action_before,
            "stack_depth": stack_depth,
            "recommended_action": gto_action["action"],
            "action_frequency": gto_action["frequency"],
            "alternative_actions": gto_action.get("alternatives", []),
            "reasoning": gto_action["reasoning"],
            "hand_strength_tier": gto_action["tier"],
            "description": f"ポジション: {position}, 推奨: {gto_action['action']} ({gto_action['frequency']}%), 理由: {gto_action['reasoning']}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"GTOチャート計算エラー: {str(e)}"
        }


def _standardize_hand(hole_cards: List[str]) -> str:
    """ハンドを標準記法に変換（例: ["A♥", "K♠"] -> "AKo"）"""
    card1_value, card1_suit = _parse_card(hole_cards[0])
    card2_value, card2_suit = _parse_card(hole_cards[1])
    
    # カード値を数値に変換
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    val1 = card_values.get(card1_value, 7)
    val2 = card_values.get(card2_value, 7)
    
    # 高い方を先に
    if val1 > val2:
        high_card, low_card = card1_value, card2_value
        high_suit, low_suit = card1_suit, card2_suit
    else:
        high_card, low_card = card2_value, card1_value
        high_suit, low_suit = card2_suit, card1_suit

    # 10をTに変換
    high_card = 'T' if high_card == '10' else high_card
    low_card = 'T' if low_card == '10' else low_card

    # ペアの場合
    if val1 == val2:
        return f"{high_card}{low_card}"

    # スーテッドかオフスーツか
    suited = "s" if high_suit == low_suit else "o"

    return f"{high_card}{low_card}{suited}"


def _get_gto_action_from_chart(hand_notation: str, position: str, action_before: str, stack_depth: int) -> Dict[str, Any]:
    """GTOチャートからアクションを取得"""
    
    # 簡易GTOチャート（実際のGTOソルバーデータに基づく近似）
    gto_chart = _get_gto_chart_data()
    
    # ハンドの強度ティアを判定
    hand_tier = _classify_hand_tier(hand_notation)
    
    # ポジション別の基本戦略
    if action_before == "none":  # オープンアクション
        return _get_opening_action(hand_notation, position, hand_tier, stack_depth)
    elif action_before == "raise":  # レイズに対する対応
        return _get_vs_raise_action(hand_notation, position, hand_tier, stack_depth)
    elif action_before == "call":  # コールに対する対応
        return _get_vs_call_action(hand_notation, position, hand_tier, stack_depth)
    else:
        return {
            "action": "fold",
            "frequency": 100,
            "reasoning": "不明なアクションに対してはフォールド",
            "tier": hand_tier
        }


def _classify_hand_tier(hand_notation: str) -> str:
    """ハンドを強度ティアに分類"""
    
    # プレミアムハンド
    premium_hands = ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
    if hand_notation in premium_hands:
        return "premium"
    
    # 強いハンド
    strong_hands = ["TT", "99", "AQs", "AQo", "AJs", "AJo", "KQs", "KQo"]
    if hand_notation in strong_hands:
        return "strong"
    
    # プレイアブルハンド
    playable_hands = ["88", "77", "66", "55", "44", "33", "22", 
                     "ATs", "ATo", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                     "KJs", "KJo", "KTs", "K9s", "QJs", "QJo", "QTs", "Q9s", 
                     "JTs", "JTo", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s", "54s"]
    if hand_notation in playable_hands:
        return "playable"
    
    # 投機的ハンド
    speculative_hands = ["A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
                        "K9o", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                        "Q8s", "Q7s", "J8s", "J7s", "T7s", "97s", "86s", "75s", "64s", "53s", "43s"]
    if hand_notation in speculative_hands:
        return "speculative"
    
    return "weak"


def _get_opening_action(hand_notation: str, position: str, hand_tier: str, stack_depth: int) -> Dict[str, Any]:
    """オープンアクションの決定"""
    
    # ポジション別のオープンレンジ
    position_ranges = {
        "UTG": {"premium": 100, "strong": 100, "playable": 30, "speculative": 0, "weak": 0},
        "MP": {"premium": 100, "strong": 100, "playable": 60, "speculative": 10, "weak": 0},
        "CO": {"premium": 100, "strong": 100, "playable": 80, "speculative": 40, "weak": 5},
        "BTN": {"premium": 100, "strong": 100, "playable": 90, "speculative": 70, "weak": 20},
        "SB": {"premium": 100, "strong": 100, "playable": 70, "speculative": 30, "weak": 10},
        "BB": {"premium": 100, "strong": 100, "playable": 50, "speculative": 20, "weak": 0}
    }
    
    raise_frequency = position_ranges[position].get(hand_tier, 0)
    
    if raise_frequency >= 80:
        return {
            "action": "raise",
            "frequency": raise_frequency,
            "reasoning": f"{hand_tier}ハンドは{position}から積極的にレイズ",
            "tier": hand_tier,
            "alternatives": [{"action": "fold", "frequency": 100 - raise_frequency}] if raise_frequency < 100 else []
        }
    elif raise_frequency >= 30:
        return {
            "action": "raise",
            "frequency": raise_frequency,
            "reasoning": f"{hand_tier}ハンドは{position}から選択的にレイズ",
            "tier": hand_tier,
            "alternatives": [{"action": "fold", "frequency": 100 - raise_frequency}]
        }
    elif raise_frequency > 0:
        return {
            "action": "fold",
            "frequency": 100 - raise_frequency,
            "reasoning": f"{hand_tier}ハンドは{position}からほぼフォールド",
            "tier": hand_tier,
            "alternatives": [{"action": "raise", "frequency": raise_frequency}]
        }
    else:
        return {
            "action": "fold",
            "frequency": 100,
            "reasoning": f"{hand_tier}ハンドは{position}からフォールド",
            "tier": hand_tier
        }


def _get_vs_raise_action(hand_notation: str, position: str, hand_tier: str, stack_depth: int) -> Dict[str, Any]:
    """レイズに対するアクション"""
    
    # レイズに対する対応レンジ
    vs_raise_ranges = {
        "premium": {"3bet": 70, "call": 25, "fold": 5},
        "strong": {"3bet": 30, "call": 60, "fold": 10},
        "playable": {"3bet": 10, "call": 40, "fold": 50},
        "speculative": {"3bet": 5, "call": 15, "fold": 80},
        "weak": {"3bet": 0, "call": 5, "fold": 95}
    }
    
    ranges = vs_raise_ranges.get(hand_tier, {"3bet": 0, "call": 0, "fold": 100})
    
    # 最も高い頻度のアクションを推奨
    max_action = max(ranges.items(), key=lambda x: x[1])
    action_name = "raise" if max_action[0] == "3bet" else max_action[0]
    
    alternatives = []
    for act, freq in ranges.items():
        if act != max_action[0] and freq > 0:
            alt_name = "raise" if act == "3bet" else act
            alternatives.append({"action": alt_name, "frequency": freq})
    
    return {
        "action": action_name,
        "frequency": max_action[1],
        "reasoning": f"{hand_tier}ハンドはレイズに対して{action_name}が最適",
        "tier": hand_tier,
        "alternatives": alternatives
    }


def _get_vs_call_action(hand_notation: str, position: str, hand_tier: str, stack_depth: int) -> Dict[str, Any]:
    """コールに対するアクション（マルチウェイポット）"""
    
    # マルチウェイでの戦略調整
    multiway_ranges = {
        "premium": {"raise": 80, "call": 20, "fold": 0},
        "strong": {"raise": 40, "call": 55, "fold": 5},
        "playable": {"raise": 15, "call": 60, "fold": 25},
        "speculative": {"raise": 5, "call": 35, "fold": 60},
        "weak": {"raise": 0, "call": 10, "fold": 90}
    }
    
    ranges = multiway_ranges.get(hand_tier, {"raise": 0, "call": 0, "fold": 100})
    
    max_action = max(ranges.items(), key=lambda x: x[1])
    
    alternatives = []
    for act, freq in ranges.items():
        if act != max_action[0] and freq > 0:
            alternatives.append({"action": act, "frequency": freq})
    
    return {
        "action": max_action[0],
        "frequency": max_action[1],
        "reasoning": f"{hand_tier}ハンドはマルチウェイで{max_action[0]}が最適",
        "tier": hand_tier,
        "alternatives": alternatives
    }


def _get_gto_chart_data():
    """GTOチャートデータ（実装用プレースホルダー）"""
    # 実際の実装では、GTOソルバーからのデータを使用
    return {}


def _parse_card(card: str) -> tuple:
    """カード文字列をパース"""
    if len(card) >= 2:
        if card.startswith('10'):
            return ('10', card[2:])
        else:
            return (card[:-1], card[-1])
    return ('7', '♠')


# ADK FunctionToolとして登録
GtoPreflopChartTool = FunctionTool(func=get_gto_preflop_action)
