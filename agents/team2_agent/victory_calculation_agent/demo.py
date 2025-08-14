#!/usr/bin/env python3
"""
EquityCalculatorツールのデモンストレーション

使用方法:
    python demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tool import calculate_equity


def demo_preflop_hands():
    """プリフロップハンドのデモ"""
    print("🃏 プリフロップハンド勝率計算デモ")
    print("=" * 40)
    
    preflop_hands = [
        (["A♥", "A♠"], "ポケットエース（最強ペア）"),
        (["K♥", "K♠"], "ポケットキング"),
        (["Q♥", "Q♠"], "ポケットクイーン"),
        (["J♥", "J♠"], "ポケットジャック"),
        (["10♥", "10♠"], "ポケット10"),
        (["9♥", "9♠"], "ポケット9"),
        (["2♥", "2♠"], "ポケット2（最弱ペア）"),
        (["A♥", "K♥"], "スーテッドAK（最強ドロー）"),
        (["A♥", "K♠"], "オフスーツAK"),
        (["A♥", "Q♥"], "スーテッドAQ"),
        (["K♥", "Q♥"], "スーテッドKQ"),
        (["Q♥", "J♥"], "スーテッドQJ"),
        (["J♥", "10♥"], "スーテッドJT"),
        (["10♥", "9♥"], "スーテッド109"),
        (["7♥", "2♠"], "7-2オフスーツ（最弱手）"),
    ]
    
    print("対戦相手1人の場合:")
    for hole_cards, description in preflop_hands:
        result = calculate_equity(hole_cards, num_opponents=1)
        if result["status"] == "success":
            equity = result["equity"]
            print(f"  {description:25} : {equity:6.1%}")
        else:
            print(f"  {description:25} : エラー")


def demo_postflop_scenarios():
    """ポストフロップシナリオのデモ"""
    print("\n🎯 ポストフロップシナリオデモ")
    print("=" * 40)
    
    scenarios = [
        (["A♥", "K♠"], ["A♠", "7♦", "2♣"], "トップペア・トップキッカー"),
        (["A♥", "A♠"], ["K♦", "Q♣", "J♠"], "オーバーペア"),
        (["K♥", "Q♥"], ["A♥", "J♥", "2♠"], "ナッツフラッシュドロー"),
        (["10♥", "9♠"], ["Q♦", "J♣", "8♥"], "オープンエンドストレートドロー"),
        (["A♥", "K♠"], ["7♦", "8♣", "2♠"], "エアー（何もない）"),
        (["7♥", "7♠"], ["A♦", "K♣", "Q♠"], "ポケットペア（アンダーペア）"),
        (["A♥", "K♠"], ["A♠", "K♦", "7♣"], "ツーペア"),
        (["Q♥", "Q♠"], ["Q♦", "7♣", "2♠"], "セット（スリーカード）"),
    ]
    
    for hole_cards, community_cards, description in scenarios:
        result = calculate_equity(hole_cards, community_cards, num_opponents=1)
        if result["status"] == "success":
            equity = result["equity"]
            print(f"  {description:30} : {equity:6.1%}")
        else:
            print(f"  {description:30} : エラー")


def demo_opponent_count_effect():
    """対戦相手数の影響デモ"""
    print("\n👥 対戦相手数による勝率変化デモ")
    print("=" * 40)
    
    test_hands = [
        (["A♥", "A♠"], "ポケットエース"),
        (["K♥", "K♠"], "ポケットキング"),
        (["A♥", "K♥"], "スーテッドAK"),
        (["Q♥", "J♥"], "スーテッドQJ"),
    ]
    
    for hole_cards, description in test_hands:
        print(f"\n{description}:")
        for opponents in range(1, 6):
            result = calculate_equity(hole_cards, num_opponents=opponents)
            if result["status"] == "success":
                equity = result["equity"]
                print(f"  対戦相手{opponents}人: {equity:6.1%}")


def demo_interactive():
    """インタラクティブデモ"""
    print("\n🎮 インタラクティブ勝率計算")
    print("=" * 40)
    print("カード形式: A♥, K♠, Q♦, J♣, 10♠, 9♥, 8♦, 7♣, 6♠, 5♥, 4♦, 3♣, 2♠")
    print("終了するには 'quit' と入力してください")
    
    while True:
        try:
            print("\n--- 新しい計算 ---")
            
            # ホールカード入力
            hole_input = input("ホールカード（例: A♥ K♠）: ").strip()
            if hole_input.lower() == 'quit':
                break
            
            hole_cards = hole_input.split()
            if len(hole_cards) != 2:
                print("❌ ホールカードは2枚入力してください")
                continue
            
            # コミュニティカード入力（オプション）
            community_input = input("コミュニティカード（オプション、例: Q♥ J♦ 10♣）: ").strip()
            community_cards = community_input.split() if community_input else []
            
            # 対戦相手数入力
            opponents_input = input("対戦相手数（デフォルト: 1）: ").strip()
            try:
                num_opponents = int(opponents_input) if opponents_input else 1
            except ValueError:
                num_opponents = 1
            
            # 勝率計算
            result = calculate_equity(hole_cards, community_cards, num_opponents)
            
            if result["status"] == "success":
                print(f"\n🎯 結果:")
                print(f"   勝率: {result['equity']:.1%}")
                print(f"   ホールカード: {' '.join(result['hole_cards'])}")
                if result['community_cards']:
                    print(f"   コミュニティカード: {' '.join(result['community_cards'])}")
                print(f"   対戦相手: {result['num_opponents']}人")
                print(f"   説明: {result['description']}")
            else:
                print(f"❌ エラー: {result.get('error_message', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print("\n\n👋 終了します")
            break
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")


def main():
    """メイン関数"""
    print("🃏 EquityCalculator ツールデモ 🃏")
    print("=" * 50)
    
    # 各デモを実行
    demo_preflop_hands()
    demo_postflop_scenarios()
    demo_opponent_count_effect()
    
    # インタラクティブモードの選択
    print("\n" + "=" * 50)
    choice = input("インタラクティブモードを試しますか？ (y/n): ").strip().lower()
    if choice in ['y', 'yes', 'はい']:
        demo_interactive()
    
    print("\n🎉 デモ終了！EquityCalculatorツールをお楽しみください！")


if __name__ == "__main__":
    main()
