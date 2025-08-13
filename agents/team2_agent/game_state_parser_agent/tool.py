from google.adk.tools import FunctionTool
from typing import Dict, Any, List
import json
import re





def parse_game_state(game_state_json: str) -> Dict[str, Any]:
    """
    ゲーム状態JSONを解析し、各ツールで使用可能な形式に変換
    
    Args:
        game_state_json: ゲームシステムからのJSON文字列
    
    Returns:
        Dict containing parsed game state information
    """
    try:
        # JSONパースを試行
        if isinstance(game_state_json, str):
            game_state = json.loads(game_state_json)
        else:
            game_state = game_state_json
        
        # 基本情報の抽出
        your_id = game_state.get("your_id", 0)
        phase = game_state.get("phase", "preflop")
        hole_cards = game_state.get("your_cards", [])
        community_cards = game_state.get("community", [])
        your_chips = game_state.get("your_chips", 1000)
        pot_size = game_state.get("pot", 0)
        to_call = game_state.get("to_call", 0)
        available_actions = game_state.get("actions", [])
        dealer_button = game_state.get("dealer_button", 0)
        current_turn = game_state.get("current_turn", 0)
        players = game_state.get("players", [])
        
        # 対戦相手数の計算
        active_opponents = len([p for p in players if p.get("status") == "active"])
        num_opponents = max(1, active_opponents)  # 最低1人
        
        # ポジションの判定
        position = _determine_position(your_id, dealer_button, len(players))
        
        # ボードテクスチャの分析
        board_texture = _analyze_board_texture(community_cards)
        
        # 前のアクションの分析
        action_before = _analyze_previous_action(game_state.get("history", []))
        
        # スタック深度の計算（BBの倍数）
        big_blind = _estimate_big_blind(game_state)
        stack_depth = your_chips // big_blind if big_blind > 0 else 100
        
        return {
            "status": "success",
            "your_id": your_id,
            "phase": phase,
            "hole_cards": hole_cards,
            "community_cards": community_cards,
            "your_chips": your_chips,
            "pot_size": float(pot_size),
            "call_amount": float(to_call),
            "available_actions": available_actions,
            "num_opponents": num_opponents,
            "position": position,
            "board_texture": board_texture,
            "action_before": action_before,
            "stack_depth": stack_depth,
            "dealer_button": dealer_button,
            "current_turn": current_turn,
            "players": players,
            "raw_game_state": game_state,
            "description": f"解析完了: {phase}フェーズ, ポット{pot_size}, コール{to_call}, 対戦相手{num_opponents}人"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"ゲーム状態解析エラー: {str(e)}",
            "raw_input": game_state_json
        }


def _determine_position(your_id: int, dealer_button: int, total_players: int) -> str:
    """ポジションを判定"""
    if total_players <= 2:
        return "BTN" if your_id == dealer_button else "BB"

    # ディーラーボタンからの時計回りの位置を計算
    # ディーラーボタンの次がSB、その次がBB
    position_offset = (your_id - dealer_button) % total_players

    if total_players <= 6:
        position_map = {
            0: "BTN",  # ディーラー
            1: "SB",   # スモールブラインド
            2: "BB",   # ビッグブラインド
            3: "UTG",  # アンダーザガン
            4: "MP",   # ミドルポジション
            5: "CO",   # カットオフ
        }
    else:
        position_map = {
            0: "BTN",
            1: "SB",
            2: "BB",
            3: "UTG",
            4: "UTG+1",
            5: "MP",
            6: "MP+1",
            7: "CO",
            8: "CO-1"
        }

    return position_map.get(position_offset, "MP")


def _analyze_board_texture(community_cards: List[str]) -> str:
    """ボードテクスチャを分析"""
    if len(community_cards) < 3:
        return "preflop"
    
    # カードの値とスートを分離
    values = []
    suits = []
    
    for card in community_cards:
        if len(card) >= 2:
            if card.startswith('10'):
                value, suit = '10', card[2:]
            else:
                value, suit = card[:-1], card[-1]
            values.append(value)
            suits.append(suit)
    
    # 数値変換
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    numeric_values = [card_values.get(v, 7) for v in values]
    numeric_values.sort()
    
    # フラッシュドローの判定
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    max_suit_count = max(suit_counts.values()) if suit_counts else 0
    has_flush_draw = max_suit_count >= 3
    
    # ストレートドローの判定
    has_straight_draw = _has_straight_potential(numeric_values)
    
    # ペアボードの判定
    value_counts = {}
    for val in numeric_values:
        value_counts[val] = value_counts.get(val, 0) + 1
    
    has_pair = any(count >= 2 for count in value_counts.values())
    
    # テクスチャの決定
    if has_flush_draw and has_straight_draw:
        return "coordinated"
    elif has_flush_draw or has_straight_draw or has_pair:
        return "wet"
    else:
        return "dry"


def _has_straight_potential(values: List[int]) -> bool:
    """ストレートの可能性があるかチェック"""
    if len(values) < 3:
        return False
    
    # 連続する3枚以上があるかチェック
    for i in range(len(values) - 2):
        if values[i+2] - values[i] <= 4:  # 4以下の差なら可能性あり
            return True
    
    # A-2-3-4-5のローストレート可能性
    if 14 in values and 2 in values and 3 in values:
        return True
    
    return False


def _analyze_previous_action(history: List[str]) -> str:
    """直前のアクションを分析"""
    if not history:
        return "none"
    
    last_action = history[-1].lower()
    
    if "raise" in last_action or "bet" in last_action:
        return "raise"
    elif "call" in last_action:
        return "call"
    elif "check" in last_action:
        return "check"
    elif "fold" in last_action:
        return "fold"
    else:
        return "none"


def _estimate_big_blind(game_state: Dict[str, Any]) -> int:
    """ビッグブラインドサイズを推定"""
    # ヒストリーからブラインド情報を抽出
    history = game_state.get("history", [])
    for action in history:
        if "big blind" in action.lower():
            # "Player 2 posted big blind 20" のような形式から抽出
            match = re.search(r"big blind (\d+)", action)
            if match:
                return int(match.group(1))
    
    # ポットサイズから推定（プリフロップの場合）
    if game_state.get("phase") == "preflop":
        pot = game_state.get("pot", 30)
        return max(10, pot // 3)  # 大体SB+BBがポットの初期値
    
    return 20  # デフォルト値


# ADK FunctionToolとして登録
GameStateParser = FunctionTool(func=parse_game_state)
