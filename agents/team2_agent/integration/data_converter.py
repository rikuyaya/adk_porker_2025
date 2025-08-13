"""
データ変換レイヤー: ゲーム状態から各ツール用パラメータを抽出
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def extract_tool_parameters(parsed_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析済みゲーム状態から各ツール用パラメータを抽出
    
    Args:
        parsed_state: GameStateParserからの出力
    
    Returns:
        各ツール用のパラメータ辞書
    """
    try:
        if parsed_state.get("status") != "success":
            raise ValueError(f"Invalid parsed state: {parsed_state.get('error_message', 'Unknown error')}")
        
        # 基本情報の抽出
        hole_cards = parsed_state.get("hole_cards", [])
        community_cards = parsed_state.get("community_cards", [])
        pot_size = parsed_state.get("pot_size", 0.0)
        call_amount = parsed_state.get("call_amount", 0.0)
        num_opponents = parsed_state.get("num_opponents", 1)
        position = parsed_state.get("position", "MP")
        board_texture = parsed_state.get("board_texture", "dry")
        action_before = parsed_state.get("action_before", "none")
        stack_depth = parsed_state.get("stack_depth", 100)
        phase = parsed_state.get("phase", "preflop")
        your_chips = parsed_state.get("your_chips", 1000)
        
        # EquityCalculator用パラメータ
        equity_params = {
            "hole_cards": hole_cards,
            "community_cards": community_cards,
            "num_opponents": num_opponents
        }
        
        # GtoPreflopChartTool用パラメータ（プリフロップのみ）
        gto_params = {
            "hole_cards": hole_cards,
            "position": _convert_position_for_gto(position),
            "action_before": action_before,
            "stack_depth": stack_depth
        }
        
        # PotOddsCalculator用パラメータ（equity は後で設定）
        pot_odds_params = {
            "pot_size": pot_size,
            "call_amount": call_amount,
            "equity": 0.5,  # プレースホルダー、勝率計算後に更新
            "implied_odds_factor": _calculate_implied_odds_factor(position, board_texture, stack_depth)
        }
        
        # SizingTool用パラメータ（equity は後で設定）
        sizing_params = {
            "pot_size": pot_size,
            "hand_strength": 0.5,  # プレースホルダー、勝率計算後に更新
            "board_texture": board_texture,
            "position": _convert_position_for_sizing(position),
            "action_type": "bet",
            "num_opponents": num_opponents,
            "stack_depth": stack_depth
        }
        
        return {
            "status": "success",
            "equity_params": equity_params,
            "pot_odds_params": pot_odds_params,
            "gto_params": gto_params,
            "sizing_params": sizing_params,
            "context": {
                "phase": phase,
                "position": position,
                "your_chips": your_chips,
                "available_actions": parsed_state.get("available_actions", []),
                "board_texture": board_texture
            }
        }
    
    except Exception as e:
        logger.error(f"Parameter extraction error: {e}")
        return {
            "status": "error",
            "error_message": f"パラメータ抽出エラー: {str(e)}"
        }


def _convert_position_for_gto(position: str) -> str:
    """GTOツール用のポジション形式に変換"""
    position_map = {
        "UTG": "UTG",
        "UTG+1": "UTG", 
        "MP": "MP",
        "MP+1": "MP",
        "CO": "CO",
        "CO-1": "CO",
        "BTN": "BTN",
        "SB": "SB",
        "BB": "BB"
    }
    return position_map.get(position, "MP")


def _convert_position_for_sizing(position: str) -> str:
    """SizingTool用のポジション形式に変換"""
    # インポジション vs アウトオブポジション
    ip_positions = ["CO", "BTN"]
    return "IP" if position in ip_positions else "OOP"


def _calculate_implied_odds_factor(position: str, board_texture: str, stack_depth: int) -> float:
    """インプライドオッズ係数を計算"""
    base_factor = 1.0
    
    # ポジションボーナス
    if position in ["BTN", "CO"]:
        base_factor += 0.2
    elif position in ["SB", "BB"]:
        base_factor -= 0.1
    
    # ボードテクスチャ調整
    if board_texture == "dry":
        base_factor += 0.1
    elif board_texture == "coordinated":
        base_factor -= 0.2
    
    # スタック深度調整
    if stack_depth > 150:
        base_factor += 0.3
    elif stack_depth < 30:
        base_factor -= 0.3
    
    return max(0.5, min(2.0, base_factor))


def update_equity_dependent_params(
    tool_params: Dict[str, Any], 
    equity_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    勝率計算結果を使って、他のツールパラメータを更新
    
    Args:
        tool_params: extract_tool_parameters()の結果
        equity_result: EquityCalculatorの結果
    
    Returns:
        更新されたツールパラメータ
    """
    try:
        if equity_result.get("status") != "success":
            logger.warning(f"Equity calculation failed: {equity_result}")
            equity = 0.5  # デフォルト値
            hand_strength = 0.5
        else:
            equity = equity_result.get("equity", 0.5)
            hand_strength = equity_result.get("hand_strength", equity)
        
        # PotOddsCalculator用パラメータを更新
        tool_params["pot_odds_params"]["equity"] = equity
        
        # SizingTool用パラメータを更新
        tool_params["sizing_params"]["hand_strength"] = hand_strength
        
        # コンテキスト情報を追加
        tool_params["context"]["calculated_equity"] = equity
        tool_params["context"]["hand_strength"] = hand_strength
        tool_params["context"]["hand_category"] = equity_result.get("hand_category", "不明")
        
        return tool_params
    
    except Exception as e:
        logger.error(f"Parameter update error: {e}")
        return tool_params


def safe_tool_execution(tool_func, params: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """
    ツール実行時のエラーを安全に処理
    
    Args:
        tool_func: 実行するツール関数
        params: ツールパラメータ
        tool_name: ツール名（ログ用）
    
    Returns:
        ツール実行結果またはエラー情報
    """
    try:
        logger.debug(f"Executing {tool_name} with params: {params}")
        result = tool_func(**params)
        logger.debug(f"{tool_name} result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"{tool_name} execution failed: {e}")
        return {
            "status": "error",
            "error_message": f"{tool_name}実行エラー: {str(e)}",
            "tool_name": tool_name
        }


def get_fallback_action(available_actions: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ツールが全て失敗した場合の安全なアクション
    
    Args:
        available_actions: 利用可能なアクション
        context: ゲーム状況のコンテキスト
    
    Returns:
        フォールバックアクション
    """
    logger.warning("Using fallback action due to tool failures")
    
    # 安全な順序でアクションを選択
    action_priority = ["check", "fold", "call"]
    
    for action in action_priority:
        for available in available_actions:
            if action in available.lower():
                if action == "call":
                    # コール額を抽出
                    import re
                    match = re.search(r"call \((\d+)\)", available)
                    amount = int(match.group(1)) if match else 0
                    return {
                        "action": "call",
                        "amount": amount,
                        "reasoning": "ツール実行エラーのため、安全なコールを選択"
                    }
                else:
                    return {
                        "action": action,
                        "amount": 0,
                        "reasoning": f"ツール実行エラーのため、安全な{action}を選択"
                    }
    
    # 最後の手段
    return {
        "action": "fold",
        "amount": 0,
        "reasoning": "ツール実行エラーのため、フォールドを選択"
    }
