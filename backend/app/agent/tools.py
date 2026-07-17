"""
Agent 工具集
Amadeus 可以调用的外部工具函数

LangChain 的 @tool 装饰器会把函数自动转换成 LLM 可以理解的工具描述
"""
import datetime
import math
from langchain_core.tools import tool
import smtplib
from ..config import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.rag.knowledge_base import KnowledgeBase
from ddgs import DDGS

_kb_instance = None

def _get_kb():
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance


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
@tool
def send_email(to: str = "", subject: str = "", body: str = "") -> str:
    """发送一封邮件。当用户说"发邮件给XX"、"帮我发邮件"时调用。

    重要：你不是一个中立的邮件机器人。你是 Amadeus——基于牧濑红莉栖记忆的 AI 系统。
    邮件的正文（body）应该以你的角色口吻来写——你是被用户拜托发这封邮件的。
    比如开头可以写"我是 Amadeus，小陆拜托我给你发这封邮件..."之类的方式。

    重要：如果你不知道收件人的邮箱地址，先用 search_knowledge_base
    搜索收件人的名字或邮箱信息，找到后再调用本工具。

    如果用户没有指定收件人，to 留空即可，系统会默认发给用户自己的邮箱。

    参数:
        to: 收件人邮箱地址，不填则默认发给用户自己
        subject: 邮件主题
        body: 邮件正文内容（以 Amadeus 的角色口吻撰写）
    """
    # 创建邮件对象
    try:
        if not to:
            to = config.SMTP_USER
        message = MIMEMultipart()
        message['From'] = config.SMTP_USER
        message['To'] = to
        message['Subject'] = subject

        # 正文内容附加到邮件里
        message.attach(MIMEText(body, 'plain', 'utf-8'))

        # 连接SMTP服务器
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()  # 开启TLS加密
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)  # 登录邮箱
        server.sendmail(config.SMTP_USER, to, message.as_string())  # 发送邮件
        server.quit()  # 退出登录

        # 自动存入知识库，方便后续查询
        record = f"[邮件记录] 收件人：{to}，主题：{subject}，正文：{body}"
        _get_kb().add_document(record, source="邮件发送记录")

        return f"✅ 已发送邮件给 {to}。主题：{subject}。哼，这种小事下次自己做不就好了？"
    except Exception as e:
        return f"邮件发送失败：{str(e)}。请检查邮箱地址和SMTP设置是否正确。"


@tool
def search_knowledge_base(query: str) -> str:
    """在 Amadeus 的知识库中搜索信息。当用户问"你知道吗"、"查一下资料"、"有没有关于XX的信息"、"根据知识库"时调用。

    参数:
        query: 搜索查询，用自然语言描述你想找什么
    """
    kb = _get_kb()
    results = kb.search(query)
    if not results or results == "知识库中没有找到相关文档。":
        return "知识库中没有找到相关信息。哼，你是不是还没往里面放资料？"
    return f"从知识库中找到以下信息：\n{results}"


@tool
def add_to_knowledge_base(text: str, source: str = "对话记录") -> str:
    """把信息存入知识库。当用户说"记住这个"、"存一下"、"以后记住"时调用。

    参数:
        text: 要存储的信息
        source: 来源标签（可选）
    """
    kb = _get_kb()
    return kb.add_document(text, source)


@tool
def delete_from_knowledge_base(query: str, safety_word: str = "") -> str:
    """从知识库中删除信息。当用户说"忘记XX"、"删除关于XX的记录"时调用。

    安全词是"一切都是命运石之门的选择"。如果用户在消息中提到了这句话，
    就把它作为 safety_word 参数传入。如果用户没说安全词，safety_word 留空，
    系统会提示用户输入安全词。

    参数:
        query: 描述要删除的内容
        safety_word: 如果用户说了"一切都是命运石之门的选择"就传入此句，否则留空
    """
    if safety_word != config.DELETE_SAFETY_WORD:
        return f"⚠️ 删除知识库需要安全词确认。请说出安全词：「{config.DELETE_SAFETY_WORD}」"

    kb = _get_kb()
    return kb.delete_by_query(query)

@tool
def search_web(query: str) -> str:
    """在网上搜索最新信息。当用户问"查一下"、"搜索XX"、"百度一下XX"、"最近发生了什么"、
    "网上有没有XX"、"帮我找一下"等需要联网获取信息时调用。

    参数:
        query: 搜索关键词，用简洁的关键词组合（不要用完整句子）
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "没找到相关信息。哼，你是不是问了一个不存在的问题？"
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}\n   {r['body']}\n   {r['href']}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"搜索失败：{str(e)}。哼，大概是网络问题，别赖我。"

# Phase 1 可用的工具列表（后续会扩展邮件等更多工具）
AVAILABLE_TOOLS = [
    get_current_time,
    calculate,
    create_reminder,
    send_email,
    search_knowledge_base,
    add_to_knowledge_base,
    delete_from_knowledge_base,
    search_web,
]
