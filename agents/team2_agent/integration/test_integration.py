#!/usr/bin/env python3
"""
team2_agent統合テストコード

使用方法:
    python test_integration.py
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent import process_poker_decision


def test_preflop_scenario():
    """プリフロップシナリオのテスト"""
    print("=== プリフロップシナリオテスト ===")
    
    # テストケース1: ポケットエース
    print("\n1. ポケットエース UTG")
    game_state = {
        "your_id": 0,
        "phase": "preflop",
        "your_cards": ["A♥", "A♠"],
        "community": [],
        "your_chips": 1000,
        "pot": 30,
        "to_call": 20,
        "actions": ["fold", "call (20)", "raise (min 40)"],
        "dealer_button": 2,
        "current_turn": 0,
        "players": [
            {"id": 0, "status": "active", "chips": 1000},
            {"id": 1, "status": "active", "chips": 980},
            {"id": 2, "status": "active", "chips": 970}
        ],
        "history": ["Player 1 posted small blind 10", "Player 2 posted big blind 20"]
    }
    
    result = process_poker_decision(json.dumps(game_state))
    print(f"結果: {result}")
    assert "action" in result
    assert "amount" in result
    assert "reasoning" in result
    assert result["action"] in ["fold", "check", "call", "raise", "all_in"]
    
    # テストケース2: 弱いハンド
    print("\n2. 弱いハンド (7♥ 2♠)")
    game_state["your_cards"] = ["7♥", "2♠"]
    result = process_poker_decision(json.dumps(game_state))
    print(f"結果: {result}")
    assert result["action"] in ["fold", "check", "call", "raise", "all_in"]


def test_postflop_scenario():
    """ポストフロップシナリオのテスト"""
    print("\n=== ポストフロップシナリオテスト ===")
    
    # テストケース1: フロップでトップペア
    print("\n1. フロップでトップペア")
    game_state = {
        "your_id": 0,
        "phase": "flop",
        "your_cards": ["A♥", "K♠"],
        "community": ["A♠", "7♦", "2♣"],
        "your_chips": 950,
        "pot": 100,
        "to_call": 0,
        "actions": ["check", "bet (min 25)"],
        "dealer_button": 2,
        "current_turn": 0,
        "players": [
            {"id": 0, "status": "active", "chips": 950},
            {"id": 1, "status": "active", "chips": 930}
        ],
        "history": ["Player 1 called 20", "Player 0 raised to 50", "Player 1 called 30"]
    }
    
    result = process_poker_decision(json.dumps(game_state))
    print(f"結果: {result}")
    assert result["action"] in ["fold", "check", "call", "raise", "all_in"]
    
    # テストケース2: フラッシュドロー
    print("\n2. フラッシュドロー")
    game_state["your_cards"] = ["A♥", "K♥"]
    game_state["community"] = ["Q♥", "J♦", "2♥"]
    game_state["to_call"] = 50
    game_state["actions"] = ["fold", "call (50)", "raise (min 100)"]
    
    result = process_poker_decision(json.dumps(game_state))
    print(f"結果: {result}")
    assert result["action"] in ["fold", "check", "call", "raise", "all_in"]


def test_turn_river_scenarios():
    """ターン・リバーシナリオのテスト"""
    print("\n=== ターン・リバーシナリオテスト ===")
    
    # テストケース1: ターンでナッツ
    print("\n1. ターンでナッツ")
    game_state = {
        "your_id": 0,
        "phase": "turn",
        "your_cards": ["A♥", "K♠"],
        "community": ["Q♥", "J♦", "10♣", "9♠"],
        "your_chips": 800,
        "pot": 300,
        "to_call": 100,
        "actions": ["fold", "call (100)", "raise (min 200)", "all-in (800)"],
        "dealer_button": 1,
        "current_turn": 0,
        "players": [
            {"id": 0, "status": "active", "chips": 800},
            {"id": 1, "status": "active", "chips": 700}
        ],
        "history": ["Flop betting", "Turn: Player 1 bet 100"]
    }
    
    result = process_poker_decision(json.dumps(game_state))
    print(f"結果: {result}")
    assert result["action"] in ["fold", "check", "call", "raise", "all_in"]


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # テストケース1: 無効なJSON
    print("\n1. 無効なJSON")
    result = process_poker_decision("invalid json")
    print(f"結果: {result}")
    assert "action" in result
    assert result["action"] == "fold"
    
    # テストケース2: 不完全なゲーム状態
    print("\n2. 不完全なゲーム状態")
    incomplete_state = {"your_id": 0}
    result = process_poker_decision(json.dumps(incomplete_state))
    print(f"結果: {result}")
    assert "action" in result


def test_different_positions():
    """異なるポジションでのテスト"""
    print("\n=== ポジション別テスト ===")
    
    base_game_state = {
        "your_id": 0,
        "phase": "preflop",
        "your_cards": ["Q♥", "J♠"],
        "community": [],
        "your_chips": 1000,
        "pot": 30,
        "to_call": 20,
        "actions": ["fold", "call (20)", "raise (min 40)"],
        "current_turn": 0,
        "players": [
            {"id": 0, "status": "active", "chips": 1000},
            {"id": 1, "status": "active", "chips": 980},
            {"id": 2, "status": "active", "chips": 970},
            {"id": 3, "status": "active", "chips": 960},
            {"id": 4, "status": "active", "chips": 950},
            {"id": 5, "status": "active", "chips": 940}
        ],
        "history": ["Player 4 posted small blind 10", "Player 5 posted big blind 20"]
    }
    
    positions = [
        (0, "UTG"),
        (2, "MP"), 
        (3, "CO"),
        (4, "BTN"),
        (5, "SB")
    ]
    
    for dealer_button, position_name in positions:
        print(f"\n{position_name}ポジション")
        game_state = base_game_state.copy()
        game_state["dealer_button"] = dealer_button
        
        result = process_poker_decision(json.dumps(game_state))
        print(f"結果: {result['action']} - {result['reasoning'][:100]}...")
        assert result["action"] in ["fold", "check", "call", "raise", "all_in"]


def test_stack_sizes():
    """異なるスタックサイズでのテスト"""
    print("\n=== スタックサイズ別テスト ===")
    
    base_game_state = {
        "your_id": 0,
        "phase": "preflop",
        "your_cards": ["A♥", "K♠"],
        "community": [],
        "pot": 30,
        "to_call": 20,
        "dealer_button": 2,
        "current_turn": 0,
        "players": [
            {"id": 0, "status": "active"},
            {"id": 1, "status": "active", "chips": 1000},
            {"id": 2, "status": "active", "chips": 1000}
        ],
        "history": ["Player 1 posted small blind 10", "Player 2 posted big blind 20"]
    }
    
    stack_sizes = [500, 1000, 2000, 5000]  # ショート、ミディアム、ディープ、超ディープ
    
    for stack_size in stack_sizes:
        print(f"\nスタック{stack_size}")
        game_state = base_game_state.copy()
        game_state["your_chips"] = stack_size
        game_state["actions"] = ["fold", "call (20)", f"raise (min 40)", f"all-in ({stack_size})"]
        
        result = process_poker_decision(json.dumps(game_state))
        print(f"結果: {result['action']} {result['amount']} - スタック{stack_size}")
        assert result["action"] in ["fold", "check", "call", "raise", "all_in"]


def main():
    """メイン関数"""
    print("🃏 team2_agent 統合テスト開始 🃏")
    print("=" * 60)
    
    try:
        test_preflop_scenario()
        test_postflop_scenario()
        test_turn_river_scenarios()
        test_error_handling()
        test_different_positions()
        test_stack_sizes()
        
        print("\n" + "=" * 60)
        print("🎉 すべての統合テストが完了しました！")
        print("team2_agentは正常に動作しています。")
        print("ゲームシステムとの統合準備が完了しました。")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
