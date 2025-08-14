from typing import List
from google.adk.tools import FunctionTool

"""
ポーカーゲームのポジション計算ユーティリティ

ディーラーボタンの位置から、スモールブラインド（SB）とビッグブラインド（BB）の位置を計算し、
各プレイヤーのポジション情報を提供します。
positionは5人まで。
"""


def get_position_type(player_id: int, dealer_button: int, active_players: List[int]) -> str:
    """
    プレイヤーのポジションタイプを、現在のアクティブプレイヤー数に応じて計算します。
    
    Args:
        player_id: 判定したいプレイヤーのID
        dealer_button: ディーラーボタンを持っているプレイヤーのID
        active_players: 現在有効なプレイヤーIDのリスト（席順）
    
    Returns:
        str: 計算されたプレイヤーのポジションタイプ ("BTN", "SB", "BB", "CO", "UTG")
    """
    num_players = len(active_players)
    dealer_pos_index = active_players.index(dealer_button)
    player_pos_index = active_players.index(player_id)
    
    # ディーラーからの相対位置を計算（時計回り）
    relative_pos = (player_pos_index - dealer_pos_index + num_players) % num_players
    
    # プレイヤー数に応じたポジションのマッピング
    if num_players == 5:
        positions = ["BTN", "SB", "BB", "UTG", "CO"]
        return positions[relative_pos]
        
    elif num_players == 4:
        positions = ["BTN", "SB", "BB", "CO"]
        return positions[relative_pos]
        
    elif num_players == 3:
        positions = ["BTN", "SB", "BB"]
        return positions[relative_pos]
        
    elif num_players == 2:  # ヘッズアップ
        positions = ["BTN", "BB"]
        return positions[relative_pos]
    
    # デフォルト（エラー時）
    return "UTG"


# ADK FunctionToolとして登録
PositionCalculator = FunctionTool(func=get_position_type)