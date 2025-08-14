from google.adk.agents import Agent

calc_raise_amount = Agent(
    name="calc_raise_amount",
    model="gemini-2.5-flash-lite",
    description=("Calculates the amount to raise based on the situation."),
    instruction=("あなたはレイズ量を計算します。"
                "あなたはanalyze_agentの結果を参考に、最適なレイズ量を計算します。")
)