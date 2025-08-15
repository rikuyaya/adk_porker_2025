import csv
import json
import ast
import os
from typing import Dict, Any, List
from google.adk.tools import ToolContext, FunctionTool

def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """
    LLMが生成する様々な形式の文字列を安全にパースする
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError):
            fixed_str = json_str.replace("'", '"')
            return json.loads(fixed_str)

def convert_card_format(card: str) -> str:
    """
    カード形式を変換: "8♦" -> "8d", "J♠" -> "Js" など
    """
    if len(card) < 2:
        return card

    rank = card[0]
    suit_symbol = card[1:]

    # スート記号を英字に変換
    suit_map = {
        "♠": "s", "♤": "s",  # スペード
        "♥": "h", "♡": "h",  # ハート
        "♦": "d", "♢": "d",  # ダイヤ
        "♣": "c", "♧": "c"   # クラブ
    }

    suit = suit_map.get(suit_symbol, suit_symbol.lower())
    return f"{rank}{suit}"

def get_hand_representation(hand: List[str]) -> str:
    """Converts a two-card hand like ['Jd', '8d'] to standard notation 'J8s'."""
    if not hand or len(hand) != 2:
        return ""

    card1, card2 = hand[0], hand[1]
    rank1, suit1 = card1[0], card1[1]
    rank2, suit2 = card2[0], card2[1]

    rank_order = 'AKQJT98765432'

    if rank_order.index(rank1) > rank_order.index(rank2):
        # Swap to ensure rank1 is always the higher card
        rank1, rank2 = rank2, rank1

    if rank1 == rank2:
        return f"{rank1}{rank2}"
    elif suit1 == suit2:
        return f"{rank1}{rank2}s"
    else:
        return f"{rank1}{rank2}o"

def _get_postflop_action(hand: List[str], community: List[str], to_call: int, pot: int) -> Dict[str, Any]:
    """
    フロップ以降の簡単なハンド強度ベースの判断
    """
    # カード形式を変換
    converted_hand = [convert_card_format(card) for card in hand]
    converted_community = [convert_card_format(card) for card in community]

    # 簡単なハンド強度評価
    hand_strength = _evaluate_hand_strength(converted_hand, converted_community)

    # ポットオッズを考慮した判断
    if to_call == 0:  # チェック可能
        if hand_strength >= 0.7:  # 強いハンド
            return {"mix": {"raise": 0.8, "call": 0.0, "fold": 0.2}, "open_size_bb": 0.75}
        elif hand_strength >= 0.4:  # 中程度のハンド
            return {"mix": {"raise": 0.3, "call": 0.5, "fold": 0.2}, "open_size_bb": 0.5}
        else:  # 弱いハンド
            return {"mix": {"raise": 0.0, "call": 0.8, "fold": 0.2}, "open_size_bb": 0.0}
    else:  # コールが必要
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 1.0
        if hand_strength >= pot_odds + 0.2:  # 十分に強い
            return {"mix": {"raise": 0.6, "call": 0.3, "fold": 0.1}, "open_size_bb": 0.75}
        elif hand_strength >= pot_odds:  # ギリギリ
            return {"mix": {"raise": 0.1, "call": 0.7, "fold": 0.2}, "open_size_bb": 0.5}
        else:  # 弱い
            return {"mix": {"raise": 0.0, "call": 0.2, "fold": 0.8}, "open_size_bb": 0.0}

def _evaluate_hand_strength(hand: List[str], community: List[str]) -> float:
    """
    PokerKitを使用したハンド強度評価（0.0-1.0）
    """
    from .pokerkit_utils import get_hand_string, get_community_string, calculate_hand_strength

    # ダミーのゲームデータを作成
    dummy_data = {
        "your_cards": hand,
        "community": community
    }

    try:
        hole_cards_str = get_hand_string(dummy_data)
        community_cards_str = get_community_string(dummy_data)

        # PokerKitで正確な強度を計算
        return calculate_hand_strength(hole_cards_str, community_cards_str)

    except Exception as e:
        print(f"PokerKit評価エラー: {e}")
        # フォールバック：簡易評価
        return _simple_fallback_evaluation(hand, community)


def _simple_fallback_evaluation(hand: List[str], community: List[str]) -> float:
    """
    PokerKitが使えない場合のフォールバック評価
    """
    all_cards = hand + community
    ranks = [card[0] for card in all_cards]
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    max_count = max(rank_counts.values()) if rank_counts else 0

    if max_count >= 4:
        return 0.98
    elif max_count >= 3:
        return 0.95
    elif len([r for r, c in rank_counts.items() if c >= 2]) >= 2:
        return 0.7
    elif max_count >= 2:
        return 0.5
    else:
        return 0.2

def get_poker_action(state: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    ゲーム状況に応じたアクション推奨を返す。
    プリフロップ/フロップ/ターン/リバーに対応。
    Returns: {"mix":{"raise":0.6,"call":0.0,"fold":0.4}, "open_size_bb":2.0}
    """
    # JSON文字列をパース（シングルクォート問題の対処）
    state = safe_json_loads(state)

    position = state.get("position")
    hand = state.get("your_cards")
    phase = state.get("phase", "preflop")
    community = state.get("community", [])
    to_call = state.get("to_call", 0)
    pot = state.get("pot", 0)

    # Default conservative action
    default_action = {"mix": {"raise": 0.0, "call": 0.0, "fold": 1.0}, "open_size_bb": 0.0}

    if not position or not hand:
        return default_action

    # フロップ以降の場合は簡単なハンド強度ベースの判断
    if phase != "preflop" and community:
        return _get_postflop_action(hand, community, to_call, pot)

    # プリフロップの場合は既存のロジック

    # カード形式を変換
    converted_hand = [convert_card_format(card) for card in hand]
    hand_str = get_hand_representation(converted_hand)

    # This assumes the script is run from the repository root.
    # A more robust solution might use absolute paths or package resources.
    range_file_path = os.path.join("team3", "resources", "ranges", f"preflop_{position.lower()}.csv")

    if not os.path.exists(range_file_path):
        return default_action

    try:
        with open(range_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if row['hand'] == hand_str:
                    mix = {
                        "raise": float(row['raise']),
                        "call": float(row['call']),
                        "fold": float(row['fold'])
                    }
                    size = float(row['open_size_bb'])
                    return {"mix": mix, "open_size_bb": size}
    except (FileNotFoundError, KeyError, ValueError):
        # If file not found, or CSV is malformed, return default action
        return default_action

    # If hand not found in the file, fold
    return default_action

PokerActionTool = FunctionTool(func=get_poker_action)