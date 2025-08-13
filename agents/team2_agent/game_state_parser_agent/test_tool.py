#!/usr/bin/env python3
"""
GameStateParserツールのテストコード

使用方法:
    python test_tool.py
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import parse_game_state, GameStateParser


def test_basic_parsing():
    """基本的なゲーム状態解析テスト"""
    print("=== 基本解析テスト ===")
    
    # テストケース1: プリフロップ状態
    print("\n1. プリフロップ状態")
    game_state = {
        "your_id": 0,
        "phase": "preflop",
        "your_cards": ["A♥", "K♠"],
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
    
    result = parse_game_state(json.dumps(game_state))
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["phase"] == "preflop"
    assert result["hole_cards"] == ["A♥", "K♠"]
    assert result["community_cards"] == []
    assert result["pot_size"] == 30.0
    assert result["call_amount"] == 20.0
    assert result["num_opponents"] == 3


def test_position_detection():
    """ポジション判定テスト"""
    print("\n=== ポジション判定テスト ===")
    
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
            {"id": 0, "status": "active"},
            {"id": 1, "status": "active"},
            {"id": 2, "status": "active"},
            {"id": 3, "status": "active"},
            {"id": 4, "status": "active"},
            {"id": 5, "status": "active"}
        ]
    }
    
    # 異なるディーラーボタンでテスト
    # your_id=0 固定で、dealer_buttonを変更
    test_cases = [
        (0, "BTN"),  # your_id=0, dealer_button=0 → BTN (自分がディーラー)
        (5, "SB"),   # your_id=0, dealer_button=5 → SB (ディーラーの次)
        (4, "BB"),   # your_id=0, dealer_button=4 → BB (ディーラーの2つ次)
        (3, "UTG"),  # your_id=0, dealer_button=3 → UTG (ディーラーの3つ次)
        (2, "MP"),   # your_id=0, dealer_button=2 → MP (ディーラーの4つ次)
        (1, "CO"),   # your_id=0, dealer_button=1 → CO (ディーラーの5つ次)
    ]
    
    for dealer_button, expected_position in test_cases:
        game_state = base_game_state.copy()
        game_state["dealer_button"] = dealer_button
        
        result = parse_game_state(json.dumps(game_state))
        print(f"ディーラー{dealer_button}: {result['position']} (期待: {expected_position})")
        assert result["status"] == "success"
        assert result["position"] == expected_position


def test_board_texture_analysis():
    """ボードテクスチャ分析テスト"""
    print("\n=== ボードテクスチャ分析テスト ===")
    
    base_game_state = {
        "your_id": 0,
        "phase": "flop",
        "your_cards": ["A♥", "K♠"],
        "your_chips": 1000,
        "pot": 100,
        "to_call": 0,
        "actions": ["check", "bet (min 25)"],
        "dealer_button": 2,
        "players": [{"id": 0, "status": "active"}, {"id": 1, "status": "active"}]
    }
    
    # 異なるボードテクスチャ
    test_cases = [
        ([], "preflop"),
        (["A♠", "7♦", "2♣"], "dry"),        # レインボー、コネクトなし
        (["A♥", "K♥", "Q♦"], "wet"),        # フラッシュドロー
        (["9♥", "8♦", "7♣"], "wet"),        # ストレートドロー
        (["A♥", "A♠", "K♦"], "wet"),        # ペアボード
        (["J♥", "10♥", "9♥"], "coordinated"), # フラッシュ＋ストレートドロー
    ]
    
    for community_cards, expected_texture in test_cases:
        game_state = base_game_state.copy()
        game_state["community"] = community_cards
        if not community_cards:
            game_state["phase"] = "preflop"
        
        result = parse_game_state(json.dumps(game_state))
        print(f"ボード{community_cards}: {result['board_texture']} (期待: {expected_texture})")
        assert result["status"] == "success"
        assert result["board_texture"] == expected_texture


def test_stack_depth_calculation():
    """スタック深度計算テスト"""
    print("\n=== スタック深度計算テスト ===")
    
    base_game_state = {
        "your_id": 0,
        "phase": "preflop",
        "your_cards": ["A♥", "K♠"],
        "community": [],
        "pot": 30,
        "to_call": 20,
        "actions": ["fold", "call (20)", "raise (min 40)"],
        "dealer_button": 2,
        "players": [{"id": 0, "status": "active"}, {"id": 1, "status": "active"}],
        "history": ["Player 1 posted small blind 10", "Player 2 posted big blind 20"]
    }
    
    # 異なるチップ量でテスト
    test_cases = [
        (400, 20),   # 400チップ、BB20 → 20BB
        (1000, 50),  # 1000チップ、BB20 → 50BB
        (2000, 100), # 2000チップ、BB20 → 100BB
        (5000, 250), # 5000チップ、BB20 → 250BB
    ]
    
    for your_chips, expected_depth in test_cases:
        game_state = base_game_state.copy()
        game_state["your_chips"] = your_chips
        
        result = parse_game_state(json.dumps(game_state))
        print(f"チップ{your_chips}: {result['stack_depth']}BB (期待: {expected_depth}BB)")
        assert result["status"] == "success"
        assert result["stack_depth"] == expected_depth


def test_action_history_analysis():
    """アクション履歴分析テスト"""
    print("\n=== アクション履歴分析テスト ===")
    
    base_game_state = {
        "your_id": 0,
        "phase": "flop",
        "your_cards": ["A♥", "K♠"],
        "community": ["A♠", "7♦", "2♣"],
        "your_chips": 1000,
        "pot": 100,
        "to_call": 50,
        "actions": ["fold", "call (50)", "raise (min 100)"],
        "dealer_button": 2,
        "players": [{"id": 0, "status": "active"}, {"id": 1, "status": "active"}]
    }
    
    # 異なる履歴でテスト
    test_cases = [
        ([], "none"),
        (["Player 1 posted small blind 10"], "none"),
        (["Player 1 called 20"], "call"),
        (["Player 1 raised to 50"], "raise"),
        (["Player 1 checked"], "check"),
        (["Player 1 folded"], "fold"),
        (["Player 1 bet 50"], "raise"),
    ]
    
    for history, expected_action in test_cases:
        game_state = base_game_state.copy()
        game_state["history"] = history
        
        result = parse_game_state(json.dumps(game_state))
        print(f"履歴{history}: {result['action_before']} (期待: {expected_action})")
        assert result["status"] == "success"
        assert result["action_before"] == expected_action


def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # テストケース1: 無効なJSON
    print("\n1. 無効なJSON")
    result = parse_game_state("invalid json")
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース2: 空の辞書
    print("\n2. 空の辞書")
    result = parse_game_state(json.dumps({}))
    print(f"結果: {result}")
    assert result["status"] == "success"  # デフォルト値で処理される
    
    # テストケース3: 部分的なデータ
    print("\n3. 部分的なデータ")
    partial_state = {"your_id": 0, "phase": "preflop"}
    result = parse_game_state(json.dumps(partial_state))
    print(f"結果: {result}")
    assert result["status"] == "success"


def test_adk_function_tool():
    """ADK FunctionToolとしてのテスト"""
    print("\n=== ADK FunctionTool テスト ===")
    
    # ツールの関数が正しく設定されているか確認
    assert GameStateParser.func == parse_game_state
    print("✓ ADK FunctionToolとして正しく設定されています")
    
    # ツールの基本情報を表示
    print(f"ツール関数: {GameStateParser.func.__name__}")
    print(f"ツール関数のドキュメント: {GameStateParser.func.__doc__[:100]}...")


def main():
    """メイン関数"""
    print("🎯 GameStateParser ツールテスト開始 🎯")
    print("=" * 50)
    
    try:
        test_basic_parsing()
        test_position_detection()
        test_board_texture_analysis()
        test_stack_depth_calculation()
        test_action_history_analysis()
        test_error_handling()
        test_adk_function_tool()
        
        print("\n" + "=" * 50)
        print("🎉 すべてのテストが完了しました！")
        print("GameStateParserツールは正常に動作しています。")
        
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
