#!/usr/bin/env python3
"""
SizingToolのテストコード

使用方法:
    python test_tool.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import calculate_bet_sizing, SizingTool


def test_basic_sizing():
    """基本的なベットサイズテスト"""
    print("=== 基本ベットサイズテスト ===")
    
    # テストケース1: 強いハンド、ドライボード
    print("\n1. 強いハンド、ドライボード")
    result = calculate_bet_sizing(100, 0.8, "dry", "IP")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_size"] > 0
    assert result["size_category"] in ["スモール", "ミディアム", "ラージ", "オーバー", "マッシブ"]
    
    # テストケース2: 弱いハンド（ブラフ）、ウェットボード
    print("\n2. 弱いハンド（ブラフ）、ウェットボード")
    result = calculate_bet_sizing(100, 0.2, "wet", "OOP")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_size"] > 0
    
    # テストケース3: 中程度ハンド、コーディネートボード
    print("\n3. 中程度ハンド、コーディネートボード")
    result = calculate_bet_sizing(100, 0.5, "coordinated", "IP")
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["recommended_size"] > 0


def test_hand_strength_scaling():
    """ハンド強度によるサイズスケーリングテスト"""
    print("\n=== ハンド強度スケーリングテスト ===")
    
    pot_size = 100
    hand_strengths = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    print("ハンド強度別ベットサイズ:")
    for strength in hand_strengths:
        result = calculate_bet_sizing(pot_size, strength, "dry", "IP")
        if result["status"] == "success":
            print(f"  強度 {strength:.1f}: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%) - {result['size_category']}")
        assert result["status"] == "success"


def test_board_texture_differences():
    """ボードテクスチャ別の違いテスト"""
    print("\n=== ボードテクスチャテスト ===")
    
    pot_size = 100
    hand_strength = 0.7
    textures = ["dry", "wet", "coordinated"]
    
    print("ボードテクスチャ別ベットサイズ:")
    for texture in textures:
        result = calculate_bet_sizing(pot_size, hand_strength, texture, "IP")
        if result["status"] == "success":
            print(f"  {texture}: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%) - {result['strategic_goal']}")
        assert result["status"] == "success"


def test_position_effects():
    """ポジション効果テスト"""
    print("\n=== ポジション効果テスト ===")
    
    pot_size = 100
    hand_strength = 0.6
    positions = ["IP", "OOP"]
    textures = ["dry", "wet"]
    
    for texture in textures:
        print(f"\n{texture}ボード:")
        for position in positions:
            result = calculate_bet_sizing(pot_size, hand_strength, texture, position)
            if result["status"] == "success":
                print(f"  {position}: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%)")
            assert result["status"] == "success"


def test_multiway_adjustments():
    """マルチウェイ調整テスト"""
    print("\n=== マルチウェイ調整テスト ===")
    
    pot_size = 100
    hand_strength = 0.6
    opponent_counts = [1, 2, 3]
    
    print("対戦相手数別ベットサイズ:")
    for num_opponents in opponent_counts:
        result = calculate_bet_sizing(pot_size, hand_strength, "wet", "IP", num_opponents=num_opponents)
        if result["status"] == "success":
            print(f"  {num_opponents}人: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%)")
        assert result["status"] == "success"


def test_action_types():
    """アクションタイプ別テスト"""
    print("\n=== アクションタイプテスト ===")
    
    pot_size = 100
    hand_strength = 0.7
    action_types = ["bet", "raise", "3bet"]
    
    print("アクションタイプ別サイズ:")
    for action_type in action_types:
        result = calculate_bet_sizing(pot_size, hand_strength, "dry", "IP", action_type=action_type)
        if result["status"] == "success":
            print(f"  {action_type}: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%)")
        assert result["status"] == "success"


def test_stack_depth_effects():
    """スタック深度効果テスト"""
    print("\n=== スタック深度効果テスト ===")
    
    pot_size = 100
    hand_strength = 0.6
    stack_depths = [20, 50, 100, 200]
    
    print("スタック深度別ベットサイズ:")
    for stack_depth in stack_depths:
        result = calculate_bet_sizing(pot_size, hand_strength, "dry", "IP", stack_depth=stack_depth)
        if result["status"] == "success":
            print(f"  {stack_depth}BB: {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%)")
        assert result["status"] == "success"


def test_alternative_sizes():
    """代替サイズテスト"""
    print("\n=== 代替サイズテスト ===")
    
    result = calculate_bet_sizing(100, 0.7, "wet", "IP")
    print(f"メインサイズ: {result['recommended_size']:.0f}")
    
    if result["status"] == "success" and result["alternative_sizes"]:
        print("代替サイズ:")
        for alt in result["alternative_sizes"]:
            print(f"  {alt['category']}: {alt['size']:.0f} ({alt['percentage']:.0f}%) - {alt['use_case']}")
        assert len(result["alternative_sizes"]) > 0


def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # テストケース1: 無効なポットサイズ
    print("\n1. 無効なポットサイズ")
    result = calculate_bet_sizing(0, 0.5, "dry", "IP")
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース2: 無効なハンド強度
    print("\n2. 無効なハンド強度")
    result = calculate_bet_sizing(100, 1.5, "dry", "IP")
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース3: 無効なボードテクスチャ
    print("\n3. 無効なボードテクスチャ")
    result = calculate_bet_sizing(100, 0.5, "invalid", "IP")
    print(f"結果: {result}")
    assert result["status"] == "error"


def test_adk_function_tool():
    """ADK FunctionToolとしてのテスト"""
    print("\n=== ADK FunctionTool テスト ===")
    
    # ツールの関数が正しく設定されているか確認
    assert SizingTool.func == calculate_bet_sizing
    print("✓ ADK FunctionToolとして正しく設定されています")
    
    # ツールの基本情報を表示
    print(f"ツール関数: {SizingTool.func.__name__}")
    print(f"ツール関数のドキュメント: {SizingTool.func.__doc__[:100]}...")


def test_real_scenarios():
    """実戦的なシナリオテスト"""
    print("\n=== 実戦シナリオテスト ===")
    
    scenarios = [
        (100, 0.9, "dry", "IP", "bet", 1, "ナッツハンド、ドライボード"),
        (150, 0.7, "wet", "OOP", "bet", 2, "強いハンド、ウェットボード、マルチウェイ"),
        (80, 0.3, "coordinated", "IP", "bet", 1, "ブラフ、コーディネートボード"),
        (200, 0.6, "dry", "IP", "raise", 1, "中強ハンド、レイズサイズ"),
        (120, 0.8, "wet", "OOP", "3bet", 1, "強いハンド、3ベットサイズ"),
    ]
    
    for pot_size, hand_strength, board_texture, position, action_type, num_opponents, description in scenarios:
        result = calculate_bet_sizing(pot_size, hand_strength, board_texture, position, action_type, num_opponents)
        if result["status"] == "success":
            print(f"{description}: {result['size_category']} {result['recommended_size']:.0f} ({result['pot_percentage']:.0f}%)")
        else:
            print(f"{description}: エラー")


def main():
    """メイン関数"""
    print("🎯 SizingTool ツールテスト開始 🎯")
    print("=" * 50)
    
    try:
        test_basic_sizing()
        test_hand_strength_scaling()
        test_board_texture_differences()
        test_position_effects()
        test_multiway_adjustments()
        test_action_types()
        test_stack_depth_effects()
        test_alternative_sizes()
        test_error_handling()
        test_adk_function_tool()
        test_real_scenarios()
        
        print("\n" + "=" * 50)
        print("🎉 すべてのテストが完了しました！")
        print("SizingToolは正常に動作しています。")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
