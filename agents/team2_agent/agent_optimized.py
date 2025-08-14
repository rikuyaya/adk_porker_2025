from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import FunctionTool, ToolContext
from typing import Dict, Any, List, Optional

# 各ツールのインポート
from .game_state_parser_agent.tool import GameStateParser
from .victory_calculation_agent.tool import EquityCalculator
from .pot_odds_calculator_agent.tool import PotOddsCalculator
from .bet_sizing_tool_agent.tool import SizingTool

# エージェントの名前定義
AGENT_NAME = "team2_agent_optimized"

# 最適化版：統合エージェント（LLM呼び出しを削減）
integrated_analysis_agent = Agent(
    name="integrated_analysis_agent",
    model="gemini-2.5-flash",
    description="統合分析エージェント（高速版）",
    instruction="""
    あなたはポーカー戦略の統合分析エージェントです。
    
    以下のツールを順次使用して、効率的に分析を行ってください：
    1. GameStateParser: ゲーム状態の解析
    2. EquityCalculator: 勝率計算
    3. PotOddsCalculator: ポットオッズ計算
    4. SizingTool: ベットサイズ計算（必要な場合のみ）
    
    各ツールの結果を統合し、最終的なアクション決定を行ってください。
    
    【重要な最適化】
    - 不要なベットサイズ計算はスキップ（フォールド/コールの場合）
    - エラーが発生した場合は適切なフォールバック処理
    - 結果は必ずJSON形式で返す
    
    【出力形式】
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ）>,
      "reasoning": "決定理由",
      "analysis_summary": "各ツールの分析結果の要約"
    }
    """,
    tools=[GameStateParser, EquityCalculator, PotOddsCalculator, SizingTool],
)

# 最適化版：シーケンシャルエージェント（エージェント数を削減）
root_agent_optimized = SequentialAgent(
    name=AGENT_NAME,
    sub_agents=[integrated_analysis_agent],
)

# 高速版の処理関数
def process_poker_decision_fast(game_state_json: str) -> Dict[str, Any]:
    """
    高速版のポーカー決定処理
    
    Args:
        game_state_json: ゲーム状態のJSON文字列
    
    Returns:
        Dict[str, Any]: 決定結果
    """
    try:
        # 統合エージェントで一度に処理
        result = root_agent_optimized.run(game_state_json)
        
        # 結果の形式を統一
        if isinstance(result, dict) and "action" in result:
            return result
        else:
            # 結果が期待される形式でない場合のフォールバック
            return {
                "action": "fold",
                "amount": 0,
                "reasoning": "分析エラーのためフォールド",
                "analysis_summary": "エラーが発生したため安全なアクションを選択"
            }
            
    except Exception as e:
        return {
            "action": "fold",
            "amount": 0,
            "reasoning": f"処理エラー: {str(e)}",
            "analysis_summary": "エラーが発生したためフォールド"
        }
