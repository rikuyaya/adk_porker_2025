from google.adk.tools import FunctionTool, ToolContext
from typing import Dict, Any, List, Optional
import time

def calculate_equity_fast(
    hole_cards: List[str],
    community_cards: Optional[List[str]] = None,
    num_opponents: int = 1,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    高速版ポーカーハンドの勝率（エクイティ）計算
    
    最適化ポイント:
    - キャッシュ機能の活用
    - 簡易計算の優先
    - エラーハンドリングの簡素化
    """
    start_time = time.time()
    
    try:
        if community_cards is None:
            community_cards = []

        # 入力検証（高速化）
        if not hole_cards or len(hole_cards) != 2:
            return {
                "status": "error",
                "error_message": "ホールカードは正確に2枚である必要があります"
            }

        # キャッシュチェック
        if tool_context and "equity_cache" in tool_context.state:
            cache_key = f"{','.join(hole_cards)}_{','.join(community_cards)}_{num_opponents}"
            if cache_key in tool_context.state["equity_cache"]:
                cached_result = tool_context.state["equity_cache"][cache_key]
                cached_result["cached"] = True
                cached_result["calculation_time"] = time.time() - start_time
                return cached_result

        # 高速勝率計算
        if len(community_cards) == 0:
            # プリフロップ：簡易計算
            equity_result = _calculate_preflop_equity_fast(hole_cards, num_opponents)
        else:
            # ポストフロップ：簡易計算
            equity_result = _calculate_postflop_equity_fast(hole_cards, community_cards, num_opponents)

        # キャッシュに保存
        if tool_context:
            if "equity_cache" not in tool_context.state:
                tool_context.state["equity_cache"] = {}
            cache_key = f"{','.join(hole_cards)}_{','.join(community_cards)}_{num_opponents}"
            tool_context.state["equity_cache"][cache_key] = equity_result

        equity_result["calculation_time"] = time.time() - start_time
        return equity_result

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"勝率計算エラー: {str(e)}",
            "calculation_time": time.time() - start_time
        }


def _calculate_preflop_equity_fast(hole_cards: List[str], num_opponents: int) -> Dict[str, Any]:
    """高速プリフロップ勝率計算"""
    # 簡易的なハンド強度判定
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    card1_value, card1_suit = _parse_card_fast(hole_cards[0])
    card2_value, card2_suit = _parse_card_fast(hole_cards[1])
    
    val1 = card_values.get(card1_value, 7)
    val2 = card_values.get(card2_value, 7)
    
    # 高速ハンド分類
    if val1 == val2:  # ペア
        if val1 >= 14:  # エース
            base_equity = 0.85
            category = "ポケットエース"
        elif val1 >= 13:  # キング
            base_equity = 0.82
            category = "ポケットキング"
        elif val1 >= 12:  # クイーン
            base_equity = 0.79
            category = "ポケットクイーン"
        elif val1 >= 11:  # ジャック
            base_equity = 0.76
            category = "ポケットジャック"
        elif val1 >= 10:  # 10
            base_equity = 0.73
            category = "ポケット10"
        else:
            base_equity = 0.65
            category = "ミドルペア"
    else:
        # スーテッドかどうか
        is_suited = card1_suit == card2_suit
        high_card = max(val1, val2)
        low_card = min(val1, val2)
        
        # エースキング
        if high_card == 14 and low_card == 13:
            base_equity = 0.70 if is_suited else 0.65
            category = "AKスーテッド" if is_suited else "AKオフスーツ"
        # エースクイーン
        elif high_card == 14 and low_card == 12:
            base_equity = 0.68 if is_suited else 0.62
            category = "AQスーテッド" if is_suited else "AQオフスーツ"
        # その他のエース
        elif high_card == 14:
            suited_bonus = 0.05 if is_suited else 0.0
            base_equity = 0.55 + (low_card - 7) * 0.02 + suited_bonus
            category = f"エース{'s' if is_suited else 'o'}"
        else:
            suited_bonus = 0.05 if is_suited else 0.0
            base_equity = 0.45 + (high_card - 7) * 0.01 + suited_bonus
            category = f"ハイカード{'s' if is_suited else 'o'}"
    
    # 対戦相手数による調整
    opponent_adjustment = 1.0 / (1.0 + num_opponents * 0.25)
    final_equity = base_equity * opponent_adjustment
    
    return {
        "equity": max(0.05, min(0.95, final_equity)),
        "hand_strength": base_equity,
        "hand_category": category,
        "confidence": "中"
    }


def _calculate_postflop_equity_fast(hole_cards: List[str], community_cards: List[str], num_opponents: int) -> Dict[str, Any]:
    """高速ポストフロップ勝率計算"""
    # 簡易的なハンド強度計算
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    all_cards = hole_cards + community_cards
    values = []
    suits = []
    
    for card in all_cards:
        value, suit = _parse_card_fast(card)
        values.append(card_values.get(value, 7))
        suits.append(suit)
    
    # 簡易ハンド判定
    value_counts = {}
    for val in values:
        value_counts[val] = value_counts.get(val, 0) + 1
    
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    max_count = max(value_counts.values()) if value_counts else 1
    max_suit_count = max(suit_counts.values()) if suit_counts else 1
    
    # ハンド強度の簡易判定
    if max_suit_count >= 5 and _check_straight_fast(values):
        if max(values) == 14 and min(values) == 10:
            base_equity = 0.99
            category = "ロイヤルフラッシュ"
        else:
            base_equity = 0.95
            category = "ストレートフラッシュ"
    elif max_count >= 4:
        base_equity = 0.90
        category = "フォーカード"
    elif max_count == 3 and len([c for c in value_counts.values() if c >= 2]) >= 2:
        base_equity = 0.85
        category = "フルハウス"
    elif max_suit_count >= 5:
        base_equity = 0.80
        category = "フラッシュ"
    elif _check_straight_fast(values):
        base_equity = 0.75
        category = "ストレート"
    elif max_count == 3:
        base_equity = 0.70
        category = "スリーカード"
    elif len([c for c in value_counts.values() if c >= 2]) >= 2:
        base_equity = 0.65
        category = "ツーペア"
    elif max_count == 2:
        pair_value = max([val for val, count in value_counts.items() if count >= 2])
        if pair_value >= 11:
            base_equity = 0.60
            category = "ハイペア"
        else:
            base_equity = 0.55
            category = "ローペア"
    else:
        high_card = max(values)
        if high_card >= 12:
            base_equity = 0.52
            category = "ハイカード(強)"
        else:
            base_equity = 0.48
            category = "ハイカード(弱)"
    
    # 対戦相手数による調整
    opponent_adjustment = 1.0 / (1.0 + num_opponents * 0.25)
    final_equity = base_equity * opponent_adjustment
    
    return {
        "equity": max(0.05, min(0.95, final_equity)),
        "hand_strength": base_equity,
        "hand_category": category,
        "confidence": "中"
    }


def _parse_card_fast(card: str) -> tuple:
    """高速カードパース"""
    if len(card) >= 2:
        if card.startswith('10'):
            return ('10', card[2:])
        else:
            return (card[:-1], card[-1])
    return ('7', '♠')


def _check_straight_fast(values: List[int]) -> bool:
    """高速ストレート判定"""
    if len(values) < 5:
        return False
    
    unique_values = sorted(set(values))
    
    # 通常のストレート
    for i in range(len(unique_values) - 4):
        if unique_values[i+4] - unique_values[i] == 4:
            return True
    
    # A-2-3-4-5のローストレート
    if set([14, 2, 3, 4, 5]).issubset(set(unique_values)):
        return True
    
    return False


# ADK FunctionToolとして登録
EquityCalculatorFast = FunctionTool(func=calculate_equity_fast)
