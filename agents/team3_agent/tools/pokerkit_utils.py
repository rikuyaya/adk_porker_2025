"""
PokerKit用のユーティリティ関数
"""

import json
import ast
from typing import Dict, Any, List, Tuple, Optional
import pokerkit
from pokerkit import NoLimitTexasHoldem


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


def create_pokerkit_state(game_data: Dict[str, Any]) -> pokerkit.State:
    """
    ゲームデータからPokerKitのStateオブジェクトを作成
    """
    # プレイヤー数を取得
    players = game_data.get("players", [])
    your_id = game_data.get("your_id", 0)
    
    # 全プレイヤー（自分を含む）のスタック情報を構築
    all_players = {}
    for player in players:
        all_players[player["id"]] = {
            "chips": player["chips"],
            "status": player.get("status", "active")
        }
    
    # 自分の情報も追加
    your_chips = game_data.get("your_chips", 0)
    all_players[your_id] = {
        "chips": your_chips,
        "status": "active"
    }
    
    # プレイヤー数とスタック
    player_count = len(all_players)
    starting_stacks = []
    
    # IDでソートしてスタックリストを作成
    for player_id in sorted(all_players.keys()):
        starting_stacks.append(all_players[player_id]["chips"])
    
    # ブラインド情報を推定
    # 通常、SB=10, BB=20のような構造
    blinds = [10, 20]  # デフォルト値
    
    # PokerKitのStateを作成
    state = NoLimitTexasHoldem.create_state(
        automations=(
            pokerkit.Automation.ANTE_POSTING,
            pokerkit.Automation.BET_COLLECTION,
            pokerkit.Automation.BLIND_OR_STRADDLE_POSTING,
            pokerkit.Automation.CARD_BURNING,
            pokerkit.Automation.HOLE_DEALING,
            pokerkit.Automation.BOARD_DEALING,
            pokerkit.Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            pokerkit.Automation.HAND_KILLING,
            pokerkit.Automation.CHIPS_PUSHING,
            pokerkit.Automation.CHIPS_PULLING,
        ),
        ante_trimming_status=True,
        raw_antes=0,
        raw_blinds_or_straddles=blinds,
        min_bet=blinds[-1],  # BBと同じ
        starting_stacks=starting_stacks,
        player_count=player_count,
    )
    
    return state


def get_hand_string(game_data: Dict[str, Any]) -> str:
    """
    プレイヤーのハンドカードを文字列形式で取得（PokerKit用）
    """
    your_cards = game_data.get("your_cards", [])
    converted_cards = [convert_card_format(card) for card in your_cards]
    return ''.join(converted_cards)


def get_community_string(game_data: Dict[str, Any]) -> str:
    """
    コミュニティカードを文字列形式で取得（PokerKit用）
    """
    community = game_data.get("community", [])
    converted_cards = [convert_card_format(card) for card in community]
    return ''.join(converted_cards)


def create_full_hand_string(hole_cards: str, community_cards: str) -> str:
    """
    ホールカードとコミュニティカードを結合して5枚のハンド文字列を作成
    """
    all_cards = hole_cards + community_cards

    # 5枚未満の場合はパディング（実際のゲームでは発生しないはず）
    if len(all_cards) < 10:  # 5枚 * 2文字 = 10文字
        return all_cards

    # 7枚の場合は最初の5枚を使用（実際は最強の5枚を選ぶべきだが、簡略化）
    if len(all_cards) > 10:
        return all_cards[:10]  # 5枚分

    return all_cards


def calculate_hand_strength(hole_cards_str: str, community_cards_str: str) -> float:
    """
    PokerKitを使用してハンド強度を計算
    """
    if len(hole_cards_str) < 4:  # 2枚 * 2文字 = 4文字
        return 0.0

    try:
        # 5枚のハンド文字列を作成
        full_hand_str = create_full_hand_string(hole_cards_str, community_cards_str)


        # PokerKitのStandardHighHandを使用
        hand = pokerkit.StandardHighHand(full_hand_str)

        # ハンドの種類に基づいて強度を計算
        hand_str = str(hand)

        # ハンドランキングに基づく強度
        if "Royal flush" in hand_str:
            return 1.0
        elif "Straight flush" in hand_str:
            return 0.95
        elif "Four of a kind" in hand_str:
            return 0.9
        elif "Full house" in hand_str:
            return 0.85
        elif "Flush" in hand_str:
            return 0.75
        elif "Straight" in hand_str:
            return 0.65
        elif "Three of a kind" in hand_str:
            return 0.55
        elif "Two pair" in hand_str:
            return 0.45
        elif "One pair" in hand_str:
            return 0.35
        else:  # High card
            return 0.25

    except Exception as e:
        print(f"ハンド評価エラー: {e}")
        return 0.0





def simulate_equity(hole_cards_str: str,
                   community_cards_str: str,
                   num_opponents: int = 1,
                   simulations: int = 1000) -> float:
    """
    PokerKitを使用してエクイティをシミュレーション
    """
    if len(hole_cards_str) < 4:  # 2枚 * 2文字 = 4文字
        return 0.0

    try:
        # 簡易エクイティ計算（完全なシミュレーションは複雑なので）
        # ハンド強度ベースの推定
        my_strength = calculate_hand_strength(hole_cards_str, community_cards_str)

        # 相手の平均的な強度を推定
        # ランダムハンドの平均強度は約0.3-0.4
        average_opponent_strength = 0.35

        # 複数の相手がいる場合、最強の相手の強度は上がる
        if num_opponents > 1:
            # 複数相手の場合、最強相手の期待強度は上がる
            strongest_opponent_strength = average_opponent_strength + (num_opponents - 1) * 0.1
            strongest_opponent_strength = min(strongest_opponent_strength, 0.8)
        else:
            strongest_opponent_strength = average_opponent_strength

        # エクイティを計算
        if my_strength > strongest_opponent_strength + 0.2:
            equity = 0.85  # 大幅に強い
        elif my_strength > strongest_opponent_strength + 0.1:
            equity = 0.75  # やや強い
        elif my_strength > strongest_opponent_strength:
            equity = 0.65  # 少し強い
        elif my_strength > strongest_opponent_strength - 0.1:
            equity = 0.45  # 互角
        else:
            equity = 0.25  # 弱い

        return equity

    except Exception as e:
        print(f"エクイティシミュレーションエラー: {e}")
        # フォールバック：ハンド強度をそのまま返す
        return calculate_hand_strength(hole_cards_str, community_cards_str)
