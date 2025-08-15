# test_pokerkit_tool.py
import math
import time

# pokerkittool.py から関数をインポート
from pokerkittool import pokerkit_tool


def pretty(label, equity, req, ratio):
    print(f"[{label}]")
    print(f"  equity               : {equity:.4f}")
    print(f"  required_equity (BE) : {req*100:.2f}%")
    print(f"  pot_odds_ratio       : {'inf' if math.isinf(ratio) else f'{ratio:.2f}:1'}")
    print("-" * 48)


def assert_0_1(x, name):
    assert 0.0 <= x <= 1.0, f"{name} must be in [0,1], got {x}"


def run_case(label, **kwargs):
    equity, req, ratio = pokerkit_tool(**kwargs)
    assert_0_1(equity, f"equity ({label})")
    assert_0_1(req, f"required_equity ({label})")
    pretty(label, equity, req, ratio)


if __name__ == "__main__":
    # 再現性が必要なら seed 固定（任意）
    import random
    random.seed(42)

    t0 = time.time()

    # -----------------------------------------------------------
    # 1) 正常系：pokerkitの標準形式でテスト
    # -----------------------------------------------------------
    # プリフロップ、ヘッズアップ
    run_case(
        "Preflop HU - AK vs random",
        hole_cards=["As", "Kd"],
        community_cards=[],
        num_opponents=1,
        pot_before=0,
        to_call=0,
        simulations=500
    )

    # プリフロップ、4人戦
    run_case(
        "Preflop 4-way - pocket fives",
        hole_cards=["5s", "5d"],
        community_cards=[],
        num_opponents=3,
        pot_before=30,
        to_call=20,
        simulations=500
    )

    # プリフロップ、ヘッズアップ（10のカード）
    run_case(
        "Preflop HU - AT suited",
        hole_cards=["As", "Tc"],
        community_cards=[],
        num_opponents=1,
        pot_before=100,
        to_call=50,
        simulations=500
    )

    # フロップ、3人戦
    run_case(
        "Flop 3-way - top pair",
        hole_cards=["As", "Kd"],
        community_cards=["Ah", "8s", "5d"],
        num_opponents=2,
        pot_before=180,
        to_call=60,
        simulations=500
    )

    # ターン、ヘッズアップ
    run_case(
        "Turn HU - straight draw",
        hole_cards=["Ah", "Kc"],
        community_cards=["Jc", "Ts", "5d", "2c"],
        num_opponents=1,
        pot_before=400,
        to_call=200,
        simulations=500
    )

    # リバー、3人戦
    run_case(
        "River 3-way - top pair",
        hole_cards=["As", "Kd"],
        community_cards=["Ac", "8s", "5d", "2c", "Qh"],
        num_opponents=2,
        pot_before=1000,
        to_call=300,
        simulations=500
    )

    # -----------------------------------------------------------
    # 2) 例外系チェック（重複カード / ボード枚数 / デッキ不足）
    # -----------------------------------------------------------
    def expect_raises(fn, exc=ValueError, label=""):
        try:
            fn()
            raise AssertionError(f"[{label}] 期待した例外 {exc.__name__} が発生しませんでした")
        except exc:
            print(f"[{label}] OK: {exc.__name__} を検出")

    expect_raises(
        lambda: pokerkit_tool(
            hole_cards=["As", "As"],
            community_cards=[],
            num_opponents=1,
            pot_before=100,
            to_call=50
        ),
        label="Duplicate cards"
    )

    expect_raises(
        lambda: pokerkit_tool(
            hole_cards=["As", "Kd"],
            community_cards=["Jc", "8s"],
            num_opponents=1,
            pot_before=100,
            to_call=50
        ),
        label="Invalid board length (2 cards)"
    )

    # デッキ不足（プレイヤー多すぎ）
    expect_raises(
        lambda: pokerkit_tool(
            hole_cards=["As", "Kd"],
            community_cards=["Jc", "8s", "5d", "2c", "Qh"],
            num_opponents=23,
            pot_before=100,
            to_call=50
        ),
        label="Insufficient deck (too many opponents)"
    )

    print(f"\nAll tests finished in {time.time() - t0:.2f}s ✅")