from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

calc_raise_amount = Agent(
    name="calc_raise_amount",
    model="gemini-2.5-flash-lite",
    description=("Calculates the amount to raise based on the situation."),
    instruction=("あなたはレイズ量を計算します。"
                "あなたはanalyze_agentの結果を参考に、最適なレイズ量を計算します。")
)

decision_agent = Agent(
    name="decision_agent",
    model="gemini-2.5-flash-lite",
    description=("Decides on the best action to take based on the situation."),
    instruction=("""あなたはテキサスホールデム・ポーカーのエキスパートプレイヤーです。

                あなたは、以下の情報を参考に、最適なアクションを決定してください:

      


                  必ず次のJSON形式で回答してください:
                  {
                    "action": "fold|check|call|raise|all_in",
                    "amount": <数値>,
                    "reasoning": "あなたの決定の理由を簡潔に説明"
                  }

                  ルール:
                  - "fold"と"check"の場合: amountは0にしてください
                  - "call"の場合: コールに必要な正確な金額を指定してください
                  - "raise"の場合: レイズ後の合計金額を指定してください
                  - "all_in"の場合: あなたの残りチップ全額を指定してください

                  初心者がわかるように専門用語には解説を加えてください"""
                  ),
    tools=[AgentTool(agent=calc_raise_amount)]
)

                # - 現在のプレイ状況からGTO戦略に基づいて考えられた行動
                #   {GTO_result}
                #   この行動は、GTO戦略に基づいて考えられており、とても論理的な案です。
                #   しかし、ブラフといった、対戦相手のミスを利用する様な行動ではありません。

                # - 各対戦相手のコンフリクト率
                #   {confidence_result}
                #   コンフリクト率は、対戦相手が強気なプレイヤーであるか、弱気なプレイヤーであるかを0~100の整数で示します。
                #   100に近いほど対戦相手が強気なプレイヤーである確率が高く、0に近いほど対戦相手が弱気なプレイヤーである確率が高くなります。
                #   例えば、コンフリクト率が低い対戦相手に対しては、ブラフが通用し易いと考えられます。
                #   対して、コンフリクト率が高い対戦相手に対しては、ブラフが通用し難いと考えられます。

                # - 各対戦相手のブラフ率
                #   {bluff_rate_result}
                #   ブラフ率は、各対戦相手のベットがブラフである確率を示します。
                #   100に近いほど対戦相手のベットがブラフである確率が高く、0に近いほど対戦相手のベットがブラフである確率が低くなります。
                #   例えば、ブラフ率が低い対戦相手に対しては、ブラフが通用し難いと考えられます。
                #   対して、ブラフ率が高い対戦相手に対しては、ブラフが通用し易いと考えられます。