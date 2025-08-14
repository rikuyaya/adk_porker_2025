#!/usr/bin/env python3
"""
Test script for calc_gto function
"""

from agents.team1_agent.tools.calc_gto import calc_gto
import json


def test_calc_gto():
    """Test various scenarios for calc_gto function"""
    
    print("=== Testing calc_gto function ===\n")
    
    # Test Case 1: Strong hand (AK suited)
    print("Test Case 1: Strong hand (AK suited)")
    print("Cards: A♠ K♠, Board: 7♥ J♦ 2♣")
    print("Pot: 100, To call: 20, Actions: fold/call/raise/all-in")
    result1 = calc_gto(
        'flop', 
        ['A♠', 'K♠'], 
        ['7♥', 'J♦', '2♣'], 
        100, 20, 
        ['fold', 'call (20)', 'raise (min 60)', 'all-in (1000)'], 
        num_players=2, stack=1000, iterations=50
    )
    print(f"Equity: {result1['equity']:.3f}")
    print(f"Pot Odds: {result1['pot_odds']:.3f}")
    print(f"SPR: {result1['spr']}")
    print(f"Strategy: {result1['strategy']}")
    print(f"Recommended: {result1['recommended']}")
    print(f"Reasoning: {result1['reasoning']}")
    print()
    
    # Test Case 2: Weak hand (72 offsuit)
    print("Test Case 2: Weak hand (72 offsuit)")
    print("Cards: 7♣ 2♥, Board: (preflop)")
    print("Pot: 30, To call: 20, Actions: fold/call/raise/all-in")
    result2 = calc_gto(
        'preflop', 
        ['7♣', '2♥'], 
        [], 
        30, 20, 
        ['fold', 'call (20)', 'raise (min 40)', 'all-in (1000)'], 
        num_players=3, stack=1000, iterations=50
    )
    print(f"Equity: {result2['equity']:.3f}")
    print(f"Pot Odds: {result2['pot_odds']:.3f}")
    print(f"SPR: {result2['spr']}")
    print(f"Strategy: {result2['strategy']}")
    print(f"Recommended: {result2['recommended']}")
    print(f"Reasoning: {result2['reasoning']}")
    print()
    
    # Test Case 3: Check situation
    print("Test Case 3: Check situation")
    print("Cards: Q♠ J♠, Board: A♥ K♦ T♣")
    print("Pot: 50, To call: 0, Actions: check/bet/all-in")
    result3 = calc_gto(
        'flop', 
        ['Q♠', 'J♠'], 
        ['A♥', 'K♦', 'T♣'], 
        50, 0, 
        ['check', 'bet (min 10)', 'all-in (1000)'], 
        num_players=2, stack=1000, iterations=50
    )
    print(f"Equity: {result3['equity']:.3f}")
    print(f"Pot Odds: {result3['pot_odds']:.3f}")
    print(f"SPR: {result3['spr']}")
    print(f"Strategy: {result3['strategy']}")
    print(f"Recommended: {result3['recommended']}")
    print(f"Reasoning: {result3['reasoning']}")
    print()
    
    # Test Case 4: Marginal hand
    print("Test Case 4: Marginal hand")
    print("Cards: T♠ 9♠, Board: 7♥ 8♦ 2♣")
    print("Pot: 80, To call: 40, Actions: fold/call/raise/all-in")
    result4 = calc_gto(
        'flop', 
        ['T♠', '9♠'], 
        ['7♥', '8♦', '2♣'], 
        80, 40, 
        ['fold', 'call (40)', 'raise (min 80)', 'all-in (1000)'], 
        num_players=2, stack=1000, iterations=50
    )
    print(f"Equity: {result4['equity']:.3f}")
    print(f"Pot Odds: {result4['pot_odds']:.3f}")
    print(f"SPR: {result4['spr']}")
    print(f"Strategy: {result4['strategy']}")
    print(f"Recommended: {result4['recommended']}")
    print(f"Reasoning: {result4['reasoning']}")
    print()
    
    # Test Case 5: River situation
    print("Test Case 5: River situation")
    print("Cards: A♠ K♠, Board: A♥ K♦ T♣ 7♠ 2♥")
    print("Pot: 200, To call: 100, Actions: fold/call/raise/all-in")
    result5 = calc_gto(
        'river', 
        ['A♠', 'K♠'], 
        ['A♥', 'K♦', 'T♣', '7♠', '2♥'], 
        200, 100, 
        ['fold', 'call (100)', 'raise (min 200)', 'all-in (1000)'], 
        num_players=2, stack=1000, iterations=50
    )
    print(f"Equity: {result5['equity']:.3f}")
    print(f"Pot Odds: {result5['pot_odds']:.3f}")
    print(f"SPR: {result5['spr']}")
    print(f"Strategy: {result5['strategy']}")
    print(f"Recommended: {result5['recommended']}")
    print(f"Reasoning: {result5['reasoning']}")
    print()
    
    print("=== All tests completed ===")


if __name__ == "__main__":
    test_calc_gto()
