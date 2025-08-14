#!/usr/bin/env python3
"""
PotOddsCalculatorツールのテストコード

使用方法:
    python test_tool.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import calculate_pot_odds, calculate_reverse_implied_odds, PotOddsCalculator


def test_basic_pot_odds():
    """基本的なポットオッズテスト"""
    print("=== 基本ポットオッズテスト ===")
    
    # テストケース1: 利益的なコール
    print("\n1. 利益的なコール (ポット100, コール20, 勝率30%)")
    result = calculate_pot_odds(100, 20, 0.30)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["is_profitable"] == True
    assert result["recommendation"] in ["call", "strong_call", "marginal_call"]
    
    # テストケース2: 不利なコール
    print("\n2. 不利なコール (ポット100, コール50, 勝率20%)")
    result = calculate_pot_odds(100, 50, 0.20)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["is_profitable"] == False
    assert result["recommendation"] in ["fold", "strong_fold", "marginal_fold"]
    
    # テストケース3: ギリギリのコール
    print("\n3. ギリギリのコール (ポット100, コール25, 勝率20%)")
    result = calculate_pot_odds(100, 25, 0.20)
    print(f"結果: {result}")
    assert result["status"] == "success"
    print(f"利益的: {result['is_profitable']}, 推奨: {result['recommendation']}")


def test_pot_odds_calculations():
    """ポットオッズ計算の正確性テスト"""
    print("\n=== ポットオッズ計算正確性テスト ===")
    
    # テストケース1: 2:1のポットオッズ
    print("\n1. 2:1のポットオッズ (ポット200, コール100)")
    result = calculate_pot_odds(200, 100, 0.40)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert abs(result["pot_odds_percentage"] - 33.33) < 0.1  # 約33.33%
    assert abs(result["required_equity_percentage"] - 33.33) < 0.1
    
    # テストケース2: 3:1のポットオッズ
    print("\n2. 3:1のポットオッズ (ポット300, コール100)")
    result = calculate_pot_odds(300, 100, 0.30)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert abs(result["pot_odds_percentage"] - 25.0) < 0.1  # 25%
    assert abs(result["required_equity_percentage"] - 25.0) < 0.1


def test_expected_value():
    """期待値計算テスト"""
    print("\n=== 期待値計算テスト ===")
    
    # テストケース1: プラスEV
    print("\n1. プラスEV (ポット100, コール20, 勝率30%)")
    result = calculate_pot_odds(100, 20, 0.30)
    print(f"結果: {result}")
    assert result["status"] == "success"
    expected_ev = (0.30 * 120) - 20  # 36 - 20 = 16
    assert abs(result["expected_value"] - 16.0) < 0.1
    
    # テストケース2: マイナスEV
    print("\n2. マイナスEV (ポット100, コール50, 勝率20%)")
    result = calculate_pot_odds(100, 50, 0.20)
    print(f"結果: {result}")
    assert result["status"] == "success"
    expected_ev = (0.20 * 150) - 50  # 30 - 50 = -20
    assert abs(result["expected_value"] - (-20.0)) < 0.1


def test_implied_odds():
    """インプライドオッズテスト"""
    print("\n=== インプライドオッズテスト ===")
    
    # テストケース1: インプライドオッズ考慮
    print("\n1. インプライドオッズ考慮 (ポット100, コール30, 勝率22%, 係数1.5)")
    result = calculate_pot_odds(100, 30, 0.22, 1.5)
    print(f"結果: {result}")
    assert result["status"] == "success"
    # 通常は不利だが、インプライドオッズで利益的になる可能性
    
    # テストケース2: リバースインプライドオッズ
    print("\n2. リバースインプライドオッズ (ポット100, コール20, 勝率30%, 係数0.8)")
    result = calculate_reverse_implied_odds(100, 20, 0.30, 0.8)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert "reverse_implied_factor" in result
    assert result["original_equity"] == 0.30


def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # テストケース1: 無効なコール金額
    print("\n1. 無効なコール金額 (0以下)")
    result = calculate_pot_odds(100, 0, 0.30)
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース2: 無効な勝率
    print("\n2. 無効な勝率 (範囲外)")
    result = calculate_pot_odds(100, 20, 1.5)
    print(f"結果: {result}")
    assert result["status"] == "error"
    
    # テストケース3: 負のポットサイズ
    print("\n3. 負のポットサイズ")
    result = calculate_pot_odds(-50, 20, 0.30)
    print(f"結果: {result}")
    assert result["status"] == "error"


def test_adk_function_tool():
    """ADK FunctionToolとしてのテスト"""
    print("\n=== ADK FunctionTool テスト ===")
    
    # ツールの関数が正しく設定されているか確認
    assert PotOddsCalculator.func == calculate_pot_odds
    print("✓ ADK FunctionToolとして正しく設定されています")
    
    # ツールの基本情報を表示
    print(f"ツール関数: {PotOddsCalculator.func.__name__}")
    print(f"ツール関数のドキュメント: {PotOddsCalculator.func.__doc__[:100]}...")


def test_real_scenarios():
    """実戦的なシナリオテスト"""
    print("\n=== 実戦シナリオテスト ===")
    
    scenarios = [
        (100, 20, 0.25, "フラッシュドロー (9アウツ)"),
        (200, 50, 0.17, "ガットショット (4アウツ)"),
        (150, 75, 0.35, "オープンエンドストレートドロー (8アウツ)"),
        (80, 40, 0.45, "トップペア"),
        (300, 100, 0.20, "弱いドロー"),
    ]
    
    for pot_size, call_amount, equity, description in scenarios:
        result = calculate_pot_odds(pot_size, call_amount, equity)
        if result["status"] == "success":
            print(f"{description}: {result['recommendation']} (EV: {result['expected_value']:+.1f})")
        else:
            print(f"{description}: エラー")


def main():
    """メイン関数"""
    print("🎯 PotOddsCalculator ツールテスト開始 🎯")
    print("=" * 50)
    
    try:
        test_basic_pot_odds()
        test_pot_odds_calculations()
        test_expected_value()
        test_implied_odds()
        test_error_handling()
        test_adk_function_tool()
        test_real_scenarios()
        
        print("\n" + "=" * 50)
        print("🎉 すべてのテストが完了しました！")
        print("PotOddsCalculatorツールは正常に動作しています。")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
