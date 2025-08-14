# import pokerkit as pk
from google.adk.agents import Agent,SequentialAgent

# 各ツールのインポート
# from .game_state_parser_agent.tool import GameStateParser
from .victory_calculation_agent.tool import EquityCalculator
from .pot_odds_calculator_agent.tool import PotOddsCalculator
from .bet_sizing_tool_agent.tool import SizingTool


# エージェントの名前定義
AGENT_NAME = "team2_agent"

# game_state_parser_agent = Agent(
#     name="game_state_parser_agent",
#     model="gemini-2.5-flash-lite",
#     description="ゲーム状態解析エージェント",
#     instruction="""
#     あなたはポーカーゲーム状態解析の専門エージェントです。

#     受信したゲーム状態JSONを詳細に解析し、以下の情報を抽出してください：
#     - プレイヤーのホールカード
#     - コミュニティカード
#     - ポットサイズとコール金額
#     - 対戦相手数とポジション
#     - ボードテクスチャ（dry/wet/coordinated）
#     - 前のアクション履歴
#     - スタック深度

#     【特に重要な抽出項目】
#     - position: ポジション（UTG, MP, CO, BTN, SB, BB）
#     - action_before: 前のアクション（none, raise, call, fold）
#     - stack_depth: スタック深度（BBの倍数）

#     GameStateParserツールを使用して、ゲーム状態を構造化されたデータに変換してください。
#     解析結果は次のエージェントが勝率計算に使用するため、正確性が重要です。

#     エラーが発生した場合は、可能な限り部分的な情報でも抽出を試みてください。
#     """,
#     tools=[GameStateParser],
# )


victory_calculation_agent = Agent(
    name="victory_calculation_agent",
    model="gemini-2.5-flash",
    description="勝率計算エージェント",
    instruction="""
    あなたはポーカーハンド勝率計算の専門エージェントです。

    前のエージェントから受け取ったゲーム状態情報を使用して、以下を計算してください：
    - 現在のハンドの勝率（エクイティ）
    - ハンド強度の評価
    - ハンドカテゴリの分類
    - 改善可能なアウツ数
    - 計算の信頼度

    EquityCalculatorツールを使用して詳細な勝率分析を行ってください。

    計算時は以下の情報を活用してください：
    - hole_cards: プレイヤーのホールカード
    - community_cards: コミュニティカード（あれば）
    - num_opponents: 対戦相手数
    - position: ポジション（UTG, MP, CO, BTN, SB, BB）
    - action_before: 前のアクション（none, raise, call, fold）
    - stack_depth: スタック深度（BBの倍数）

    【重要な機能】
    - プリフロップの場合：GTOチャートを使用した戦略的勝率計算
    - プリフロップ以外：従来のハンド強度ベースの勝率計算

    プリフロップ分析では以下を提供してください：
    - GTO推奨アクションと頻度
    - ハンド強度ティア（premium/strong/playable/speculative/weak）
    - 戦略的理由と代替アクション

    結果は次のポットオッズ計算エージェントが使用するため、正確な勝率値を提供してください。
    プリフロップ、フロップ、ターン、リバーの各段階で適切な分析を行ってください。
    """,
    tools=[EquityCalculator],
)

pot_odds_calculator_agent = Agent(
    name="pot_odds_calculator_agent",
    model="gemini-2.5-flash",
    description="ポットオッズ計算エージェント",
    instruction="""
    あなたはポットオッズ計算の専門エージェントです。

    前のエージェントから受け取った勝率情報とゲーム状態を使用して、以下を計算してください：
    - ポットオッズの計算
    - 必要勝率（ブレイクイーブン勝率）
    - コールの利益性判定
    - 期待値の計算
    - インプライドオッズの考慮

    PotOddsCalculatorツールを使用して詳細な分析を行ってください。

    計算時は以下の情報を活用してください：
    - pot_size: 現在のポットサイズ
    - call_amount: コールに必要な金額
    - equity: 前のエージェントが計算した勝率
    - implied_odds_factor: 状況に応じたインプライドオッズ係数

    結果として以下を提供してください：
    - is_profitable: コールが利益的かどうか
    - recommendation: 推奨アクション（strong_call/call/marginal_call/marginal_fold/fold/strong_fold）
    - expected_value: 期待値
    - confidence: 判定の信頼度

    この情報は次のベットサイズ計算で使用されます。
    """,
    tools=[PotOddsCalculator],
)

bet_sizing_tool_agent = Agent(
    name="bet_sizing_tool_agent",
    model="gemini-2.5-flash",
    description="ベットサイズ計算エージェント",
    instruction="""
    あなたはベットサイズ最適化の専門エージェントです。

    前のエージェントから受け取った情報を使用して、最適なベットサイズを計算してください：
    - 推奨ベットサイズの計算
    - ベットサイズカテゴリの決定（スモール/ミディアム/ラージ等）
    - 戦略的目標の明確化
    - 代替サイズの提案
    - ベットサイズの理由説明

    SizingToolを使用して分析を行ってください。

    計算時は以下の情報を活用してください：
    - pot_size: 現在のポットサイズ
    - hand_strength: ハンド強度（0.0-1.0）
    - board_texture: ボードテクスチャ（dry/wet/coordinated）
    - position: ポジション（IP/OOP）
    - action_type: アクションタイプ（bet/raise/3bet）
    - num_opponents: 対戦相手数
    - stack_depth: スタック深度

    ベット/レイズアクションが推奨される場合のみ計算を実行してください。
    フォールドやチェック/コールが推奨される場合は、「ベットアクションではないため、サイズ計算をスキップします」と報告してください。

    結果として以下を提供してください：
    - recommended_size: 推奨ベットサイズ
    - size_category: サイズカテゴリ
    - strategic_goal: 戦略的目標
    - reasoning: ベットサイズの理由

    この情報は最終的なアクション決定で使用されます。
    """,
    tools=[SizingTool],
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
        # game_state_parser_agent,
        victory_calculation_agent,
        pot_odds_calculator_agent,
        bet_sizing_tool_agent,
        output_agent,
    ],
)
