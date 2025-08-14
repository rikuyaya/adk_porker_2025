from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import SequentialAgent

# SequentialAgentのモデル名を引数に入れていたのが原因だった


GTO_agent = Agent(
    name="GTO_agent",
    model="gemini-2.5-flash-lite",
    description=("GTOエージェント"),
    instruction=("""あなたはテキサスホルデムのゲーム理論的な最適戦略を適用するエージェントです。


                  あなたは以下のツールを使用して、最善の意思決定を行います。
                  - calc_gto: ゲーム理論的な最適戦略を適用するツール


                  ツールがエラーを吐いた場合は、あなたが世界一のプレイヤーとして代わりに意思決定を行ってください。
                 
                  あなたには以下の情報が与えられます:
                  - あなたの手札（ホールカード）
                  - コミュニティカード（あれば）
                  - 選択可能なアクション
                  - ポットサイズやベット情報
                  - 対戦相手の情報
                 
                  必ず次のJSON形式で回答してください:
                  {
                    "action": "fold|check|call|raise|all_in",
                    "amount": <数値>,
                    "reasoning": "あなたの決定の理由を簡潔に説明"
                  }
                  """

    
    # "あなたはテキサスホールデム・ポーカーのプレイを補佐するエージェントです。"
    #             "あなたはGTO戦略を使用して、最適なアクションを決定します。"
    #             "プレイ状況: {input_information}"
    #             "現在の手札と、コミュニティカードから、calc_gtoを使用して、勝率を計算してください。"
    #             "勝率から最適なアクションを決定してください。"
    #             "アクションは、fold, check, call, raise, all_inのいずれかを指定してください。"
    #             "アクションの理由も簡潔に説明してください。"
                ),
    output_key="GTO_result",
    #tools=[calc_gto]
)

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
                - 現在のプレイ状況からGTO戦略に基づいて考えられた行動
                   {GTO_result}
                   この行動は、GTO戦略に基づいて考えられており、とても論理的な案です。
                   しかし、ブラフといった、対戦相手のミスを利用する様な行動ではありません。
      


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

pipeline_agent = SequentialAgent(
    name="pipeline_agent",
    sub_agents=[GTO_agent, decision_agent], #analyze_agent, 
    description=("Coordinating agents to analyze the situation and make a decision.")
)

root_agent = pipeline_agent