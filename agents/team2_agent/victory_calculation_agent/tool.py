from google.adk.tools import FunctionTool
from typing import List
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


# def calculate_equity(
#     hole_cards: List[str],
#     community_cards: Optional[List[str]] = None,
#     num_opponents: int = 1,
#     tool_context: Optional[ToolContext] = None
# ) -> Dict[str, Any]:
#     """
#     ポーカーハンドの勝率（エクイティ）を計算します。
#     プリフロップの場合は、GTOチャートに基づいて勝率を計算します。

#     Args:
#         hole_cards: プレイヤーのホールカード（例: ["A♥", "K♠"]）
#         community_cards: コミュニティカード（例: ["Q♥", "J♦", "10♣"]）
#         num_opponents: 対戦相手の数（デフォルト: 1）
#         tool_context: ツールコンテキスト（オプション）

#     Returns:
#         Dict[str, Any]: 勝率計算結果
#     """
#     try:
#         if community_cards is None:
#             community_cards = []

#         # 入力検証
#         if not hole_cards or len(hole_cards) != 2:
#             return {
#                 "status": "error",
#                 "error_message": "ホールカードは正確に2枚である必要があります"
#             }

#         if num_opponents < 1 or num_opponents > 9:
#             return {
#                 "status": "error",
#                 "error_message": "対戦相手数は1-9人である必要があります"
#             }

#         # 詳細な勝率計算
#         if len(community_cards) == 0:
#             # プリフロップの場合は、GTOチャートに基づいて勝率を計算
#             equity_result = _calculate_preflop_equity(hole_cards, num_opponents)
#         else:
#             equity_result = _calculate_detailed_equity(hole_cards, community_cards, num_opponents)

#         # ツールコンテキストがある場合、状態を保存
#         if tool_context:
#             tool_context.state["last_equity_calculation"] = {
#                 "hole_cards": hole_cards,
#                 "community_cards": community_cards,
#                 "equity": equity_result["equity"],
#                 "hand_strength": equity_result["hand_strength"]
#             }

#         return {
#             "status": "success",
#             "equity": equity_result["equity"],
#             "hand_strength": equity_result["hand_strength"],
#             "hand_category": equity_result["hand_category"],
#             "outs": equity_result.get("outs", 0),
#             "hole_cards": hole_cards,
#             "community_cards": community_cards,
#             "num_opponents": num_opponents,
#             "confidence": equity_result["confidence"],
#             "description": f"勝率: {equity_result['equity']:.1%} (対戦相手{num_opponents}人) - {equity_result['hand_category']}"
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "error_message": f"勝率計算エラー: {str(e)}"
#         }


# def _calculate_preflop_equity(
#     hole_cards: List[str],
#     num_opponents: int,
#     position: str = "UTG",
#     stack_depth: int = 100,
#     action_before: str = "none"
# ) -> Dict[str, Any]:
#     """
#     プリフロップのエクイティをGTOツールを使って計算します。
#     """
#     try:
#         # GTOプリフロップチャートツールを直接呼び出し
#         from ..gto_preflop_chart_agent.tool import get_gto_preflop_action
        
#         gto_result = get_gto_preflop_action(
#             hole_cards=hole_cards,
#             position=position,
#             action_before=action_before,
#             stack_depth=stack_depth
#         )
        
#         # GTO結果から勝率を推定
#         equity = _estimate_equity_from_gto(gto_result, num_opponents)
        
#         return {
#             "equity": equity,
#             "hand_strength": _convert_tier_to_strength(gto_result["hand_strength_tier"]),
#             "hand_category": gto_result["hand_notation"],
#             "confidence": "中"  # GTOベースの計算は中程度の信頼度
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "error_message": f"勝率計算エラー: {str(e)}"
#         }


# def _estimate_equity_from_gto(gto_result: Dict[str, Any], num_opponents: int) -> float:
#     """GTO結果から勝率を推定"""
#     # ハンド強度ティアに基づく基本勝率
#     tier_equity = {
#         "premium": 0.75,
#         "strong": 0.65,
#         "playable": 0.55,
#         "speculative": 0.45,
#         "weak": 0.35
#     }
    
#     base_equity = tier_equity.get(gto_result["hand_strength_tier"], 0.5)
    
#     # 推奨アクションによる調整
#     action = gto_result["recommended_action"]
#     action_frequency = gto_result["action_frequency"]
    
#     if action == "raise" and action_frequency >= 80:
#         # 積極的なレイズは強いハンドを示唆
#         base_equity *= 1.1
#     elif action == "fold" and action_frequency >= 80:
#         # 積極的なフォールドは弱いハンドを示唆
#         base_equity *= 0.9
    
#     # 対戦相手数による調整
#     opponent_adjustment = 1.0 / (1.0 + num_opponents * 0.25)
#     final_equity = base_equity * opponent_adjustment
    
#     # 0.05から0.95の範囲に制限
#     return max(0.05, min(0.95, final_equity))


# def _convert_tier_to_strength(tier: str) -> float:
#     """GTOティアを数値強度に変換"""
#     tier_strength = {
#         "premium": 0.85,
#         "strong": 0.75,
#         "playable": 0.65,
#         "speculative": 0.55,
#         "weak": 0.45
#     }
#     return tier_strength.get(tier, 0.5)


# def _calculate_detailed_equity(hole_cards: List[str], community_cards: List[str], num_opponents: int) -> Dict[str, Any]:
#     """
#     詳細なハンド勝率計算

#     Returns:
#         Dict containing equity, hand_strength, hand_category, outs, confidence
#     """
#     # カードの強さを数値化
#     card_values = {
#         '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
#         'J': 11, 'Q': 12, 'K': 13, 'A': 14
#     }

#     # ハンド分析
#     hand_analysis = _analyze_hand(hole_cards, community_cards, card_values)

#     # 基本勝率計算
#     base_equity = _calculate_base_equity(hand_analysis, num_opponents)

#     # アウツ計算（改善可能性）
#     outs = _calculate_outs(hole_cards, community_cards, card_values)

#     # 信頼度計算
#     confidence = _calculate_confidence(hand_analysis, len(community_cards))

#     return {
#         "equity": base_equity,
#         "hand_strength": hand_analysis["strength"],
#         "hand_category": hand_analysis["category"],
#         "outs": outs,
#         "confidence": confidence
#     }


# def _analyze_hand(hole_cards: List[str], community_cards: List[str], card_values: Dict[str, int]) -> Dict[str, Any]:
#     """ハンドの詳細分析"""
#     # プリフロップの場合は特別処理
#     if len(community_cards) == 0:
#         return _analyze_preflop_hand(hole_cards, card_values)

#     all_cards = hole_cards + community_cards

#     if not all_cards:
#         return {"strength": 0.5, "category": "プリフロップ"}

#     # カードの値とスートを分離
#     values = []
#     suits = []

#     for card in all_cards:
#         value, suit = _parse_card(card)
#         values.append(card_values.get(value, 7))
#         suits.append(suit)

#     # 各種ハンドの判定
#     value_counts = {}
#     for val in values:
#         value_counts[val] = value_counts.get(val, 0) + 1

#     suit_counts = {}
#     for suit in suits:
#         suit_counts[suit] = suit_counts.get(suit, 0) + 1

#     max_count = max(value_counts.values()) if value_counts else 1
#     max_suit_count = max(suit_counts.values()) if suit_counts else 1

#     # ストレート判定
#     is_straight = _check_straight(values)

#     # ハンド強度とカテゴリの決定
#     if max_suit_count >= 5 and is_straight:
#         if max(values) == 14 and min(values) == 10:  # ロイヤルフラッシュ
#             return {"strength": 0.99, "category": "ロイヤルフラッシュ"}
#         else:
#             return {"strength": 0.95, "category": "ストレートフラッシュ"}
#     elif max_count >= 4:
#         return {"strength": 0.90, "category": "フォーカード"}
#     elif max_count == 3 and len([c for c in value_counts.values() if c >= 2]) >= 2:
#         return {"strength": 0.85, "category": "フルハウス"}
#     elif max_suit_count >= 5:
#         return {"strength": 0.80, "category": "フラッシュ"}
#     elif is_straight:
#         return {"strength": 0.75, "category": "ストレート"}
#     elif max_count == 3:
#         return {"strength": 0.70, "category": "スリーカード"}
#     elif len([c for c in value_counts.values() if c >= 2]) >= 2:
#         return {"strength": 0.65, "category": "ツーペア"}
#     elif max_count == 2:
#         pair_value = max([val for val, count in value_counts.items() if count >= 2])
#         if pair_value >= 11:  # J以上のペア
#             return {"strength": 0.60, "category": "ハイペア"}
#         else:
#             return {"strength": 0.55, "category": "ローペア"}
#     else:
#         high_card = max(values)
#         if high_card >= 12:  # Q以上
#             return {"strength": 0.52, "category": "ハイカード(強)"}
#         else:
#             return {"strength": 0.48, "category": "ハイカード(弱)"}


# def _analyze_preflop_hand(hole_cards: List[str], card_values: Dict[str, int]) -> Dict[str, Any]:
#     """プリフロップハンドの分析"""
#     if len(hole_cards) != 2:
#         return {"strength": 0.5, "category": "不明"}

#     # カードの値とスートを分離
#     card1_value, card1_suit = _parse_card(hole_cards[0])
#     card2_value, card2_suit = _parse_card(hole_cards[1])

#     val1 = card_values.get(card1_value, 7)
#     val2 = card_values.get(card2_value, 7)

#     # ペアの場合
#     if val1 == val2:
#         if val1 >= 14:  # エース
#             return {"strength": 0.85, "category": "ポケットエース"}
#         elif val1 >= 13:  # キング
#             return {"strength": 0.82, "category": "ポケットキング"}
#         elif val1 >= 12:  # クイーン
#             return {"strength": 0.79, "category": "ポケットクイーン"}
#         elif val1 >= 11:  # ジャック
#             return {"strength": 0.76, "category": "ポケットジャック"}
#         elif val1 >= 10:  # 10
#             return {"strength": 0.73, "category": "ポケット10"}
#         elif val1 >= 7:  # 7-9のペア
#             return {"strength": 0.65, "category": "ミドルペア"}
#         else:  # 低いペア
#             return {"strength": 0.55, "category": "ローペア"}

#     # スーテッドかどうか
#     is_suited = card1_suit == card2_suit

#     # 高いカードのボーナス
#     high_card = max(val1, val2)
#     low_card = min(val1, val2)

#     # エースキング
#     if high_card == 14 and low_card == 13:
#         base_strength = 0.70 if is_suited else 0.65
#         category = "AKスーテッド" if is_suited else "AKオフスーツ"
#         return {"strength": base_strength, "category": category}

#     # エースクイーン
#     if high_card == 14 and low_card == 12:
#         base_strength = 0.68 if is_suited else 0.62
#         category = "AQスーテッド" if is_suited else "AQオフスーツ"
#         return {"strength": base_strength, "category": category}

#     # その他のエース
#     if high_card == 14:
#         suited_bonus = 0.05 if is_suited else 0.0
#         base_strength = 0.55 + (low_card - 7) * 0.02 + suited_bonus
#         category = f"エース{'s' if is_suited else 'o'}"
#         return {"strength": min(0.75, base_strength), "category": category}

#     # コネクター
#     gap = abs(val1 - val2)
#     if gap <= 1 and high_card >= 10:  # ハイコネクター
#         suited_bonus = 0.05 if is_suited else 0.0
#         base_strength = 0.52 + suited_bonus
#         category = f"ハイコネクター{'s' if is_suited else 'o'}"
#         return {"strength": base_strength, "category": category}

#     # その他
#     suited_bonus = 0.05 if is_suited else 0.0
#     base_strength = 0.45 + (high_card - 7) * 0.01 + suited_bonus
#     category = f"ハイカード{'s' if is_suited else 'o'}"
#     return {"strength": max(0.35, min(0.65, base_strength)), "category": category}


# def _calculate_base_equity(hand_analysis: Dict[str, Any], num_opponents: int) -> float:
#     """ハンド分析結果から基本勝率を計算"""
#     base_strength = hand_analysis["strength"]

#     # 対戦相手数による調整
#     opponent_adjustment = 1.0 / (1.0 + num_opponents * 0.25)

#     final_equity = base_strength * opponent_adjustment

#     # 0.05から0.95の範囲に制限
#     return max(0.05, min(0.95, final_equity))


# def _calculate_outs(hole_cards: List[str], community_cards: List[str], card_values: Dict[str, int]) -> int:
#     """アウツ（改善可能なカード数）を計算"""
#     if len(community_cards) < 3:  # プリフロップまたはフロップ前
#         return 0

#     # 簡易的なアウツ計算
#     # 実際の実装では、より詳細な分析が必要

#     all_cards = hole_cards + community_cards
#     values = []
#     suits = []

#     for card in all_cards:
#         value, suit = _parse_card(card)
#         values.append(card_values.get(value, 7))
#         suits.append(suit)

#     outs = 0

#     # フラッシュドローのアウツ
#     suit_counts = {}
#     for suit in suits:
#         suit_counts[suit] = suit_counts.get(suit, 0) + 1

#     max_suit_count = max(suit_counts.values()) if suit_counts else 0
#     if max_suit_count == 4:  # フラッシュドロー
#         outs += 9

#     # ストレートドローのアウツ（簡易版）
#     if _has_straight_draw(values):
#         outs += 8  # オープンエンドストレートドロー

#     return min(outs, 15)  # 最大15アウツに制限


# def _calculate_confidence(hand_analysis: Dict[str, Any], community_cards_count: int) -> str:
#     """計算の信頼度を評価"""
#     strength = hand_analysis["strength"]

#     if community_cards_count >= 5:  # リバー
#         return "高"
#     elif community_cards_count >= 3:  # フロップ以降
#         if strength >= 0.8:
#             return "高"
#         elif strength >= 0.6:
#             return "中"
#         else:
#             return "低"
#     else:  # プリフロップ
#         if strength >= 0.7:
#             return "中"
#         else:
#             return "低"


# def _check_straight(values: List[int]) -> bool:
#     """ストレートの判定"""
#     if len(values) < 5:
#         return False

#     unique_values = sorted(set(values))

#     # 通常のストレート
#     for i in range(len(unique_values) - 4):
#         if unique_values[i+4] - unique_values[i] == 4:
#             return True

#     # A-2-3-4-5のローストレート
#     if set([14, 2, 3, 4, 5]).issubset(set(unique_values)):
#         return True

#     return False


# def _has_straight_draw(values: List[int]) -> bool:
#     """ストレートドローの判定（簡易版）"""
#     if len(values) < 4:
#         return False

#     unique_values = sorted(set(values))

#     # 4枚の連続する可能性をチェック
#     for i in range(len(unique_values) - 3):
#         if unique_values[i+3] - unique_values[i] == 3:
#             return True

#     return False


# def _parse_card(card: str) -> tuple:
#     """カード文字列をパース（例: "A♥" -> ("A", "♥")）"""
#     if len(card) >= 2:
#         if card.startswith('10'):
#             return ('10', card[2:])
#         else:
#             return (card[:-1], card[-1])
#     return ('7', '♠')  # デフォルト値


# # ADK FunctionToolとして登録
# EquityCalculator = FunctionTool(func=calculate_equity)