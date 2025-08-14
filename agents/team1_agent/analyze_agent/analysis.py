from google.adk.tools import FunctionTool
from typing import Dict, Any, List, Optional, Tuple
import json
from concurrent.futures import ProcessPoolExecutor

# PokerKitのimport

from pokerkit import (
    Card, Deck, StandardHighHand, 
    calculate_equities, calculate_hand_strength as pk_calculate_hand_strength,
    parse_range
)


def convert_card_format(card_str: str) -> str:
    """カード表記をPokerKit形式に変換"""
    # "A♠" -> "As", "K♥" -> "Kh", etc.
    suit_map = {
        '♠': 's', '♤': 's',  # spades
        '♥': 'h', '♡': 'h',  # hearts  
        '♦': 'd', '♢': 'd',  # diamonds
        '♣': 'c', '♧': 'c'   # clubs
    }
    
    if len(card_str) >= 2:
        rank = card_str[:-1]
        suit_symbol = card_str[-1]
        suit = suit_map.get(suit_symbol, suit_symbol.lower())
        return f"{rank}{suit}"
    return card_str

def parse_cards(cards: List[str]) -> List:
    """カードリストをPokerKit Card オブジェクトに変換"""
    parsed_cards = []
    for card_str in cards:
        try:
            converted = convert_card_format(card_str)
            card = Card.parse(converted)[0] if hasattr(Card, 'parse') else None
            if card:
                parsed_cards.append(card)
        except Exception as e:
            print(f"Error parsing card {card_str}: {e}")
            continue
    return parsed_cards

def calculate_hand_strength_pokerkit(hole_cards: List[str], community_cards: List[str], num_opponents: int = 1) -> Dict[str, Any]:
    """PokerKitを使用してハンドの強さを計算"""
    try:
        # カードをPokerKit形式に変換
        hole_parsed = parse_cards(hole_cards)
        community_parsed = parse_cards(community_cards)
        
        if len(hole_parsed) < 2:
            return {"hand_type": "invalid", "strength": 0, "error": "insufficient_hole_cards"}
        
        # PokerKitのcalculate_hand_strengthを使用
        hole_range = frozenset([frozenset(hole_parsed)])
        
        with ProcessPoolExecutor() as executor:
            strength = pk_calculate_hand_strength(
                num_opponents + 1,  # プレイヤー数（自分含む）
                hole_range,
                community_parsed,
                2,  # ホールカード数
                5,  # ボードカード数（最終的に）
                Deck.STANDARD,
                (StandardHighHand,),
                sample_count=1000,
                executor=executor
            )
        
        return {
            "hand_type": "calculated",
            "strength": strength,
            "raw_strength": strength
        }
        
    except Exception as e:
        return {"error": str(e), "hand_type": "error", "strength": 0}

def calculate_equity_pokerkit(hole_cards: List[str], community_cards: List[str], num_opponents: int = 1) -> float:
    """PokerKitを使用してエクイティを計算"""
    try:
        # カードをPokerKit形式に変換
        hole_parsed = parse_cards(hole_cards)
        community_parsed = parse_cards(community_cards)
        
        if len(hole_parsed) < 2:
            return 0.0
        
        # 自分のレンジと相手のレンジを作成
        my_range = frozenset([frozenset(hole_parsed)])
        # 相手のレンジ（ランダムハンド）
        opponent_ranges = tuple([parse_range('random')] * num_opponents)
        
        all_ranges = (my_range,) + opponent_ranges
        
        with ProcessPoolExecutor() as executor:
            equities = calculate_equities(
                all_ranges,
                community_parsed,
                2,  # ホールカード数
                5,  # ボードカード数（最終的に）
                Deck.STANDARD,
                (StandardHighHand,),
                sample_count=1000,
                executor=executor
            )
        
        # 自分のエクイティ（最初の要素）を返す
        return equities[0] if equities else 0.0
        
    except Exception as e:
        return 0.0




def calculate_pot_odds(to_call: int, pot: int) -> float:
    """ポットオッズを計算"""
    if to_call <= 0:
        return float('inf')
    return pot / to_call

def analyze_position(your_id: int, dealer_button: int, num_players: int) -> Dict[str, Any]:
    """ポジション分析"""
    # ディーラーボタンからの距離を計算
    distance = (your_id - dealer_button) % num_players
    
    if distance <= 2:
        position = "late"
        position_strength = 0.8
    elif distance <= 4:
        position = "middle"
        position_strength = 0.6
    else:
        position = "early"
        position_strength = 0.4
    
    return {
        "position": position,
        "position_strength": position_strength,
        "distance_from_button": distance
    }

def analyze_betting_pattern(history: List[str], players: List[Dict]) -> Dict[str, Any]:
    """ベッティングパターンを分析"""
    aggressive_actions = 0
    passive_actions = 0
    
    for action in history:
        if "raised" in action.lower() or "all-in" in action.lower():
            aggressive_actions += 1
        elif "called" in action.lower() or "checked" in action.lower():
            passive_actions += 1
    
    total_actions = aggressive_actions + passive_actions
    aggression_factor = aggressive_actions / max(1, total_actions)
    
    return {
        "aggression_factor": aggression_factor,
        "total_actions": total_actions,
        "aggressive_actions": aggressive_actions,
        "passive_actions": passive_actions
    }

def analyze_stack_sizes(your_chips: int, players: List[Dict], pot: int) -> Dict[str, Any]:
    """スタックサイズ分析"""
    all_stacks = [your_chips] + [p["chips"] for p in players]
    avg_stack = sum(all_stacks) / len(all_stacks)
    
    your_m_ratio = your_chips / max(1, pot)  # M ratio approximation
    
    stack_category = "unknown"
    if your_chips < avg_stack * 0.5:
        stack_category = "short"
    elif your_chips > avg_stack * 1.5:
        stack_category = "big"
    else:
        stack_category = "medium"
    
    return {
        "stack_category": stack_category,
        "m_ratio": your_m_ratio,
        "avg_stack": avg_stack,
        "relative_stack": your_chips / avg_stack
    }

def analyze_game_state(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """メインのゲーム状況分析関数 - データ取得と基本計算のみ"""
    
    # 基本情報の抽出
    hole_cards = game_state.get("your_cards", [])
    community_cards = game_state.get("community", [])
    your_chips = game_state.get("your_chips", 0)
    pot = game_state.get("pot", 0)
    to_call = game_state.get("to_call", 0)
    players = game_state.get("players", [])
    history = game_state.get("history", [])
    phase = game_state.get("phase", "preflop")
    your_id = game_state.get("your_id", 0)
    dealer_button = game_state.get("dealer_button", 0)
    
    num_opponents = len([p for p in players if p.get("status") == "active"])
    num_players = len(players) + 1  # プレイヤー + 自分
    
    # 純粋なデータ計算のみ実行
    try:
        # 1. ハンドの強さを計算
        hand_strength = calculate_hand_strength_pokerkit(hole_cards, community_cards, num_opponents)
        
        # 2. エクイティを計算
        equity = calculate_equity_pokerkit(hole_cards, community_cards, num_opponents)
        
        # 3. ポットオッズを計算
        pot_odds = calculate_pot_odds(to_call, pot)
        
        # 4. ポジション分析
        position_analysis = analyze_position(your_id, dealer_button, num_players)
        
        # 5. ベッティングパターン分析
        betting_analysis = analyze_betting_pattern(history, players)
        
        # 6. スタックサイズ分析
        stack_analysis = analyze_stack_sizes(your_chips, players, pot)
        
        # データのみを返す（推奨は含めない）
        return {
            "hand_strength": hand_strength,
            "equity": equity,
            "pot_odds": pot_odds,
            "position_analysis": position_analysis,
            "betting_analysis": betting_analysis,
            "stack_analysis": stack_analysis,
            "phase": phase,
            "num_opponents": num_opponents,
            "to_call": to_call,
            "pot": pot,
            "your_chips": your_chips,
            "pokerkit_available": POKERKIT_AVAILABLE
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "hand_strength": {"hand_type": "error", "strength": 0},
            "equity": 0.0,
            "pot_odds": 0.0,
            "phase": phase,
            "pokerkit_available": POKERKIT_AVAILABLE
        }



# ADK FunctionToolとして定義
analyze_tool = FunctionTool(
    name="analyze_game_state",
    description="テキサスホールデムのゲーム状況を分析し、ハンドの強さ、エクイティ、ポジション、ベッティングパターンなどを総合的に評価します",
    func=analyze_game_state,
    parameters={
        "game_state": {
            "type": "object",
            "description": "ゲームの現在の状況を表すオブジェクト",
            "properties": {
                "your_cards": {"type": "array", "items": {"type": "string"}, "description": "自分のホールカード"},
                "community": {"type": "array", "items": {"type": "string"}, "description": "コミュニティカード"},
                "your_chips": {"type": "integer", "description": "自分のチップ数"},
                "pot": {"type": "integer", "description": "ポットサイズ"},
                "to_call": {"type": "integer", "description": "コールに必要な金額"},
                "players": {"type": "array", "description": "他のプレイヤー情報"},
                "history": {"type": "array", "items": {"type": "string"}, "description": "アクション履歴"},
                "phase": {"type": "string", "description": "ゲームフェーズ"},
                "your_id": {"type": "integer", "description": "自分のプレイヤーID"},
                "dealer_button": {"type": "integer", "description": "ディーラーボタンの位置"}
            },
            "required": ["your_cards", "community", "your_chips", "pot", "to_call"]
        }
    }
)