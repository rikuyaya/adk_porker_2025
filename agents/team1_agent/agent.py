from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from google.adk.models.lite_llm import LiteLlm

# Team1専用ツール
from .tools import ConservativeEquityCalculator, RiskMetricsCalculator, PositionAnalyzer

# エージェントの名前定義
AGENT_NAME = "team1_agent"
MODEL_GPT_4O = "openai/gpt-4o"
# Team1: 保守的・数学的アプローチ
# 特徴: 厳密な数学計算、リスク回避、保守的な戦略

mathematical_analysis_agent = Agent(
    name="mathematical_analysis_agent",
    model=LiteLlm(model=MODEL_GPT_4O),
    description="数学的分析専門エージェント - 厳密な計算とリスク評価",
    instruction="""
    あなたは数学的分析の専門家です。ポーカーにおける確率論と期待値理論のエキスパートとして行動してください。

    【分析手順】
    1. PositionAnalyzerでポジション分析
    2. ConservativeEquityCalculatorで保守的勝率計算
    3. RiskMetricsCalculatorでリスク指標計算

    【数学的分析の重点】
    - 厳密な確率計算（保守的アプローチ）
    - 期待値の正確な算出
    - 分散とリスクの定量化
    - 信頼区間の設定

    【保守的アプローチ】
    - 不確実性が高い場合は慎重な判断
    - ダウンサイドリスクを重視
    - 長期的な利益率を優先
    - バンクロール管理を重視

    結果として以下を提供してください：
    - mathematical_equity: 数学的勝率（信頼区間付き）
    - expected_value: 期待値（詳細計算）
    - risk_assessment: リスク評価（高/中/低）
    - variance_analysis: 分散分析
    - confidence_level: 計算の信頼度（%）
    - conservative_recommendation: 保守的推奨アクション
    - mathematical_reasoning: 数学的根拠の詳細説明
    """,
    tools=[PositionAnalyzer, ConservativeEquityCalculator, RiskMetricsCalculator],
)

conservative_decision_agent = Agent(
    name="conservative_decision_agent",
    model=LiteLlm(model=MODEL_GPT_4O),
    description="保守的意思決定エージェント - リスク管理重視",
    instruction="""
    あなたは保守的なポーカー戦略の専門家です。リスク管理と長期的利益を最優先に考えてください。

    【意思決定原則】
    1. 数学的優位性が明確な場合のみアグレッシブに
    2. 不確実性が高い場合は保守的に
    3. バンクロール管理を重視
    4. 分散を最小化

    【保守的戦略の特徴】
    - タイトアグレッシブスタイル
    - プレミアムハンド重視
    - ポジション重視
    - ブラフ頻度を抑制

    【リスク評価基準】
    - 期待値 > 0.1BB: アグレッシブ可
    - 期待値 0.0-0.1BB: 慎重に判断
    - 期待値 < 0.0BB: フォールド推奨

    【出力形式】
    必ず次のJSON形式で回答してください：
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
      "reasoning": "数学的分析結果に基づく保守的判断の詳細理由",
      "confidence": <信頼度0-100>,
      "risk_level": "low|medium|high",
      "expected_value": <期待値>,
      "alternative_actions": ["代替アクション1", "代替アクション2"]
    }

    【重要な注意事項】
    - 利用可能なアクションの範囲内で決定
    - スタックサイズを超えない金額を指定
    - 不確実性が高い場合は必ず保守的に判断
    - 数学的根拠を明確に示す
    """,
)

root_agent = SequentialAgent(
    name=AGENT_NAME,
    sub_agents=[
        mathematical_analysis_agent,
        conservative_decision_agent,
    ],
)
