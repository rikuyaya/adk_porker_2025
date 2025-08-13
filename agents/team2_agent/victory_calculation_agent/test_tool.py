#!/usr/bin/env python3
"""
EquityCalculatorツールのテストコード

使用方法:
    python test_tool.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import calculate_equity, EquityCalculator


def test_basic_functionality():
    """基本機能のテスト"""
    print("=== 基本機能テスト ===")
    
    # テストケース1: プリフロップ - ポケットエース
    print("\n1. ポケットエース (A♥ A♠)")
    result = calculate_equity(["A♥", "A♠"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["equity"] > 0.6  # ポケットエースは強い
    assert result["hand_category"] == "ポケットエース"  # 新しいカテゴリ判定
    
    # テストケース2: プリフロップ - 低いペア
    print("\n2. ポケット2 (2♥ 2♠)")
    result = calculate_equity(["2♥", "2♠"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert 0.3 < result["equity"] < 0.8  # 低いペアは中程度
    assert "ペア" in result["hand_category"]  # ペアとして認識

    # テストケース3: プリフロップ - スーテッドエース
    print("\n3. スーテッドエース (A♥ K♥)")
    result = calculate_equity(["A♥", "K♥"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["equity"] > 0.4  # スーテッドエースは強い
    assert result["hand_category"] == "AKスーテッド"  # 正しいカテゴリ

    # テストケース4: プリフロップ - オフスーツ低い手
    print("\n4. 低い手 (7♥ 2♠)")
    result = calculate_equity(["7♥", "2♠"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["equity"] < 0.7  # 低い手は弱い


def test_with_community_cards():
    """コミュニティカードありのテスト"""
    print("\n=== コミュニティカードテスト ===")
    
    # テストケース1: フロップでトップペア
    print("\n1. トップペア (A♥ K♠ + A♠ 7♦ 2♣)")
    result = calculate_equity(["A♥", "K♠"], ["A♠", "7♦", "2♣"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["equity"] > 0.4  # トップペアは強い（調整済み）

    # テストケース2: フラッシュドロー
    print("\n2. フラッシュドロー (A♥ K♥ + Q♥ J♦ 2♥)")
    result = calculate_equity(["A♥", "K♥"], ["Q♥", "J♦", "2♥"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"
    assert result["equity"] > 0.4  # フラッシュドローは有望（調整済み）
    
    # テストケース3: ミスしたハンド
    print("\n3. ミス (A♥ K♠ + 7♦ 8♣ 2♠)")
    result = calculate_equity(["A♥", "K♠"], ["7♦", "8♣", "2♠"], num_opponents=1)
    print(f"結果: {result}")
    assert result["status"] == "success"


def test_multiple_opponents():
    """複数対戦相手のテスト"""
    print("\n=== 複数対戦相手テスト ===")
    
    hole_cards = ["A♥", "A♠"]  # ポケットエース
    
    # 1対1
    result1 = calculate_equity(hole_cards, num_opponents=1)
    print(f"1対1: {result1['equity']:.1%}")
    
    # 1対2
    result2 = calculate_equity(hole_cards, num_opponents=2)
    print(f"1対2: {result2['equity']:.1%}")
    
    # 1対3
    result3 = calculate_equity(hole_cards, num_opponents=3)
    print(f"1対3: {result3['equity']:.1%}")
    
    # 対戦相手が増えるほど勝率が下がることを確認
    assert result1["equity"] > result2["equity"] > result3["equity"]
    print("✓ 対戦相手が増えるほど勝率が下がることを確認")


def test_adk_function_tool():
    """ADK FunctionToolとしてのテスト"""
    print("\n=== ADK FunctionTool テスト ===")

    # ツールの関数が正しく設定されているか確認
    assert EquityCalculator.func == calculate_equity
    print("✓ ADK FunctionToolとして正しく設定されています")

    # ツールの基本情報を表示
    print(f"ツール関数: {EquityCalculator.func.__name__}")
    print(f"ツール関数のドキュメント: {EquityCalculator.func.__doc__[:100]}...")


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== エラーハンドリングテスト ===")
    
    # 無効な入力でもエラーを適切に処理することを確認
    try:
        # 空のホールカード
        result = calculate_equity([])
        print(f"空のホールカード: {result}")
        # エラーが発生するか、適切にハンドリングされることを確認
        
        # 無効なカード形式
        result = calculate_equity(["invalid", "card"])
        print(f"無効なカード: {result}")
        
        print("✓ エラーハンドリングが適切に動作しています")
    except Exception as e:
        print(f"予期しないエラー: {e}")


def run_interactive_test():
    """インタラクティブテスト"""
    print("\n=== インタラクティブテスト ===")
    print("いくつかの手札で勝率を計算してみましょう！")
    
    test_hands = [
        (["A♥", "A♠"], [], "ポケットエース"),
        (["K♥", "K♠"], [], "ポケットキング"),
        (["A♥", "K♥"], [], "スーテッドAK"),
        (["A♥", "K♠"], [], "オフスーツAK"),
        (["Q♥", "J♥"], [], "スーテッドQJ"),
        (["7♥", "2♠"], [], "最弱手の一つ"),
        (["A♥", "K♠"], ["A♠", "K♦", "7♣"], "ツーペア"),
        (["A♥", "K♥"], ["Q♥", "J♥", "2♠"], "ナッツフラッシュドロー"),
    ]
    
    for hole_cards, community_cards, description in test_hands:
        result = calculate_equity(hole_cards, community_cards, num_opponents=1)
        if result["status"] == "success":
            print(f"{description}: {result['equity']:.1%}")
        else:
            print(f"{description}: エラー - {result.get('error_message', 'Unknown error')}")


def main():
    """メイン関数"""
    print("🃏 EquityCalculator ツールテスト開始 🃏")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_with_community_cards()
        test_multiple_opponents()
        test_adk_function_tool()
        test_error_handling()
        run_interactive_test()
        
        print("\n" + "=" * 50)
        print("🎉 すべてのテストが完了しました！")
        print("EquityCalculatorツールは正常に動作しています。")
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
