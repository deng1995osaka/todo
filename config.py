"""Configuration management for the Todo application"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import shutil

# ==============================================================================
# Part 1: .env ファイルの読み込み 
# ==============================================================================

# まず、プログラムが開発環境で実行されているか、パッケージ後に実行されているかを判断
if hasattr(sys, '_MEIPASS'):
    # パッケージ環境の場合、The base path is the temporary directory created by PyInstaller
    base_path = sys._MEIPASS
else:
    # 開発環境の場合、The base path is the current project directory
    base_path = os.path.abspath(".")

# --- .env の読み込み ---

env_path = os.path.join(base_path, ".env")
load_dotenv(dotenv_path=env_path)


# ==============================================================================
# Part 2: API キーと設定の読み込み 
# ==============================================================================

# DeepSeek API設定
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# タスク分解プロンプト
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

# ==============================================================================
# Part 3: tasks.json 
# ==============================================================================

def get_persistent_tasks_path():
    """
    永続化tasks.jsonのパスを取得 
   
    """
    # 1. ホームディレクトリ下に隠しプログラム設定フォルダを作成
    app_data_dir = Path.home() / ".TodoApp"
    app_data_dir.mkdir(exist_ok=True)  # フォルダが既に存在する場合は何もしない

    # 2. 読み書きしたいjsonファイルのパスを定義
    persistent_tasks_path = app_data_dir / "tasks.json"

    # 3. 初回実行チェック：このファイルがまだ存在しない場合...
    if not persistent_tasks_path.exists():
              
        # a. パッケージ内部のjsonファイルパスを見つける
        source_template_path = os.path.join(base_path, "tasks.json")
        
        # b. jsonファイルが実際に存在する場合
        if os.path.exists(source_template_path):
        
            shutil.copy2(source_template_path, persistent_tasks_path)
        else:
            # c. jsonファイルすら見つからない場合、空のファイルを作成
            persistent_tasks_path.write_text('{"tasks": []}', encoding="utf-8")

    # 4. この永続的で読み書き可能なパスを返す
    return str(persistent_tasks_path)

# 上記の関数を呼び出し、最終的に使用するtasks.jsonのパスを取得
TASKS_PATH = get_persistent_tasks_path()