from google.adk.agent import Agent
from tools.calc_gto import calc_gto

MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"

GTO_agent = Agent(
    model=MODEL_GEMINI_2_5_FLASH,
    description="GTO(Game Theory Optimal)戦略を適用するエージェント",
    instruction="""あなたはテキサスホルデムのゲーム理論的な最適戦略を適用するエージェントです。
                  あなたには以下の情報が与えられます:
                  - あなたの手札（ホールカード）
                  - コミュニティカード（あれば）
                  - 選択可能なアクション
                  - ポットサイズやベット情報
                  - 対戦相手の情報""",
    #tools=[calc_gto],
)