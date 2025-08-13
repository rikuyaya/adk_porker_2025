from google.adk.agents import Agent

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
        EquityCalculator(),
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
        PotOddsCalculator(),
        GtoPreflopChartTool(),
        SizingTool(),
    ],
)


# -----------------------------------------------------------------------------
# エージェント1: ルートエージェント (司令塔)
# -----------------------------------------------------------------------------
root_agent = Agent(
    name=AGENT_NAME,
    model="gemini-2.5-flash-lite",
    description="ポーカーAIの司令塔。各専門エージェントに指示を出し、最終的なアクションを決定・出力します。",
    instruction="""あなたはテキサスホールデム・ポーカーAIの司令塔です。
                以下の手順に従って、最終的な意思決定を行ってください。

                1.  まず、`victory_calculation_agent`を呼び出し、現在の勝率を取得します。
                2.  次に、`action_determination_agent`を呼び出し、ステップ1で得た勝率と現在のゲーム状況を伝えて、実行すべきアクションを決定させます。
                3.  最後に、決定されたアクションに基づき、理由付け（Reasoning）を簡潔に記述し、指定されたJSON形式で最終的な回答を作成してください。
                    - 理由付けでは、勝率やポットオッズなどの判断材料となった数値を具体的に含めてください。
                    - 初心者がわかるように専門用語には解説を加えてください。

                最終回答JSONフォーマット:
                {
                "action": "fold|check|call|raise|all_in",
                "amount": <数値>,
                "reasoning": "あなたの決定の理由を簡潔に説明"
                }
                """,
    # ルートエージェント自身は計算ツールを持たず、サブエージェントに委任する
    tools=[],
    # 思考と実行を委任するサブエージェントを定義
    sub_agents=[
        victory_calculation_agent,
        action_determination_agent,
        ],
)