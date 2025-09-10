"""配置文件"""

import os

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 从环境变量读取 API 密钥
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")  # API端点
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # 使用的模型

# 任务分解提示词
TASK_DECOMPOSITION_PROMPT = """
あなたは役立つアシスタントです。与えられたタスクをサブタスクのリストに分解し、必ず日本語で回答してください。
回答は必ず数字で始まる箇条書きの形式で、余計な説明は不要です。

タスク：{task_name}

以下の形式で回答してください：
1. 最初のサブタスク
2. 二番目のサブタスク
3. 三番目のサブタスク
...
""" 