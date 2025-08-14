"""
Lightweight GTO-like strategy tool for Texas Hold'em.

This tool estimates hand equity via Monte Carlo sampling and proposes an
action distribution and a recommended action based on pot odds and stack.

It is designed to be used as an ADK tool function and can also be called
directly from Python.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
import random

from poker.game_models import Card, Suit
from poker.evaluator import HandEvaluator


SUIT_SYMBOL_TO_ENUM = {
    "♥": Suit.HEARTS,
    "♦": Suit.DIAMONDS,
    "♣": Suit.CLUBS,
    "♠": Suit.SPADES,
    # Fallback ASCII letters often used in data/export
    "h": Suit.HEARTS,
    "d": Suit.DIAMONDS,
    "c": Suit.CLUBS,
    "s": Suit.SPADES,
}

RANK_NAME_TO_VALUE = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "t": 10,
    "j": 11,
    "q": 12,
    "k": 13,
    "a": 14,
}


def _parse_card_string(card_str: str) -> Card:
    """
    Parse a card string like "A♠", "7♥", or ASCII like "Ah", "Td" into Card.
    """
    s = card_str.strip()
    if not s:
        raise ValueError("Empty card string")

    # Normalize: allow formats like "10h" or "Th" or "A♠"
    rank_part = ""
    suit_part = ""

    # If last char is a suit symbol/letter
    last_char = s[-1]
    if last_char in SUIT_SYMBOL_TO_ENUM:
        suit_part = last_char
        rank_part = s[:-1]
    else:
        # Try to find any of the known suit symbols/letters inside
        for ch in s:
            if ch in SUIT_SYMBOL_TO_ENUM:
                suit_part = ch
                rank_part = s.replace(ch, "")
                break
        if not suit_part:
            # Fallback: try to parse as rank-only and assume a default suit
            # This is for testing/debugging purposes
            rank_key = s.lower()
            if rank_key in RANK_NAME_TO_VALUE:
                # Default to spades for testing
                return Card(RANK_NAME_TO_VALUE[rank_key], Suit.SPADES)
            raise ValueError(f"Suit not found in card string: {card_str}")

    rank_key = rank_part.lower()
    if rank_key not in RANK_NAME_TO_VALUE:
        raise ValueError(f"Invalid rank in card string: {card_str}")

    suit_enum = SUIT_SYMBOL_TO_ENUM[suit_part]
    return Card(RANK_NAME_TO_VALUE[rank_key], suit_enum)


def _build_remaining_deck(excluded: List[Card]) -> List[Card]:
    """Create a 52-card deck excluding provided cards."""
    remaining: List[Card] = []
    for suit in (Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES):
        for rank in range(2, 15):
            c = Card(rank, suit)
            if c not in excluded:
                remaining.append(c)
    return remaining


def _complete_board_randomly(
    current_board: List[Card],
    remaining_deck: List[Card],
) -> Tuple[List[Card], List[Card]]:
    """
    Draw random cards to complete the community to 5 cards.
    Returns the new_board and the reduced remaining_deck (copies).
    """
    need = 5 - len(current_board)
    if need <= 0:
        return list(current_board), list(remaining_deck)
    if need > len(remaining_deck):
        return list(current_board), list(remaining_deck)

    deck_copy = list(remaining_deck)
    random.shuffle(deck_copy)
    add = deck_copy[:need]
    new_board = list(current_board) + add

    # remove the added cards from the copy to keep accounting consistent
    for c in add:
        deck_copy.remove(c)
    return new_board, deck_copy


def _sample_opponents_hands(
    remaining_deck: List[Card], num_opponents: int
) -> Tuple[List[List[Card]], List[Card]]:
    """
    Sample 2-card hands for each opponent from the remaining deck.
    Returns opponent hands and the reduced deck copy.
    """
    deck_copy = list(remaining_deck)
    random.shuffle(deck_copy)
    opponents: List[List[Card]] = []
    needed = 2 * num_opponents
    if needed > len(deck_copy):
        return [], deck_copy
    draw = deck_copy[:needed]
    for i in range(num_opponents):
        opponents.append([draw[2 * i], draw[2 * i + 1]])
    # Remove drawn cards
    for c in draw:
        deck_copy.remove(c)
    return opponents, deck_copy


def _estimate_equity(
    hole_cards: List[Card],
    community_cards: List[Card],
    num_opponents: int,
    iterations: int = 300,
) -> float:
    """
    Estimate hand equity (win probability) via Monte Carlo sampling.
    Equity is approximated as the probability of beating all opponents at showdown.
    """
    if len(hole_cards) != 2:
        return 0.0

    excluded = list(hole_cards) + list(community_cards)
    remaining = _build_remaining_deck(excluded)

    wins = 0
    ties = 0
    trials = 0

    for _ in range(max(1, iterations)):
        # Sample opponent hands and complete the board
        opponents, deck_after_opps = _sample_opponents_hands(remaining, num_opponents)
        if len(opponents) != num_opponents:
            continue

        final_board, _ = _complete_board_randomly(community_cards, deck_after_opps)
        if len(final_board) != 5:
            continue

        my_best = HandEvaluator.evaluate_hand(hole_cards, final_board)

        # Compare against each opponent; must beat all to count as a win
        outcome_flags = []
        for opp in opponents:
            opp_best = HandEvaluator.evaluate_hand(opp, final_board)
            cmp_result = HandEvaluator.compare_hands(my_best, opp_best)
            outcome_flags.append(cmp_result)

        if all(flag == 1 for flag in outcome_flags):
            wins += 1
        elif all(flag >= 0 for flag in outcome_flags) and any(flag == 0 for flag in outcome_flags):
            ties += 1
        trials += 1

    if trials == 0:
        return 0.0

    # Split ties among players involved (approximate as 0.5 per tie event)
    return (wins + 0.5 * ties) / trials


def _extract_min_raise(actions: List[str]) -> int:
    """Extract minimum raise amount from actions like "raise (min 40)"."""
    for act in actions:
        lower = str(act).lower()
        if "raise" in lower and "min" in lower:
            try:
                # e.g., "raise (min 40)"
                start = lower.index("min") + 3
                digits = "".join(ch for ch in lower[start:] if ch.isdigit())
                if digits:
                    return int(digits)
            except Exception:
                continue
    return 0


def _extract_call_amount(actions: List[str]) -> int:
    """Extract call amount from actions like "call (20)"."""
    for act in actions:
        lower = str(act).lower()
        if "call" in lower:
            try:
                digits = "".join(ch for ch in lower if ch.isdigit())
                if digits:
                    return int(digits)
            except Exception:
                continue
    return 0


def _normalize_recommended_action(
    recommendation: Dict[str, Any], actions: List[str], stack: int
) -> Dict[str, Any]:
    """
    Ensure the recommended action conforms to available actions and bounds.
    - If action unavailable, degrade to closest valid option.
    - Clamp amounts (>=0, <= stack).
    """
    action = recommendation.get("action", "fold").lower()
    amount = int(max(0, min(int(recommendation.get("amount", 0)), max(0, stack))))

    normalized = {"action": action, "amount": amount}
    available = [str(a).lower() for a in actions]

    if action == "check":
        if any(a.startswith("check") for a in available):
            return {"action": "check", "amount": 0}
        # Fallback to fold if check not available
        if "fold" in available:
            return {"action": "fold", "amount": 0}
    elif action == "call":
        if any("call" in a for a in available):
            return {"action": "call", "amount": _extract_call_amount(actions)}
        # If call isn't available, try check then fold
        if any(a.startswith("check") for a in available):
            return {"action": "check", "amount": 0}
        if "fold" in available:
            return {"action": "fold", "amount": 0}
    elif action == "raise":
        if any("raise" in a for a in available):
            min_raise = _extract_min_raise(actions)
            amount = max(amount, min_raise)
            amount = min(amount, stack)
            return {"action": "raise", "amount": amount}
        # If raise not available, consider call/check/fold fallback
        if any("call" in a for a in available):
            return {"action": "call", "amount": _extract_call_amount(actions)}
        if any(a.startswith("check") for a in available):
            return {"action": "check", "amount": 0}
        if "fold" in available:
            return {"action": "fold", "amount": 0}
    elif action in ("all_in", "all-in"):
        if any("all-in" in a for a in available):
            return {"action": "all_in", "amount": stack}
        # Fallback preferences
        if any("raise" in a for a in available):
            min_raise = _extract_min_raise(actions)
            return {"action": "raise", "amount": max(min_raise, min(stack, amount))}
        if any("call" in a for a in available):
            return {"action": "call", "amount": _extract_call_amount(actions)}
        if any(a.startswith("check") for a in available):
            return {"action": "check", "amount": 0}
        if "fold" in available:
            return {"action": "fold", "amount": 0}

    # Default safe fallback
    if any(a.startswith("check") for a in available):
        return {"action": "check", "amount": 0}
    if "fold" in available:
        return {"action": "fold", "amount": 0}
    # If nothing else, just return the original (last resort)
    return normalized


def calc_gto(
    phase: str,
    your_cards: List[str],
    community: List[str] | None,
    pot: int,
    to_call: int,
    actions: List[str],
    num_players: int = 2,
    stack: int = 1000,
    iterations: int = 300,
) -> Dict[str, Any]:
    """
    推定エクイティとポットオッズに基づいて、GTO風の戦略分布と推奨アクションを返す。

    Args:
        phase: "preflop" | "flop" | "turn" | "river" のいずれか
        your_cards: 例 ["A♠", "K♠"] のような2枚
        community: 例 ["7♥", "J♦", "2♣"] など（ない場合は [] / None）
        pot: 現在のポットサイズ
        to_call: コールに必要な額（0ならチェック可能）
        actions: 利用可能なアクションのリスト（例: ["fold", "call (20)", "raise (min 40)"]）
        num_players: 卓上の総人数（自分を含む）
        stack: 自分の残りチップ
        iterations: モンテカルロ試行回数

    Returns:
        {
          "equity": float,               # 推定勝率 (0-1)
          "pot_odds": float,             # ポットオッズ (0-1)
          "spr": float,                  # スタック・トゥ・ポット比
          "strategy": {action: prob},    # 行動分布（簡易）
          "recommended": {"action": str, "amount": int},
          "reasoning": str
        }
    """

    # Basic validation and safe defaults
    community = community or []
    try:
        hole = [_parse_card_string(c) for c in your_cards]
        board = [_parse_card_string(c) for c in community]
    except Exception:
        # Failed to parse input; return safe default
        safe_action = {"action": "check" if to_call == 0 else "fold", "amount": 0}
        return {
            "equity": 0.0,
            "pot_odds": 0.0 if to_call == 0 else to_call / max(1, pot + to_call),
            "spr": float("inf") if pot == 0 else stack / max(1, pot),
            "strategy": {safe_action["action"]: 1.0},
            "recommended": _normalize_recommended_action(safe_action, actions, stack),
            "reasoning": "カード文字列の解析に失敗したため、安全なアクションを選択しました。",
        }

    num_opponents = max(1, num_players - 1)
    equity = _estimate_equity(hole, board, num_opponents=num_opponents, iterations=iterations)

    pot_odds = 0.0 if to_call <= 0 else to_call / max(1, pot + to_call)
    spr = float("inf") if pot <= 0 else stack / max(1, pot)

    # Heuristic GTO-like policy
    strategy: Dict[str, float] = {"fold": 0.0, "check": 0.0, "call": 0.0, "raise": 0.0, "all_in": 0.0}

    # Default recommendation
    recommendation: Dict[str, Any] = {"action": "fold", "amount": 0}

    if to_call == 0:
        # No pressure to put chips: choose between check and aggressive line based on equity
        if equity >= 0.65:
            # Prefer betting/raising with a strong equity
            min_raise = _extract_min_raise(actions)
            bet_size = max(min_raise, int(0.6 * (pot + 1))) if min_raise > 0 else int(0.6 * (pot + 1))
            bet_size = min(bet_size, stack)
            strategy.update({"check": 0.25, "raise": 0.65, "all_in": 0.10})
            recommendation = {"action": "raise", "amount": bet_size}
        elif equity >= 0.5:
            strategy.update({"check": 0.7, "raise": 0.3})
            min_raise = _extract_min_raise(actions)
            bet_size = max(min_raise, int(0.4 * (pot + 1))) if min_raise > 0 else int(0.4 * (pot + 1))
            bet_size = min(bet_size, stack)
            recommendation = {"action": "raise", "amount": bet_size} if any("raise" in str(a).lower() for a in actions) else {"action": "check", "amount": 0}
        else:
            strategy.update({"check": 0.95, "raise": 0.05})
            recommendation = {"action": "check", "amount": 0}
    else:
        # Facing a bet: compare equity to pot odds
        if equity > max(pot_odds + 0.05, 0.5):
            # Strong enough to continue; prefer raise when SPR low or equity high
            min_raise = _extract_min_raise(actions)
            call_amt = _extract_call_amount(actions) or to_call
            if equity >= 0.7 or spr <= 2.0:
                if any("all-in" in str(a).lower() for a in actions):
                    strategy.update({"fold": 0.0, "call": 0.2, "raise": 0.3, "all_in": 0.5})
                    recommendation = {"action": "all_in", "amount": stack}
                else:
                    raise_amt = max(min_raise, int(2.5 * (to_call or call_amt))) if min_raise > 0 else int(2.5 * (to_call or call_amt))
                    raise_amt = min(raise_amt, stack)
                    strategy.update({"fold": 0.0, "call": 0.3, "raise": 0.7})
                    recommendation = {"action": "raise", "amount": raise_amt}
            else:
                # Continue more cautiously
                strategy.update({"fold": 0.0, "call": 0.8, "raise": 0.2})
                raise_amt = max(_extract_min_raise(actions), int(1.5 * (to_call or call_amt)))
                raise_amt = min(raise_amt, stack) if raise_amt > 0 else 0
                recommendation = {"action": "call", "amount": call_amt if call_amt > 0 else to_call}
                if raise_amt > 0 and any("raise" in str(a).lower() for a in actions):
                    # Slight chance to raise as a mixed strategy
                    if equity - pot_odds > 0.15:
                        recommendation = {"action": "raise", "amount": raise_amt}
        elif abs(equity - pot_odds) <= 0.03 and any("call" in str(a).lower() for a in actions):
            # Indifferent region: mix between call and fold
            strategy.update({"fold": 0.5, "call": 0.5})
            recommendation = {"action": "call", "amount": _extract_call_amount(actions) or to_call}
        else:
            # Not enough equity to continue
            strategy.update({"fold": 0.95, "call": 0.05})
            recommendation = {"action": "fold", "amount": 0}

    normalized_recommendation = _normalize_recommended_action(recommendation, actions, stack)

    reasoning = (
        f"Phase={phase}, Equity={equity:.3f}, PotOdds={pot_odds:.3f}, SPR={spr:.2f}. "
        f"ポットオッズと推定エクイティを比較し、混合戦略を構成しています。"
    )

    # Remove zero-prob actions and renormalize for clarity
    positive = {k: v for k, v in strategy.items() if v > 0}
    total = sum(positive.values()) or 1.0
    normalized_strategy = {k: round(v / total, 3) for k, v in positive.items()}

    return {
        "equity": round(equity, 4),
        "pot_odds": round(pot_odds, 4),
        "spr": float("inf") if spr == float("inf") else round(spr, 2),
        "strategy": normalized_strategy,
        "recommended": normalized_recommendation,
        "reasoning": reasoning,
    }


