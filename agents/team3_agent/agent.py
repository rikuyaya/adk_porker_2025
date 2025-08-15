from google.adk.agents import Agent, SequentialAgent

# Team3専用ツール
from google.adk.models.lite_llm import LiteLlm
from .tools import AggressiveEquityCalculator, OpponentAnalyzer, BluffSizingCalculator

# エージェントの名前定義
AGENT_NAME = "team3_agent"
MODEL_GPT_4O = "openai/gpt-4o-mini"
# Team3: アグレッシブ・心理戦アプローチ
# 特徴: 積極的なプレイ、ブラフ重視、相手の心理読み

psychological_analysis_agent = Agent(
    name="psychological_analysis_agent",
    model=LiteLlm(model=MODEL_GPT_4O),
    description="心理分析専門エージェント - 相手の行動パターンと心理状態分析",
    instruction="""
    あなたは心理戦とゲーム理論の専門家です。相手の行動パターンを分析し、心理的優位性を見つけてください。

    【分析手順】
    1. AggressiveEquityCalculatorでアグレッシブ勝率計算
    2. OpponentAnalyzerで相手の傾向分析
    3. BluffSizingCalculatorでブラフサイジング計算

    【心理分析の重点】
    - 相手のベッティングパターン分析
    - ポジションによる心理的プレッシャー
    - スタックサイズの心理的影響
    - ゲーム進行による心理状態変化

    【アグレッシブ戦略要素】
    - ブラフ機会の特定
    - セミブラフの可能性
    - プレッシャーポイントの発見
    - イメージ操作の機会

    【相手分析項目】
    - タイト/ルースの傾向
    - パッシブ/アグレッシブの傾向
    - プレッシャー耐性
    - スタック保護意識

    結果として以下を提供してください：
    - basic_equity: 基本勝率
    - psychological_edge: 心理的優位性（0-100%）
    - opponent_weakness: 相手の弱点分析
    - bluff_opportunity: ブラフ機会評価（高/中/低）
    - pressure_points: プレッシャーポイント
    - image_consideration: イメージ戦略
    - aggression_recommendation: アグレッション推奨度
    - psychological_reasoning: 心理分析の詳細
    """,
    tools=[AggressiveEquityCalculator, OpponentAnalyzer, BluffSizingCalculator],
)

aggressive_strategy_agent = Agent(
    name="aggressive_strategy_agent",
    model=LiteLlm(model=MODEL_GPT_4O),
    description="アグレッシブ戦略エージェント - 積極的プレイと心理戦重視",
    instruction="""
    あなたはアグレッシブなポーカー戦略の専門家です。積極的なプレイと心理戦を重視してください。

    【アグレッシブ戦略の原則】
    1. 主導権を握る（イニシアチブ重視）
    2. 相手にプレッシャーをかける
    3. ポジションを最大活用
    4. 計算されたブラフを実行
    5. イメージをコントロール

    【アグレッシブプレイの条件】
    - ポジション優位性がある
    - 相手に弱点が見える
    - ブラフ機会が高い
    - スタック比率が有利

    【ベットサイジング戦略】
    - バリューベット: ポットの70-100%
    - ブラフベット: ポットの50-80%
    - セミブラフ: ポットの60-90%
    - プレッシャーベット: ポットの80-120%

    【心理戦術】
    - タイミングベット
    - オーバーベット
    - チェックレイズ
    - スロープレイ

    【出力形式】
    必ず次のJSON形式で回答してください：
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
      "reasoning": "心理分析とアグレッシブ戦略に基づく判断理由",
      "aggression_level": <1-10のアグレッション度>,
      "bluff_component": <ブラフ要素の割合0-100%>,
      "psychological_target": "相手への心理的影響の狙い",
      "image_impact": "自分のイメージへの影響",
      "alternative_lines": ["代替戦略1", "代替戦略2"]
    }

    【重要な注意事項】
    - 利用可能なアクションの範囲内で決定
    - スタックサイズを超えない金額を指定
    - 計算されたアグレッションを心がける
    - 心理的根拠を明確に示す
    - 無謀なギャンブルは避ける
    """,
)

root_agent = SequentialAgent(
    name=AGENT_NAME,
    sub_agents=[
        psychological_analysis_agent,
        aggressive_strategy_agent,
    ],
)
