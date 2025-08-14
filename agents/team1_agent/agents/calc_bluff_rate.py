from google.adk.agents import Agent

calc_bluff_rate = Agent(
    name="calc_bluff_rate",
    model="gemini-2.5-flash-lite",
    description=("ブラフ率を計算するエージェント"),
    instruction=("あなたはテキサスホールデム・ポーカーのプレイを補佐するエージェントです。"
                "あなたは各対戦相手のブラフ率を計算します。"
                "ブラフ率は、対戦相手のベットがブラフである確率を示します。"
                "100に近いほど対戦相手のベットがブラフである確率が高く、0に近いほど対戦相手のベットがブラフである確率が低くなります。"
                "ベットをしていない対戦相手については、ブラフ率を0にしてください。"
                
                ),
    output_key="bluff_rate_result"
)