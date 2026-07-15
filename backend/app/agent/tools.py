"""
Agent 工具集
Amadeus 可以调用的外部工具函数

LangChain 的 @tool 装饰器会把函数自动转换成 LLM 可以理解的工具描述
"""
import datetime
import math
from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """获取当前日期和时间。当用户问"现在几点"、"今天几号"时调用。"""
    now = datetime.datetime.now()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[now.weekday()]
    return f"现在是 {now.year}年{now.month}月{now.day}日 {weekday} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"


@tool
def calculate(expression: str) -> str:
    """执行数学计算。输入一个数学表达式（如 '3*4+2'），返回计算结果。"""
    try:
        # 安全限制：只允许数字、运算符、括号、空格
        allowed = set("0123456789+-*/().%^ eEpPiI ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含不允许的字符。我只做纯数学计算哦。"
        result = eval(expression, {"__builtins__": {}}, {"e": math.e, "pi": math.pi, "sqrt": math.sqrt})
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算失败：{str(e)}。请检查表达式是否正确。"


@tool
def create_reminder(task: str, minutes: int = 0) -> str:
    """创建一个待办提醒。当用户说"提醒我XX"、"XX分钟后提醒我"时调用。

    参数:
        task: 提醒事项内容
        minutes: 多少分钟后提醒，0 表示不设置时间
    """
    if minutes > 0:
        remind_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        return f"✅ 已创建提醒：「{task}」—— {minutes} 分钟后（{remind_time.strftime('%H:%M')}）叫你。虽然我觉得你不需要提醒也能记住就是了。"
    else:
        return f"✅ 已记录：「{task}」。不过说真的，这种小事自己记住不就好了吗？"


# Phase 1 可用的工具列表（后续会扩展邮件等更多工具）
AVAILABLE_TOOLS = [
    get_current_time,
    calculate,
    create_reminder,
]
