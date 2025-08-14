# # import pokerkit as pk
# from google.adk.agents import Agent,SequentialAgent

# # 各ツールのインポート
# # from .game_state_parser_agent.tool import GameStateParser
# from .victory_calculation_agent.tool import EquityCalculator
# from .pot_odds_calculator_agent.tool import PotOddsCalculator
# from .victory_calculation_agent.position_tool import PositionCalculator




# # エージェントの名前定義
# AGENT_NAME = "team2_agent"

# victory_calculation_agent = Agent(
#     name="victory_calculation_agent",
#     model="gemini-2.5-flash",
#     description="勝率計算エージェント",
#     instruction="""
#     あなたは勝率計算の専門エージェントです。
#     まずは必ずポジションを計算してください。！！！！！！！！
#     必ず、PositionCalculatorを実行してから、EquityCalculatorを実行してください。


#     前のエージェントから受け取った情報を使用して、勝率を計算してください：
#     - ホールカード
#     - コミュニティカード
#     - 対戦相手数
#     - ポジション

#     計算時は以下の情報を活用してください：
#     - ホールカードとコミュニティカードからハンドの強さを評価
#     - ポジションと対戦相手数からハンドの強さを補正
#     - ハンドの強さから勝率を計算

#     結果として以下を提供してください：
#     - hand_strength: ハンド強さ（0.0-1.0）
#     - equity: 勝率（0.0-1.0）
#     - hand_category: ハンドカテゴリ（例えば、premium、medium、low等）
#     - outs: アウツの数
#     - reasoning: 勝率計算の理由
#     """,
#     tools=[EquityCalculator,PositionCalculator],
# )
# pot_odds_calculator_agent = Agent(
#     name="pot_odds_calculator_agent",
#     model="gemini-2.5-flash",
#     description="ポットオッズ計算エージェント",
#     instruction="""
#     あなたはポットオッズ計算の専門エージェントです。

#     前のエージェントから受け取った情報を使用して、ポットオッズを計算してください：


#     結果として以下を提供してください：
#     - 前のエージェントからの出力
#     expected_value, required_equity, reverse_expected_value, implied_multiplier
#     """,
#     tools=[PotOddsCalculator],
# )

# output_agent = Agent(
#     name="output_agent",
#     model="gemini-2.5-flash",
#     description="最終的なアクション決定エージェント",
#     instruction="""
#     あなたは最終的なポーカーアクション決定の専門エージェントです。

#     前の全てのエージェントから受け取った分析結果を総合的に評価し、最適なアクションを決定してください：

#     【考慮すべき情報】
#     1. ゲーム状態解析結果：
#        - ホールカード、コミュニティカード
#        - ポットサイズ、コール金額
#        - ポジション、対戦相手数
#        - 利用可能なアクション

#     2. 勝率計算結果：
#        - ハンドエクイティ
#        - ハンド強度とカテゴリ
#        - 改善可能性（アウツ）
#        - GTO分析結果（プリフロップの場合）

#     3. ポットオッズ分析結果：
#        - コールの利益性
#        - 期待値
#        - 推奨アクション（strong_call/call/fold等）

#     4. ベットサイズ計算結果（ベット/レイズの場合）：
#        - 推奨ベットサイズ
#        - 戦略的目標

#     【決定プロセス】
#     1. 利用可能なアクションを確認
#     2. 各分析結果の整合性をチェック
#     3. 最も論理的で利益的なアクションを選択
#     4. ベット/レイズの場合は適切な金額を決定

#     【出力形式】
#     必ず次のJSON形式で回答してください：
#     {
#       "action": "fold|check|call|raise|all_in",
#       "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
#       "reasoning": "各エージェントの分析結果を踏まえた決定理由を詳細に説明"
#     }

#     【重要な注意事項】
#     - 利用可能なアクションの範囲内で決定してください
#     - ベット/レイズの場合は、スタックサイズを超えない金額を指定してください
#     - 分析結果が矛盾する場合は、より信頼性の高い情報を優先してください
#     - 必ずJSON形式で回答し、他の形式は使用しないでください
#     """,
# )


# root_agent = SequentialAgent(
#     name=AGENT_NAME,

#     sub_agents=[
#         victory_calculation_agent,
#         pot_odds_calculator_agent,
#         output_agent,
#     ],
# )


# import pokerkit as pk
from google.adk.agents import Agent,SequentialAgent

# 各ツールのインポート
# from .game_state_parser_agent.tool import GameStateParser
from .victory_calculation_agent.tool import EquityCalculator
from .pot_odds_calculator_agent.tool import PotOddsCalculator
from .victory_calculation_agent.position_tool import PositionCalculator




# エージェントの名前定義
AGENT_NAME = "team2_agent"

victory_calculation_agent = Agent(
    name="victory_calculation_agent",
    model="gemini-2.5-flash",
    description="勝率計算エージェント",
    instruction="""

    あなたは勝率計算の専門エージェントです。
    必ずPositionCalculatorを実行してから、EquityCalculatorを実行し、PotOddsCalculatorを実行してください。
    この手順を守りましょう

    結果として以下を提供してください：
    - hand_strength: ハンド強さ（0.0-1.0）
    - equity: 勝率（0.0-1.0）
    - hand_category: ハンドカテゴリ（例えば、premium、medium、low等）
    - outs: アウツの数
    - reasoning: 勝率計算の理由
    - 相手の持ち点(例id:1 chips: 970,id:2 chips: 970,id:3 chips: 950.....)
    - ポットサイズ
    - expected_value: 期待値
    - required_equity: 必要勝率
    - reverse_expected_value: リバースインプライド期待値
    - implied_multiplier: インプライド倍率
    - pot_odds: ポットオッズ
    - pot_odds_reasoning: ポットオッズ計算の理由
    - action: 推奨アクション

    """,
    tools=[EquityCalculator,PositionCalculator,PotOddsCalculator],
)

output_agent = Agent(
    name="output_agent",
    model="gemini-2.5-flash",
    description="最終的なアクション決定エージェント",
    instruction="""
    あなたは最終的なポーカーアクション決定の専門エージェントです。

    前の全てのエージェントから受け取った分析結果を総合的に評価し、最適なアクションを決定してください：

    【考慮すべき情報】
    1. ゲーム状態解析結果：
       - ホールカード、コミュニティカード
       - ポットサイズ、コール金額
       - ポジション、対戦相手数
       - 利用可能なアクション

    2. 勝率計算結果：
       - ハンドエクイティ
       - ハンド強度とカテゴリ
       - 改善可能性（アウツ）
       - GTO分析結果（プリフロップの場合）

    3. ポットオッズ分析結果：
       - コールの利益性
       - 期待値
       - 推奨アクション（strong_call/call/fold等）

    4. ベットサイズ計算結果（ベット/レイズの場合）：
       - 推奨ベットサイズ
       - 戦略的目標

    【決定プロセス】
    1. 利用可能なアクションを確認
    2. 各分析結果の整合性をチェック
    3. 最も論理的で利益的なアクションを選択
    4. ベット/レイズの場合は適切な金額を決定

    【出力形式】
    必ず次のJSON形式で回答してください：
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
      "reasoning": "各エージェントの分析結果を踏まえた決定理由を詳細に説明"
    }

    【重要な注意事項】
    - 利用可能なアクションの範囲内で決定してください
    - ベット/レイズの場合は、スタックサイズを超えない金額を指定してください
    - 分析結果が矛盾する場合は、より信頼性の高い情報を優先してください
    - 必ずJSON形式で回答し、他の形式は使用しないでください
    """,
)


root_agent = SequentialAgent(
    name=AGENT_NAME,

    sub_agents=[
        victory_calculation_agent,
        output_agent,
    ],
)

