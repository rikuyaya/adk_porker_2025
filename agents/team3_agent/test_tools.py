#!/usr/bin/env python3
"""
team3エージェントの各ツールをテストするスクリプト
"""

import json
import sys
import os
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 各ツールをインポート
try:
    from agents.team3_agent.tools.state_parser import parse_game_state
    from agents.team3_agent.tools.pot_odds_calculator import calculate_pot_odds
    from agents.team3_agent.tools.range_provider import get_poker_action
    from agents.team3_agent.tools.equity_simulator import calculate_equity
    from agents.team3_agent.tools.sizing_policy import decide_bet_size
    from agents.team3_agent.tools.result_integrator import integrate_tool_results
    print("✅ 全ツールのインポートに成功しました")
except ImportError as e:
    print(f"❌ ツールのインポートに失敗: {e}")
    sys.exit(1)

# ダミーのToolContextクラス
class DummyToolContext:
    def __init__(self):
        self.invocation_context = DummyInvocationContext()

class DummyInvocationContext:
    def __init__(self):
        self.session = DummySession()

class DummySession:
    def __init__(self):
        self.state = {}

def test_state_parser():
    """ゲーム状態パーサーのテスト"""
    print("\n🧪 Testing State Parser...")

    # 実際のゲーム状態JSON（提供された形式）
    test_game_state = {
        "your_id": 2,
        "phase": "preflop",
        "your_cards": ["8♦", "J♦"],
        "community": [],
        "your_chips": 2000,
        "your_bet_this_round": 0,
        "your_total_bet_this_hand": 0,
        "pot": 30,
        "to_call": 20,
        "dealer_button": 2,
        "current_turn": 2,
        "players": [
            {"id": 0, "chips": 1990, "bet": 10, "status": "active"},
            {"id": 1, "chips": 1980, "bet": 20, "status": "active"}
        ],
        "actions": ["fold", "call (20)", "raise (min 40)", "all-in (2000)"],
        "history": ["Player 0 posted small blind 10", "Player 1 posted big blind 20"]
    }
    
    try:
        tool_context = DummyToolContext()
        result = parse_game_state(json.dumps(test_game_state), tool_context)
        print(f"✅ State Parser成功: {result}")
        return result
    except Exception as e:
        print(f"❌ State Parser失敗: {e}")
        return None

def test_pot_odds_calculator():
    """ポットオッズ計算ツールのテスト"""
    print("\n🧪 Testing Pot Odds Calculator...")

    # 実際の形式に合わせたテスト用の状態
    test_state = {
        "pot": 30,
        "to_call": 20,
        "your_chips": 2000,
        "phase": "preflop"
    }
    
    try:
        tool_context = DummyToolContext()
        result = calculate_pot_odds(json.dumps(test_state), tool_context)
        print(f"✅ Pot Odds Calculator成功: {result}")
        return result
    except Exception as e:
        print(f"❌ Pot Odds Calculator失敗: {e}")
        return None

def test_range_provider():
    """レンジプロバイダーのテスト"""
    print("\n🧪 Testing Range Provider...")

    # 実際の形式に合わせたテスト用の状態
    test_state = {
        "your_cards": ["8♦", "J♦"],
        "dealer_button": 2,
        "your_id": 2,
        "phase": "preflop",
        "players": [
            {"id": 0, "chips": 1990, "bet": 10, "status": "active"},
            {"id": 1, "chips": 1980, "bet": 20, "status": "active"}
        ]
    }
    
    try:
        tool_context = DummyToolContext()
        result = get_poker_action(json.dumps(test_state), tool_context)
        print(f"✅ Range Provider成功: {result}")
        return result
    except Exception as e:
        print(f"❌ Range Provider失敗: {e}")
        return None

def test_equity_simulator():
    """エクイティシミュレーターのテスト"""
    print("\n🧪 Testing Equity Simulator...")

    # 実際の形式に合わせたテスト用の状態
    test_state = {
        "your_cards": ["8♦", "J♦"],
        "community": [],
        "phase": "preflop",
        "players": [
            {"id": 0, "chips": 1990, "bet": 10, "status": "active"},
            {"id": 1, "chips": 1980, "bet": 20, "status": "active"}
        ]
    }
    
    try:
        tool_context = DummyToolContext()
        result = calculate_equity(json.dumps(test_state), [], tool_context)
        print(f"✅ Equity Simulator成功: {result}")
        return result
    except Exception as e:
        print(f"❌ Equity Simulator失敗: {e}")
        return None

def test_sizing_policy():
    """サイジングポリシーのテスト"""
    print("\n🧪 Testing Sizing Policy...")

    # 実際の形式に合わせたテスト用の状態とミックス
    test_state = {
        "pot": 30,
        "to_call": 20,
        "your_chips": 2000,
        "phase": "preflop"
    }

    test_mix = {
        "action": "raise",
        "frequency": 0.7
    }
    
    try:
        tool_context = DummyToolContext()
        result = decide_bet_size(json.dumps(test_state), json.dumps(test_mix), tool_context)
        print(f"✅ Sizing Policy成功: {result}")
        return result
    except Exception as e:
        print(f"❌ Sizing Policy失敗: {e}")
        return None

def test_result_integrator():
    """結果統合ツールのテスト"""
    print("\n🧪 Testing Result Integrator...")
    
    # テスト用のデータ（前のテストの結果を模擬）
    test_state = {"pot": 200, "current_bet": 50}
    test_pot_odds = {"pot_odds": 0.25}
    test_mix = {"action": "raise", "frequency": 0.7}
    test_equity = {"equity": 0.65}
    test_sizing = {"raise_amount": 150}
    
    try:
        tool_context = DummyToolContext()
        result = integrate_tool_results(
            json.dumps(test_state),
            json.dumps(test_pot_odds),
            json.dumps(test_mix),
            json.dumps(test_equity),
            json.dumps(test_sizing),
            tool_context
        )
        print(f"✅ Result Integrator成功: {result}")
        return result
    except Exception as e:
        print(f"❌ Result Integrator失敗: {e}")
        return None

def run_full_pipeline_test():
    """完全なパイプラインテスト"""
    print("\n🚀 Running Full Pipeline Test...")
    
    # 1. State Parser
    state_result = test_state_parser()
    if not state_result:
        print("❌ パイプライン中断: State Parser失敗")
        return
    
    # 2. Pot Odds Calculator
    pot_odds_result = test_pot_odds_calculator()
    if not pot_odds_result:
        print("❌ パイプライン中断: Pot Odds Calculator失敗")
        return
    
    # 3. Range Provider
    mix_result = test_range_provider()
    if not mix_result:
        print("❌ パイプライン中断: Range Provider失敗")
        return
    
    # 4. Equity Simulator
    equity_result = test_equity_simulator()
    if not equity_result:
        print("❌ パイプライン中断: Equity Simulator失敗")
        return
    
    # 5. Sizing Policy
    sizing_result = test_sizing_policy()
    if not sizing_result:
        print("❌ パイプライン中断: Sizing Policy失敗")
        return
    
    # 6. Result Integrator
    final_result = test_result_integrator()
    if not final_result:
        print("❌ パイプライン中断: Result Integrator失敗")
        return
    
    print("\n🎉 完全なパイプラインテスト成功！")
    print(f"最終結果: {final_result}")

def test_with_real_input():
    """実際の入力形式でのテスト"""
    print("\n🎮 Testing with Real Game Input...")

    # 提供された実際のゲーム状態
    real_game_state = {
        "your_id": 2,
        "phase": "preflop",
        "your_cards": ["8♦", "J♦"],
        "community": [],
        "your_chips": 2000,
        "your_bet_this_round": 0,
        "your_total_bet_this_hand": 0,
        "pot": 30,
        "to_call": 20,
        "dealer_button": 2,
        "current_turn": 2,
        "players": [
            {"id": 0, "chips": 1990, "bet": 10, "status": "active"},
            {"id": 1, "chips": 1980, "bet": 20, "status": "active"}
        ],
        "actions": ["fold", "call (20)", "raise (min 40)", "all-in (2000)"],
        "history": ["Player 0 posted small blind 10", "Player 1 posted big blind 20"]
    }

    print(f"入力: {json.dumps(real_game_state, indent=2, ensure_ascii=False)}")

    try:
        tool_context = DummyToolContext()

        # 1. State Parser
        print("\n1️⃣ State Parser...")
        state_result = parse_game_state(json.dumps(real_game_state), tool_context)
        print(f"結果: {state_result}")

        # 2. Pot Odds Calculator
        print("\n2️⃣ Pot Odds Calculator...")
        pot_odds_result = calculate_pot_odds(json.dumps(real_game_state), tool_context)
        print(f"結果: {pot_odds_result}")

        # 3. Range Provider
        print("\n3️⃣ Range Provider...")
        mix_result = get_poker_action(json.dumps(real_game_state), tool_context)
        print(f"結果: {mix_result}")

        # 4. Equity Simulator
        print("\n4️⃣ Equity Simulator...")
        equity_result = calculate_equity(json.dumps(real_game_state), [], tool_context)
        print(f"結果: {equity_result}")

        # 5. Sizing Policy
        print("\n5️⃣ Sizing Policy...")
        sizing_result = decide_bet_size(json.dumps(real_game_state), json.dumps(mix_result), tool_context)
        print(f"結果: {sizing_result}")

        # 6. Result Integrator
        print("\n6️⃣ Result Integrator...")
        final_result = integrate_tool_results(
            json.dumps(state_result),
            json.dumps(pot_odds_result),
            json.dumps(mix_result),
            json.dumps(equity_result),
            json.dumps(sizing_result),
            tool_context
        )
        print(f"最終結果: {final_result}")

        print("\n🎉 実際の入力でのテスト成功！")
        return final_result

    except Exception as e:
        print(f"❌ 実際の入力でのテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン関数"""
    print("🎯 team3エージェント ツールテスト開始")
    print("=" * 50)

    # 個別ツールテスト
    test_state_parser()
    test_pot_odds_calculator()
    test_range_provider()
    test_equity_simulator()
    test_sizing_policy()
    test_result_integrator()

    # 完全パイプラインテスト
    run_full_pipeline_test()

    # 実際の入力でのテスト
    test_with_real_input()

    print("\n" + "=" * 50)
    print("🏁 テスト完了")

if __name__ == "__main__":
    main()
