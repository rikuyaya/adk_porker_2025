"""
ポジション計算ユーティリティのテスト
"""

import pytest
from adk_porker_2025.poker.position_utils import (
    calculate_blind_positions,
    get_position_type,
    calculate_action_order,
    get_position_info,
    get_all_positions_info,
    format_position_summary,
    PositionType,
    PositionInfo
)
from adk_porker_2025.poker.game_models import GameState, PlayerInfo


class TestBlindPositions:
    """ブラインドポジション計算のテスト"""

    def test_heads_up_blinds(self):
        """ヘッズアップでのブラインド計算"""
        active_players = [0, 1]
        dealer_button = 0
        
        sb_pos, bb_pos = calculate_blind_positions(dealer_button, active_players)
        
        assert sb_pos == 0  # ディーラーがSB
        assert bb_pos == 1  # 相手がBB

    def test_heads_up_blinds_reverse(self):
        """ヘッズアップでのブラインド計算（ディーラーが1）"""
        active_players = [0, 1]
        dealer_button = 1
        
        sb_pos, bb_pos = calculate_blind_positions(dealer_button, active_players)
        
        assert sb_pos == 1  # ディーラーがSB
        assert bb_pos == 0  # 相手がBB

    def test_three_player_blinds(self):
        """3人ゲームでのブラインド計算"""
        active_players = [0, 1, 2]
        dealer_button = 0
        
        sb_pos, bb_pos = calculate_blind_positions(dealer_button, active_players)
        
        assert sb_pos == 1  # ディーラーの次がSB
        assert bb_pos == 2  # SBの次がBB

    def test_four_player_blinds(self):
        """4人ゲームでのブラインド計算"""
        active_players = [0, 1, 2, 3]
        dealer_button = 2
        
        sb_pos, bb_pos = calculate_blind_positions(dealer_button, active_players)
        
        assert sb_pos == 3  # ディーラーの次がSB
        assert bb_pos == 0  # SBの次がBB（ラップアラウンド）

    def test_invalid_dealer_button(self):
        """無効なディーラーボタンでのエラー"""
        active_players = [0, 1, 2]
        dealer_button = 5  # アクティブプレイヤーに含まれていない
        
        with pytest.raises(ValueError, match="ディーラーボタン .* がアクティブプレイヤーに含まれていません"):
            calculate_blind_positions(dealer_button, active_players)

    def test_insufficient_players(self):
        """プレイヤー数不足でのエラー"""
        active_players = [0]
        dealer_button = 0
        
        with pytest.raises(ValueError, match="アクティブプレイヤーが2人未満です"):
            calculate_blind_positions(dealer_button, active_players)


class TestPositionType:
    """ポジションタイプ取得のテスト"""

    def test_heads_up_positions(self):
        """ヘッズアップでのポジション"""
        active_players = [0, 1]
        dealer_button = 0
        
        assert get_position_type(0, dealer_button, active_players) == PositionType.SB
        assert get_position_type(1, dealer_button, active_players) == PositionType.BB

    def test_three_player_positions(self):
        """3人ゲームでのポジション"""
        active_players = [0, 1, 2]
        dealer_button = 0
        
        assert get_position_type(0, dealer_button, active_players) == PositionType.BTN
        assert get_position_type(1, dealer_button, active_players) == PositionType.SB
        assert get_position_type(2, dealer_button, active_players) == PositionType.BB

    def test_four_player_positions(self):
        """4人ゲームでのポジション"""
        active_players = [0, 1, 2, 3]
        dealer_button = 0
        
        assert get_position_type(0, dealer_button, active_players) == PositionType.BTN
        assert get_position_type(1, dealer_button, active_players) == PositionType.SB
        assert get_position_type(2, dealer_button, active_players) == PositionType.BB
        assert get_position_type(3, dealer_button, active_players) == PositionType.UTG

    def test_six_player_positions(self):
        """6人ゲームでのポジション"""
        active_players = [0, 1, 2, 3, 4, 5]
        dealer_button = 0
        
        assert get_position_type(0, dealer_button, active_players) == PositionType.BTN
        assert get_position_type(1, dealer_button, active_players) == PositionType.SB
        assert get_position_type(2, dealer_button, active_players) == PositionType.BB
        assert get_position_type(3, dealer_button, active_players) == PositionType.UTG
        assert get_position_type(4, dealer_button, active_players) == PositionType.HJ
        assert get_position_type(5, dealer_button, active_players) == PositionType.CO


class TestActionOrder:
    """アクション順序計算のテスト"""

    def test_preflop_action_order_four_players(self):
        """4人ゲームでのプリフロップアクション順序"""
        active_players = [0, 1, 2, 3]
        dealer_button = 0
        
        # プリフロップ: UTG(3) -> BTN(0) -> SB(1) -> BB(2)
        assert calculate_action_order(3, dealer_button, active_players, True) == 0  # UTG
        assert calculate_action_order(0, dealer_button, active_players, True) == 1  # BTN
        assert calculate_action_order(1, dealer_button, active_players, True) == 2  # SB
        assert calculate_action_order(2, dealer_button, active_players, True) == 3  # BB

    def test_postflop_action_order_four_players(self):
        """4人ゲームでのポストフロップアクション順序"""
        active_players = [0, 1, 2, 3]
        dealer_button = 0
        
        # ポストフロップ: SB(1) -> BB(2) -> UTG(3) -> BTN(0)
        assert calculate_action_order(1, dealer_button, active_players, False) == 0  # SB
        assert calculate_action_order(2, dealer_button, active_players, False) == 1  # BB
        assert calculate_action_order(3, dealer_button, active_players, False) == 2  # UTG
        assert calculate_action_order(0, dealer_button, active_players, False) == 3  # BTN

    def test_heads_up_action_order(self):
        """ヘッズアップでのアクション順序"""
        active_players = [0, 1]
        dealer_button = 0
        
        # プリフロップ: SB(0) -> BB(1)
        assert calculate_action_order(0, dealer_button, active_players, True) == 0  # SB
        assert calculate_action_order(1, dealer_button, active_players, True) == 1  # BB
        
        # ポストフロップ: SB(0) -> BB(1)
        assert calculate_action_order(0, dealer_button, active_players, False) == 0  # SB
        assert calculate_action_order(1, dealer_button, active_players, False) == 1  # BB


class TestPositionInfo:
    """ポジション情報取得のテスト"""

    def test_get_position_info(self):
        """ポジション情報取得のテスト"""
        # テスト用のGameStateを作成
        players = [
            PlayerInfo(id=0, chips=1000, bet=0, status="active"),
            PlayerInfo(id=1, chips=1000, bet=10, status="active"),  # SB
            PlayerInfo(id=2, chips=1000, bet=20, status="active"),  # BB
            PlayerInfo(id=3, chips=1000, bet=0, status="active"),   # UTG
        ]
        
        game_state = GameState(
            your_id=0,
            phase="preflop",
            your_cards=["A♥", "K♠"],
            community=[],
            your_chips=1000,
            your_bet_this_round=0,
            your_total_bet_this_hand=0,
            pot=30,
            to_call=20,
            dealer_button=0,  # Player 0 がディーラー
            current_turn=3,
            players=players,
            actions=["fold", "call", "raise"],
            history=[]
        )
        
        # Player 0 (ディーラー) のポジション情報
        pos_info = get_position_info(0, game_state)
        
        assert pos_info.player_id == 0
        assert pos_info.position_type == PositionType.BTN
        assert pos_info.is_dealer == True
        assert pos_info.is_small_blind == False
        assert pos_info.is_big_blind == False
        assert pos_info.position_index == 0
        
        # Player 1 (SB) のポジション情報
        pos_info_sb = get_position_info(1, game_state)
        
        assert pos_info_sb.player_id == 1
        assert pos_info_sb.position_type == PositionType.SB
        assert pos_info_sb.is_dealer == False
        assert pos_info_sb.is_small_blind == True
        assert pos_info_sb.is_big_blind == False

    def test_get_all_positions_info(self):
        """全プレイヤーのポジション情報取得のテスト"""
        players = [
            PlayerInfo(id=1, chips=1000, bet=10, status="active"),  # SB
            PlayerInfo(id=2, chips=1000, bet=20, status="active"),  # BB
            PlayerInfo(id=3, chips=1000, bet=0, status="active"),   # UTG
        ]
        
        game_state = GameState(
            your_id=0,
            phase="preflop",
            your_cards=["A♥", "K♠"],
            community=[],
            your_chips=1000,
            your_bet_this_round=0,
            your_total_bet_this_hand=0,
            pot=30,
            to_call=20,
            dealer_button=0,
            current_turn=3,
            players=players,
            actions=["fold", "call", "raise"],
            history=[]
        )
        
        all_positions = get_all_positions_info(game_state)
        
        assert len(all_positions) == 4  # 4人のプレイヤー
        assert 0 in all_positions  # 自分も含まれている
        assert all_positions[0].position_type == PositionType.BTN
        assert all_positions[1].position_type == PositionType.SB
        assert all_positions[2].position_type == PositionType.BB
        assert all_positions[3].position_type == PositionType.UTG

    def test_format_position_summary(self):
        """ポジション要約フォーマットのテスト"""
        players = [
            PlayerInfo(id=1, chips=1000, bet=10, status="active"),
            PlayerInfo(id=2, chips=1000, bet=20, status="active"),
        ]
        
        game_state = GameState(
            your_id=0,
            phase="preflop",
            your_cards=["A♥", "K♠"],
            community=[],
            your_chips=1000,
            your_bet_this_round=0,
            your_total_bet_this_hand=0,
            pot=30,
            to_call=20,
            dealer_button=0,
            current_turn=1,
            players=players,
            actions=["fold", "call", "raise"],
            history=[]
        )
        
        summary = format_position_summary(game_state)
        
        assert "ポジション情報" in summary
        assert "ディーラーボタン: Player 0" in summary
        assert "BTN" in summary
        assert "SB" in summary
        assert "BB" in summary
