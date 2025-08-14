from google.adk.agents import Agent, SequentialAgent

AGENT_NAME = "team1_agent"

analysis_agent = Agent(
    name="analisis_agent",
    model="gemini-2.5-flash-lite",
    description="テキサスホールデムのゲーム状況を分析するエージェント",
    instruction="",
    tools=[analyze_tool],
    output_key="analysis_result",
)

output_agent = Agent(
    name="output_agent",
    model="gemini-2.5-flash-lite",
    description="最終的なアクション決定エージェント",
    instruction=""" 【
    出力形式】
    必ず次のJSON形式で回答してください：
    {
      "action": "fold|check|call|raise|all_in",
      "amount": <数値（ベット/レイズの場合のみ、それ以外は0）>,
      "reasoning": "各エージェントの分析結果を踏まえた決定理由を詳細に説明""
    }""",
    tools=[output_tool],
    output_key="final_action",
)


root_agent = SequentialAgent(
    name=AGENT_NAME,
    sub_agents=[
        analysis_agent,
        output_agent,
    ],
)
