import random
from collections import Counter
from itertools import combinations
from google.adk.tools import FunctionTool
from typing import List, Tuple
import math

NUM_SIMULATIONS = 1000

def estimate_hand_strength(
    hole_cards_num: List[int],
    hole_cards_suit: List[str],
    community_num: List[int],
    community_suit: List[str],
    num_opponents: int,
    position: str,
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
        position: プレイヤーのポジション
    Returns:
        float: 勝率（0.0-1.0）
    """
    if len(community_num) == 0:
        return _calculate_preflop_strength(hole_cards_num, hole_cards_suit, num_opponents, position)
    else:
        return _calculate_postflop_strength(hole_cards_num, hole_cards_suit, community_num, community_suit, num_opponents)
    # else:
    #     # モンテカルロ法によるポストフロップ勝率計算を呼び出す
    #     return _monte_carlo_postflop_strength(
    #         hole_cards_num, hole_cards_suit, community_num, community_suit, num_opponents
    #     )

def _calculate_preflop_strength(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    num_opponents: int,
    position: str,
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

    position_multiplier = {"UTG": 0.85, "SB": 0.9, "BB": 1.0, "CO": 1.1, "BTN": 1.2}
    adjusted_strength = base_strength * position_multiplier.get(position, 1.0)

    # 対戦相手数による調整
    final_strength = math.pow(adjusted_strength, num_opponents * 0.5)
    return max(0.0, min(1.0, final_strength))

def _calculate_postflop_strength(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    community_num: List[int], 
    community_suit: List[str], 
    num_opponents: int
) -> float:
    """
    ポストフロップのハンド強度を、完成役とドローの可能性を考慮して評価します。

    Returns:
        float: 評価されたハンドの強さ（0.0-1.0）
    """
    all_cards_num = hole_cards_num + community_num
    all_cards_suit = hole_cards_suit + community_suit

    # 1. 現在の完成役の強さを評価する
    made_hand_strength = _evaluate_made_hand(all_cards_num, all_cards_suit)

    # 2. ドローの可能性を評価し、ボーナスを加える
    draw_potential_bonus = _evaluate_draw_potential(all_cards_num, all_cards_suit)

    # 3. 完成役とドローの価値を合算する
    # ドローの価値は、まだ完成していないため少し割り引いて加算します
    combined_strength = made_hand_strength + (draw_potential_bonus * 0.5)

    # 4. 対戦相手の数で最終的な強度を調整する
    # 対戦相手が多いほど、勝つ確率は下がる
    exponent = 1 + (num_opponents - 1) * 0.6  # 相手が1人なら指数は1、増えるごとに指数が大きくなる
    final_strength = math.pow(combined_strength, exponent)

    return max(0.0, min(1.0, final_strength))


def _evaluate_made_hand(all_cards_num: List[int], all_cards_suit: List[str]) -> float:
    """7枚のカードから作れる最強の5枚の役を評価し、強さを返す"""
    
    # 役の強さをランク付け
    HAND_STRENGTH_MAP = {
        "Royal Flush": 1.0, "Straight Flush": 0.98, "Four of a Kind": 0.96,
        "Full House": 0.92, "Flush": 0.85, "Straight": 0.80,
        "Three of a Kind": 0.70, "Two Pair": 0.60, "One Pair": 0.40, "High Card": 0.20
    }

    best_rank = "High Card"
    
    # 7枚のカードから5枚を選ぶ全ての組み合わせを試す
    for combo_indices in combinations(range(len(all_cards_num)), 5):
        combo_num = [all_cards_num[i] for i in combo_indices]
        combo_suit = [all_cards_suit[i] for i in combo_indices]

        # 現在の組み合わせの役を判定
        is_flush = len(set(combo_suit)) == 1
        is_straight, high_card = _check_straight(combo_num)
        
        value_counts = Counter(combo_num)
        counts = sorted(value_counts.values(), reverse=True)

        current_rank = "High Card"
        if is_straight and is_flush:
            current_rank = "Royal Flush" if high_card == 14 else "Straight Flush"
        elif counts[0] == 4:
            current_rank = "Four of a Kind"
        elif counts == [3, 2]:
            current_rank = "Full House"
        elif is_flush:
            current_rank = "Flush"
        elif is_straight:
            current_rank = "Straight"
        elif counts[0] == 3:
            current_rank = "Three of a Kind"
        elif counts == [2, 2, 1]:
            current_rank = "Two Pair"
        elif counts[0] == 2:
            current_rank = "One Pair"

        # より強い役が見つかれば更新
        if HAND_STRENGTH_MAP[current_rank] > HAND_STRENGTH_MAP[best_rank]:
            best_rank = current_rank

    return HAND_STRENGTH_MAP[best_rank]

def _evaluate_draw_potential(all_cards_num: List[int], all_cards_suit: List[str]) -> float:
    """ドローの強さを評価してボーナス値を返す"""
    bonus = 0.0
    
    # フラッシュドローの評価
    suit_counts = Counter(all_cards_suit)
    if 4 in suit_counts.values():
        bonus = max(bonus, 0.35) # フラッシュドロー（あと1枚で完成）
    
    # ストレートドローの評価
    unique_values = sorted(list(set(all_cards_num)))
    # オープンエンドストレートドロー（両端待ち）
    for i in range(len(unique_values) - 3):
        if unique_values[i+3] - unique_values[i] == 3 and len(set(range(unique_values[i], unique_values[i+3]+1)) - set(unique_values)) == 0:
            bonus = max(bonus, 0.30)
            break
            
    # ガットショットストレートドロー（中待ち）
    for i in range(len(unique_values) - 3):
        if unique_values[i+3] - unique_values[i] == 4:
            bonus = max(bonus, 0.15)
            break
            
    return bonus

def _check_straight(values: List[int]) -> (bool, int):
    """5枚のカードがストレートかどうかを判定"""
    unique_values = sorted(list(set(values)))
    if len(unique_values) < 5:
        return False, 0
    
    # A-2-3-4-5 (Wheel)
    if set(unique_values) == {14, 2, 3, 4, 5}:
        return True, 5
        
    # 通常のストレート
    for i in range(len(unique_values) - 4):
        if unique_values[i+4] - unique_values[i] == 4:
            return True, unique_values[i+4]
            
    return False, 0


def _monte_carlo_postflop_strength(
    hole_cards_num: List[int], 
    hole_cards_suit: List[str],
    community_num: List[int], 
    community_suit: List[str], 
    num_opponents: int,
    num_simulations: int = NUM_SIMULATIONS # 応答時間5秒を考慮し、シミュレーション回数を設定
) -> float:
    """
    モンテカルロ法を用いてポストフロップの勝率を計算します。
    """
    # カードを (数字, スート) のタプル形式に変換
    my_hole_cards = list(zip(hole_cards_num, hole_cards_suit))
    community_cards = list(zip(community_num, community_suit))
    
    # デッキの準備
    all_known_cards = my_hole_cards + community_cards
    deck = [(n, s) for n in range(2, 15) for s in ['s', 'h', 'd', 'c']]
    for card in all_known_cards:
        if card in deck:
            deck.remove(card)

    wins = 0
    ties = 0
    
    for _ in range(num_simulations):
        temp_deck = deck[:]
        random.shuffle(temp_deck)
        
        # 対戦相手にランダムな手札を配る
        opponent_hands = []
        for _ in range(num_opponents):
            opponent_hands.append([temp_deck.pop(), temp_deck.pop()])
        
        # 残りのコミュニティカードを配る
        num_remaining_community = 5 - len(community_cards)
        remaining_community = [temp_deck.pop() for _ in range(num_remaining_community)]
        final_community = community_cards + remaining_community
        
        # 自分の最強の役を判定
        my_best_hand_rank = _get_best_hand_rank(my_hole_cards, final_community)
        
        # 対戦相手の最強の役を判定
        best_opponent_hand_rank = (0,)
        for opp_hand in opponent_hands:
            opp_best_hand_rank = _get_best_hand_rank(opp_hand, final_community)
            if opp_best_hand_rank > best_opponent_hand_rank:
                best_opponent_hand_rank = opp_best_hand_rank
                
        # 勝敗判定
        if my_best_hand_rank > best_opponent_hand_rank:
            wins += 1
        elif my_best_hand_rank == best_opponent_hand_rank:
            ties += 1

    # 勝率を計算 (引き分けは0.5勝としてカウント)
    return (wins + ties / 2) / num_simulations


def _get_best_hand_rank(hole_cards: List[Tuple[int, str]], community_cards: List[Tuple[int, str]]) -> Tuple:
    """
    7枚のカードから作れる最強の5枚の役を判定し、比較可能なタプルとして返します。
    タプルの構造: (役ランク, 主要カードランク1, 主要カードランク2, ..., キッカー)
    """
    all_cards = hole_cards + community_cards
    best_rank_tuple = (0,)

    for combo in combinations(all_cards, 5):
        nums = sorted([c[0] for c in combo], reverse=True)
        suits = [c[1] for c in combo]
        
        is_flush = len(set(suits)) == 1
        
        # ストレート判定
        is_straight = False
        unique_nums = sorted(list(set(nums)), reverse=True)
        if len(unique_nums) >= 5:
            if unique_nums[0] - unique_nums[4] == 4:
                is_straight = True
            # A-5のストレート(Wheel)
            if set(unique_nums) == {14, 5, 4, 3, 2}:
                is_straight = True
                nums = [5, 4, 3, 2, 1] # Aを1として扱う
        
        # 役判定とランク付け
        rank_tuple = (0,)
        counts = Counter(nums)
        sorted_counts = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
        
        if is_straight and is_flush:
            rank_tuple = (8, nums[0]) # ストレートフラッシュ (ロイヤルも含む)
        elif sorted_counts[0][1] == 4:
            quad_val = sorted_counts[0][0]
            kicker = sorted_counts[1][0]
            rank_tuple = (7, quad_val, kicker)
        elif sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
            rank_tuple = (6, sorted_counts[0][0], sorted_counts[1][0])
        elif is_flush:
            rank_tuple = (5,) + tuple(nums)
        elif is_straight:
            rank_tuple = (4, nums[0])
        elif sorted_counts[0][1] == 3:
            kickers = sorted([num for num in nums if num != sorted_counts[0][0]], reverse=True)
            rank_tuple = (3, sorted_counts[0][0]) + tuple(kickers)
        elif sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            pairs = (sorted_counts[0][0], sorted_counts[1][0])
            kicker = sorted_counts[2][0]
            rank_tuple = (2, max(pairs), min(pairs), kicker)
        elif sorted_counts[0][1] == 2:
            kickers = sorted([num for num in nums if num != sorted_counts[0][0]], reverse=True)
            rank_tuple = (1, sorted_counts[0][0]) + tuple(kickers)
        else:
            rank_tuple = (0,) + tuple(nums)

        if rank_tuple > best_rank_tuple:
            best_rank_tuple = rank_tuple
            
    return best_rank_tuple


# ADK FunctionToolとして登録
EquityCalculator = FunctionTool(func=estimate_hand_strength)
