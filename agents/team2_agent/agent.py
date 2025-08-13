from google.adk.agents import Agent, SequentialAgent

# ツールは事前に定義されていると仮定します
# from your_tools import EquityCalculator, PotOddsCalculator, GtoPreflopChartTool, SizingTool

# エージェントの名前定義
AGENT_NAME = "team2_agent"


# -----------------------------------------------------------------------------
# 専門エージェント2: 勝利を計算するエージェント (分析官)
# -----------------------------------------------------------------------------
victory_calculation_agent = Agent(
    name="victory_calculation_agent",
    model="gemini-2.5-flash-lite",
    description="自分の手の勝利確率（エクイティ）を計算することに特化した専門家です。",
    instruction="""あなたはポーカーの確率計算の専門家です。
                与えられた自分の手札と場のカードから、あなたのツールを使って最終的な勝率を計算してください。
                他のことは一切考えず、計算結果の勝率（0.0から1.0の間の数値）のみを返してください。""",
    tools=[
    #     EquityCalculator(),
    ],
)


# -----------------------------------------------------------------------------
# 専門エージェント3: アクションを決定するエージェント (戦略家)
# -----------------------------------------------------------------------------
action_determination_agent = Agent(
    name="action_determination_agent",
    model="gemini-2.5-flash-lite",
    description="勝利確率やゲーム状況に基づいて、最適なポーカーアクションを決定する戦略の専門家です。",
    instruction="""あなたはポーカーの戦略家です。
                あなたには「勝利確率」と「現在のゲーム状況」が与えられます。
                あなたのツール（GTOプリフロップチャート、ポットオッズ計算、ベットサイズ決定）を駆使して、
                現時点で最も合理的と思われるアクション（fold, check, call, raise）と、
                レイズする場合の金額を決定してください。

                あなたの回答は、決定したアクションと金額のみにしてください。
                例: "raise 500" または "call 200" または "fold"
                """,
    tools=[
        # PotOddsCalculator(),
        # GtoPreflopChartTool(),
        # SizingTool(),
    ],
)


# -----------------------------------------------------------------------------
# エージェント1: ルートエージェント (司令塔)
# -----------------------------------------------------------------------------
root_agent = SequentialAgent(
    name=AGENT_NAME,
    description="ポーカーAIの司令塔。各専門エージェントに指示を出し、最終的なアクションを決定・出力します。",
    # 思考と実行を委任するサブエージェントを定義
    sub_agents=[
        victory_calculation_agent,
        action_determination_agent,
        ],
)