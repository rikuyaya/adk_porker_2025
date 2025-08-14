from google.adk.tools import FunctionTool, ToolContext
from typing import Dict, Any, List, Optional, Union
import math


def calculate_equity(
    hole_cards_num: List[int],
    hole_cards_suit: List[str],
    community_num: List[int],
    community_suit: List[str],
    num_opponents: int,
) -> float:
    """
    ポーカーハンドの勝率（エクイティ）を計算します。    
    suit_map = {
        's': '♠',
        'h': '♥',
        'd': '♦',
        'c': '♣'}
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    Args:
        hole_cards_num: プレイヤーのホールカードの数のリスト
        hole_cards_suit: プレイヤーのホールカードのスートのリスト
        community_num: コミュニティカードの数のリスト
        community_suit: コミュニティカードのスートのリスト
        num_opponents: 対戦相手の数
    Returns:
        float: 勝率（0.0-1.0）
    """
    if len(community_num) == 0:
        return _calculate_preflop_equity(hole_cards_num, hole_cards_suit, num_opponents)
    else:
        return _calculate_postflop_equity(hole_cards_num, hole_cards_suit, community_num, community_suit, num_opponents)


def _calculate_preflop_equity(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    num_opponents: int
) -> float:
    """プリフロップのエクイティを計算"""
    val1 = hole_cards_num[0]
    val2 = hole_cards_num[1]

    # ペアの場合
    if val1 == val2:
        if val1 >= 14:  # AA
            base_strength = 0.85
        elif val1 >= 13:  # KK
            base_strength = 0.82
        elif val1 >= 12:  # QQ
            base_strength = 0.79
        elif val1 >= 11:  # JJ
            base_strength = 0.76
        elif val1 >= 10:  # TT
            base_strength = 0.73
        elif val1 >= 7:  # 77-99
            base_strength = 0.65
        else:  # 22-66
            base_strength = 0.55
    else:
        is_suited = hole_cards_suit[0] == hole_cards_suit[1]
        high_card = max(val1, val2)
        low_card = min(val1, val2)

        if high_card == 14 and low_card == 13:  # AK
            base_strength = 0.70 if is_suited else 0.65
        elif high_card == 14 and low_card == 12:  # AQ
            base_strength = 0.68 if is_suited else 0.62
        elif high_card == 14:  # その他のエース
            suited_bonus = 0.05 if is_suited else 0.0
            base_strength = 0.55 + (low_card - 7) * 0.02 + suited_bonus
        elif abs(val1 - val2) <= 1 and high_card >= 10:  # ハイコネクター
            suited_bonus = 0.05 if is_suited else 0.0
            base_strength = 0.52 + suited_bonus
        else:  # その他
            suited_bonus = 0.05 if is_suited else 0.0
            base_strength = 0.45 + (high_card - 7) * 0.01 + suited_bonus

    # 対戦相手数による調整
    return max(0.05, min(0.95, math.pow(base_strength, num_opponents * 0.3)))


def _calculate_postflop_equity(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    community_num: List[int], 
    community_suit: List[str], 
    num_opponents: int
) -> float:
    """ポストフロップのエクイティを計算"""
    all_values = hole_cards_num + community_num
    all_suits = hole_cards_suit + community_suit

    # ハンドの種類を判定
    value_counts = {}
    for val in all_values:
        value_counts[val] = value_counts.get(val, 0) + 1

    suit_counts = {}
    for suit in all_suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1

    max_count = max(value_counts.values())
    max_suit_count = max(suit_counts.values())
    is_straight = _check_straight(all_values)

    # ハンド強度の決定
    if max_suit_count >= 5 and is_straight:
        if max(all_values) == 14 and min(all_values) == 10:
            strength = 0.99  # ロイヤルフラッシュ
        else:
            strength = 0.95  # ストレートフラッシュ
    elif max_count >= 4:
        strength = 0.90  # フォーカード
    elif max_count == 3 and len([c for c in value_counts.values() if c >= 2]) >= 2:
        strength = 0.85  # フルハウス
    elif max_suit_count >= 5:
        strength = 0.80  # フラッシュ
    elif is_straight:
        strength = 0.75  # ストレート
    elif max_count == 3:
        strength = 0.70  # スリーカード
    elif len([c for c in value_counts.values() if c >= 2]) >= 2:
        strength = 0.65  # ツーペア
    elif max_count == 2:
        pair_value = max([val for val, count in value_counts.items() if count >= 2])
        strength = 0.60 if pair_value >= 11 else 0.55  # ハイペア/ローペア
    else:
        high_card = max(all_values)
        strength = 0.52 if high_card >= 12 else 0.48  # ハイカード

    # 対戦相手数による調整
    return max(0.05, min(0.95, math.pow(strength, num_opponents * 0.25)))




def _check_straight(values: List[int]) -> bool:
    """ストレートの判定"""
    unique_values = sorted(set(values))
    
    # 通常のストレート
    for i in range(len(unique_values) - 4):
        if unique_values[i+4] - unique_values[i] == 4:
            return True
    
    # A-2-3-4-5のローストレート
    return set([14, 2, 3, 4, 5]).issubset(set(unique_values))


def gto_calculation(hole_cards_num: List[int], hole_cards_suit: List[str], community_num: List[int], community_suit: List[str], position: str, action_before: str, stack_depth: int, num_players: int) -> float:
    """GTO計算の統合関数"""
    if len(community_num) == 0:
        return gto_preflop_action(hole_cards_num, hole_cards_suit, position, action_before, stack_depth)
    else:
        return gto_postflop_action(hole_cards_num, hole_cards_suit, community_num, community_suit, position, action_before, stack_depth)


def gto_preflop_action(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    position: str, 
) -> float:
    """
    GTOプリフロップアクション推奨

    Returns:
        float: ハンド強度 (0.0-1.0)
    """
    val1 = hole_cards_num[0]
    val2 = hole_cards_num[1]
    is_suited = hole_cards_suit[0] == hole_cards_suit[1]

    # ハンドティアの決定
    if val1 == val2:  # ペア
        if val1 >= 13:  # KK+
            hand_tier = 0.9
        elif val1 >= 10:  # TT+
            hand_tier = 0.8
        elif val1 >= 7:  # 77+
            hand_tier = 0.6
        else:
            hand_tier = 0.4
    else:
        high_card = max(val1, val2)
        low_card = min(val1, val2)
        
        if high_card == 14:  # エース
            if low_card >= 12:  # AQ+
                hand_tier = 0.8
            elif low_card >= 9:  # A9+
                hand_tier = 0.6
            else:
                hand_tier = 0.4 if is_suited else 0.2
        elif high_card >= 12 and low_card >= 11:  # KQ, KJ
            hand_tier = 0.6 if is_suited else 0.4
        else:
            hand_tier = 0.3 if is_suited else 0.1

    # ポジション調整
    position_multiplier = {
        "UTG": 0.6, "MP": 0.8, "CO": 1.2, "BTN": 1.5, "SB": 0.7, "BB": 1.0
    }
    adjusted_tier = hand_tier * position_multiplier.get(position, 1.0)

    return adjusted_tier


def gto_postflop_action(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    community_num: List[int], 
    community_suit: List[str], 
    position: str,
) -> float:
    """
    GTOポストフロップアクション推奨

    Returns:
        float: 調整されたハンド強度 (0.0-1.0)
    """
    hand_strength = _calculate_postflop_equity(hole_cards_num, hole_cards_suit, community_num, community_suit, 1)
    board_texture = _analyze_board_texture(community_num, community_suit)
    
    # ポジション調整
    in_position = position in ["CO", "BTN"]
    position_bonus = 0.1 if in_position else 0.0
    texture_adjustment = board_texture * 0.05
    adjusted_strength = min(0.95, hand_strength + position_bonus - texture_adjustment)
    return adjusted_strength


def _analyze_board_texture(community_num: List[int], community_suit: List[str]) -> float:
    """ボードテクスチャを数値で返す（0.0=dry, 1.0=wet）"""
    # フラッシュドロー
    suit_counts = {}
    for suit in community_suit:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    max_suit_count = max(suit_counts.values())
    flush_draw_score = 0.4 if max_suit_count >= 3 else 0.0

    # ストレートドロー
    sorted_values = sorted(community_num)
    straight_draw_score = 0.0
    for i in range(len(sorted_values) - 1):
        if sorted_values[i+1] - sorted_values[i] <= 2:
            straight_draw_score = 0.3
            break

    # スプレッド
    spread_score = min(0.3, (max(community_num) - min(community_num)) / 15.0)

    return min(1.0, flush_draw_score + straight_draw_score + spread_score)


# ADK FunctionToolとして登録
EquityCalculator = FunctionTool(func=calculate_equity)