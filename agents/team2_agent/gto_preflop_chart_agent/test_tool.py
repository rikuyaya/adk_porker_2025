#!/usr/bin/env python3
"""
GtoPreflopChartToolのテストコード

使用方法:
    python test_tool.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import get_gto_preflop_action, GtoPreflopChartTool


def test_premium_hands():
    """プレミアムハンドのテスト"""
    print("=== プレミアムハンドテスト ===")
    
    # テストケース1: ポケットエース UTG
    print("\n1. ポケットエース UTG")
    result = get_gto_preflop_action(["A♥", "A♠"], "UTG")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_action"] == "raise"
    assert result["hand_strength_tier"] == "premium"
    
    # テストケース2: AKスーテッド BTN
    print("\n2. AKスーテッド BTN")
    result = get_gto_preflop_action(["A♥", "K♥"], "BTN")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_action"] == "raise"
    assert result["hand_notation"] == "AKs"


def test_position_differences():
    """ポジション別の違いテスト"""
    print("\n=== ポジション別テスト ===")
    
    test_hand = ["Q♥", "J♠"]  # QJo
    positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
    
    for position in positions:
        result = get_gto_preflop_action(test_hand, position)
        print(f"{position}: {result['recommended_action']} ({result['action_frequency']}%)")
        assert result["status"] == "success"
        assert result["hand_notation"] == "QJo"


def test_vs_raise_scenarios():
    """レイズに対する対応テスト"""
    print("\n=== レイズ対応テスト ===")
    
    # テストケース1: プレミアムハンドでレイズに対応
    print("\n1. ポケットキング vs レイズ")
    result = get_gto_preflop_action(["K♥", "K♠"], "CO", "raise")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_action"] in ["raise", "call"]  # 3betまたはコール
    
    # テストケース2: 弱いハンドでレイズに対応
    print("\n2. 弱いハンド vs レイズ")
    result = get_gto_preflop_action(["7♥", "2♠"], "BTN", "raise")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_action"] == "fold"


def test_hand_notation():
    """ハンド記法テスト"""
    print("\n=== ハンド記法テスト ===")
    
    test_cases = [
        (["A♥", "A♠"], "AA"),
        (["A♥", "K♥"], "AKs"),
        (["A♥", "K♠"], "AKo"),
        (["Q♥", "J♥"], "QJs"),
        (["Q♥", "J♠"], "QJo"),
        (["10♥", "9♠"], "T9o"),
        (["2♥", "2♠"], "22"),
    ]
    
    for hole_cards, expected_notation in test_cases:
        result = get_gto_preflop_action(hole_cards, "BTN")
        print(f"{hole_cards} -> {result['hand_notation']} (期待: {expected_notation})")
        assert result["status"] == "success"
        assert result["hand_notation"] == expected_notation


def test_hand_tiers():
    """ハンド強度ティアテスト"""
    print("\n=== ハンド強度ティアテスト ===")
    
    tier_tests = [
        (["A♥", "A♠"], "premium"),
        (["K♥", "K♠"], "premium"),
        (["A♥", "K♠"], "premium"),
        (["Q♥", "Q♠"], "premium"),
        (["10♥", "10♠"], "strong"),
        (["A♥", "Q♠"], "strong"),
        (["8♥", "8♠"], "playable"),
        (["A♥", "5♠"], "speculative"),
        (["7♥", "2♠"], "weak"),
    ]
    
    for hole_cards, expected_tier in tier_tests:
        result = get_gto_preflop_action(hole_cards, "BTN")
        print(f"{hole_cards} -> {result['hand_strength_tier']} (期待: {expected_tier})")
        assert result["status"] == "success"
        assert result["hand_strength_tier"] == expected_tier


def test_multiway_scenarios():
    """マルチウェイシナリオテスト"""
    print("\n=== マルチウェイテスト ===")
    
    # テストケース1: コールに対する対応
    print("\n1. 中程度ハンド vs コール")
    result = get_gto_preflop_action(["9♥", "9♠"], "CO", "call")
    print(f"結果: {result}")
    assert result["status"] == "success"
    
    # テストケース2: 投機的ハンド vs コール
    print("\n2. 投機的ハンド vs コール")
    result = get_gto_preflop_action(["7♥", "6♥"], "BTN", "call")
    print(f"結果: {result}")
    assert result["status"] == "success"


def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # テストケース1: 無効なポジション
    print("\n1. 無効なポジション")
    result = get_gto_preflop_action(["A♥", "K♠"], "INVALID")
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース2: 無効なホールカード数
    print("\n2. 無効なホールカード数")
    result = get_gto_preflop_action(["A♥"], "BTN")
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース3: 空のホールカード
    print("\n3. 空のホールカード")
    result = get_gto_preflop_action([], "BTN")
    print(f"結果: {result}")
    assert result["status"] == "error"


def test_adk_function_tool():
    """ADK FunctionToolとしてのテスト"""
    print("\n=== ADK FunctionTool テスト ===")
    
    # ツールの関数が正しく設定されているか確認
    assert GtoPreflopChartTool.func == get_gto_preflop_action
    print("✓ ADK FunctionToolとして正しく設定されています")
    
    # ツールの基本情報を表示
    print(f"ツール関数: {GtoPreflopChartTool.func.__name__}")
    print(f"ツール関数のドキュメント: {GtoPreflopChartTool.func.__doc__[:100]}...")


def test_real_scenarios():
    """実戦的なシナリオテスト"""
    print("\n=== 実戦シナリオテスト ===")
    
    scenarios = [
        (["A♥", "A♠"], "UTG", "none", "プレミアムハンド早いポジション"),
        (["K♥", "Q♥"], "BTN", "none", "スーテッドブロードウェイ レイト"),
        (["5♥", "5♠"], "MP", "raise", "ポケットペア vs レイズ"),
        (["A♥", "7♠"], "SB", "call", "エースラグ マルチウェイ"),
        (["J♥", "10♥"], "CO", "none", "スーテッドコネクター"),
    ]
    
    for hole_cards, position, action_before, description in scenarios:
        result = get_gto_preflop_action(hole_cards, position, action_before)
        if result["status"] == "success":
            print(f"{description}: {result['recommended_action']} ({result['action_frequency']}%)")
        else:
            print(f"{description}: エラー")


def main():
    """メイン関数"""
    print("🎯 GtoPreflopChartTool ツールテスト開始 🎯")
    print("=" * 50)
    
    try:
        test_premium_hands()
        test_position_differences()
        test_vs_raise_scenarios()
        test_hand_notation()
        test_hand_tiers()
        test_multiway_scenarios()
        test_error_handling()
        test_adk_function_tool()
        test_real_scenarios()
        
        print("\n" + "=" * 50)
        print("🎉 すべてのテストが完了しました！")
        print("GtoPreflopChartToolは正常に動作しています。")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
