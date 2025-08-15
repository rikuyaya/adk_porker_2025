import json
from typing import Dict, Any

# In a real ADK environment, these would be imported from google.adk
from google.adk.tools import ToolContext, FunctionTool


def decide_bet_size(state: str, mix: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    プリフロップのベットサイズを決定する。
    現在の実装は、オープンレイズのシナリオに焦点を当てています。
    """
    # JSON文字列をパース
    state = json.loads(state)
    mix = json.loads(mix)

    # ビッグブラインドを推定（実際の入力にはないので、デフォルト値を使用）
    big_blind = state.get("big_blind", 20)  # デフォルトで20と仮定
    if not big_blind or big_blind == 0:
        # ビッグブラインドの情報なしにはサイズを決定できない
        return {"raise_amount": 0}

    # 'mix' (RangeProviderから) には、推奨されるオープンサイズがBB単位で含まれている
    open_size_bb = mix.get("open_size_bb")

    amount = 0
    if open_size_bb is not None:
        amount = open_size_bb * big_blind

    # 3ベットのようなより複雑なシナリオでは、ここに追加のロジックが必要になる。
    # 例:
    # actions = state.get("actions", [])
    # is_raised_before = any(a.get('action') == 'raise' for a in actions)
    # if is_raised_before:
    #     last_bet = state.get("to_call", 0)
    #     amount = 3 * last_bet

    # チップは整数であるため、金額を丸めて整数で返す
    return {"raise_amount": int(round(amount))}

SizingTool = FunctionTool(func=decide_bet_size)