from typing import List, Optional, Tuple
from google.adk.tools import FunctionTool
from pokerkit import Deck, Card, StandardHighHand
import random
import logging
import re

# ログ設定


def convert_card_notation(card_str: str) -> str:
    """
    ゲームエンジンのカード表記をpokerkitの表記に変換
    例: "10♥" -> "Th", "A♠" -> "As"
    既に正しい形式の場合はそのまま返す: "As" -> "As"
    """
    # 既に正しい形式かチェック（2文字で、最後が s/h/d/c）
    if len(card_str) == 2 and card_str[1].lower() in 'shdc':
        return card_str

    # 絵文字スートをアルファベットに変換
    suit_map = {'♠': 's',
                '♥': 'h', '♦': 'd', '♣': 'c'}

    # 10を T に変換
    if card_str.startswith('10'):
        rank = 'T'
        suit_symbol = card_str[2:]
    else:
        rank = card_str[0]
        suit_symbol = card_str[1:]

    # スート変換
    suit = suit_map.get(suit_symbol, suit_symbol.lower())

    return rank + suit



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

        num_opponents: 対戦相手数 必ず、現在activeな人数を入れて。

        pot_before: コール前のポット総額（相手のベットも含む）
            例: 100, 1500, 0 (チェック可能な場合)

        to_call: コールに必要な額
            例: 50, 200, 0 (チェック可能な場合)

        simulations: モンテカルロシミュレーション回数（デフォルト1000）
            例: 1000 (標準), 10000 (高精度)

    Returns:
        tuple[float, float, float]: (equity, required_equity, pot_odds_ratio)

    """

    community_cards = community_cards or []

    # カード表記を変換
    converted_hole_cards = [convert_card_notation(card) for card in hole_cards]
    converted_community_cards = [convert_card_notation(card) for card in community_cards]

    # --- validation ---
    if len(converted_hole_cards) != 2:
        raise ValueError("hole_cards は2枚で指定してください。カードの枚数を確認して、再度実行してください。")
    if len(converted_community_cards) not in (0, 3, 4, 5):
        raise ValueError("community_cards の枚数は 0 / 3 / 4 / 5 のいずれかにしてください。カードの枚数を確認して、再度実行してください。")
    if num_opponents < 1:
        raise ValueError("num_opponents は1以上にしてください。対戦相手の数を確認して、再度実行してください。")

    # 重複チェック（変換後のカードで）
    all_converted_cards = converted_hole_cards + converted_community_cards
    if len(set(all_converted_cards)) != len(all_converted_cards):
        raise ValueError("重複しているカードがあります。カードの枚数を確認して、再度実行してください。")

    # pokerkitの標準形式で文字列作成
    hole_str  = "".join(converted_hole_cards)
    board_str = "".join(converted_community_cards)

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
        full_board = converted_community_cards + [repr(c) for c in board_draw]

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