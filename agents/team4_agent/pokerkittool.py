from typing import List, Optional, Tuple
from google.adk.tools import FunctionTool
from pokerkit import Deck, Card, StandardHighHand
import random



def pokerkit_tool(
    hole_cards: List[str],
    community_cards: Optional[List[str]] = None,
    num_opponents: int = 1,
    pot_before: int = 0,
    to_call: int = 0,
    simulations: int = 1000
) -> Tuple[float, float, float]:
    """
    pokerkitを使用してポーカーハンドのエクイティとポットオッズを計算します。

    Args:
        hole_cards: ホールカード（2枚）
            例: ["As", "Kd"], ["Tc", "9h"], ["2c", "2d"]
            ランク: 2,3,4,5,6,7,8,9,T,J,Q,K,A（10は'T'で表記）
            スート: s(スペード), h(ハート), d(ダイヤ), c(クラブ)

        community_cards: コミュニティカード（0,3,4,5枚）
            例: [] (プリフロップ)
                ["Js", "Qh", "9d"] (フロップ)
                ["Js", "Qh", "9d", "2c"] (ターン)
                ["Js", "Qh", "9d", "2c", "Ah"] (リバー)

        num_opponents: 対戦相手数（1以上）
            例: 1 (ヘッズアップ), 2 (3人), 3 (4人)

        pot_before: コール前のポット総額（相手のベットも含む）
            例: 100, 1500, 0 (チェック可能な場合)

        to_call: コールに必要な額
            例: 50, 200, 0 (チェック可能な場合)

        simulations: モンテカルロシミュレーション回数（デフォルト1000）
            例: 1000 (標準), 10000 (高精度)

    Returns:
        tuple[float, float, float]: (equity, required_equity, pot_odds_ratio)

        equity: ヒーローの勝率（0.0-1.0）
            例: 0.65 = 65%の勝率

        required_equity: コールに必要な勝率（ブレイクイーブンエクイティ）
            例: 0.33 = 33%以上の勝率が必要
            計算式: to_call / (pot_before + to_call)

        pot_odds_ratio: ポットオッズの比率（X:1のX）
            例: 2.0 = 2:1のオッズ（33%の勝率が必要）
            計算式: pot_before / to_call

    使用例:
        # プリフロップ、ヘッズアップ
        equity, req, ratio = pokerkit_tool(
            hole_cards=["As", "Kd"],
            community_cards=[],
            num_opponents=1,
            pot_before=100,
            to_call=50,
            simulations=1000
        )

        # フロップ、3人戦
        equity, req, ratio = pokerkit_tool(
            hole_cards=["Tc", "Th"],
            community_cards=["Js", "9h", "2d"],
            num_opponents=2,
            pot_before=300,
            to_call=100,
            simulations=1000
        )

    """

    community_cards = community_cards or []

    # --- validation ---
    if len(hole_cards) != 2:
        raise ValueError("hole_cards は2枚で指定してください。カードの枚数を確認して、再度実行してください。")
    if len(community_cards) not in (0, 3, 4, 5):
        raise ValueError("community_cards の枚数は 0 / 3 / 4 / 5 のいずれかにしてください。カードの枚数を確認して、再度実行してください。")
    if num_opponents < 1:
        raise ValueError("num_opponents は1以上にしてください。対戦相手の数を確認して、再度実行してください。")

    # 重複チェック
    all_cards = hole_cards + community_cards
    if len(set(all_cards)) != len(all_cards):
        raise ValueError("重複しているカードがあります。カードの枚数を確認して、再度実行してください。")

    # カード表記をそのまま使用（pokerkitの標準形式を想定）
    hole_str  = "".join(hole_cards)
    board_str = "".join(community_cards)

    # 既知カードを取り除いた残りデッキ（Card オブジェクト）
    known_cards = set(Card.parse(hole_str + board_str))
    deck_remain = [c for c in Deck.STANDARD if c not in known_cards]

    board_needed = 5 - len(community_cards)
    draw_needed  = 2 * num_opponents + max(0, board_needed)  # 1試行で必要な残り札

    hero_share_sum = 0.0

    # --- Monte Carlo ---
    for _ in range(simulations):
        draw = random.sample(deck_remain, draw_needed)

        # 相手ホール (2枚ずつ)
        opp_holes = [draw[i*2:(i+1)*2] for i in range(num_opponents)]

        # 残りボード
        board_draw = draw[2*num_opponents:]  # board_needed 枚
        full_board = community_cards + [repr(c) for c in board_draw]

        # ヒーローとオポーネントの手を構築
        hero_hand = StandardHighHand.from_game(hole_str, "".join(full_board))
        opp_hands = [
            StandardHighHand.from_game("".join(map(repr, oh)), "".join(full_board))
            for oh in opp_holes
        ]

        # マルチウェイの分割勝ちを正しく計算
        hands = [hero_hand] + opp_hands
        best_hand = max(hands)
        winners = sum(1 for h in hands if h == best_hand)
        if hero_hand == best_hand:
            hero_share_sum += 1.0 / winners  # 等分取り分

    equity = hero_share_sum / simulations  # 期待取り分（引き分けは自動で等分）

    # --- Pot odds ---
    def _required_equity(pot_before: float, to_call: float) -> float:
        if to_call <= 0:
            return 0.0
        return to_call / (pot_before + to_call)

    def _pot_odds_ratio(pot_before: float, to_call: float) -> float:
        if to_call <= 0:
            return float("inf")
        return pot_before / to_call

    req_equity = _required_equity(pot_before, to_call)
    ratio      = _pot_odds_ratio(pot_before, to_call)

    return equity, req_equity, ratio

    
PokerKitTool = FunctionTool(func=pokerkit_tool)